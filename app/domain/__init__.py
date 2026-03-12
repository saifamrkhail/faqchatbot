"""Domain models for the FAQ chatbot."""
"""Domain package exports."""

from app.domain.faq import FAQEntry, FAQValidationError

__all__ = ["FAQEntry", "FAQValidationError"]
