"""Repository layer for local project data sources."""
"""Repository package exports."""

from app.repositories.faq_repository import FAQRepository, FAQRepositoryError

__all__ = ["FAQRepository", "FAQRepositoryError"]
