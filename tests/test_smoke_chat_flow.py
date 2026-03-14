from __future__ import annotations

from dataclasses import dataclass

from app.domain import PromptTemplate
from app.infrastructure.qdrant_client import QdrantSearchResult
from app.services.answer_generator import AnswerGenerator
from app.services.chat_service import ChatService
from app.services.retriever import Retriever


@dataclass
class FakeOllamaClient:
    def embed_text(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]

    def generate(self, prompt: str) -> str:
        return "Sie können Ihr Passwort im Profil unter Sicherheit ändern."


@dataclass
class FakeQdrantClient:
    score: float

    def search(self, vector: list[float], *, limit: int, with_payload: bool = True) -> list[QdrantSearchResult]:
        assert vector
        assert limit > 0
        assert with_payload is True

        return [
            QdrantSearchResult(
                id="faq-1",
                score=self.score,
                payload={
                    "id": "faq-1",
                    "question": "Wie ändere ich mein Passwort?",
                    "answer": "Öffnen Sie Profil > Sicherheit und setzen Sie ein neues Passwort.",
                    "category": "konto",
                    "tags": ["passwort", "konto"],
                },
            )
        ]


def _build_chat_service(score: float) -> ChatService:
    retriever = Retriever(
        ollama_client=FakeOllamaClient(),
        qdrant_client=FakeQdrantClient(score=score),
        top_k=3,
        score_threshold=0.70,
    )
    answer_generator = AnswerGenerator(
        ollama_client=FakeOllamaClient(),
        prompt_template=PromptTemplate(),
        fallback_message="Fallback",
    )
    return ChatService(retriever=retriever, answer_generator=answer_generator)


def test_smoke_chat_flow_returns_grounded_answer_when_score_is_high() -> None:
    service = _build_chat_service(score=0.91)

    response = service.handle_question("Wie ändere ich mein Passwort?")

    assert response.is_fallback is False
    assert response.used_retrieval is True
    assert response.source_faq_id == "faq-1"
    assert "Passwort" in response.answer


def test_smoke_chat_flow_returns_fallback_when_score_is_below_threshold() -> None:
    service = _build_chat_service(score=0.40)

    response = service.handle_question("Wie ändere ich mein Passwort?")

    assert response.is_fallback is True
    assert response.used_retrieval is False
    assert response.source_faq_id is None
    assert response.answer == "Fallback"
