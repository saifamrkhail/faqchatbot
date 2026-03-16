"""Fast grid search for qwen3.5:9b (CPU-optimised: 10 cases, 6 combos).

Tests top_k=[3,5] × threshold=[0.55,0.60,0.65] × temp=[0.20].
Uses a representative 10-case subset so each combo runs in ~7 min.

Usage:
    uv run python -m tests.evaluation.grid_search_fast
    uv run python -m tests.evaluation.grid_search_fast --model qwen3.5:9b
"""

from __future__ import annotations

import argparse
import csv
import datetime
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from app.config import AppSettings
from tests.evaluation.runner import EvalResult, _overall_pass, run_evaluation
from tests.evaluation.grid_search import (
    GridPoint,
    _aggregate_score,
    _compute_metrics,
    format_grid_report,
)
from tests.evaluation.test_cases import (
    COMPANY_OFFTOPIC,
    FAQ_DIRECT,
    FAQ_PARAPHRASE,
    GENERAL_CHAT,
    HALLUCINATION_PROBES,
)

# Representative 10-case subset — one from each FAQ, safety, chat
_FAST_CASES = (
    FAQ_DIRECT[:4]
    + FAQ_PARAPHRASE[:3]
    + COMPANY_OFFTOPIC[:1]
    + HALLUCINATION_PROBES[:1]
    + GENERAL_CHAT[:1]
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fast grid search for slow models")
    parser.add_argument(
        "--ollama",
        default=os.environ.get("FAQ_CHATBOT_OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    parser.add_argument(
        "--qdrant",
        default=os.environ.get("FAQ_CHATBOT_QDRANT_URL", "http://localhost:6333"),
    )
    parser.add_argument("--model", default="qwen3.5:9b")
    parser.add_argument(
        "--embedding-model",
        default=os.environ.get(
            "FAQ_CHATBOT_OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe"
        ),
    )
    parser.add_argument("--max-tokens", type=int, default=512)
    args = parser.parse_args()

    top_k_values = [3, 5]
    threshold_values = [0.55, 0.60, 0.65]
    temperature_values = [0.20]

    total = len(top_k_values) * len(threshold_values) * len(temperature_values)
    print(f"Fast grid search: {total} combinations  model={args.model}")
    print(
        f"top_k={top_k_values}  threshold={threshold_values}  temp={temperature_values}"
    )
    print(f"Cases per combo: {len(_FAST_CASES)}")
    print()

    base = AppSettings(
        ollama_base_url=args.ollama,
        qdrant_url=args.qdrant,
        ollama_generate_model=args.model,
        ollama_embedding_model=args.embedding_model,
        ollama_generate_max_tokens=args.max_tokens,
    )

    points: list[GridPoint] = []
    idx = 0
    for top_k in top_k_values:
        for threshold in threshold_values:
            for temp in temperature_values:
                idx += 1
                print(
                    f"[{idx:02d}/{total}] top_k={top_k}  threshold={threshold:.2f}"
                    f"  temp={temp:.2f}",
                    end="  ",
                    flush=True,
                )
                settings = AppSettings(
                    ollama_base_url=base.ollama_base_url,
                    qdrant_url=base.qdrant_url,
                    ollama_generate_model=base.ollama_generate_model,
                    ollama_embedding_model=base.ollama_embedding_model,
                    top_k=top_k,
                    score_threshold=threshold,
                    ollama_generate_temperature=temp,
                    ollama_generate_max_tokens=base.ollama_generate_max_tokens,
                )
                results = run_evaluation(settings, list(_FAST_CASES), verbose=False)
                metrics = _compute_metrics(results)
                agg = _aggregate_score(metrics)
                p = GridPoint(
                    top_k=top_k,
                    score_threshold=threshold,
                    temperature=temp,
                    faq_direct_pass_rate=metrics["faq_direct"],
                    faq_paraphrase_pass_rate=metrics["faq_paraphrase"],
                    safety_pass_rate=(
                        metrics["company_offtopic"] + metrics["hallucination"]
                    )
                    / 2,
                    general_chat_pass_rate=metrics["general_chat"],
                    aggregate_score=agg,
                    avg_latency_s=metrics["avg_latency_s"],
                )
                points.append(p)
                print(
                    f"score={agg:.3f}  direct={metrics['faq_direct']:.0%}"
                    f"  para={metrics['faq_paraphrase']:.0%}"
                    f"  safe={p.safety_pass_rate:.0%}"
                    f"  chat={metrics['general_chat']:.0%}"
                    f"  {metrics['avg_latency_s']:.1f}s/q",
                    flush=True,
                )

    points.sort(key=lambda p: p.aggregate_score, reverse=True)
    report = format_grid_report(points, args.model)
    print("\n" + report)

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    model_slug = args.model.replace(":", "-").replace(".", "_")

    txt_path = results_dir / f"grid_fast_{ts}_{model_slug}.txt"
    txt_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved → {txt_path}")

    csv_path = results_dir / f"grid_fast_{ts}_{model_slug}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "top_k",
                "score_threshold",
                "temperature",
                "aggregate_score",
                "faq_direct_pass_rate",
                "faq_paraphrase_pass_rate",
                "safety_pass_rate",
                "general_chat_pass_rate",
                "avg_latency_s",
            ],
        )
        writer.writeheader()
        for i, p in enumerate(points, 1):
            writer.writerow(
                {
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
                }
            )
    print(f"CSV saved  → {csv_path}")


if __name__ == "__main__":
    main()
