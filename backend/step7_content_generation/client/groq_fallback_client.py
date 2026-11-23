"""High-speed Groq LPU Fallback Client for Step 7 Content Generation.

Activates automatically when Google Gemini encounters rate limits (429),
prepayment depletion (402), service unavailability (503), or network timeouts.
"""
import json
import re
import time
from typing import Any, Dict, List, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel

from backend.common.logging.logger import logger
from backend.step7_content_generation.config.gemini_settings import (
    GeminiSettings,
    get_gemini_settings,
)
from backend.step7_content_generation.exceptions import (
    GenerationExecutionError,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews

T = TypeVar("T", bound=BaseModel)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Primary and secondary Groq models
GROQ_PRIMARY_MODEL = "openai/gpt-oss-120b"
GROQ_SECONDARY_MODEL = "openai/gpt-oss-20b"


class GroqFallbackClient:
    """Ultra-fast LPU inference fallback client using Groq OpenAI-compatible API."""

    def __init__(self, settings: Optional[GeminiSettings] = None, timeout: float = 25.0):
        self.settings = settings or get_gemini_settings()
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check whether a Groq API key is configured."""
        return self.settings.has_groq_api_key()

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T] = GeneratedNews,
        temperature: Optional[float] = None,
    ) -> T:
        """Call Groq LPU to generate structured JSON matching response_schema.

        Tries primary model (120b), cascading to secondary model (20b) if needed.
        """
        api_key = self.settings.get_groq_api_key()
        if not api_key:
            raise GenerationExecutionError(
                "Groq fallback requested but GROQ_API_KEY is not configured in backend/.env"
            )

        temp = temperature if temperature is not None else 0.2
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ESTD-NewsEngine/1.0",
        }

        # Build schema instructions to guarantee strict compliance
        schema_json_str = json.dumps(response_schema.model_json_schema(), indent=2)
        system_instruction = (
            "You are the ESTD Editorial News Synthesizer. You synthesize factual source information "
            "into structured editorial briefs without speculation or hallucination.\n"
            "CRITICAL: You MUST respond ONLY with a single valid JSON object strictly matching this JSON Schema:\n"
            f"{schema_json_str}\n"
            "Do not include any markdown formatting, markdown backticks (e.g. ```json), or text outside the JSON object."
        )

        models_to_try = [
            self.settings.groq_model or GROQ_PRIMARY_MODEL,
            GROQ_SECONDARY_MODEL,
        ]
        # Deduplicate while preserving order
        unique_models = []
        for m in models_to_try:
            if m not in unique_models:
                unique_models.append(m)

        last_error: Optional[Exception] = None

        for model_name in unique_models:
            try:
                logger.info(f"[Groq Fallback] Dispatching generation to Groq LPU model '{model_name}'...")
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temp,
                    "max_tokens": 6144,
                    "response_format": {"type": "json_object"},
                }

                start_time = time.monotonic()
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(GROQ_API_URL, headers=headers, json=payload)

                elapsed_ms = (time.monotonic() - start_time) * 1000

                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise GenerationExecutionError("Groq returned empty choices.")

                    raw_content = choices[0].get("message", {}).get("content", "").strip()
                    logger.info(
                        f"[Groq Fallback] Inference completed in {elapsed_ms:.1f}ms via {model_name}."
                    )

                    # Strip code fences if model enclosed JSON in ```json ... ```
                    cleaned_content = re.sub(r"^```(?:json)?\s*", "", raw_content, flags=re.MULTILINE)
                    cleaned_content = re.sub(r"\s*```$", "", cleaned_content, flags=re.MULTILINE).strip()

                    parsed_obj = json.loads(cleaned_content)
                    return response_schema.model_validate(parsed_obj)

                # If non-200, check code
                safe_err = self.settings.mask_secret(resp.text)
                logger.warning(
                    f"[Groq Fallback] Model '{model_name}' returned status {resp.status_code}: {safe_err[:120]}"
                )
                last_error = GenerationExecutionError(f"Groq {model_name} HTTP {resp.status_code}: {safe_err}")

                # If rate-limited (429), backoff briefly before cascading to next fallback model
                if resp.status_code == 429:
                    time.sleep(2.0)

            except Exception as exc:
                safe_msg = self.settings.mask_secret(str(exc))
                logger.warning(f"[Groq Fallback] Attempt with model '{model_name}' notice: {safe_msg}")
                last_error = exc

        # If all models failed, raise last error
        raise GenerationExecutionError(f"All Groq fallback models failed: {last_error}")
