"""Dedicated Gemini AI client for Step 7 content generation."""
import json
import time
from typing import Any, Dict, Optional, Type, TypeVar

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel

from backend.common.logging.logger import logger
from backend.step7_content_generation.config.gemini_settings import (
    GeminiSettings,
    get_gemini_settings,
)
from backend.step7_content_generation.exceptions import (
    GeminiAuthenticationError,
    GeminiConfigurationError,
    GeminiConnectionError,
    GeminiModelError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GenerationExecutionError,
)
from backend.step7_content_generation.schemas.generated_news import GeneratedNews

T = TypeVar("T", bound=BaseModel)


class GeminiClient:
    """Client for generating fact-grounded content using Google Gemini models."""

    def __init__(
        self,
        settings: Optional[GeminiSettings] = None,
        client: Optional[genai.Client] = None,
    ):
        self.settings = settings or get_gemini_settings()
        self._external_client = client
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> genai.Client:
        """Lazily initialize and return the authenticated google-genai Client."""
        if self._external_client is not None:
            return self._external_client

        if self._client is None:
            api_key = self.settings.get_gemini_api_key()
            logger.info("Initializing Google Gemini client...")
            try:
                self._client = genai.Client(api_key=api_key)
            except Exception as exc:
                safe_msg = self.settings.mask_secret(str(exc))
                logger.error(f"Failed to initialize Gemini client: {safe_msg}")
                raise GeminiConfigurationError(f"Client initialization failed: {safe_msg}")
        return self._client

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T] = GeneratedNews,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        """Send a generation prompt to Gemini and return validated structured output.

        Implements controlled retry policy for transient errors (429, 503, timeouts),
        masks all sensitive tokens in logs/errors, and strictly enforces structured JSON schema.

        Args:
            prompt: Formatted text generation prompt.
            response_schema: Pydantic model class to constrain Gemini output.
            model: Optional model override. Defaults to configured settings.gemini_model.
            temperature: Optional temperature override. Defaults to settings.gemini_temperature.

        Returns:
            Instance of response_schema populated with Gemini response.

        Raises:
            GeminiAuthenticationError: On 401/403 or invalid API key (non-retryable).
            GeminiModelError: On invalid or non-existent model (non-retryable).
            GeminiRateLimitError: On persistent rate limits.
            GeminiTimeoutError: On request timeout.
            GenerationExecutionError: On malformed or empty output.
        """
        target_model = model or self.settings.gemini_model
        temp = temperature if temperature is not None else self.settings.gemini_temperature
        max_retries = self.settings.gemini_max_retries
        client = self._get_client()

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=temp,
            max_output_tokens=self.settings.gemini_max_output_tokens,
        )

        last_error: Optional[Exception] = None

        for attempt in range(1, max_retries + 2):
            try:
                logger.info(
                    f"Calling Gemini API | model='{target_model}' | attempt={attempt}/{max_retries + 1}"
                )
                start_time = time.monotonic()

                response = client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=config,
                )

                elapsed_ms = (time.monotonic() - start_time) * 1000
                logger.info(f"Gemini API returned response in {elapsed_ms:.1f}ms")

                # Handle parsed response
                if hasattr(response, "parsed") and response.parsed is not None:
                    if isinstance(response.parsed, response_schema):
                        return response.parsed
                    if isinstance(response.parsed, dict):
                        return response_schema.model_validate(response.parsed)

                # Fallback to parsing response.text if parsed is None
                raw_text = getattr(response, "text", "")
                if not raw_text or not raw_text.strip():
                    raise GenerationExecutionError("Gemini returned an empty response.")

                return response_schema.model_validate_json(raw_text.strip())

            except genai_errors.APIError as exc:
                status_code = getattr(exc, "code", None)
                raw_msg = self.settings.mask_secret(str(exc))

                # 1. Authentication / Permission errors (NON-RETRYABLE)
                if status_code in (401, 403) or "API_KEY_INVALID" in raw_msg or "PERMISSION_DENIED" in raw_msg:
                    logger.error(f"Gemini authentication failed: {raw_msg}")
                    raise GeminiAuthenticationError(
                        "Gemini API authentication failed. Verify GEMINI_API_KEY."
                    )

                # 2. Model Not Found / Invalid Argument (NON-RETRYABLE)
                if status_code in (404, 400) or "NOT_FOUND" in raw_msg:
                    logger.error(f"Gemini model error: {raw_msg}")
                    raise GeminiModelError(target_model, raw_msg)

                # 3. Rate Limit / Quota Exhaustion (RETRYABLE)
                if status_code == 429 or "RESOURCE_EXHAUSTED" in raw_msg:
                    logger.warning(
                        f"Gemini rate limit encountered on attempt {attempt}: {raw_msg}"
                    )
                    last_error = GeminiRateLimitError(raw_msg)
                    if attempt <= max_retries:
                        backoff = 2.0 ** attempt
                        time.sleep(backoff)
                        continue
                    raise last_error

                # 4. Server Errors / Transient (RETRYABLE)
                if status_code and status_code >= 500:
                    logger.warning(f"Gemini server error on attempt {attempt}: {raw_msg}")
                    last_error = GeminiConnectionError(f"Server error {status_code}: {raw_msg}")
                    if attempt <= max_retries:
                        time.sleep(1.5 * attempt)
                        continue
                    raise last_error

                logger.error(f"Gemini unhandled APIError: {raw_msg}")
                raise GenerationExecutionError(f"Gemini API failure: {raw_msg}")

            except (TimeoutError, Exception) as exc:
                raw_msg = self.settings.mask_secret(str(exc))
                if isinstance(exc, (GeminiAuthenticationError, GeminiModelError, GeminiRateLimitError)):
                    raise exc

                if "timeout" in raw_msg.lower():
                    last_error = GeminiTimeoutError(self.settings.gemini_timeout_seconds)
                    if attempt <= max_retries:
                        time.sleep(1.0)
                        continue
                    raise last_error

                logger.warning(f"Unexpected generation failure on attempt {attempt}: {raw_msg}")
                last_error = GenerationExecutionError(f"Content generation error: {raw_msg}")
                if attempt <= max_retries:
                    time.sleep(1.0)
                    continue
                raise last_error

        if last_error:
            raise last_error
        raise GenerationExecutionError("Generation failed after maximum retries.")

    def test_connectivity(self) -> Dict[str, Any]:
        """Perform a minimal, non-destructive test request to verify API connectivity.

        Returns:
            Dict containing model name, status, and latency.

        Raises:
            GenerationException: If connectivity fails.
        """
        target_model = self.settings.gemini_model
        client = self._get_client()
        start = time.monotonic()
        try:
            resp = client.models.generate_content(
                model=target_model,
                contents="Ping",
                config=types.GenerateContentConfig(max_output_tokens=10),
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            raw_text = getattr(resp, "text", "") or ""
            text = raw_text.strip()
            return {
                "status": "connected",
                "model": target_model,
                "latency_ms": round(elapsed_ms, 2),
                "response_received": bool(text or getattr(resp, "candidates", None)),
            }
        except genai_errors.APIError as exc:
            code = getattr(exc, "code", None)
            safe_msg = self.settings.mask_secret(str(exc))
            if code in (401, 403) or "API_KEY_INVALID" in safe_msg:
                raise GeminiAuthenticationError("Invalid or unauthorized GEMINI_API_KEY.")
            if code == 404:
                raise GeminiModelError(target_model, f"Model '{target_model}' not found.")
            raise GeminiConnectionError(f"Connection test failed: {safe_msg}")
        except Exception as exc:
            safe_msg = self.settings.mask_secret(str(exc))
            raise GeminiConnectionError(f"Connection error: {safe_msg}")
