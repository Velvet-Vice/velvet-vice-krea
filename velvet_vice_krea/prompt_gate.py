from __future__ import annotations

from .memory_gate import log_memory_snapshot
from .ollama_client import OllamaClient, OllamaDirectorError
from .workflow_router import validate_workflow_mode

try:
    from comfy_execution.graph_utils import ExecutionBlocker
except ImportError:  # pragma: no cover
    try:
        from comfy_execution.graph import ExecutionBlocker
    except ImportError:  # pragma: no cover
        class ExecutionBlocker:  # type: ignore[no-redef]
            def __init__(self, message):
                self.message = message


class VelvetViceKreaOllamaReleaseBarrier:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt_package": ("VELVET_VICE_KREA_PROMPT_PACKAGE", {"forceInput": True}),
                "strict_release": ("BOOLEAN", {"default": True}),
                "timeout_seconds": ("INT", {"default": 20, "min": 3, "max": 120, "step": 1}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "release"
    CATEGORY = "VELVET VICE/KREA 2"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def release(self, prompt_package, strict_release, timeout_seconds):
        if not isinstance(prompt_package, dict) or prompt_package.get("schema") != "VELVET_VICE_KREA_PROMPT_PACKAGE":
            raise ValueError("Invalid Krea prompt package. Reconnect the Prompt Director directly to the Ollama Release Barrier.")
        prompt = prompt_package.get("final_prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("The Krea prompt package does not contain a valid prompt.")
        models = prompt_package.get("used_models") or []
        if not (prompt_package.get("release_required") and models):
            print("[VELVET VICE KREA] Ollama release bypassed: the selected prompt mode made no Ollama calls.")
            return (prompt,)
        try:
            OllamaClient().release_models(
                base_url=prompt_package.get("ollama_url", ""),
                models=models,
                timeout_seconds=int(timeout_seconds),
            )
            print("[VELVET VICE KREA] Ollama model release confirmed before Krea rendering: " + ", ".join(models))
        except (OllamaDirectorError, ValueError) as error:
            message = f"[VELVET VICE KREA] Could not confirm Ollama release before Krea rendering: {error}"
            if strict_release:
                raise RuntimeError(message) from error
            print(f"WARNING: {message}")
        return (prompt,)


class VelvetViceKreaPromptFirstGate:
    """Resolve only the selected branch and block every inactive branch."""

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
                "create_model": lazy_model,
                "create_clip": lazy_clip,
                "create_vae": lazy_vae,
                "native_model": lazy_model,
                "native_clip": lazy_clip,
                "native_vae": lazy_vae,
                "classic_model": lazy_model,
                "classic_clip": lazy_clip,
                "classic_vae": lazy_vae,
                "native_preprocessed_image": lazy_image,
                "native_original_latent": lazy_latent,
            },
            "hidden": {
                "graph_prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
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

    @staticmethod
    def _prefix(workflow_mode):
        mode = validate_workflow_mode(workflow_mode)
        if mode == "CREATE":
            return "create"
        if mode.startswith("NATIVE EDIT"):
            return "native"
        return "classic"

    @classmethod
    def _selected_names(cls, workflow_mode):
        mode = validate_workflow_mode(workflow_mode)
        prefix = cls._prefix(mode)
        names = [f"{prefix}_model", f"{prefix}_clip", f"{prefix}_vae"]
        if mode.startswith("NATIVE EDIT"):
            names.append("native_preprocessed_image")
        if mode == "NATIVE EDIT — ORIGINAL":
            names.append("native_original_latent")
        return names

    @staticmethod
    def _submitted_input_names(graph_prompt, unique_id):
        if not isinstance(graph_prompt, dict) or unique_id is None:
            return None
        node = graph_prompt.get(str(unique_id), graph_prompt.get(unique_id))
        if not isinstance(node, dict) or not isinstance(node.get("inputs"), dict):
            return None
        return set(node["inputs"])

    @staticmethod
    def _values(create_model=None, create_clip=None, create_vae=None,
                native_model=None, native_clip=None, native_vae=None,
                classic_model=None, classic_clip=None, classic_vae=None,
                native_preprocessed_image=None, native_original_latent=None):
        return locals()

    def check_lazy_status(self, prompt, workflow_mode,
                          create_model=None, create_clip=None, create_vae=None,
                          native_model=None, native_clip=None, native_vae=None,
                          classic_model=None, classic_clip=None, classic_vae=None,
                          native_preprocessed_image=None, native_original_latent=None,
                          graph_prompt=None, unique_id=None):
        del prompt
        values = self._values(
            create_model, create_clip, create_vae,
            native_model, native_clip, native_vae,
            classic_model, classic_clip, classic_vae,
            native_preprocessed_image, native_original_latent,
        )
        selected = self._selected_names(workflow_mode)
        submitted = self._submitted_input_names(graph_prompt, unique_id)
        requestable = selected if submitted is None else [name for name in selected if name in submitted]
        missing = [name for name in requestable if values[name] is None]
        marker = (workflow_mode, tuple(missing))
        if missing and getattr(self, "_last_lazy_marker", None) != marker:
            log_memory_snapshot(f"before lazy Krea input resolution · {workflow_mode}")
            self._last_lazy_marker = marker
        return missing

    def release_render_inputs(self, prompt, workflow_mode,
                              create_model=None, create_clip=None, create_vae=None,
                              native_model=None, native_clip=None, native_vae=None,
                              classic_model=None, classic_clip=None, classic_vae=None,
                              native_preprocessed_image=None, native_original_latent=None,
                              graph_prompt=None, unique_id=None):
        mode = validate_workflow_mode(workflow_mode)
        prefix = self._prefix(mode)
        values = self._values(
            create_model, create_clip, create_vae,
            native_model, native_clip, native_vae,
            classic_model, classic_clip, classic_vae,
            native_preprocessed_image, native_original_latent,
        )
        selected = self._selected_names(mode)
        submitted = self._submitted_input_names(graph_prompt, unique_id)
        absent = [] if submitted is None else [name for name in selected if name not in submitted]
        if absent:
            if mode.startswith("NATIVE EDIT"):
                hint = "Enable 04 — IMAGE EDIT STUDIO and INTERNAL B — NATIVE EDIT ENGINE, then select the Native Edit source image."
            elif mode == "CLASSIC IMG2IMG":
                hint = "Enable 04 — IMAGE EDIT STUDIO and INTERNAL C — CLASSIC IMG2IMG ENGINE, then select the Classic Img2Img source image."
            else:
                hint = "Enable INTERNAL A — CREATE ENGINE and the CREATE core loadout."
            raise RuntimeError(
                f"VELVET VICE KREA PROMPT-FIRST GATE: {mode} is missing link(s): {', '.join(absent)}. {hint}"
            )
        unresolved = [name for name in selected if values[name] is None]
        if unresolved:
            raise RuntimeError(
                f"VELVET VICE KREA PROMPT-FIRST GATE: selected render inputs for {mode} were not resolved: {', '.join(unresolved)}."
            )

        log_memory_snapshot(f"after lazy Krea input resolution · {mode}")
        print(f"[VELVET VICE KREA] Prompt-first gate completed. {mode} render inputs may load now. Inactive branches are blocked.")
        self._last_lazy_marker = None
        blocked = ExecutionBlocker(None)

        def branch_value(name):
            return values[name] if name.startswith(prefix + "_") else blocked

        native_image = values["native_preprocessed_image"] if prefix == "native" else blocked
        native_latent = values["native_original_latent"] if mode == "NATIVE EDIT — ORIGINAL" else blocked

        return (
            prompt,
            branch_value("create_model"), branch_value("create_clip"), branch_value("create_vae"),
            branch_value("native_model"), branch_value("native_clip"), branch_value("native_vae"),
            branch_value("classic_model"), branch_value("classic_clip"), branch_value("classic_vae"),
            native_image, native_latent, mode,
        )
