# FAQ Chatbot – Improvement Plan

Based on empirical evaluation against 48 test cases (6 categories) using `qwen3.5:9b`
with `nomic-embed-text-v2-moe` embeddings.

---

## Status: ALL IMPROVEMENTS IMPLEMENTED ✅ (2026-03-16)

### Grid Search Results — `qwen3.5:9b` + `nomic-embed-text-v2-moe`

All 6 parameter combinations achieved **100% on every metric**:

| Rank | top_k | threshold | temp | Aggregate | Direct | Paraphrase | Safe | Chat | Latency |
|------|-------|-----------|------|-----------|--------|------------|------|------|---------|
| 1 | 3 | 0.55 | 0.20 | 1.000 | 100% | 100% | 100% | 100% | 73.0s/q |
| 2 | 3 | **0.60** | 0.20 | 1.000 | 100% | 100% | 100% | 100% | 72.3s/q |
| 3 | 3 | 0.65 | 0.20 | 1.000 | 100% | 100% | 100% | 100% | 76.3s/q |
| 4 | 5 | 0.55 | 0.20 | 1.000 | 100% | 100% | 100% | 100% | 65.6s/q |
| 5 | 5 | 0.60 | 0.20 | 1.000 | 100% | 100% | 100% | 100% | 64.8s/q |
| 6 | 5 | 0.65 | 0.20 | 1.000 | 100% | 100% | 100% | 100% | 37.3s/q |

**Chosen defaults**: `top_k=3`, `threshold=0.60`, `temp=0.20`

Rationale: threshold=0.60 provides a conservative safety margin (all company off-topic scores
≤ 0.31 — at least 0.29 below threshold). top_k=3 uses fewer Qdrant reads. temp=0.20 gives
deterministic enough answers while allowing natural German phrasing.

Result file: `tests/evaluation/results/grid_fast_20260316_162246_qwen3_5-9b.txt`

---

## Baseline Evaluation Results (before improvements, threshold=0.70, qwen3.5:2b)

| Category          | Pass | Total | Rate  | Notes |
|-------------------|------|-------|-------|-------|
| faq_direct        | 10   | 10    | 100%  | Avg score 0.89, avg latency 55s |
| faq_paraphrase    |  6   | 13    |  46%  | 7 failures — scores 0.55–0.68, just below threshold |
| company_offtopic  |  7   |  7    | 100%  | Avg score 0.31 — well below any reasonable threshold |
| hallucination     |  5   |  5    | 100%  | No hallucination detected |
| general_chat      |  6   |  7    |  86%  | "Wie geht es Ihnen?" falls through regex gaps |
| boundary          |  6   |  6    | 100%  | Typos, English, mixed language all handled |
| **TOTAL**         | **40** | **48** | **83%** | |

---

## Implemented Improvements

### Fix 0 — `_should_allow_general_response` default `False` → `True` ✅

`app/services/answer_generator.py`

**Problem**: "Wie geht es Ihnen?" and other unrecognized harmless questions fell through
all pattern checks and hit the `return False` default → deterministic fallback.

**Fix**: Changed to `return True`. The `build_general()` prompt already instructs the LLM
to use the fallback for company-specific questions.

---

### P1a — Streaming Output ✅

**Files changed**:
- `app/infrastructure/ollama_client.py`: Added `generate_streaming()` — uses `httpx` streaming
  with `iter_lines()` to yield tokens as they arrive from Ollama `/api/generate`
- `app/services/answer_generator.py`: Added `generate_streaming()` delegating to ollama client
- `app/services/chat_service.py`: Added `handle_question_streaming()` threading streaming through
- `app/ui/protocol.py`: Added `ask_streaming()` to `ChatServiceAdapter`
- `app/ui/chat_app.py`: Detects `ask_streaming` and streams tokens to terminal

**Impact**: Perceived latency drops from ~70s to ~1–3s for first token. User sees tokens
flowing instead of a frozen terminal.

---

### P1b — Shorter FAQ Context Prompt ✅

**File**: `app/domain/prompt_template.py:build()`

Truncates FAQ answer to 200 chars in the grounded prompt:
```python
answer_preview = faq_entry.answer[:200] + "…" if len(faq_entry.answer) > 200 else faq_entry.answer
```

Reduces prompt length and speeds up generation without affecting answer quality.

---

### P2a — FAQ `alt_questions` Field ✅

**Files changed**:
- `app/domain/faq.py`: Added `alt_questions: tuple[str, ...] = ()` field with validation
- `data/faq.json`: Added 3 alternative German phrasings per FAQ entry (30 total)
- `app/services/ingestion_service.py`: `_build_embedding_text()` now embeds alt_questions
  before the answer, enriching the vector representation

**Impact**: Paraphrase recall went from **46% → 100%**. The embedding model now has diverse
query patterns anchored to each FAQ vector.

---

### P2b — Query Rewriting (already implemented pre-plan) ✅

Borderline scores in `[query_rewrite_borderline_min_score, score_threshold)` trigger an LLM
rewrite of the user question. Up to `query_rewrite_max_variants` alternatives are tried.
Configured via `FAQ_CHATBOT_QUERY_REWRITE_*` env vars.

---

### P3 — Relax `_is_grounded_answer` Length Check ✅

**File**: `app/services/answer_generator.py:_is_grounded_answer()`

Changed length multiplier from `2×` to `3×`:
```python
if len(normalized_answer) > max(400, len(faq_entry.answer) * 3):
```

Reduces false-positive rejections for concise, well-structured LLM answers that correctly
paraphrase a longer FAQ answer. The grounding instruction in the prompt remains the primary
guard; this lexical check is a safety net.

---

### P4 — Remove `"it"` from `_COMPANY_HINT_TERMS` ✅

**File**: `app/services/answer_generator.py`

Removed `"it"` — a 2-character English word that incorrectly matched German text containing
"ist". IT-security topics are already captured by `"security"`, `"sicherheit"` and the
grounding prompt.

---

### Prompt Hardening for `build_general()` ✅

**File**: `app/domain/prompt_template.py`

Strengthened the instruction for company-specific questions to prevent `qwen3.5:9b` from
giving polite "I don't have information about X" non-answers instead of the exact fallback:

```python
"- Wenn der Kunde nach konkreten Dienstleistungen, Preisen, Prozessen, "
"Unternehmensdetails, Partnerschaften, Standorten, Zertifizierungen oder sonstigen "
"unternehmensspezifischen Fakten fragt, antworte AUSSCHLIESSLICH und WORTWÖRTLICH "
f'mit exakt dieser Nachricht – ohne jeden weiteren Satz: "{self.fallback_message}"\n'
```

---

## Recommended Defaults (production-ready)

```
Model (generation):  qwen3.5:9b
Model (embedding):   nomic-embed-text-v2-moe
top_k:               3
score_threshold:     0.60
temperature:         0.20
max_tokens:          512
thinking:            false
query_rewrite:       enabled (borderline_min=0.35, max_variants=3)
```

These are set as code defaults in `app/config.py` and take effect when no environment
overrides are present.

---

## Remaining Improvements (not yet implemented)

### P5 — FAQ Data Quality and Coverage (MEDIUM)

**Improvements**:
1. Add more FAQ entries covering edge cases from real user queries
2. Consider bilingual FAQ: English `alt_questions` for multilingual support
   (`nomic-embed-text-v2-moe` is multilingual)
3. Normalize FAQ answer length: very long answers (>300 chars) should be split into
   sub-FAQs to reduce hallucination risk during generation

### P6 — Infrastructure

**Model pull via HTTP API** (more reliable than `docker exec ollama pull`):
```bash
curl -X POST http://localhost:11434/api/pull \
  -H 'Content-Type: application/json' \
  -d '{"name":"qwen3.5:9b","stream":false}' --max-time 600
```

### P7 — Soft Threshold Zone (LOW priority, diminishing returns post-P2a)

With alt_questions in place and 100% paraphrase recall, the soft-zone logic (P2c from
original plan) adds complexity without measurable benefit. Consider only if new FAQ entries
show paraphrase gaps.

---

## Key Architectural Observations

**What works well**:
- The two-path design (FAQ grounded / general conversation) is architecturally sound.
- The `_is_grounded_answer` safety net prevents the LLM from going off-topic.
- Score threshold provides a clean, auditable decision boundary.
- Safety (hallucination prevention) is robust — 100% on off-topic and hallucination probes.
- alt_questions dramatically improved paraphrase recall without any runtime overhead.

**Design principle to maintain**:
> The LLM must never fabricate information about the company. This is guaranteed by:
> 1. Retrieval → grounded prompt (primary guard)
> 2. `_is_grounded_answer` lexical check (secondary guard)
> 3. `_COMPANY_HINT_TERMS` blocking + fallback message (tertiary guard)
>
> Never remove all three guards at once. With only the LLM prompt as guard, a small
> model may occasionally hallucinate under adversarial prompting.
