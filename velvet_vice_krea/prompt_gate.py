from __future__ import annotations

from .memory_gate import log_memory_snapshot
from .ollama_client import OllamaClient, OllamaDirectorError
from .workflow_router import validate_workflow_mode


class VelvetViceKreaOllamaReleaseBarrier:
    """Verify that Ollama/Qwen is gone before Krea render models may load."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_package": (
                    "VELVET_VICE_KREA_PROMPT_PACKAGE",
                    {"forceInput": True},
                ),
                "strict_release": (
                    "BOOLEAN",
                    {"default": True},
                ),
                "timeout_seconds": (
                    "INT",
                    {
                        "default": 20,
                        "min": 3,
                        "max": 120,
                        "step": 1,
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "release"
    CATEGORY = "VELVET VICE/KREA 2"
    DESCRIPTION = (
        "Verifies that every Ollama model used by the Krea Prompt Director "
        "has been released before the prompt may enter the Krea render gate."
    )

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def release(self, prompt_package, strict_release, timeout_seconds):
        if not isinstance(prompt_package, dict):
            raise TypeError(
                "Expected VELVET_VICE_KREA_PROMPT_PACKAGE from the Krea Prompt Director."
            )
        if prompt_package.get("schema") != "VELVET_VICE_KREA_PROMPT_PACKAGE":
            raise ValueError(
                "Invalid Krea prompt package schema. Reconnect the Prompt Director "
                "directly to the Krea Ollama Release Barrier."
            )

        prompt = prompt_package.get("final_prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("The Krea prompt package does not contain a valid prompt.")

        models = prompt_package.get("used_models") or []
        release_required = bool(
            prompt_package.get("release_required") and models
        )
        if not release_required:
            print(
                "[VELVET VICE KREA] Ollama release bypassed: "
                "the selected prompt mode made no Ollama calls."
            )
            return (prompt,)

        try:
            OllamaClient().release_models(
                base_url=prompt_package.get("ollama_url", ""),
                models=models,
                timeout_seconds=int(timeout_seconds),
            )
            print(
                "[VELVET VICE KREA] Ollama model release confirmed before "
                f"Krea rendering: {', '.join(models)}"
            )
        except (OllamaDirectorError, ValueError) as error:
            message = (
                "[VELVET VICE KREA] Could not confirm Ollama release before "
                f"Krea rendering: {error}"
            )
            if strict_release:
                raise RuntimeError(message) from error
            print(f"WARNING: {message}")
        return (prompt,)


class VelvetViceKreaPromptFirstGate:
    """Request only the selected Krea branch after Ollama has been released."""

    @classmethod
    def INPUT_TYPES(cls):
        lazy_model = ("MODEL", {"lazy": True})
        lazy_clip = ("CLIP", {"lazy": True})
        lazy_vae = ("VAE", {"lazy": True})
        lazy_image = ("IMAGE", {"lazy": True})
        lazy_latent = ("LATENT", {"lazy": True})
        return {
            "required": {
                "prompt": ("STRING", {"forceInput": True}),
                "workflow_mode": ("VELVET_VICE_KREA_MODE", {"forceInput": True}),
            },
            "optional": {
                # Branch resources are intentionally optional *and* lazy. ComfyUI
                # removes links whose source nodes are bypassed when it serializes
                # the prompt. Keeping inactive branches in `required` therefore
                # makes prompt validation fail before lazy evaluation can select
                # the active branch. check_lazy_status() below still requests all
                # resources belonging to the selected workflow mode.
                "create_model": lazy_model,
                "create_clip": lazy_clip,
                "create_vae": lazy_vae,
                "native_model": lazy_model,
                "native_clip": lazy_clip,
                "native_vae": lazy_vae,
                "classic_model": lazy_model,
                "classic_clip": lazy_clip,
                "classic_vae": lazy_vae,
                # Native Edit preprocessing depends on its MODEL/VAE. Keep the
                # produced image/latent behind the same prompt-first barrier so
                # no side dependency can make node 93 load before Qwen release.
                "native_preprocessed_image": lazy_image,
                "native_original_latent": lazy_latent,
            },
        }

    RETURN_TYPES = (
        "STRING",
        "MODEL", "CLIP", "VAE",
        "MODEL", "CLIP", "VAE",
        "MODEL", "CLIP", "VAE",
        "IMAGE", "LATENT",
        "STRING",
    )
    RETURN_NAMES = (
        "prompt",
        "create_model", "create_clip", "create_vae",
        "native_model", "native_clip", "native_vae",
        "classic_model", "classic_clip", "classic_vae",
        "native_preprocessed_image", "native_original_latent",
        "active_branch",
    )
    FUNCTION = "release_render_inputs"
    CATEGORY = "VELVET VICE/KREA 2"
    DESCRIPTION = (
        "Krea prompt-first lazy gate. CREATE, Native Edit, and Classic Img2Img "
        "model/CLIP/VAE inputs remain unresolved until Ollama release has been "
        "confirmed, then only the selected workflow branch is requested. Native "
        "Edit preprocessing IMAGE/LATENT outputs are gated as well so no side "
        "dependency can load its model before release. Branch outputs stay "
        "physically separate so models can never cross between modes."
    )

    @staticmethod
    def _prefix(workflow_mode: str) -> str:
        mode = validate_workflow_mode(workflow_mode)
        if mode == "CREATE":
            return "create"
        if mode.startswith("NATIVE EDIT"):
            return "native"
        return "classic"

    def check_lazy_status(
        self,
        prompt,
        workflow_mode,
        create_model=None,
        create_clip=None,
        create_vae=None,
        native_model=None,
        native_clip=None,
        native_vae=None,
        classic_model=None,
        classic_clip=None,
        classic_vae=None,
        native_preprocessed_image=None,
        native_original_latent=None,
    ):
        del prompt
        prefix = self._prefix(workflow_mode)
        values = {
            "create_model": create_model,
            "create_clip": create_clip,
            "create_vae": create_vae,
            "native_model": native_model,
            "native_clip": native_clip,
            "native_vae": native_vae,
            "classic_model": classic_model,
            "classic_clip": classic_clip,
            "classic_vae": classic_vae,
            "native_preprocessed_image": native_preprocessed_image,
            "native_original_latent": native_original_latent,
        }
        selected_names = [
            f"{prefix}_model",
            f"{prefix}_clip",
            f"{prefix}_vae",
        ]
        if prefix == "native":
            selected_names.extend((
                "native_preprocessed_image",
                "native_original_latent",
            ))
        missing = [name for name in selected_names if values[name] is None]
        marker = (workflow_mode, tuple(missing))
        if missing and getattr(self, "_last_lazy_marker", None) != marker:
            log_memory_snapshot(
                f"before lazy Krea input resolution · {workflow_mode}"
            )
            self._last_lazy_marker = marker
        return missing

    def release_render_inputs(
        self,
        prompt,
        workflow_mode,
        create_model=None,
        create_clip=None,
        create_vae=None,
        native_model=None,
        native_clip=None,
        native_vae=None,
        classic_model=None,
        classic_clip=None,
        classic_vae=None,
        native_preprocessed_image=None,
        native_original_latent=None,
    ):
        prefix = self._prefix(workflow_mode)
        values = {
            "create_model": create_model,
            "create_clip": create_clip,
            "create_vae": create_vae,
            "native_model": native_model,
            "native_clip": native_clip,
            "native_vae": native_vae,
            "classic_model": classic_model,
            "classic_clip": classic_clip,
            "classic_vae": classic_vae,
            "native_preprocessed_image": native_preprocessed_image,
            "native_original_latent": native_original_latent,
        }
        selected_names = [
            f"{prefix}_model",
            f"{prefix}_clip",
            f"{prefix}_vae",
        ]
        if prefix == "native":
            selected_names.extend((
                "native_preprocessed_image",
                "native_original_latent",
            ))
        if any(values[name] is None for name in selected_names):
            raise RuntimeError(
                "VELVET VICE KREA PROMPT-FIRST GATE: selected render inputs "
                f"for {workflow_mode} were not resolved."
            )

        log_memory_snapshot(
            f"after lazy Krea input resolution · {workflow_mode}"
        )
        print(
            "[VELVET VICE KREA] Prompt-first gate completed. "
            f"{workflow_mode} render inputs may load now."
        )
        self._last_lazy_marker = None

        def selected(name):
            return values[name] if name.startswith(prefix + "_") else None

        return (
            prompt,
            selected("create_model"), selected("create_clip"), selected("create_vae"),
            selected("native_model"), selected("native_clip"), selected("native_vae"),
            selected("classic_model"), selected("classic_clip"), selected("classic_vae"),
            values["native_preprocessed_image"] if prefix == "native" else None,
            values["native_original_latent"] if prefix == "native" else None,
            workflow_mode,
        )
