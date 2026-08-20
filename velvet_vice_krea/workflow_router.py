"""Lazy workflow and output routing nodes for VELVET VICE KREA."""

from __future__ import annotations


WORKFLOW_MODES = (
    "CREATE",
    "NATIVE EDIT — ORIGINAL",
    "NATIVE EDIT — CUSTOM",
    "CLASSIC IMG2IMG",
)

MODE_TO_PROFILE = {
    "CREATE": "CREATE",
    "NATIVE EDIT — ORIGINAL": "NATIVE EDIT",
    "NATIVE EDIT — CUSTOM": "NATIVE EDIT",
    "CLASSIC IMG2IMG": "CLASSIC IMG2IMG",
}

MODE_TO_IMAGE_INPUT = {
    "CREATE": "create_image",
    "NATIVE EDIT — ORIGINAL": "native_original_image",
    "NATIVE EDIT — CUSTOM": "native_custom_image",
    "CLASSIC IMG2IMG": "classic_img2img_image",
}


def validate_workflow_mode(workflow_mode: str) -> str:
    if workflow_mode not in WORKFLOW_MODES:
        raise ValueError(
            f"Unsupported Workflow Mode: {workflow_mode!r}. "
            f"Supported modes: {', '.join(WORKFLOW_MODES)}."
        )
    return workflow_mode


def prompt_profile_for_mode(workflow_mode: str) -> str:
    return MODE_TO_PROFILE[validate_workflow_mode(workflow_mode)]


class VelvetViceKreaModeSelector:
    """Single source of truth for workflow mode and prompt profile."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "select"
    RETURN_TYPES = ("VELVET_VICE_KREA_MODE", "STRING", "STRING")
    RETURN_NAMES = ("workflow_mode", "prompt_profile", "active_branch")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "workflow_mode": (WORKFLOW_MODES,),
            }
        }

    def select(self, workflow_mode):
        validate_workflow_mode(workflow_mode)
        profile = prompt_profile_for_mode(workflow_mode)
        return (workflow_mode, profile, workflow_mode)


class VelvetViceKreaImageRouter:
    """Request and return only the image branch selected by workflow mode."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "route"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("selected_image", "active_branch")

    @classmethod
    def INPUT_TYPES(cls):
        lazy_image = ("IMAGE", {"lazy": True})
        return {
            "required": {
                "workflow_mode": ("VELVET_VICE_KREA_MODE",),
                "create_image": lazy_image,
                "native_original_image": lazy_image,
                "native_custom_image": lazy_image,
                "classic_img2img_image": lazy_image,
            },
        }

    def check_lazy_status(
        self,
        workflow_mode,
        create_image=None,
        native_original_image=None,
        native_custom_image=None,
        classic_img2img_image=None,
    ):
        del self
        images = {
            "create_image": create_image,
            "native_original_image": native_original_image,
            "native_custom_image": native_custom_image,
            "classic_img2img_image": classic_img2img_image,
        }
        input_name = MODE_TO_IMAGE_INPUT[
            validate_workflow_mode(workflow_mode)
        ]
        if images.get(input_name) is None:
            return [input_name]
        return []

    def route(self, workflow_mode, **images):
        input_name = MODE_TO_IMAGE_INPUT[
            validate_workflow_mode(workflow_mode)
        ]
        image = images.get(input_name)
        if image is None:
            raise RuntimeError(
                "VELVET VICE KREA IMAGE ROUTER: "
                f"The selected input {input_name!r} is not connected."
            )
        return (image, workflow_mode)


class VelvetViceKreaSelectedBasePreview:
    """Preview the selected branch before passing it to CREATE refinement."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "preview"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("selected_image", "active_branch")
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        lazy_image = ("IMAGE", {"lazy": True})
        return {
            "required": {
                "workflow_mode": ("VELVET_VICE_KREA_MODE",),
                "create_image": lazy_image,
                "native_original_image": lazy_image,
                "native_custom_image": lazy_image,
                "classic_img2img_image": lazy_image,
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def check_lazy_status(
        self,
        workflow_mode,
        create_image=None,
        native_original_image=None,
        native_custom_image=None,
        classic_img2img_image=None,
    ):
        del self
        images = {
            "create_image": create_image,
            "native_original_image": native_original_image,
            "native_custom_image": native_custom_image,
            "classic_img2img_image": classic_img2img_image,
        }
        input_name = MODE_TO_IMAGE_INPUT[
            validate_workflow_mode(workflow_mode)
        ]
        if images.get(input_name) is None:
            return [input_name]
        return []

    def preview(
        self,
        workflow_mode,
        prompt=None,
        extra_pnginfo=None,
        **images,
    ):
        input_name = MODE_TO_IMAGE_INPUT[
            validate_workflow_mode(workflow_mode)
        ]
        image = images.get(input_name)
        if image is None:
            raise RuntimeError(
                "VELVET VICE KREA SELECTED BASE PREVIEW: "
                f"The selected input {input_name!r} is not connected."
            )

        try:
            from nodes import PreviewImage
        except ImportError as exc:
            raise RuntimeError(
                "VELVET VICE KREA SELECTED BASE PREVIEW: "
                "ComfyUI PreviewImage is unavailable."
            ) from exc

        response = PreviewImage().save_images(
            image,
            filename_prefix="VELVET_VICE_KREA_BASE_PREVIEW",
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
        response.setdefault("ui", {})["status"] = [
            f"{workflow_mode} base complete — before refinement"
        ]
        response["result"] = (image, workflow_mode)
        return response


class VelvetViceKreaCreateBasePreviewPassthrough:
    """Preview and pass through the CREATE base image without lazy routing."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "preview"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def preview(self, images, prompt=None, extra_pnginfo=None):
        try:
            from nodes import PreviewImage
        except ImportError as exc:
            raise RuntimeError(
                "VELVET VICE KREA CREATE BASE PREVIEW: "
                "ComfyUI PreviewImage is unavailable."
            ) from exc

        response = PreviewImage().save_images(
            images,
            filename_prefix="VELVET_VICE_KREA_CREATE_BASE_PREVIEW",
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
        response.setdefault("ui", {})["status"] = [
            "CREATE base complete — first sampler, before refinement"
        ]
        response["result"] = (images,)
        return response


class VelvetViceKreaCreateRefinementPreviewPassthrough:
    """Preview and pass through the CREATE refinement result."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "preview"
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def preview(self, images, prompt=None, extra_pnginfo=None):
        try:
            from nodes import PreviewImage
        except ImportError as exc:
            raise RuntimeError(
                "VELVET VICE KREA CREATE REFINEMENT PREVIEW: "
                "ComfyUI PreviewImage is unavailable."
            ) from exc

        response = PreviewImage().save_images(
            images,
            filename_prefix="VELVET_VICE_KREA_CREATE_REFINEMENT_PREVIEW",
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
        response.setdefault("ui", {})["status"] = [
            "CREATE refinement complete — after Mild Refinement"
        ]
        response["result"] = (images,)
        return response


class VelvetViceKreaSeedVR2Router:
    """Lazy raw/upscaled image selector placed after the final image router."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "route"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("final_image", "upscale_status")

    @classmethod
    def INPUT_TYPES(cls):
        lazy_image = ("IMAGE", {"lazy": True})
        return {
            "required": {
                "seedvr2_enabled": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "label_on": "ON · USE SEEDVR2",
                        "label_off": "OFF · USE ORIGINAL",
                    },
                ),
                "original_image": lazy_image,
                "seedvr2_image": lazy_image,
            },
        }

    @staticmethod
    def _selected_input(seedvr2_enabled):
        return "seedvr2_image" if seedvr2_enabled else "original_image"

    def check_lazy_status(
        self,
        seedvr2_enabled,
        original_image=None,
        seedvr2_image=None,
    ):
        images = {
            "original_image": original_image,
            "seedvr2_image": seedvr2_image,
        }
        input_name = self._selected_input(seedvr2_enabled)
        if images.get(input_name) is None:
            return [input_name]
        return []

    def route(self, seedvr2_enabled, **images):
        input_name = self._selected_input(seedvr2_enabled)
        image = images.get(input_name)
        if image is None:
            raise RuntimeError(
                "VELVET VICE KREA SEEDVR2 ROUTER: "
                f"The selected input {input_name!r} is not connected."
            )
        status = (
            "SEEDVR2 ON · upscaled output"
            if seedvr2_enabled
            else "SEEDVR2 OFF · original output"
        )
        return (image, status)


class VelvetViceKreaCreateRefinementPreview:
    """Show the refinement image only in CREATE without pulling other modes."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "preview"
    RETURN_TYPES = ()
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "workflow_mode": ("VELVET_VICE_KREA_MODE",),
                "refined_image": ("IMAGE", {"lazy": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    def check_lazy_status(
        self,
        workflow_mode,
        refined_image=None,
        **kwargs,
    ):
        del self
        del kwargs
        validate_workflow_mode(workflow_mode)
        if workflow_mode == "CREATE" and refined_image is None:
            return ["refined_image"]
        return []

    def preview(
        self,
        workflow_mode,
        refined_image=None,
        prompt=None,
        extra_pnginfo=None,
    ):
        validate_workflow_mode(workflow_mode)
        if workflow_mode != "CREATE":
            return {
                "ui": {
                    "status": [
                        "Refinement Preview skipped — selected mode is not CREATE"
                    ]
                },
                "result": (),
            }
        if refined_image is None:
            raise RuntimeError(
                "VELVET VICE KREA REFINEMENT PREVIEW: "
                "The CREATE refinement image is not connected."
            )

        try:
            from nodes import PreviewImage
        except ImportError as exc:
            raise RuntimeError(
                "VELVET VICE KREA REFINEMENT PREVIEW: "
                "ComfyUI PreviewImage is unavailable."
            ) from exc

        response = PreviewImage().save_images(
            refined_image,
            filename_prefix="VELVET_VICE_KREA_REFINEMENT_PREVIEW",
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
        response.setdefault("ui", {})["status"] = [
            "CREATE refinement complete — after Mild Refinement"
        ]
        return response
