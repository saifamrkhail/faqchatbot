"""Prompt templates for grounded answer generation."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.faq import FAQEntry


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Single place where grounded and general-chat prompt contracts live."""

    fallback_message: str = "Leider konnte ich Ihre Frage nicht verstehen."

    def build_general(self, question: str) -> str:
        """Build the prompt used when retrieval found no trusted FAQ match."""

        question_normalized = question.strip()
        if not question_normalized:
            raise ValueError("Question must not be empty")

        return (
            "Du bist ein freundlicher Kundenservice-Assistent eines IT-Dienstleistungsunternehmens.\n\n"
            "Regeln:\n"
            "- Beantworte nur harmlose soziale Konversation wie Begrüßungen, Dank oder kurzen Smalltalk frei und natürlich auf Deutsch.\n"
            "- Wenn der Kunde nach konkreten Dienstleistungen, Preisen, Prozessen, "
            "Unternehmensdetails, Partnerschaften, Standorten, Zertifizierungen oder sonstigen "
            "unternehmensspezifischen Fakten fragt, antworte AUSSCHLIESSLICH und WORTWÖRTLICH "
            f'mit exakt dieser Nachricht – ohne jeden weiteren Satz: "{self.fallback_message}"\n'
            "- Erfinde niemals Informationen über das Unternehmen.\n"
            "- Erfinde keine Echtzeit-, Wetter- oder sonstigen Wissensfakten.\n"
            "- Antworte immer auf Deutsch. Sei freundlich und kurz.\n\n"
            f"Kunde: {question_normalized}\n\n"
            "Antwort:"
        )

    def build(self, question: str, faq_entry: FAQEntry) -> str:
        """Build the concrete prompt for one question and one FAQ match."""

        question_normalized = question.strip()
        if not question_normalized:
            raise ValueError("Question must not be empty")

        tags_str = ", ".join(faq_entry.tags) if faq_entry.tags else "keine"
        category_str = faq_entry.category or "allgemein"
        answer_preview = (
            faq_entry.answer[:200] + "…"
            if len(faq_entry.answer) > 200
            else faq_entry.answer
        )

        return (
            "Du bist ein FAQ-Assistent eines IT-Dienstleistungsunternehmens. "
            "Beantworte die Kundenfrage NUR anhand des folgenden FAQ-Kontexts. "
            f'Falls der Kontext nicht ausreicht, antworte genau mit: "{self.fallback_message}"\n'
            "Antworte auf Deutsch, kurz und sachlich.\n\n"
            f"Kundenfrage: {question_normalized}\n\n"
            f"FAQ-Kontext:\n"
            f"Frage: {faq_entry.question}\n"
            f"Antwort: {answer_preview}\n"
            f"Kategorie: {category_str}\n"
            f"Tags: {tags_str}\n\n"
            "Antwort:"
        )
