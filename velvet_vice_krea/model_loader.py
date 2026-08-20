"""Model-neutral Krea 2 diffusion-model selector for Velvet Vice workflows.

The public workflow deliberately stores a sentinel instead of a creator-specific
filename.  The dropdown is populated from the user's local ComfyUI
``diffusion_models`` folder at runtime and delegates actual loading to ComfyUI's
core UNETLoader, preserving its dtype behavior.
"""

MODEL_PLACEHOLDER = "SELECT KREA 2 MODEL"
WEIGHT_DTYPES = ["default", "fp8_e4m3fn", "fp8_e4m3fn_fast", "fp8_e5m2"]


class VelvetViceKreaModelLoader:
    @classmethod
    def INPUT_TYPES(cls):
        import folder_paths

        installed = list(folder_paths.get_filename_list("diffusion_models"))
        choices = [MODEL_PLACEHOLDER] + [name for name in installed if name != MODEL_PLACEHOLDER]
        return {
            "required": {
                "model_name": (choices, {"default": MODEL_PLACEHOLDER}),
                "weight_dtype": (WEIGHT_DTYPES, {"default": "default", "advanced": True}),
            }
        }

    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "load_model"
    CATEGORY = "Velvet Vice/KREA 2"
    DESCRIPTION = (
        "Select any locally installed Krea 2-compatible diffusion model. "
        "The public workflow intentionally ships without a creator-specific model dependency."
    )

    def load_model(self, model_name, weight_dtype="default"):
        if not model_name or model_name == MODEL_PLACEHOLDER:
            raise RuntimeError(
                "VELVET VICE KREA: Select your installed Krea 2 diffusion model in "
                "the KREA 2 model loader before starting this branch."
            )

        import folder_paths
        installed = set(folder_paths.get_filename_list("diffusion_models"))
        if model_name not in installed:
            raise RuntimeError(
                f"VELVET VICE KREA: Selected diffusion model is not installed: {model_name}. "
                "Choose an available Krea 2-compatible model from this node."
            )

        import nodes
        return nodes.UNETLoader().load_unet(model_name, weight_dtype)
