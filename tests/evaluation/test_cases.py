"""Evaluation test cases for the FAQ chatbot.

Each test case belongs to one of six categories:
  faq_direct       - Verbatim or near-verbatim FAQ questions → must retrieve
  faq_paraphrase   - Semantically equivalent reformulations → should retrieve
  company_offtopic - Company-specific questions NOT in FAQ → must fallback
  hallucination    - Questions designed to elicit fabricated company info
  general_chat     - Greetings, smalltalk, general IT questions → must NOT fallback
  boundary         - Edge-case inputs (typos, short, long, mixed lang)

Expected fields:
  expect_retrieved  - True/False/None (None = don't assert)
  expect_fallback   - True/False/None
  hallucination_flags - Substrings that, if present in answer, indicate hallucination
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Category = Literal[
    "faq_direct",
    "faq_paraphrase",
    "company_offtopic",
    "hallucination",
    "general_chat",
    "boundary",
]


@dataclass(frozen=True)
class EvalCase:
    question: str
    category: Category
    description: str
    expect_retrieved: bool | None = None   # None = don't assert
    expect_fallback: bool | None = None    # None = don't assert
    # Strings whose presence in the answer would signal hallucination
    hallucination_flags: tuple[str, ...] = field(default_factory=tuple)


# ============================================================================
# A - FAQ DIRECT: verbatim or near-verbatim questions from data/faq.json
#     Expected: retrieved=True, fallback=False
# ============================================================================

FAQ_DIRECT: list[EvalCase] = [
    EvalCase(
        question="Welche IT-Dienstleistungen bieten Sie an?",
        category="faq_direct",
        description="FAQ #1 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Welche Support-Optionen stehen zur Verfügung?",
        category="faq_direct",
        description="FAQ #2 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Wie gehen Sie mit IT-Sicherheitsbedrohungen um?",
        category="faq_direct",
        description="FAQ #3 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Bieten Sie Cloud-Migrationsdienste an?",
        category="faq_direct",
        description="FAQ #4 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Wie können Sie uns bei der Einhaltung von Datenschutzvorschriften unterstützen?",
        category="faq_direct",
        description="FAQ #5 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Welche Maßnahmen ergreifen Sie, um die Ausfallsicherheit meiner IT-Systeme zu gewährleisten?",
        category="faq_direct",
        description="FAQ #6 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Können Sie maßgeschneiderte Softwarelösungen für unser Unternehmen entwickeln?",
        category="faq_direct",
        description="FAQ #7 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Wie läuft eine typische IT-Beratung ab?",
        category="faq_direct",
        description="FAQ #8 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Welche Branchen bedienen Sie?",
        category="faq_direct",
        description="FAQ #9 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
    EvalCase(
        question="Wie viel kostet Ihre Dienstleistung?",
        category="faq_direct",
        description="FAQ #10 verbatim",
        expect_retrieved=True,
        expect_fallback=False,
    ),
]

# ============================================================================
# B - FAQ PARAPHRASE: semantically equivalent rewordings
#     Expected: ideally retrieved=True, fallback=False  (retrieval quality test)
# ============================================================================

FAQ_PARAPHRASE: list[EvalCase] = [
    EvalCase(
        question="Was für Leistungen bieten Sie an?",
        category="faq_paraphrase",
        description="FAQ #1 – short paraphrase",
        expect_fallback=False,
    ),
    EvalCase(
        question="Welche Services bietet Ihre Firma an?",
        category="faq_paraphrase",
        description="FAQ #1 – 'Services' instead of 'Dienstleistungen'",
        expect_fallback=False,
    ),
    EvalCase(
        question="Wie kann ich Hilfe bekommen, wenn mein System nicht funktioniert?",
        category="faq_paraphrase",
        description="FAQ #2 – support options rephrased",
        expect_fallback=False,
    ),
    EvalCase(
        question="Was tun Sie gegen Hackerangriffe?",
        category="faq_paraphrase",
        description="FAQ #3 – security rephrased",
        expect_fallback=False,
    ),
    EvalCase(
        question="Können Sie uns in die Cloud migrieren?",
        category="faq_paraphrase",
        description="FAQ #4 – cloud migration rephrased",
        expect_fallback=False,
    ),
    EvalCase(
        question="Helfen Sie bei der DSGVO-Compliance?",
        category="faq_paraphrase",
        description="FAQ #5 – DSGVO short form",
        expect_fallback=False,
    ),
    EvalCase(
        question="Wie stellen Sie sicher, dass meine IT nicht ausfällt?",
        category="faq_paraphrase",
        description="FAQ #6 – availability rephrased",
        expect_fallback=False,
    ),
    EvalCase(
        question="Entwickeln Sie auch individuelle Software?",
        category="faq_paraphrase",
        description="FAQ #7 – custom software rephrased",
        expect_fallback=False,
    ),
    EvalCase(
        question="Wie läuft eine Beratung bei Ihnen ab?",
        category="faq_paraphrase",
        description="FAQ #8 – consulting rephrased",
        expect_fallback=False,
    ),
    EvalCase(
        question="Für welche Unternehmen und Branchen arbeiten Sie?",
        category="faq_paraphrase",
        description="FAQ #9 – industries rephrased",
        expect_fallback=False,
    ),
    EvalCase(
        question="Was kostet es, Ihre Dienste zu nutzen?",
        category="faq_paraphrase",
        description="FAQ #10 – pricing rephrased",
        expect_fallback=False,
    ),
    EvalCase(
        question="Haben Sie auch 24/7 Support?",
        category="faq_paraphrase",
        description="FAQ #2 – specific detail from support FAQ",
        expect_fallback=False,
    ),
    EvalCase(
        question="Arbeiten Sie mit AWS oder Azure?",
        category="faq_paraphrase",
        description="FAQ #4 – specific cloud providers from answer text",
        expect_fallback=False,
    ),
]

# ============================================================================
# C - COMPANY OFF-TOPIC: company-specific questions NOT in FAQ
#     Expected: fallback=True (never hallucinate, even if partial match)
# ============================================================================

COMPANY_OFFTOPIC: list[EvalCase] = [
    EvalCase(
        question="Wie viele Mitarbeiter hat Ihr Unternehmen?",
        category="company_offtopic",
        description="Company size – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("mitarbeiter", "angestellte", "personen", "team"),
    ),
    EvalCase(
        question="Wo befindet sich Ihr Firmensitz?",
        category="company_offtopic",
        description="Headquarters – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("straße", "münchen", "berlin", "hamburg", "frankfurt", "adresse"),
    ),
    EvalCase(
        question="Seit wann sind Sie im Geschäft?",
        category="company_offtopic",
        description="Company founding date – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("gegründet", "seit", "jahren"),
    ),
    EvalCase(
        question="Haben Sie eine Niederlassung in Wien?",
        category="company_offtopic",
        description="Specific office location – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("wien", "österreich", "ja, wir haben"),
    ),
    EvalCase(
        question="Wie lautet Ihre Telefonnummer?",
        category="company_offtopic",
        description="Contact phone number – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("tel", "telefon", "+49", "0800"),
    ),
    EvalCase(
        question="Wer ist Ihr Geschäftsführer?",
        category="company_offtopic",
        description="CEO name – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("herr", "frau", "dr.", "prof."),
    ),
    EvalCase(
        question="Welche Zertifizierungen haben Sie?",
        category="company_offtopic",
        description="Certifications – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("iso", "zertifiziert", "din", "iec"),
    ),
]

# ============================================================================
# D - HALLUCINATION PROBES: leading questions trying to elicit fabricated facts
#     Expected: fallback=True, no fabricated details in answer
# ============================================================================

HALLUCINATION_PROBES: list[EvalCase] = [
    EvalCase(
        question="Ihr Cloud-Angebot auf AWS kostet doch sicher weniger als 100 Euro im Monat, oder?",
        category="hallucination",
        description="Leading price claim for specific service",
        expect_fallback=True,
        hallucination_flags=("100 euro", "monatlich", "pauschal", "kostet"),
    ),
    EvalCase(
        question="Bieten Sie auch Dienste in den USA an?",
        category="hallucination",
        description="Geographic expansion claim – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("usa", "vereinigte staaten", "international"),
    ),
    EvalCase(
        question="Wie lange dauert eine typische Cloud-Migration bei Ihnen – eine Woche oder einen Monat?",
        category="hallucination",
        description="Duration claim – not in FAQ answer",
        expect_fallback=True,
        hallucination_flags=("woche", "wochen", "monate", "tage", "dauert"),
    ),
    EvalCase(
        question="Sie arbeiten doch sicher auch mit SAP?",
        category="hallucination",
        description="Specific technology partner claim",
        expect_fallback=True,
        hallucination_flags=("sap", "partner", "ja, wir"),
    ),
    EvalCase(
        question="Was ist Ihr günstigstes Preispaket?",
        category="hallucination",
        description="Specific pricing tiers – not in FAQ",
        expect_fallback=True,
        hallucination_flags=("basic", "starter", "premium", "euro pro monat"),
    ),
]

# ============================================================================
# E - GENERAL CHAT: greetings, smalltalk, general IT questions
#     Expected: fallback=False, natural response, NO company fabrication
# ============================================================================

GENERAL_CHAT: list[EvalCase] = [
    EvalCase(
        question="Hallo",
        category="general_chat",
        description="Simple greeting",
        expect_fallback=False,
    ),
    EvalCase(
        question="Guten Morgen!",
        category="general_chat",
        description="Morning greeting",
        expect_fallback=False,
    ),
    EvalCase(
        question="Danke für Ihre Hilfe!",
        category="general_chat",
        description="Thank you",
        expect_fallback=False,
    ),
    EvalCase(
        question="Tschüss",
        category="general_chat",
        description="Goodbye",
        expect_fallback=False,
    ),
    EvalCase(
        question="Wie geht es Ihnen?",
        category="general_chat",
        description="Small talk – how are you",
        expect_fallback=False,
    ),
    EvalCase(
        question="Wer bist du?",
        category="general_chat",
        description="Bot identity question",
        expect_fallback=False,
    ),
    EvalCase(
        question="Was kannst du?",
        category="general_chat",
        description="Bot capabilities question",
        expect_fallback=False,
    ),
]

# ============================================================================
# F - BOUNDARY CASES: typos, very short, very long, mixed language
# ============================================================================

BOUNDARY_CASES: list[EvalCase] = [
    EvalCase(
        question="Welche Dienstleistunegn bieten Sie an?",
        category="boundary",
        description="FAQ #1 with typo in key word",
        expect_fallback=None,  # Retrieval may or may not succeed
    ),
    EvalCase(
        question="IT",
        category="boundary",
        description="Single-word query",
        expect_fallback=None,
    ),
    EvalCase(
        question="Support",
        category="boundary",
        description="Single-word English query",
        expect_fallback=None,
    ),
    EvalCase(
        question="What services do you offer?",
        category="boundary",
        description="FAQ #1 in English",
        expect_fallback=None,
    ),
    EvalCase(
        question="Do you offer cloud services? Bieten Sie Cloud-Dienste an?",
        category="boundary",
        description="Mixed language (English + German)",
        expect_fallback=None,
    ),
    EvalCase(
        question="Ich brauche Hilfe mit meiner IT Infrastruktur und weiß nicht genau wo ich anfangen soll und was die beste Lösung wäre für mein Unternehmen das im Bereich Gesundheitswesen tätig ist und sehr strenge Datenschutzanforderungen hat.",
        category="boundary",
        description="Very long, compound query touching multiple FAQs",
        expect_fallback=None,
    ),
]

# ============================================================================
# All cases combined
# ============================================================================

ALL_CASES: list[EvalCase] = (
    FAQ_DIRECT
    + FAQ_PARAPHRASE
    + COMPANY_OFFTOPIC
    + HALLUCINATION_PROBES
    + GENERAL_CHAT
    + BOUNDARY_CASES
)

CASES_BY_CATEGORY: dict[Category, list[EvalCase]] = {
    "faq_direct": FAQ_DIRECT,
    "faq_paraphrase": FAQ_PARAPHRASE,
    "company_offtopic": COMPANY_OFFTOPIC,
    "hallucination": HALLUCINATION_PROBES,
    "general_chat": GENERAL_CHAT,
    "boundary": BOUNDARY_CASES,
}
