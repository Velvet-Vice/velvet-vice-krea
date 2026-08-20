from __future__ import annotations

import gc
from dataclasses import dataclass
from typing import Any

from .interrupt_cleanup import MemorySnapshot, _memory_snapshot


@dataclass(frozen=True)
class ComfyUnloadResult:
    loaded_model_count: int
    before: MemorySnapshot
    after: MemorySnapshot

    def summary(self) -> str:
        return (
            "pre-Qwen ComfyUI unload completed "
            f"({self.loaded_model_count} tracked model(s)); "
            f"after | {self.after.format()}"
        )


def log_memory_snapshot(label: str) -> MemorySnapshot:
    snapshot = _memory_snapshot()
    print(f"[VELVET VICE KREA] MEMORY | {label} | {snapshot.format()}")
    return snapshot


def unload_comfy_models_before_ollama() -> ComfyUnloadResult:
    """Mirror the proven LTX prompt-first handoff before Ollama/Qwen.

    This runs only for ASSISTED prompting. MANUAL mode never calls this path.
    It intentionally uses ComfyUI's own model manager, matching the LTX gate
    architecture that is already used in the Velvet Vice LTX workflows.
    """

    try:
        import comfy.model_management as model_management
    except ImportError as error:
        raise RuntimeError(
            "ComfyUI model management is unavailable. The Krea Prompt Director "
            "must run inside ComfyUI."
        ) from error

    before = log_memory_snapshot("before pre-Qwen unload")
    try:
        loaded_models: list[Any] = list(model_management.loaded_models())
        model_management.unload_all_models()
        gc.collect()
        model_management.soft_empty_cache()
    except (AttributeError, RuntimeError) as error:
        raise RuntimeError(
            "Could not unload ComfyUI models before starting Ollama/Qwen."
        ) from error

    after = log_memory_snapshot("after pre-Qwen unload")
    result = ComfyUnloadResult(len(loaded_models), before, after)
    print(f"[VELVET VICE KREA] MEMORY | {result.summary()}")
    return result
