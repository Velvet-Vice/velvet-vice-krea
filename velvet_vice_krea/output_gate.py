from __future__ import annotations

from .memory_gate import log_memory_snapshot
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


EDIT_OUTPUT_MODES = (
    "NATIVE EDIT — ORIGINAL",
    "NATIVE EDIT — CUSTOM",
    "CLASSIC IMG2IMG",
)


class VelvetViceKreaSeedVR2BranchGate:
    """Keep edit SeedVR2 outputs isolated from inactive workflow branches."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "gate"
    RETURN_TYPES = ("IMAGE", "SEEDVR2_DIT", "SEEDVR2_VAE")
    RETURN_NAMES = ("image", "dit", "vae")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "workflow_mode": (
                    "VELVET_VICE_KREA_MODE",
                    {"forceInput": True},
                ),
                "target_mode": (EDIT_OUTPUT_MODES,),
            },
            "optional": {
                "image": ("IMAGE", {"lazy": True}),
                "dit": ("SEEDVR2_DIT", {"lazy": True}),
                "vae": ("SEEDVR2_VAE", {"lazy": True}),
            },
            "hidden": {
                "graph_prompt": "PROMPT",
                "unique_id": "UNIQUE_ID",
            },
        }

    @staticmethod
    def _submitted_input_names(graph_prompt, unique_id):
        if not isinstance(graph_prompt, dict) or unique_id is None:
            return None
        node = graph_prompt.get(str(unique_id))
        if node is None:
            node = graph_prompt.get(unique_id)
        if not isinstance(node, dict):
            return None
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            return None
        return set(inputs)

    def check_lazy_status(
        self,
        workflow_mode,
        target_mode,
        image=None,
        dit=None,
        vae=None,
        graph_prompt=None,
        unique_id=None,
    ):
        mode = validate_workflow_mode(workflow_mode)
        if target_mode not in EDIT_OUTPUT_MODES:
            raise ValueError(f"Unsupported SeedVR2 target mode: {target_mode!r}")
        if mode != target_mode:
            return []

        values = {"image": image, "dit": dit, "vae": vae}
        submitted = self._submitted_input_names(graph_prompt, unique_id)
        requestable = ("image", "dit", "vae")
        if submitted is not None:
            requestable = tuple(name for name in requestable if name in submitted)
        missing = [name for name in requestable if values[name] is None]
        if missing:
            log_memory_snapshot(
                f"before lazy SeedVR2 output resolution · {target_mode}"
            )
        return missing

    def gate(
        self,
        workflow_mode,
        target_mode,
        image=None,
        dit=None,
        vae=None,
        graph_prompt=None,
        unique_id=None,
    ):
        mode = validate_workflow_mode(workflow_mode)
        if target_mode not in EDIT_OUTPUT_MODES:
            raise ValueError(f"Unsupported SeedVR2 target mode: {target_mode!r}")

        if mode != target_mode:
            blocker = ExecutionBlocker(None)
            return (blocker, blocker, blocker)

        submitted = self._submitted_input_names(graph_prompt, unique_id)
        if submitted is not None:
            absent = [name for name in ("image", "dit", "vae") if name not in submitted]
            if absent:
                engine = (
                    "INTERNAL C — CLASSIC IMG2IMG ENGINE"
                    if target_mode == "CLASSIC IMG2IMG"
                    else "INTERNAL B — NATIVE EDIT ENGINE"
                )
                raise RuntimeError(
                    "VELVET VICE KREA SEEDVR2 OUTPUT GATE: active output branch "
                    f"{target_mode} is missing {', '.join(absent)}. Enable {engine} "
                    "and load the source image before enabling this finish path."
                )

        unresolved = [
            name
            for name, value in (("image", image), ("dit", dit), ("vae", vae))
            if value is None
        ]
        if unresolved:
            raise RuntimeError(
                "VELVET VICE KREA SEEDVR2 OUTPUT GATE: active branch inputs "
                f"were not resolved for {target_mode}: {', '.join(unresolved)}."
            )

        print(
            "[VELVET VICE KREA] SeedVR2 output gate opened for "
            f"{target_mode}; inactive edit finish paths remain blocked."
        )
        return (image, dit, vae)
