from __future__ import annotations

from app.llm.openrouter_client import OpenRouterClient


def classify_note_text(client: OpenRouterClient, text: str) -> dict:
    return client.chat_json(
        "Classify this note into one of: project, concept, entity, source-note, synthesis, decision.\n"
        f"Text:\n{text}",
        schema_name="ClassificationResult",
    )
