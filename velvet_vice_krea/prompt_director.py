"""VELVET VICE KREA PROMPT DIRECTOR v2 ComfyUI node."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable

from .memory_gate import unload_comfy_models_before_ollama
from .ollama_client import (
    OllamaClient,
    OllamaDirectorError,
    OllamaGenerationOptions,
)
from .prompt_profiles import PROFILE_PROMPTS, get_profile_prompt
from .workflow_router import prompt_profile_for_mode


PROMPT_MODES = ("MANUAL", "ASSISTED")
DIRECTOR_FREEDOM = ("STRICT", "BALANCED", "CREATIVE")


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def _adaptive_word_range(profile: str, source_words: int, freedom: str) -> tuple[int, int]:
    source_words = max(1, int(source_words))
    freedom = freedom if freedom in DIRECTOR_FREEDOM else "BALANCED"

    if profile == "NATIVE EDIT":
        base = (
            (35, 65) if source_words <= 12 else
            (45, 85) if source_words <= 35 else
            (55, 105)
        )
    elif profile == "CLASSIC IMG2IMG":
        base = (
            (45, 80) if source_words <= 12 else
            (60, 105) if source_words <= 35 else
            (75, 130)
        )
    else:
        base = (
            (45, 75) if source_words <= 12 else
            (60, 105) if source_words <= 35 else
            (75, 130)
        )

    adjustments = {
        "STRICT": (-10, -10),
        "BALANCED": (0, 0),
        "CREATIVE": (15, 25),
    }
    low_adjust, high_adjust = adjustments[freedom]
    return max(30, base[0] + low_adjust), min(180, base[1] + high_adjust)


def _v2_system_prompt(profile: str, source_words: int, freedom: str) -> str:
    low, high = _adaptive_word_range(profile, source_words, freedom)
    freedom_rules = {
        "STRICT": (
            "Make the smallest useful intervention. Correct, translate, organize, "
            "and clarify. Add only details that are necessary to make the image "
            "instruction executable."
        ),
        "BALANCED": (
            "Preserve every explicit fact while adding compatible camera, lighting, "
            "material, spatial, and atmosphere details only where the user left a gap."
        ),
        "CREATIVE": (
            "Preserve every explicit fact, then provide stronger art direction in "
            "unspecified areas such as lighting, composition, material response, depth, "
            "and atmosphere. Never change the requested subject, action, location, or style."
        ),
    }[freedom]

    return (
        get_profile_prompt(profile)
        + "\n\nVELVET VICE KREA PROMPT DIRECTOR v2 OVERRIDE:\n"
        + "The user's source text is authoritative. Treat every explicit number, subject count, "
          "identity, age statement, anatomy fact, pose, action, gaze, expression, clothing item, "
          "color, object, location, camera instruction, composition instruction, style request, "
          "and spatial relationship as a HARD CONSTRAINT. Do not remove, contradict, swap, or "
          "silently reinterpret those facts. Do not invent extra people or major objects.\n"
        + f"DIRECTOR FREEDOM: {freedom}. {freedom_rules}\n"
        + f"ADAPTIVE LENGTH TARGET: normally {low} to {high} English words. If the user's source "
          "is already detailed, prefer compression and deduplication over expansion.\n"
        + "Normalize repeated concepts, contradictory accidental wording, mixed-language fragments, "
          "and tag-like clutter into one clean natural-language instruction while preserving intent.\n"
        + "For multiple subjects, make placement and contact explicit enough to reduce merged bodies, "
          "limbs, clothing, and identities.\n"
        + "Return STRICT JSON only, with exactly these keys: final_prompt, intent_summary, "
          "hard_constraints, added_details. final_prompt must be one clean English paragraph with no "
          "markdown, headings, bullets, negative prompt, sampler settings, CFG, seed, or resolution. "
          "hard_constraints and added_details must be JSON arrays of short strings."
    )


def _normalize_final_prompt(text: str) -> str:
    text = str(text or "").strip()
    text = re.sub(r"^\s*(?:final[_ ]prompt|prompt)\s*:\s*", "", text, flags=re.I)
    text = text.replace("```", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_assisted_response(raw: str) -> tuple[str, dict]:
    diagnostics = {
        "intent_summary": "",
        "hard_constraints": [],
        "added_details": [],
        "structured": False,
    }
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return _normalize_final_prompt(raw), diagnostics

    if not isinstance(payload, dict):
        return _normalize_final_prompt(raw), diagnostics

    final_prompt = _normalize_final_prompt(payload.get("final_prompt", ""))
    if not final_prompt:
        return _normalize_final_prompt(raw), diagnostics

    diagnostics["intent_summary"] = str(payload.get("intent_summary", "")).strip()
    for key in ("hard_constraints", "added_details"):
        value = payload.get(key, [])
        if isinstance(value, list):
            diagnostics[key] = [str(item).strip() for item in value if str(item).strip()]
    diagnostics["structured"] = True
    return final_prompt, diagnostics


def _validation_summary(final_prompt: str, low: int, high: int, structured: bool) -> str:
    warnings: list[str] = []
    words = count_words(final_prompt)
    if words < max(20, int(low * 0.55)):
        warnings.append(f"short {words}w")
    if words > int(high * 1.35):
        warnings.append(f"long {words}w")
    if re.search(r"(^|\s)[#*•]\s", final_prompt):
        warnings.append("formatting")
    if "```" in final_prompt:
        warnings.append("markdown")
    if not structured:
        warnings.append("JSON fallback")
    return "VALID" if not warnings else "CHECK · " + ", ".join(warnings)


@dataclass(frozen=True)
class PromptDirectorResult:
    final_prompt: str
    word_count: int
    character_count: int
    profile: str
    status: str
    prompt_package: dict
    validation: str

    def as_tuple(self):
        return (
            self.final_prompt,
            self.word_count,
            self.character_count,
            self.profile,
            self.status,
            self.prompt_package,
            self.validation,
        )


class PromptDirectorEngine:
    """Pure prompt composition layer. External Comfy memory handoff lives in the node."""

    def __init__(self, client_factory: Callable[[], OllamaClient] = OllamaClient) -> None:
        self._client_factory = client_factory

    def run(
        self,
        *,
        profile: str,
        prompt_mode: str,
        manual_prompt: str | None,
        short_idea: str | None,
        ollama_url: str,
        ollama_model: str,
        num_ctx: int,
        num_predict: int,
        temperature: float,
        repeat_penalty: float,
        top_p: float,
        ollama_seed: int,
        timeout_seconds: int,
        unload_after_generation: bool,
        director_freedom: str = "BALANCED",
    ) -> tuple:
        get_profile_prompt(profile)
        if director_freedom not in DIRECTOR_FREEDOM:
            raise ValueError(
                f"Unsupported Director Freedom: {director_freedom!r}. "
                f"Supported values: {', '.join(DIRECTOR_FREEDOM)}."
            )

        if prompt_mode == "MANUAL":
            selected_prompt = manual_prompt if manual_prompt is not None else ""
            if not selected_prompt.strip():
                raise ValueError("Manual Prompt is empty.")
            final_prompt = selected_prompt
            validation = "MANUAL · unchanged"
            package = {
                "schema": "VELVET_VICE_KREA_PROMPT_PACKAGE",
                "schema_version": 2,
                "final_prompt": final_prompt,
                "mode": prompt_mode,
                "profile": profile,
                "director_freedom": director_freedom,
                "ollama_url": ollama_url,
                "ollama_model": ollama_model,
                "used_models": [],
                "ollama_call_count": 0,
                "release_required": False,
                "validation": validation,
            }
            status = "MANUAL · Ollama not contacted"
        elif prompt_mode == "ASSISTED":
            idea = short_idea if short_idea is not None else ""
            if not idea.strip():
                raise ValueError("Short Idea is empty.")
            model_name = str(ollama_model).strip()
            if not model_name:
                raise ValueError("Ollama model name is empty.")

            source_words = count_words(idea)
            low, high = _adaptive_word_range(profile, source_words, director_freedom)
            client = self._client_factory()
            raw = client.generate(
                base_url=ollama_url,
                model=model_name,
                system_prompt=_v2_system_prompt(profile, source_words, director_freedom),
                user_prompt=idea,
                options=OllamaGenerationOptions(
                    num_ctx=int(num_ctx),
                    num_predict=int(num_predict),
                    temperature=float(temperature),
                    repeat_penalty=float(repeat_penalty),
                    top_p=float(top_p),
                    seed=int(ollama_seed),
                ),
                timeout_seconds=int(timeout_seconds),
                unload_after_generation=bool(unload_after_generation),
                response_format="json",
            )
            final_prompt, diagnostics = _parse_assisted_response(raw)
            if not final_prompt:
                raise OllamaDirectorError("Ollama returned no usable final Krea prompt.")
            validation = _validation_summary(
                final_prompt,
                low,
                high,
                bool(diagnostics.get("structured")),
            )
            package = {
                "schema": "VELVET_VICE_KREA_PROMPT_PACKAGE",
                "schema_version": 2,
                "final_prompt": final_prompt,
                "mode": prompt_mode,
                "profile": profile,
                "director_freedom": director_freedom,
                "ollama_url": ollama_url,
                "ollama_model": model_name,
                "used_models": [model_name],
                "ollama_call_count": 1,
                "release_required": True,
                "validation": validation,
                "intent_summary": diagnostics.get("intent_summary", ""),
                "hard_constraints": diagnostics.get("hard_constraints", []),
                "added_details": diagnostics.get("added_details", []),
                "adaptive_word_target": [low, high],
            }
            status = (
                f"ASSISTED · 1 Ollama call · {director_freedom} · "
                f"target {low}-{high}w · release barrier required · {validation}"
            )
        else:
            raise ValueError(
                f"Unsupported Prompt Mode: {prompt_mode!r}. "
                f"Supported modes: {', '.join(PROMPT_MODES)}."
            )

        result = PromptDirectorResult(
            final_prompt=final_prompt,
            word_count=count_words(final_prompt),
            character_count=len(final_prompt),
            profile=profile,
            status=status,
            prompt_package=package,
            validation=validation,
        )
        return result.as_tuple()


class VelvetViceKreaPromptDirector:
    """Manual/Assisted Krea director with one-call Qwen v2 composition."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "direct"
    RETURN_TYPES = (
        "STRING",
        "INT",
        "INT",
        "STRING",
        "STRING",
        "VELVET_VICE_KREA_PROMPT_PACKAGE",
        "STRING",
    )
    RETURN_NAMES = (
        "final_prompt",
        "word_count",
        "character_count",
        "profile",
        "status",
        "prompt_package",
        "validation",
    )
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "profile": (tuple(PROFILE_PROMPTS.keys()),),
                "prompt_mode": (PROMPT_MODES,),
                "manual_prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": False,
                        "lazy": True,
                    },
                ),
                "short_idea": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "dynamicPrompts": False,
                        "lazy": True,
                    },
                ),
                "ollama_url": ("STRING", {"default": "http://127.0.0.1:11434"}),
                "ollama_model": (
                    "STRING",
                    {
                        "default": (
                            "fredrezones55/"
                            "Qwen3.5-Uncensored-HauhauCS-Aggressive:9b"
                        )
                    },
                ),
                "unload_after_generation": ("BOOLEAN", {"default": True}),
                "num_ctx": (
                    "INT",
                    {
                        "default": 4096,
                        "min": 512,
                        "max": 131072,
                        "step": 512,
                        "advanced": True,
                    },
                ),
                "num_predict": (
                    "INT",
                    {
                        "default": 600,
                        "min": 32,
                        "max": 4096,
                        "step": 16,
                        "advanced": True,
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.22,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.01,
                        "round": 0.01,
                        "advanced": True,
                    },
                ),
                "repeat_penalty": (
                    "FLOAT",
                    {
                        "default": 1.1,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.01,
                        "round": 0.01,
                        "advanced": True,
                    },
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 0.85,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "round": 0.01,
                        "advanced": True,
                    },
                ),
                "ollama_seed": (
                    "INT",
                    {
                        "default": 728461,
                        "min": 0,
                        "max": 0x7FFFFFFF,
                        "step": 1,
                        "advanced": True,
                    },
                ),
                "timeout_seconds": (
                    "INT",
                    {
                        "default": 300,
                        "min": 5,
                        "max": 1800,
                        "step": 5,
                        "advanced": True,
                    },
                ),
                # Added at the end to preserve widget-order compatibility with v1.0.x workflows.
                "director_freedom": (DIRECTOR_FREEDOM, {"default": "BALANCED"}),
            },
            "optional": {
                "mode_override": ("VELVET_VICE_KREA_MODE",),
            },
        }

    def check_lazy_status(
        self,
        profile,
        prompt_mode,
        manual_prompt=None,
        short_idea=None,
        mode_override=None,
        **kwargs,
    ):
        del self
        del profile, mode_override, kwargs
        if prompt_mode == "MANUAL" and manual_prompt is None:
            return ["manual_prompt"]
        if prompt_mode == "ASSISTED" and short_idea is None:
            return ["short_idea"]
        return []

    def direct(
        self,
        profile,
        prompt_mode,
        manual_prompt=None,
        short_idea=None,
        ollama_url="http://127.0.0.1:11434",
        ollama_model="",
        unload_after_generation=True,
        num_ctx=4096,
        num_predict=600,
        temperature=0.22,
        repeat_penalty=1.1,
        top_p=0.85,
        ollama_seed=728461,
        timeout_seconds=300,
        director_freedom="BALANCED",
        mode_override=None,
    ):
        try:
            effective_profile = (
                prompt_profile_for_mode(mode_override)
                if mode_override is not None
                else profile
            )
            unload_result = None
            if prompt_mode == "ASSISTED":
                unload_result = unload_comfy_models_before_ollama()

            result = PromptDirectorEngine().run(
                profile=effective_profile,
                prompt_mode=prompt_mode,
                manual_prompt=manual_prompt,
                short_idea=short_idea,
                ollama_url=ollama_url,
                ollama_model=ollama_model,
                num_ctx=num_ctx,
                num_predict=num_predict,
                temperature=temperature,
                repeat_penalty=repeat_penalty,
                top_p=top_p,
                ollama_seed=ollama_seed,
                timeout_seconds=timeout_seconds,
                unload_after_generation=unload_after_generation,
                director_freedom=director_freedom,
            )
        except (ValueError, OllamaDirectorError, RuntimeError) as exc:
            raise RuntimeError(f"VELVET VICE KREA PROMPT DIRECTOR: {exc}") from exc

        final_prompt, words, characters, selected_profile, status, package, validation = result
        if unload_result is not None:
            status = f"{status} · {unload_result.summary()}"
            result = (
                final_prompt,
                words,
                characters,
                selected_profile,
                status,
                package,
                validation,
            )

        print(f"[VELVET VICE KREA] {status}")
        return {
            "ui": {
                "final_prompt": [final_prompt],
                "word_count": [str(words)],
                "character_count": [str(characters)],
                "profile": [selected_profile],
                "status": [status],
                "validation": [validation],
            },
            "result": result,
        }
