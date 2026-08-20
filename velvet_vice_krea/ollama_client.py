"""Dependency-free Ollama client used by the Krea Prompt Director."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable
from urllib import error, parse, request


class OllamaDirectorError(RuntimeError):
    """Raised when Ollama cannot produce or release a usable prompt model."""


@dataclass(frozen=True)
class OllamaGenerationOptions:
    num_ctx: int = 4096
    num_predict: int = 600
    temperature: float = 0.22
    repeat_penalty: float = 1.1
    top_p: float = 0.85
    seed: int = 728461

    def as_api_options(self) -> dict[str, int | float]:
        return {
            "num_ctx": self.num_ctx,
            "num_predict": self.num_predict,
            "temperature": self.temperature,
            "repeat_penalty": self.repeat_penalty,
            "top_p": self.top_p,
            "seed": self.seed,
        }


def _normalize_base_url(value: str) -> str:
    base_url = str(value).strip().rstrip("/")
    parsed = parse.urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise OllamaDirectorError(
            "Ollama URL must be a complete http:// or https:// address."
        )
    return base_url


def _clean_generated_text(value: str) -> str:
    text = value.strip()
    text = re.sub(r"^\s*<think>.*?</think>\s*", "", text, flags=re.DOTALL)
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    return text


class OllamaClient:
    """Call Ollama's HTTP API without external Python packages."""

    def __init__(self, opener: Callable[..., object] | None = None) -> None:
        self._opener = opener or request.urlopen

    def _request_json(
        self,
        *,
        base_url: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        timeout_seconds: int,
    ) -> dict[str, Any]:
        normalized_url = _normalize_base_url(base_url)
        body = None
        headers: dict[str, str] = {"Accept": "application/json"}
        method = "GET"
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
            method = "POST"

        http_request = request.Request(
            f"{normalized_url}{endpoint}",
            data=body,
            headers=headers,
            method=method,
        )

        try:
            with self._opener(
                http_request,
                timeout=max(1, int(timeout_seconds)),
            ) as response:
                raw_response = response.read()
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise OllamaDirectorError(
                f"Ollama returned HTTP {exc.code}: {details or exc.reason}"
            ) from exc
        except error.URLError as exc:
            raise OllamaDirectorError(
                f"Cannot reach Ollama at {normalized_url}: {exc.reason}"
            ) from exc
        except TimeoutError as exc:
            raise OllamaDirectorError(
                f"Ollama did not respond within {timeout_seconds} seconds."
            ) from exc
        except OSError as exc:
            raise OllamaDirectorError(f"Ollama request failed: {exc}") from exc

        try:
            return json.loads(raw_response.decode("utf-8")) if raw_response else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OllamaDirectorError(
                f"Ollama returned invalid JSON from {endpoint}."
            ) from exc

    def generate(
        self,
        *,
        base_url: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        options: OllamaGenerationOptions,
        timeout_seconds: int,
        unload_after_generation: bool,
        response_format: str | None = None,
    ) -> str:
        model_name = str(model).strip()
        if not model_name:
            raise OllamaDirectorError("Ollama model name is empty.")

        payload: dict[str, Any] = {
            "model": model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "think": False,
            "keep_alive": 0 if unload_after_generation else "1m",
            "options": options.as_api_options(),
        }
        if response_format:
            payload["format"] = response_format

        response_data = self._request_json(
            base_url=base_url,
            endpoint="/api/generate",
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        generated = response_data.get("response")
        if not isinstance(generated, str):
            api_error = response_data.get("error")
            if api_error:
                raise OllamaDirectorError(f"Ollama error: {api_error}")
            raise OllamaDirectorError(
                "Ollama response did not contain generated text."
            )

        final_text = _clean_generated_text(generated)
        if not final_text:
            raise OllamaDirectorError("Ollama returned an empty prompt.")
        return final_text

    def running_models(
        self,
        *,
        base_url: str,
        timeout_seconds: int = 5,
    ) -> list[dict[str, Any]]:
        response = self._request_json(
            base_url=base_url,
            endpoint="/api/ps",
            payload=None,
            timeout_seconds=timeout_seconds,
        )
        models = response.get("models", [])
        return models if isinstance(models, list) else []

    @staticmethod
    def _normal_model_name(value: Any) -> tuple[str, str]:
        name = str(value or "").strip().lower()
        return name, name.split(":", 1)[0]

    @classmethod
    def model_is_loaded(
        cls,
        models: Iterable[dict[str, Any]],
        requested_model: str,
    ) -> bool:
        requested, requested_base = cls._normal_model_name(requested_model)
        for entry in models:
            if not isinstance(entry, dict):
                continue
            candidate = (
                entry.get("name")
                or entry.get("model")
                or entry.get("model_name")
            )
            candidate, candidate_base = cls._normal_model_name(candidate)
            if candidate and (
                candidate == requested or candidate_base == requested_base
            ):
                return True
        return False

    def release_models(
        self,
        *,
        base_url: str,
        models: Iterable[str],
        timeout_seconds: int,
    ) -> None:
        unique_models = tuple(
            dict.fromkeys(
                str(model).strip() for model in models if str(model).strip()
            )
        )
        if not unique_models:
            return

        timeout_seconds = max(3, int(timeout_seconds))
        deadline = time.monotonic() + timeout_seconds
        running = self.running_models(
            base_url=base_url,
            timeout_seconds=min(5, timeout_seconds),
        )
        loaded_models = [
            model
            for model in unique_models
            if self.model_is_loaded(running, model)
        ]
        if not loaded_models:
            return

        for model in loaded_models:
            self._request_json(
                base_url=base_url,
                endpoint="/api/generate",
                payload={
                    "model": model,
                    "prompt": "",
                    "keep_alive": 0,
                    "stream": False,
                },
                timeout_seconds=timeout_seconds,
            )

        still_loaded = loaded_models
        while time.monotonic() < deadline:
            remaining = max(1, int(deadline - time.monotonic()))
            running = self.running_models(
                base_url=base_url,
                timeout_seconds=min(5, remaining),
            )
            still_loaded = [
                model
                for model in loaded_models
                if self.model_is_loaded(running, model)
            ]
            if not still_loaded:
                return
            time.sleep(0.25)

        raise OllamaDirectorError(
            "Ollama acknowledged the unload request, but these models "
            f"remained loaded after {timeout_seconds} seconds: "
            f"{', '.join(still_loaded)}"
        )
