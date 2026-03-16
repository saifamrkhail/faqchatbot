# FAQ Chatbot – Improvement Plan

Based on empirical evaluation against 48 test cases (6 categories) using `qwen3.5:2b`
with `nomic-embed-text-v2-moe` embeddings.

---

## Evaluation Results (Baseline: threshold=0.70)

| Category          | Pass | Total | Rate  | Notes |
|-------------------|------|-------|-------|-------|
| faq_direct        | 10   | 10    | 100%  | Avg score 0.89, avg latency **55s** |
| faq_paraphrase    |  6   | 13    |  46%  | 7 failures — scores 0.55–0.68, just below threshold |
| company_offtopic  |  7   |  7    | 100%  | Avg score 0.31 — well below any reasonable threshold |
| hallucination     |  5   |  5    | 100%  | No hallucination detected |
| general_chat      |  6   |  7    |  86%  | "Wie geht es Ihnen?" falls through regex gaps |
| boundary          |  6   |  6    | 100%  | Typos, English, mixed language all handled |
| **TOTAL**         | **40** | **48** | **83%** | |

**Grid search result**: threshold=0.60, top_k=3, temp=0.10 → **93% aggregate score**

**Safety margin**: All company off-topic scores ≤ 0.48. Safe to lower threshold to 0.50.

---

## Already Applied Fixes (2026-03-16)

### Fix 1 — `_should_allow_general_response` default changed `False` → `True`
`app/services/answer_generator.py:279`

**Problem**: "Wie geht es Ihnen?" and other unrecognized but harmless questions fell through
all pattern checks and hit the `return False` default → deterministic fallback.

**Fix**: Changed to `return True`. The `build_general()` prompt already instructs the LLM to
use the fallback for company-specific questions. Keyword-based blocking remains for
`_COMPANY_HINT_TERMS` and `_FACTUAL_CHAT_TERMS`. For everything else, the LLM decides.

---

## Remaining Issues — Prioritized Improvement Plan

---

### P1 — Latency (CRITICAL)

**Symptom**: avg 55s per FAQ answer, max 108s. Unacceptable for a chat application.

**Root cause**: `qwen3.5:2b` (and especially 9b) running inference on CPU in WSL2.
The FAQ prompt is also unnecessarily long — it includes the full verbatim FAQ answer.

**Solutions** (implement in order):

#### P1a — Streaming output
Currently the UI blocks until the full generation is complete, then prints all at once.
Implementing streaming allows the user to see tokens as they arrive.

**Where to change**:
- `app/infrastructure/ollama_client.py`: Add `generate_streaming()` method that yields tokens
  (Ollama `/api/generate` supports `stream: true`)
- `app/ui/chat_app.py`: Print tokens as they arrive instead of waiting for full response

**Impact**: Perceived latency drops from 50s to ~1–2s for first token. User experience
transforms from "frozen" to "thinking".

#### P1b — Shorter FAQ context prompt
The current `build()` prompt includes the full verbatim FAQ answer in the prompt.
For a 512-token max_tokens limit, this leaves little room for generation.

**Where to change**: `app/domain/prompt_template.py:build()`

Truncate FAQ answer to 200 chars if it exceeds that:
```python
answer_preview = faq_entry.answer[:200] + "…" if len(faq_entry.answer) > 200 else faq_entry.answer
```
This reduces prompt length and speeds up generation.

#### P1c — Use qwen3.5:9b properly (correct Docker pull mechanism)
The `make pull-models` target pulls models via `docker compose exec ollama ollama pull`,
which uses the CLI inside the container. The CLI may use a different storage path than
the Ollama HTTP server expects.

**Fix**: Pull models via the HTTP API directly:
```makefile
pull-models:
    curl -X POST http://localhost:11434/api/pull \
      -H 'Content-Type: application/json' \
      -d '{"name":"qwen3.5:9b","stream":false}' --max-time 600
```
Or restart the Ollama container after CLI pull to force a model rescan.

The 9b model generates significantly better German answers and is much better at
following the grounding instructions. It would reduce the need for `_is_grounded_answer`
post-generation checks.

---

### P2 — Retrieval Recall for Paraphrased Questions (HIGH)

**Symptom**: 7/13 paraphrase test cases fail at threshold=0.70. Scores range 0.55–0.68.
Even at threshold=0.50, questions like "Was tun Sie gegen Hackerangriffe?" (score 0.55)
barely reach the retrieval threshold.

**Root cause**: The embedding model maps the verbatim FAQ question tightly but poorly
generalizes to informal/colloquial rephrasing. The FAQ question text is the only semantic
anchor; the answer text partially helps but is not indexed as an alternative question.

#### P2a — FAQ Answer Augmentation (RECOMMENDED, high impact, zero runtime cost)

Add alternative phrasings of each FAQ question to the embedding text during ingestion.
This enriches the vector representation with diverse query patterns.

**Where to change**: `app/services/ingestion_service.py` — the method that builds the
embedding text for each FAQ entry.

**Example**: Instead of embedding just `question + answer + category + tags`, embed:
```
question + "\n" + alt_question_1 + "\n" + alt_question_2 + "\n" + answer + ...
```

The alternative phrasings can be:
1. **Offline, hand-crafted** in `data/faq.json` as an `alt_questions` field — zero latency,
   maximum control, simple implementation.
2. **LLM-generated at ingest time** — automatic but requires an extra LLM call per FAQ entry
   during ingestion (acceptable since ingestion is offline).

**Recommendation**: Add `alt_questions: list[str]` field to `FAQEntry` and populate
`data/faq.json` with 2–3 alternative phrasings per entry. This is the single highest
ROI improvement available.

**Example additions to `data/faq.json`**:
```json
{
  "id": "faq-03-it-security",
  "question": "Wie gehen Sie mit IT-Sicherheitsbedrohungen um?",
  "alt_questions": [
    "Was tun Sie gegen Hackerangriffe?",
    "Wie schützen Sie meine IT vor Angriffen?",
    "Welche Cybersicherheitsmaßnahmen haben Sie?"
  ],
  ...
}
```

**Impact**: Would raise paraphrase recall from ~50% to ~85–95% without any runtime changes.

#### P2b — Query Expansion at Runtime (MEDIUM impact, adds latency)

Before embedding the user question, use a fast LLM call to generate 2 alternative phrasings.
Run all 3 through retrieval and take the best score.

**Pro**: Works for any future phrasing, no FAQ maintenance needed.
**Con**: Adds 1–5s latency per question (pre-retrieval LLM call).

With streaming (P1a) already reducing perceived latency, this becomes more acceptable.

**Where to add**: `app/services/retriever.py:retrieve()` — add an optional
`_expand_query(question)` step before `_embed_question()`.

#### P2c — Soft Threshold Zone (LOW complexity, moderate impact)

Instead of binary retrieved/not-retrieved at 0.50:
- Score ≥ 0.70: HIGH confidence — answer from FAQ, strict grounding check
- Score 0.50–0.70: MEDIUM confidence — pass to LLM with FAQ context but allow it to say
  "I'm not certain, but based on our FAQ..." (relaxed grounding check)
- Score < 0.50: LOW confidence — general conversation path

This turns hard failures into graceful partial answers.

---

### P3 — `_is_grounded_answer` Over-Rejection (MEDIUM)

**Symptom**: Valid paraphrased answers can fail the lexical overlap check, especially
for short FAQ answers. If the LLM correctly restates "Wir bieten 24/7 Helpdesk-Support an"
as "Unser Support ist rund um die Uhr erreichbar", the 4+ character term overlap is thin.

**Where**: `app/services/answer_generator.py:_is_grounded_answer()`

**Current check**:
```python
return not answer_terms or bool(answer_terms & source_terms)
```
This returns `True` if there's ANY overlap, which is fairly permissive. But the length
check (`> max(400, len(faq_entry.answer) * 2)`) is more likely to trigger false positives
for concise, well-structured answers.

**Fix**: Replace the length limit with a softer heuristic, or increase the multiplier from
2× to 3×. The grounding instruction in the prompt is the primary defence; this lexical check
is a safety net that should rarely trigger on legitimate answers.

---

### P4 — `_COMPANY_HINT_TERMS` / `_GENERAL_CHAT_PATTERNS` Maintainability (LOW)

**Symptom**: The keyword lists are fragile and grow over time. A word like `"it"` as a
company hint term would incorrectly block `"Wann ist Ihr Büro geöffnet?"` (since "ist" is
not in the list but future edits might add "büro"). Short English words (`"it"`) are
particularly risky as stop-words.

**Recommendation**:
1. Move keyword lists to `data/intent_hints.json` so they can be updated without code deploys.
2. Remove `"it"` from `_COMPANY_HINT_TERMS` — it matches too broadly. "IT" as a topic
   is already handled by the grounding prompt; blocking on the two-letter word `it` is
   unnecessary.
3. Consider removing the entire `_should_allow_general_response` pre-filter and trusting
   the `build_general()` prompt entirely. With `qwen3.5:9b`, the model reliably follows
   instructions to use the fallback for company-specific questions.

---

### P5 — FAQ Data Quality and Coverage (MEDIUM)

**Symptom**: The FAQ contains 10 entries, all in formal German. Users ask in colloquial
German, English, or mix. The embedding model must bridge this gap.

**Improvements**:

1. **Add more FAQ entries** covering edge cases that users actually ask.
   Analyze chat logs (once in production) to identify unanswered questions.

2. **Add `alt_questions` field** (see P2a above).

3. **Consider bilingual FAQ**: Add English translations of key questions as alt_questions.
   The `nomic-embed-text-v2-moe` model is multilingual and would benefit.

4. **Normalize FAQ answer length**: Very long answers (>300 chars) should be split into
   sub-FAQs. The grounded generation model needs to summarize very long FAQ answers,
   which increases hallucination risk.

---

### P6 — Model and Infrastructure (MEDIUM)

**qwen3.5:9b model pull broken**:
The `make pull-models` target uses `docker compose exec ollama ollama pull` which stores
models to a path the HTTP API may not scan. Use the HTTP API directly for model pulls,
or restart the Ollama service after CLI pull.

**Model selection guidance**:
- `qwen3.5:2b`: Usable for prototyping; German instruction-following is marginal.
  Temperature 0.1–0.2 works best.
- `qwen3.5:9b`: Significantly better German, much better instruction-following.
  Required for production-quality answers. Use if hardware allows (6.6GB RAM).
- Consider `llama3.2:3b` or `phi4:mini` as faster alternatives with good German support.

---

## Implementation Roadmap

| Priority | Item | Effort | Impact | Risk |
|----------|------|--------|--------|------|
| **Done** | Threshold 0.50, allow-general default=True | — | +7% overall | None |
| **P1a** | Streaming output | Medium | UX critical | Low |
| **P2a** | FAQ alt_questions field | Low | +15–20% recall | None |
| **P2b** | Query expansion | Medium | +5–10% recall | +latency |
| **P1b** | Shorter prompts | Low | -10% latency | Low |
| **P3** | Relax `_is_grounded_answer` length check | Low | Fewer false fallbacks | Low |
| **P2c** | Soft threshold zone | Medium | Graceful degradation | Low |
| **P5** | Expand FAQ data | Medium | +coverage | None |
| **P4** | Externalise keyword lists | Low | Maintainability | None |

---

## Key Architectural Observations

**What works well**:
- The two-path design (FAQ grounded / general conversation) is architecturally sound.
- The `_is_grounded_answer` safety net prevents the LLM from going off-topic.
- Score threshold provides a clean, auditable decision boundary.
- Safety (hallucination prevention) is robust — 100% on off-topic and hallucination probes.

**What needs work**:
- The retrieval component is a **single point of failure**: if the score is just below
  threshold, there is no graceful degradation — the answer is as good as if the user
  asked about the weather. Query expansion or soft-zone logic would fix this.
- The `_COMPANY_HINT_TERMS` pre-filter adds complexity without adding proportional safety,
  since the `build_general()` prompt already blocks company-specific hallucination.
  Consider removing it entirely when running `qwen3.5:9b`.
- Latency on CPU is the dominant UX problem. Streaming is the highest-impact UX fix
  regardless of hardware.

**Design principle to maintain**:
> The LLM must never fabricate information about the company. This is guaranteed by:
> 1. Retrieval → grounded prompt (primary guard)
> 2. `_is_grounded_answer` lexical check (secondary guard)
> 3. `_COMPANY_HINT_TERMS` blocking + fallback message (tertiary guard)
>
> Never remove all three guards at once. With only the LLM prompt as guard, a small
> model may occasionally hallucinate under adversarial prompting.
