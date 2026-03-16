"""Empirical parameter grid search for top_k, score_threshold, and temperature.

Tests multiple combinations and ranks them by an aggregate score that weights:
  - FAQ coverage (retrieval recall on direct FAQ questions)
  - Hallucination safety (company off-topic + hallucination probe pass rate)
  - General chat success (greetings answered, not fallen back)

Usage:
    uv run python -m tests.evaluation.grid_search
    uv run python -m tests.evaluation.grid_search --quick   # fewer combinations
"""

from __future__ import annotations

import argparse
import csv
import datetime
import os
import sys
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import AppSettings
from tests.evaluation.runner import EvalResult, _overall_pass, run_evaluation
from tests.evaluation.test_cases import (
    CASES_BY_CATEGORY,
    FAQ_DIRECT,
    FAQ_PARAPHRASE,
    COMPANY_OFFTOPIC,
    HALLUCINATION_PROBES,
    GENERAL_CHAT,
)


@dataclass
class GridPoint:
    top_k: int
    score_threshold: float
    temperature: float
    # Metrics
    faq_direct_pass_rate: float      # coverage of verbatim FAQ questions
    faq_paraphrase_pass_rate: float  # coverage of paraphrased FAQ questions
    safety_pass_rate: float          # off-topic + hallucination pass rate
    general_chat_pass_rate: float    # greeting/smalltalk pass rate
    aggregate_score: float           # weighted composite
    avg_latency_s: float


def _compute_metrics(results: list[EvalResult]) -> dict[str, float]:
    """Compute per-category pass rates from a result set."""
    by_cat: dict[str, list[EvalResult]] = {}
    for r in results:
        by_cat.setdefault(r.case.category, []).append(r)

    def pass_rate(cat: str) -> float:
        cat_results = by_cat.get(cat, [])
        if not cat_results:
            return 1.0
        return sum(1 for r in cat_results if _overall_pass(r)) / len(cat_results)

    avg_latency = sum(r.latency_s for r in results) / len(results) if results else 0
    return {
        "faq_direct": pass_rate("faq_direct"),
        "faq_paraphrase": pass_rate("faq_paraphrase"),
        "company_offtopic": pass_rate("company_offtopic"),
        "hallucination": pass_rate("hallucination"),
        "general_chat": pass_rate("general_chat"),
        "avg_latency_s": avg_latency,
    }


def _aggregate_score(metrics: dict[str, float]) -> float:
    """Composite score: safety weighted highest, then coverage, then chat."""
    # Weights: safety (hallucination + offtopic) = 0.45, coverage = 0.35, chat = 0.20
    safety = (metrics["company_offtopic"] + metrics["hallucination"]) / 2
    coverage = (metrics["faq_direct"] + metrics["faq_paraphrase"]) / 2
    chat = metrics["general_chat"]
    return 0.45 * safety + 0.35 * coverage + 0.20 * chat


# Use smaller case sets for grid search to keep runtime reasonable
_GRID_CASES = (
    FAQ_DIRECT[:5]        # 5 verbatim FAQ
    + FAQ_PARAPHRASE[:5]  # 5 paraphrases
    + COMPANY_OFFTOPIC[:4]
    + HALLUCINATION_PROBES[:3]
    + GENERAL_CHAT[:4]
)


def run_grid_search(
    base_settings: AppSettings,
    top_k_values: list[int],
    threshold_values: list[float],
    temperature_values: list[float],
    *,
    verbose: bool = False,
) -> list[GridPoint]:
    points: list[GridPoint] = []
    total = len(top_k_values) * len(threshold_values) * len(temperature_values)
    idx = 0

    for top_k in top_k_values:
        for threshold in threshold_values:
            for temperature in temperature_values:
                idx += 1
                print(
                    f"[{idx:02d}/{total}] top_k={top_k}  threshold={threshold:.2f}"
                    f"  temp={temperature:.2f}",
                    end="  ",
                    flush=True,
                )

                settings = AppSettings(
                    ollama_base_url=base_settings.ollama_base_url,
                    qdrant_url=base_settings.qdrant_url,
                    ollama_generate_model=base_settings.ollama_generate_model,
                    ollama_embedding_model=base_settings.ollama_embedding_model,
                    top_k=top_k,
                    score_threshold=threshold,
                    ollama_generate_temperature=temperature,
                    ollama_generate_max_tokens=base_settings.ollama_generate_max_tokens,
                )
                results = run_evaluation(settings, _GRID_CASES, verbose=False)
                metrics = _compute_metrics(results)
                agg = _aggregate_score(metrics)

                point = GridPoint(
                    top_k=top_k,
                    score_threshold=threshold,
                    temperature=temperature,
                    faq_direct_pass_rate=metrics["faq_direct"],
                    faq_paraphrase_pass_rate=metrics["faq_paraphrase"],
                    safety_pass_rate=(metrics["company_offtopic"] + metrics["hallucination"]) / 2,
                    general_chat_pass_rate=metrics["general_chat"],
                    aggregate_score=agg,
                    avg_latency_s=metrics["avg_latency_s"],
                )
                points.append(point)
                print(
                    f"score={agg:.3f}  direct={metrics['faq_direct']:.0%}"
                    f"  safe={point.safety_pass_rate:.0%}"
                    f"  chat={metrics['general_chat']:.0%}"
                    f"  {metrics['avg_latency_s']:.1f}s/q"
                )

    points.sort(key=lambda p: p.aggregate_score, reverse=True)
    return points


def format_grid_report(points: list[GridPoint], model: str) -> str:
    lines: list[str] = []
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append("=" * 80)
    lines.append("FAQ CHATBOT PARAMETER GRID SEARCH")
    lines.append(f"Timestamp: {ts}  Model: {model}")
    lines.append("=" * 80)
    lines.append(
        f"\n{'Rank':>4}  {'k':>2}  {'thresh':>6}  {'temp':>5}  "
        f"{'Agg':>5}  {'Direct':>6}  {'Para':>6}  {'Safe':>6}  {'Chat':>6}  {'Lat':>5}"
    )
    lines.append("-" * 80)
    for i, p in enumerate(points, 1):
        lines.append(
            f"{i:>4}  {p.top_k:>2}  {p.score_threshold:>6.2f}  {p.temperature:>5.2f}  "
            f"{p.aggregate_score:>5.3f}  {p.faq_direct_pass_rate:>6.0%}  "
            f"{p.faq_paraphrase_pass_rate:>6.0%}  {p.safety_pass_rate:>6.0%}  "
            f"{p.general_chat_pass_rate:>6.0%}  {p.avg_latency_s:>4.1f}s"
        )

    if points:
        best = points[0]
        lines.append("\n" + "=" * 80)
        lines.append("RECOMMENDED CONFIGURATION (best aggregate score)")
        lines.append(f"  FAQ_CHATBOT_TOP_K={best.top_k}")
        lines.append(f"  FAQ_CHATBOT_SCORE_THRESHOLD={best.score_threshold}")
        lines.append(f"  FAQ_CHATBOT_OLLAMA_GENERATE_TEMPERATURE={best.temperature}")
        lines.append(f"  Aggregate score: {best.aggregate_score:.3f}")
        lines.append(
            f"  FAQ direct: {best.faq_direct_pass_rate:.0%}  "
            f"Paraphrase: {best.faq_paraphrase_pass_rate:.0%}  "
            f"Safety: {best.safety_pass_rate:.0%}  "
            f"Chat: {best.general_chat_pass_rate:.0%}"
        )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Grid search for FAQ chatbot parameters")
    parser.add_argument("--ollama", default=os.environ.get("FAQ_CHATBOT_OLLAMA_BASE_URL", "http://localhost:11434"))
    parser.add_argument("--qdrant", default=os.environ.get("FAQ_CHATBOT_QDRANT_URL", "http://localhost:6333"))
    parser.add_argument("--model", default=os.environ.get("FAQ_CHATBOT_OLLAMA_GENERATE_MODEL", "qwen3.5:9b"))
    parser.add_argument("--embedding-model", default=os.environ.get("FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe"))
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--quick", action="store_true", help="Fewer combinations for faster run")
    parser.add_argument("--output", help="Output path for report and CSV")
    args = parser.parse_args()

    if args.quick:
        top_k_values = [3, 5]
        threshold_values = [0.60, 0.70, 0.75]
        temperature_values = [0.1, 0.2]
    else:
        top_k_values = [1, 3, 5]
        threshold_values = [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]
        temperature_values = [0.0, 0.1, 0.2, 0.3]

    base_settings = AppSettings(
        ollama_base_url=args.ollama,
        qdrant_url=args.qdrant,
        ollama_generate_model=args.model,
        ollama_embedding_model=args.embedding_model,
        ollama_generate_max_tokens=args.max_tokens,
    )

    total_combos = len(top_k_values) * len(threshold_values) * len(temperature_values)
    print(f"Grid search: {total_combos} combinations  model={args.model}")
    print(f"top_k={top_k_values}  threshold={threshold_values}  temp={temperature_values}")
    print()

    points = run_grid_search(
        base_settings, top_k_values, threshold_values, temperature_values
    )
    report = format_grid_report(points, args.model)
    print("\n" + report)

    # Save outputs
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    model_slug = args.model.replace(":", "-").replace(".", "_")

    txt_path = results_dir / f"grid_{ts}_{model_slug}.txt"
    txt_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved → {txt_path}")

    # CSV for spreadsheet analysis
    csv_path = results_dir / f"grid_{ts}_{model_slug}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank", "top_k", "score_threshold", "temperature",
                "aggregate_score", "faq_direct_pass_rate", "faq_paraphrase_pass_rate",
                "safety_pass_rate", "general_chat_pass_rate", "avg_latency_s",
            ],
        )
        writer.writeheader()
        for i, p in enumerate(points, 1):
            writer.writerow({
                "rank": i,
                "top_k": p.top_k,
                "score_threshold": p.score_threshold,
                "temperature": p.temperature,
                "aggregate_score": round(p.aggregate_score, 4),
                "faq_direct_pass_rate": round(p.faq_direct_pass_rate, 4),
                "faq_paraphrase_pass_rate": round(p.faq_paraphrase_pass_rate, 4),
                "safety_pass_rate": round(p.safety_pass_rate, 4),
                "general_chat_pass_rate": round(p.general_chat_pass_rate, 4),
                "avg_latency_s": round(p.avg_latency_s, 2),
            })
    print(f"CSV saved  → {csv_path}")


if __name__ == "__main__":
    main()
