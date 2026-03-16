"""Empirical evaluation for FAQ retrieval and generation settings."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import re
from statistics import mean
import sys

from app.config import AppSettings
from app.domain import RetrievalResult
from app.repositories import FAQRepository
from app.services import AnswerGenerator, Retriever

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FAQ_TEXT_PATH = PROJECT_ROOT / "data" / "faq.txt"
DEFAULT_THRESHOLD_CANDIDATES = [0.45, 0.50, 0.55, 0.58, 0.60, 0.65, 0.70]
DEFAULT_TEMPERATURE_CANDIDATES = [0.00, 0.05, 0.10, 0.15, 0.20]
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9À-ÿ]{2,}")
TOKEN_STOPWORDS = {
    "aber",
    "als",
    "auch",
    "bei",
    "das",
    "dem",
    "den",
    "der",
    "des",
    "die",
    "ein",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "es",
    "für",
    "hat",
    "ich",
    "ihr",
    "ihre",
    "im",
    "in",
    "ist",
    "mit",
    "oder",
    "sie",
    "sind",
    "und",
    "von",
    "wie",
    "wir",
    "zu",
}

PARAPHRASE_CASES = [
    {
        "id": "faq-01-services-overview",
        "question": "Welche Leistungen bietet eure IT-Firma an?",
    },
    {
        "id": "faq-02-support-options",
        "question": "Habt ihr auch 24/7 Support?",
    },
    {
        "id": "faq-03-security-threats",
        "question": "Wie schützt ihr Kunden vor Cyberangriffen?",
    },
    {
        "id": "faq-04-cloud-migration",
        "question": "Könnt ihr beim Umzug in die Cloud helfen?",
    },
    {
        "id": "faq-05-data-protection",
        "question": "Unterstützt ihr bei DSGVO und Datenschutz?",
    },
    {
        "id": "faq-06-resilience",
        "question": "Wie sorgt ihr dafür, dass unsere Systeme nicht ausfallen?",
    },
    {
        "id": "faq-07-custom-software",
        "question": "Entwickelt ihr auch individuelle Software für Firmen?",
    },
    {
        "id": "faq-08-consulting-process",
        "question": "Wie läuft eure IT-Beratung normalerweise ab?",
    },
    {
        "id": "faq-09-industries",
        "question": "Für welche Branchen arbeitet ihr?",
    },
    {
        "id": "faq-10-pricing",
        "question": "Wie teuer ist das ungefähr?",
    },
]

GENERAL_CHAT_CASES = [
    "Hallo",
    "Danke dir",
    "Wer bist du?",
]

OFF_TOPIC_CASES = [
    "Was ist das Wetter morgen?",
    "Wer ist aktuell US-Präsident?",
    "Erkläre mir Quantenphysik.",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--thresholds",
        nargs="*",
        type=float,
        default=DEFAULT_THRESHOLD_CANDIDATES,
    )
    parser.add_argument(
        "--temperatures",
        nargs="*",
        type=float,
        default=DEFAULT_TEMPERATURE_CANDIDATES,
    )
    return parser.parse_args()


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def _load_faq_txt_questions(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    matches = re.findall(
        r"\d+\.\s*Frage:\s*(.*?)\nAntwort:",
        content,
        flags=re.DOTALL,
    )
    return [_normalize_whitespace(match) for match in matches]


def _tokenize(text: str) -> Counter[str]:
    return Counter(
        token
        for token in TOKEN_PATTERN.findall(text.casefold())
        if token not in TOKEN_STOPWORDS
    )


def _token_f1(candidate: str, reference: str) -> float:
    candidate_tokens = _tokenize(candidate)
    reference_tokens = _tokenize(reference)
    if not candidate_tokens or not reference_tokens:
        return 0.0

    overlap = sum((candidate_tokens & reference_tokens).values())
    if overlap == 0:
        return 0.0

    precision = overlap / sum(candidate_tokens.values())
    recall = overlap / sum(reference_tokens.values())
    return 2 * precision * recall / (precision + recall)


def _build_settings() -> AppSettings:
    return AppSettings.from_env()


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def _evaluate_retrieval(
    retriever: Retriever,
    cases: list[dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case in cases:
        result = retriever.retrieve(case["question"])
        best_entry = result.top_k_results[0][0] if result.top_k_results else None
        best_score = result.top_k_results[0][1] if result.top_k_results else 0.0
        rows.append(
            {
                "question": case["question"],
                "expected_id": case["id"],
                "best_id": None if best_entry is None else best_entry.id,
                "best_score": round(best_score, 6),
            }
        )
    return rows


def _evaluate_noise(
    retriever: Retriever,
    cases: list[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for question in cases:
        result = retriever.retrieve(question)
        best_entry = result.top_k_results[0][0] if result.top_k_results else None
        best_score = result.top_k_results[0][1] if result.top_k_results else 0.0
        rows.append(
            {
                "question": question,
                "best_id": None if best_entry is None else best_entry.id,
                "best_score": round(best_score, 6),
            }
        )
    return rows


def _choose_threshold(
    exact_rows: list[dict[str, object]],
    paraphrase_rows: list[dict[str, object]],
    noise_rows: list[dict[str, object]],
    thresholds: list[float],
) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for threshold in thresholds:
        exact_hits = sum(
            row["best_id"] == row["expected_id"] and float(row["best_score"]) >= threshold
            for row in exact_rows
        )
        paraphrase_hits = sum(
            row["best_id"] == row["expected_id"] and float(row["best_score"]) >= threshold
            for row in paraphrase_rows
        )
        false_positives = sum(float(row["best_score"]) >= threshold for row in noise_rows)
        objective = exact_hits * 5 + paraphrase_hits * 3 - false_positives * 6
        summary.append(
            {
                "threshold": threshold,
                "exact_hits": exact_hits,
                "paraphrase_hits": paraphrase_hits,
                "noise_false_positives": false_positives,
                "objective": objective,
            }
        )

    summary.sort(
        key=lambda row: (
            row["objective"],
            row["exact_hits"],
            row["paraphrase_hits"],
            -row["noise_false_positives"],
        ),
        reverse=True,
    )
    return summary


def _evaluate_temperature(
    settings: AppSettings,
    exact_cases: list[dict[str, str]],
    general_chat_cases: list[str],
    temperatures: list[float],
) -> list[dict[str, object]]:
    repository = FAQRepository.from_settings(settings)
    entries = {entry.id: entry for entry in repository.list_entries()}
    summary: list[dict[str, object]] = []

    for temperature in temperatures:
        _log(f"Evaluating temperature={temperature:.2f}")
        generator_settings = replace(settings, ollama_generate_temperature=temperature)
        generator = AnswerGenerator.from_settings(generator_settings)

        faq_scores: list[float] = []
        faq_fallbacks = 0
        faq_answers: list[dict[str, str]] = []
        for index, case in enumerate(exact_cases, start=1):
            _log(f"  FAQ question {index}/{len(exact_cases)}")
            entry = entries[case["id"]]
            retrieval = RetrievalResult(
                matched_entry=entry,
                score=1.0,
                top_k_results=[(entry, 1.0)],
                retrieved=True,
            )
            response = generator.generate(case["question"], retrieval)
            if response.is_fallback:
                faq_fallbacks += 1
            else:
                faq_scores.append(_token_f1(response.answer, entry.answer))
            faq_answers.append(
                {
                    "id": entry.id,
                    "question": case["question"],
                    "answer": response.answer,
                }
            )

        chat_non_fallbacks = 0
        chat_answers: list[dict[str, str]] = []
        for question in general_chat_cases:
            _log(f"  General chat sample: {question}")
            retrieval = RetrievalResult(
                matched_entry=None,
                score=0.0,
                top_k_results=[],
                retrieved=False,
            )
            response = generator.generate(question, retrieval)
            if not response.is_fallback:
                chat_non_fallbacks += 1
            chat_answers.append({"question": question, "answer": response.answer})

        summary.append(
            {
                "temperature": temperature,
                "faq_average_token_f1": round(mean(faq_scores), 4) if faq_scores else 0.0,
                "faq_fallbacks": faq_fallbacks,
                "general_chat_non_fallbacks": chat_non_fallbacks,
                "sample_faq_answers": faq_answers[:3],
                "sample_chat_answers": chat_answers,
            }
        )

    summary.sort(
        key=lambda row: (
            row["faq_average_token_f1"],
            -row["faq_fallbacks"],
            row["general_chat_non_fallbacks"],
        ),
        reverse=True,
    )
    return summary


def main() -> int:
    args = _parse_args()
    settings = _build_settings()
    _log("Loading FAQ corpus...")
    repository = FAQRepository.from_settings(settings)
    entries = repository.list_entries()
    faq_txt_questions = _load_faq_txt_questions(FAQ_TEXT_PATH)
    if len(faq_txt_questions) != len(entries):
        raise SystemExit("FAQ question count mismatch between faq.txt and faq.json")

    exact_cases = [
        {"id": entry.id, "question": question}
        for entry, question in zip(entries, faq_txt_questions, strict=True)
    ]

    retrieval_settings = replace(settings, score_threshold=0.0)
    retriever = Retriever.from_settings(retrieval_settings)
    _log("Running retrieval evaluation...")
    exact_rows = _evaluate_retrieval(retriever, exact_cases)
    paraphrase_rows = _evaluate_retrieval(retriever, PARAPHRASE_CASES)
    noise_rows = _evaluate_noise(retriever, GENERAL_CHAT_CASES + OFF_TOPIC_CASES)
    threshold_summary = _choose_threshold(
        exact_rows,
        paraphrase_rows,
        noise_rows,
        args.thresholds,
    )
    temperature_summary = _evaluate_temperature(
        settings,
        exact_cases,
        GENERAL_CHAT_CASES,
        args.temperatures,
    )

    print(
        json.dumps(
            {
                "model": settings.ollama_generate_model,
                "embedding_model": settings.ollama_embedding_model,
                "exact_retrieval": exact_rows,
                "paraphrase_retrieval": paraphrase_rows,
                "noise_retrieval": noise_rows,
                "threshold_summary": threshold_summary,
                "recommended_threshold": threshold_summary[0],
                "temperature_summary": temperature_summary,
                "recommended_temperature": temperature_summary[0],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
