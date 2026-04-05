from __future__ import annotations

from app.llm.openrouter_client import OpenRouterClient


def synthesize_notes(client: OpenRouterClient, excerpts: str) -> str:
    return client.chat(
        "Create a concise synthesis page draft with wikilinks where semantically useful.\n\n"
        f"Excerpts:\n{excerpts}"
    )
