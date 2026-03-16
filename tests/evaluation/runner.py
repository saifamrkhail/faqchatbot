"""Evaluation runner for the FAQ chatbot.

Connects to live Ollama + Qdrant services and runs all test cases,
producing a scored report with pass/fail for each case.

Usage (requires Ollama + Qdrant running locally):
    uv run python -m tests.evaluation.runner
    uv run python -m tests.evaluation.runner --ollama http://localhost:11434
    uv run python -m tests.evaluation.runner --output results/run_$(date +%Y%m%d).txt
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Add project root to path if running as script
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import AppSettings
from app.services.chat_service import ChatService
from tests.evaluation.test_cases import (
    ALL_CASES,
    CASES_BY_CATEGORY,
    EvalCase,
)


@dataclass
class EvalResult:
    case: EvalCase
    answer: str
    is_fallback: bool
    used_retrieval: bool
    score: float
    source_faq_id: str | None
    latency_s: float
    # Assertion outcomes
    retrieved_pass: bool | None  # None = not asserted
    fallback_pass: bool | None
    hallucination_pass: bool  # True = no hallucination detected
    # Detected hallucination keywords
    detected_flags: list[str]
    error: str | None = None


def _check_hallucination(answer: str, flags: tuple[str, ...]) -> tuple[bool, list[str]]:
    """Return (no_hallucination, detected_keywords)."""
    answer_lower = answer.casefold()
    detected = [f for f in flags if f.casefold() in answer_lower]
    return len(detected) == 0, detected


def run_evaluation(
    settings: AppSettings,
    cases: list[EvalCase] | None = None,
    *,
    verbose: bool = False,
) -> list[EvalResult]:
    service = ChatService.from_settings(settings)
    eval_cases = cases or ALL_CASES
    results: list[EvalResult] = []

    for i, case in enumerate(eval_cases, 1):
        if verbose:
            print(f"  [{i:02d}/{len(eval_cases)}] {case.description[:50]:<50}", end="", flush=True)

        t0 = time.monotonic()
        try:
            response = service.handle_question(case.question)
            latency = time.monotonic() - t0

            no_hallucination, detected = _check_hallucination(
                response.answer or "", case.hallucination_flags
            )

            retrieved_pass = None
            if case.expect_retrieved is not None:
                retrieved_pass = response.used_retrieval == case.expect_retrieved

            fallback_pass = None
            if case.expect_fallback is not None:
                fallback_pass = response.is_fallback == case.expect_fallback

            result = EvalResult(
                case=case,
                answer=response.answer or "",
                is_fallback=response.is_fallback,
                used_retrieval=response.used_retrieval,
                score=response.confidence or 0.0,
                source_faq_id=response.source_faq_id,
                latency_s=latency,
                retrieved_pass=retrieved_pass,
                fallback_pass=fallback_pass,
                hallucination_pass=no_hallucination,
                detected_flags=detected,
                error=None,
            )
        except Exception as exc:
            latency = time.monotonic() - t0
            result = EvalResult(
                case=case,
                answer="",
                is_fallback=True,
                used_retrieval=False,
                score=0.0,
                source_faq_id=None,
                latency_s=latency,
                retrieved_pass=None,
                fallback_pass=None,
                hallucination_pass=True,
                detected_flags=[],
                error=str(exc),
            )

        results.append(result)

        if verbose:
            status_parts = []
            if result.error:
                status_parts.append("ERROR")
            else:
                if result.retrieved_pass is False:
                    status_parts.append("RETRIEVAL:FAIL")
                elif result.retrieved_pass is True:
                    status_parts.append("RETRIEVAL:OK")
                if result.fallback_pass is False:
                    status_parts.append("FALLBACK:FAIL")
                elif result.fallback_pass is True:
                    status_parts.append("FALLBACK:OK")
                if not result.hallucination_pass:
                    status_parts.append(f"HALLUCINATION:{result.detected_flags}")
            status = " | ".join(status_parts) if status_parts else "OK"
            print(f" score={result.score:.2f} {status}")

    return results


def _overall_pass(r: EvalResult) -> bool:
    if r.error:
        return False
    if r.retrieved_pass is False:
        return False
    if r.fallback_pass is False:
        return False
    if not r.hallucination_pass:
        return False
    return True


def format_report(results: list[EvalResult], settings: AppSettings) -> str:
    lines: list[str] = []
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("=" * 72)
    lines.append("FAQ CHATBOT EVALUATION REPORT")
    lines.append(f"Timestamp : {ts}")
    lines.append(f"Model     : {settings.ollama_generate_model}")
    lines.append(f"Embedding : {settings.ollama_embedding_model}")
    lines.append(f"top_k     : {settings.top_k}")
    lines.append(f"threshold : {settings.score_threshold}")
    lines.append(f"temp      : {settings.ollama_generate_temperature}")
    lines.append(f"max_tokens: {settings.ollama_generate_max_tokens}")
    lines.append("=" * 72)

    # Per-category summary
    categories = list(CASES_BY_CATEGORY.keys())
    results_by_cat: dict[str, list[EvalResult]] = {c: [] for c in categories}
    for r in results:
        results_by_cat[r.case.category].append(r)

    lines.append("\nSUMMARY BY CATEGORY")
    lines.append("-" * 72)
    total_pass = sum(1 for r in results if _overall_pass(r))
    total = len(results)

    for cat in categories:
        cat_results = results_by_cat[cat]
        if not cat_results:
            continue
        cat_pass = sum(1 for r in cat_results if _overall_pass(r))
        pct = cat_pass / len(cat_results) * 100
        avg_score = sum(r.score for r in cat_results) / len(cat_results)
        avg_latency = sum(r.latency_s for r in cat_results) / len(cat_results)
        lines.append(
            f"  {cat:<22} {cat_pass:2}/{len(cat_results):2} ({pct:5.1f}%)"
            f"  avg_score={avg_score:.2f}  avg_latency={avg_latency:.1f}s"
        )

    overall_pct = total_pass / total * 100 if total else 0
    lines.append("-" * 72)
    lines.append(f"  {'TOTAL':<22} {total_pass:2}/{total:2} ({overall_pct:.1f}%)")

    # Latency stats
    latencies = [r.latency_s for r in results if not r.error]
    if latencies:
        lines.append(
            f"\nLatency: min={min(latencies):.1f}s  max={max(latencies):.1f}s"
            f"  avg={sum(latencies)/len(latencies):.1f}s"
        )

    # Detailed failures
    failures = [r for r in results if not _overall_pass(r)]
    if failures:
        lines.append(f"\nFAILURES ({len(failures)})")
        lines.append("-" * 72)
        for r in failures:
            lines.append(f"\n  [{r.case.category}] {r.case.description}")
            lines.append(f"  Q: {r.case.question[:80]}")
            if r.error:
                lines.append(f"  ERROR: {r.error}")
            else:
                lines.append(
                    f"  score={r.score:.2f}  retrieved={r.used_retrieval}"
                    f"  fallback={r.is_fallback}  faq={r.source_faq_id}"
                )
                if r.retrieved_pass is False:
                    lines.append(
                        f"  FAIL retrieved: expected={r.case.expect_retrieved}"
                        f" got={r.used_retrieval}"
                    )
                if r.fallback_pass is False:
                    lines.append(
                        f"  FAIL fallback: expected={r.case.expect_fallback}"
                        f" got={r.is_fallback}"
                    )
                if not r.hallucination_pass:
                    lines.append(
                        f"  HALLUCINATION DETECTED: flags={r.detected_flags}"
                    )
                lines.append(f"  A: {r.answer[:150]}")

    # All results table
    lines.append(f"\nALL RESULTS")
    lines.append("-" * 72)
    lines.append(f"{'#':>3} {'Cat':<18} {'Score':>5} {'Ret':>3} {'FB':>3} {'Halu':>4} {'ms':>5}  Description / Answer")
    lines.append("-" * 72)
    for i, r in enumerate(results, 1):
        ret_s = "YES" if r.used_retrieval else "NO "
        fb_s = "YES" if r.is_fallback else "NO "
        halu_s = "FAIL" if not r.hallucination_pass else "OK  "
        answer_preview = (r.answer or r.error or "")[:60].replace("\n", " ")
        lines.append(
            f"{i:>3} {r.case.category:<18} {r.score:>5.2f} {ret_s} {fb_s} {halu_s}"
            f" {int(r.latency_s*1000):>5}  {r.case.description[:30]}: {answer_preview}"
        )

    lines.append("\n" + "=" * 72)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate FAQ chatbot against live services")
    parser.add_argument("--ollama", default=os.environ.get("FAQ_CHATBOT_OLLAMA_BASE_URL", "http://localhost:11434"))
    parser.add_argument("--qdrant", default=os.environ.get("FAQ_CHATBOT_QDRANT_URL", "http://localhost:6333"))
    parser.add_argument("--model", default=os.environ.get("FAQ_CHATBOT_OLLAMA_GENERATE_MODEL", "qwen3.5:2b"))
    parser.add_argument("--embedding-model", default=os.environ.get("FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe"))
    parser.add_argument("--top-k", type=int, default=int(os.environ.get("FAQ_CHATBOT_TOP_K", "3")))
    parser.add_argument("--threshold", type=float, default=float(os.environ.get("FAQ_CHATBOT_SCORE_THRESHOLD", "0.50")))
    parser.add_argument("--temperature", type=float, default=float(os.environ.get("FAQ_CHATBOT_OLLAMA_GENERATE_TEMPERATURE", "0.1")))
    parser.add_argument("--max-tokens", type=int, default=int(os.environ.get("FAQ_CHATBOT_OLLAMA_GENERATE_MAX_TOKENS", "512")))
    parser.add_argument("--category", help="Run only this category (e.g. faq_direct)")
    parser.add_argument("--output", help="Write report to file (default: auto-named in tests/evaluation/results/)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    settings = AppSettings(
        ollama_base_url=args.ollama,
        qdrant_url=args.qdrant,
        ollama_generate_model=args.model,
        ollama_embedding_model=args.embedding_model,
        top_k=args.top_k,
        score_threshold=args.threshold,
        ollama_generate_temperature=args.temperature,
        ollama_generate_max_tokens=args.max_tokens,
    )

    if args.category:
        from tests.evaluation.test_cases import CASES_BY_CATEGORY
        cases = CASES_BY_CATEGORY.get(args.category)
        if cases is None:
            print(f"Unknown category: {args.category}. Valid: {list(CASES_BY_CATEGORY)}")
            sys.exit(1)
    else:
        cases = None  # all

    print(f"Running FAQ chatbot evaluation...")
    print(f"  Model: {settings.ollama_generate_model}  threshold={settings.score_threshold}  top_k={settings.top_k}")
    print(f"  Ollama: {settings.ollama_base_url}  Qdrant: {settings.qdrant_url}")
    print()

    results = run_evaluation(settings, cases, verbose=True)
    report = format_report(results, settings)

    print("\n" + report)

    # Save report
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        out_path = Path(args.output)
    else:
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        model_slug = settings.ollama_generate_model.replace(":", "-").replace(".", "_")
        out_path = results_dir / f"eval_{ts}_k{settings.top_k}_t{settings.score_threshold}_{model_slug}.txt"

    out_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved → {out_path}")

    # Exit with error if any assertion failures
    failures = [r for r in results if not _overall_pass(r)]
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
