from __future__ import annotations

import json
import time
from typing import Any

from openai import OpenAI

from app.config import Settings
from app.llm.prompts import SYSTEM_PROMPT


class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )

    def chat(self, user_prompt: str, *, temperature: float = 0.1) -> str:
        response = self._with_retry(
            lambda: self._client.chat.completions.create(
                model=self._settings.openrouter_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                extra_headers={
                    "HTTP-Referer": self._settings.openrouter_http_referer,
                    "X-Title": self._settings.openrouter_title,
                },
            )
        )
        return response.choices[0].message.content or ""

    def chat_json(self, user_prompt: str, schema_name: str) -> dict[str, Any]:
        payload = self.chat(
            f"{user_prompt}\n\nReturn valid JSON matching schema name: {schema_name}.",
            temperature=0.0,
        )
        return json.loads(payload)

    def _with_retry(self, fn: Any, retries: int = 3, base_delay: float = 0.5) -> Any:
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt == retries - 1:
                    raise
                # Exponential backoff for transient OpenRouter/network failures.
                time.sleep(base_delay * (2 ** attempt))
        raise RuntimeError("OpenRouter request failed unexpectedly") from last_error
