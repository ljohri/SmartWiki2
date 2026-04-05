from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.llm.openrouter_client import OpenRouterClient
from app.llm.prompts import query_prompt
from app.services.linker import collect_markdown_pages

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
def query(payload: QueryRequest, settings: Settings = Depends(get_settings)) -> dict[str, object]:
    content_root = Path(settings.resolved_vault_path) / "content"
    pages = collect_markdown_pages(content_root)
    snippets: list[str] = []
    citations: list[str] = []
    for page in pages[:8]:
        text = page.read_text(encoding="utf-8")
        snippets.append(f"FILE: {page}\n{text[:1400]}")
        citations.append(str(page))
    context = "\n\n".join(snippets)

    if not settings.openrouter_api_key:
        return {
            "answer": "OPENROUTER_API_KEY is not set, so LLM query is disabled.",
            "citations": citations,
            "uncertainty": "No model call performed.",
        }

    client = OpenRouterClient(settings)
    answer = client.chat(query_prompt(payload.question, context), temperature=0.1)
    return {"answer": answer, "citations": citations}
