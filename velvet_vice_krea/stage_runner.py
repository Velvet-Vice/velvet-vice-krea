"""UI-only stage runner node for Velvet Vice Krea partial execution."""


class VelvetViceKreaStageRunner:
    """Frontend controller for targeted CREATE-stage partial execution.

    The node intentionally has no execution inputs or outputs.  Its DOM buttons are
    implemented in ``web/js/stage_runner.js`` and queue existing PreviewImage
    output nodes through ComfyUI's partial-execution path.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ()
    FUNCTION = "idle"
    CATEGORY = "VELVET VICE/KREA"
    DESCRIPTION = (
        "Run only the selected CREATE stage (Base, Refinement, active Detailer, "
        "or final SeedVR2) using ComfyUI partial execution. UI-only controller."
    )

    def idle(self):
        return ()
