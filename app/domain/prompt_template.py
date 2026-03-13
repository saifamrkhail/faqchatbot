"""Prompt templates for grounded answer generation."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.faq import FAQEntry


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Template for building grounded answer generation prompts."""

    system_instruction: str = (
        "You are a helpful FAQ assistant. Answer the user's question using ONLY "
        "the provided FAQ context. Be concise, factual, and helpful. "
        "Do not answer outside the FAQ context."
    )

    def build(self, question: str, faq_entry: FAQEntry) -> str:
        """Build a grounded prompt from a question and FAQ entry.

        Returns a prompt string suitable for answer generation.
        """

        question_normalized = question.strip()
        if not question_normalized:
            raise ValueError("Question must not be empty")

        tags_str = ", ".join(faq_entry.tags) if faq_entry.tags else "none"
        category_str = faq_entry.category or "uncategorized"

        prompt = f"""{self.system_instruction}

User Question: {question_normalized}

FAQ Context:
Q: {faq_entry.question}
A: {faq_entry.answer}
Category: {category_str}
Tags: {tags_str}

Answer:"""

        return prompt
