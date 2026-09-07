"""VELVET VICE custom nodes for Krea 2 workflows."""

from .velvet_vice_krea.prompt_director import VelvetViceKreaPromptDirector
from .velvet_vice_krea.model_loader import VelvetViceKreaModelLoader
from .velvet_vice_krea.prompt_gate import (
    VelvetViceKreaOllamaReleaseBarrier,
    VelvetViceKreaPromptFirstGate,
)
from .velvet_vice_krea.resolution_selector import VelvetViceKreaResolutionSelector
from .velvet_vice_krea.stage_runner import VelvetViceKreaStageRunner
from .velvet_vice_krea.seedvr2_handoff import VelvetViceKreaSeedVR2MemoryHandoff
from .velvet_vice_krea.output_gate import VelvetViceKreaSeedVR2BranchGate
from .velvet_vice_krea.interrupt_cleanup import install_interruption_cleanup_hook
from .velvet_vice_krea.workflow_router import (
    VelvetViceKreaCreateBasePreviewPassthrough,
    VelvetViceKreaCreateRefinementPreview,
    VelvetViceKreaCreateRefinementPreviewPassthrough,
    VelvetViceKreaImageRouter,
    VelvetViceKreaModeSelector,
    VelvetViceKreaSelectedBasePreview,
    VelvetViceKreaSeedVR2Router,
)

NODE_CLASS_MAPPINGS = {
    "VelvetViceKreaModelLoader": VelvetViceKreaModelLoader,
    "VelvetViceKreaStageRunner": VelvetViceKreaStageRunner,
    "VelvetViceKreaSeedVR2MemoryHandoff": VelvetViceKreaSeedVR2MemoryHandoff,
    "VelvetViceKreaSeedVR2BranchGate": VelvetViceKreaSeedVR2BranchGate,
    "VelvetViceKreaPromptDirector": VelvetViceKreaPromptDirector,
    "VelvetViceKreaOllamaReleaseBarrier": VelvetViceKreaOllamaReleaseBarrier,
    "VelvetViceKreaPromptFirstGate": VelvetViceKreaPromptFirstGate,
    "VelvetViceKreaResolutionSelector": VelvetViceKreaResolutionSelector,
    "VelvetViceKreaCreateBasePreviewPassthrough": VelvetViceKreaCreateBasePreviewPassthrough,
    "VelvetViceKreaModeSelector": VelvetViceKreaModeSelector,
    "VelvetViceKreaImageRouter": VelvetViceKreaImageRouter,
    "VelvetViceKreaSelectedBasePreview": VelvetViceKreaSelectedBasePreview,
    "VelvetViceKreaSeedVR2Router": VelvetViceKreaSeedVR2Router,
    "VelvetViceKreaCreateRefinementPreview": VelvetViceKreaCreateRefinementPreview,
    "VelvetViceKreaCreateRefinementPreviewPassthrough": VelvetViceKreaCreateRefinementPreviewPassthrough,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "VelvetViceKreaModelLoader": "VELVET VICE KREA — Select Krea 2 Model",
    "VelvetViceKreaStageRunner": "VELVET VICE KREA — Render This Stage",
    "VelvetViceKreaSeedVR2MemoryHandoff": "VELVET VICE KREA — SeedVR2 Memory Handoff",
    "VelvetViceKreaSeedVR2BranchGate": "VELVET VICE KREA — SeedVR2 Branch Gate",
    "VelvetViceKreaPromptDirector": "VELVET VICE KREA — Vision Prompt Director v2",
    "VelvetViceKreaOllamaReleaseBarrier": "VELVET VICE KREA — Ollama Release Barrier",
    "VelvetViceKreaPromptFirstGate": "VELVET VICE KREA — Prompt-First Gate",
    "VelvetViceKreaResolutionSelector": "VELVET VICE KREA — Format & Resolution",
    "VelvetViceKreaCreateBasePreviewPassthrough": "VELVET VICE KREA — Create Base Preview",
    "VelvetViceKreaModeSelector": "VELVET VICE KREA — Mode Selector",
    "VelvetViceKreaImageRouter": "VELVET VICE KREA — Image Router",
    "VelvetViceKreaSelectedBasePreview": "VELVET VICE KREA — Selected Base Preview",
    "VelvetViceKreaSeedVR2Router": "VELVET VICE KREA — SeedVR2 Router",
    "VelvetViceKreaCreateRefinementPreview": "VELVET VICE KREA — Create Refinement Preview",
    "VelvetViceKreaCreateRefinementPreviewPassthrough": "VELVET VICE KREA — Refinement Preview",
}

WEB_DIRECTORY = "./web"

INTERRUPT_CLEANUP_HOOK_INSTALLED = install_interruption_cleanup_hook()

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
    "INTERRUPT_CLEANUP_HOOK_INSTALLED",
]

__version__ = "2.0.4"
