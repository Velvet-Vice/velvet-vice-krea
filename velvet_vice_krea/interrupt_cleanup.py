from __future__ import annotations

import gc
import logging
from dataclasses import dataclass
from functools import wraps
from typing import Any


GIB = 1024 ** 3
_PATCH_MARKER = "_velvet_vice_krea_interrupt_cleanup_v101"


@dataclass(frozen=True)
class MemorySnapshot:
    ram_available_gib: float | None
    process_rss_gib: float | None
    vram_free_gib: float | None
    vram_total_gib: float | None
    torch_allocated_gib: float | None
    torch_reserved_gib: float | None

    def format(self) -> str:
        fields: list[str] = []
        if self.ram_available_gib is not None:
            fields.append(f"RAM available {self.ram_available_gib:.1f} GiB")
        if self.process_rss_gib is not None:
            fields.append(f"ComfyUI RSS {self.process_rss_gib:.1f} GiB")
        if self.vram_free_gib is not None and self.vram_total_gib is not None:
            fields.append(
                f"VRAM free {self.vram_free_gib:.1f}/{self.vram_total_gib:.1f} GiB"
            )
        if self.torch_allocated_gib is not None:
            fields.append(f"Torch alloc {self.torch_allocated_gib:.2f} GiB")
        if self.torch_reserved_gib is not None:
            fields.append(f"Torch reserved {self.torch_reserved_gib:.2f} GiB")
        return " | ".join(fields) if fields else "memory telemetry unavailable"


def prompt_uses_velvet_vice_krea(prompt: Any) -> bool:
    if not isinstance(prompt, dict):
        return False
    for node in prompt.values():
        if not isinstance(node, dict):
            continue
        if str(node.get("class_type", "")).startswith("VelvetViceKrea"):
            return True
    return False


def execution_was_interrupted(executor: Any) -> bool:
    for message in getattr(executor, "status_messages", ()):
        if isinstance(message, (tuple, list)) and message:
            if message[0] == "execution_interrupted":
                return True
    return False


def _memory_snapshot(model_management: Any | None = None) -> MemorySnapshot:
    ram_available = None
    process_rss = None
    vram_free = None
    vram_total = None
    torch_allocated = None
    torch_reserved = None

    try:
        import psutil

        ram_available = float(psutil.virtual_memory().available) / GIB
        process_rss = float(psutil.Process().memory_info().rss) / GIB
    except Exception:
        pass

    try:
        import torch

        if torch.cuda.is_available():
            torch_allocated = float(torch.cuda.memory_allocated()) / GIB
            torch_reserved = float(torch.cuda.memory_reserved()) / GIB
    except Exception:
        pass

    try:
        if model_management is None:
            import comfy.model_management as model_management
        device = model_management.get_torch_device()
        vram_total = float(model_management.get_total_memory(device)) / GIB
        vram_free = float(model_management.get_free_memory(device)) / GIB
    except Exception:
        pass

    return MemorySnapshot(
        ram_available_gib=ram_available,
        process_rss_gib=process_rss,
        vram_free_gib=vram_free,
        vram_total_gib=vram_total,
        torch_allocated_gib=torch_allocated,
        torch_reserved_gib=torch_reserved,
    )


def _drop_interrupted_execution_caches(executor: Any) -> bool:
    """Discard only ComfyUI execution caches after an interrupted prompt."""
    reset = getattr(executor, "reset", None)
    if not callable(reset):
        return False
    reset()
    return True


def cleanup_after_interruption(
    executor: Any,
    *,
    model_management: Any | None = None,
) -> tuple[MemorySnapshot, MemorySnapshot]:
    """Release aborted-prompt references without forcing model GPU->CPU offload."""
    if model_management is None:
        import comfy.model_management as model_management

    before = _memory_snapshot(model_management)
    print(f"[VELVET VICE KREA] INTERRUPT CLEANUP | before | {before.format()}")

    cache_reset = _drop_interrupted_execution_caches(executor)

    cleanup = getattr(model_management, "cleanup_models_gc", None)
    if not callable(cleanup):
        cleanup = getattr(model_management, "cleanup_models", None)
    if callable(cleanup):
        cleanup()

    gc.collect()

    soft_empty_cache = getattr(model_management, "soft_empty_cache", None)
    if callable(soft_empty_cache):
        try:
            soft_empty_cache(force=True)
        except TypeError:
            soft_empty_cache()

    after = _memory_snapshot(model_management)
    print(
        "[VELVET VICE KREA] INTERRUPT SAFE CLEANUP | "
        f"execution cache reset={'yes' if cache_reset else 'no'} | "
        "models preserved; no unload_all_models() | "
        f"after | {after.format()}"
    )
    return before, after


def install_interruption_cleanup_hook(executor_class: type | None = None) -> bool:
    """Install one Krea-only cleanup hook around PromptExecutor.execute_async."""
    if executor_class is None:
        try:
            import execution
        except ImportError:
            return False
        executor_class = getattr(execution, "PromptExecutor", None)

    if executor_class is None:
        return False
    if getattr(executor_class, _PATCH_MARKER, False):
        return True

    original = getattr(executor_class, "execute_async", None)
    if original is None:
        return False

    @wraps(original)
    async def execute_async_with_krea_interrupt_cleanup(
        executor,
        prompt,
        prompt_id,
        *args,
        **kwargs,
    ):
        try:
            return await original(executor, prompt, prompt_id, *args, **kwargs)
        finally:
            should_cleanup = (
                prompt_uses_velvet_vice_krea(prompt)
                and execution_was_interrupted(executor)
            )
            if should_cleanup:
                try:
                    cleanup_after_interruption(executor)
                except Exception:
                    logging.exception(
                        "VELVET VICE KREA interrupted-render cleanup failed"
                    )

    setattr(executor_class, "_velvet_vice_krea_original_execute_async", original)
    setattr(
        executor_class,
        "execute_async",
        execute_async_with_krea_interrupt_cleanup,
    )
    setattr(executor_class, _PATCH_MARKER, True)
    logging.info("VELVET VICE KREA interruption-only memory cleanup hook installed")
    return True
