from __future__ import annotations

import gc

from .memory_gate import log_memory_snapshot


class VelvetViceKreaSeedVR2MemoryHandoff:
    """Release ComfyUI-managed Krea models immediately before SeedVR2 loads.

    The node is deliberately placed only on the lazy SeedVR2 branch. Prompt
    previews and normal non-upscaled outputs therefore retain ComfyUI's model
    cache, while an enabled SeedVR2 run starts with dedicated VRAM reclaimed.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "handoff"
    CATEGORY = "Velvet Vice/KREA 2"
    DESCRIPTION = (
        "Runs only when the lazy SeedVR2 branch is enabled. Releases "
        "ComfyUI-managed Krea/CLIP/VAE models before SeedVR2 loads."
    )

    def handoff(self, image):
        try:
            import comfy.model_management as model_management
        except ImportError as error:
            raise RuntimeError(
                "VELVET VICE KREA: ComfyUI model management is unavailable "
                "for the SeedVR2 memory handoff."
            ) from error

        before = log_memory_snapshot("before SeedVR2 handoff")
        try:
            model_management.unload_all_models()
            gc.collect()
            soft_empty_cache = getattr(model_management, "soft_empty_cache", None)
            if callable(soft_empty_cache):
                try:
                    soft_empty_cache(force=True)
                except TypeError:
                    soft_empty_cache()
        except (AttributeError, RuntimeError) as error:
            raise RuntimeError(
                "VELVET VICE KREA: Could not release Krea models before SeedVR2."
            ) from error

        after = log_memory_snapshot("after SeedVR2 handoff")
        print(
            "[VELVET VICE KREA] SEEDVR2 MEMORY HANDOFF | "
            f"before | {before.format()} | after | {after.format()}"
        )
        return (image,)
