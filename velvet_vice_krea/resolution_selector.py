from __future__ import annotations


RESOLUTION_MODES = ("PRESET", "MANUAL")
FORMATS = (
    "SQUARE 1:1",
    "PORTRAIT 4:5",
    "PORTRAIT 3:4",
    "PORTRAIT 2:3",
    "LANDSCAPE 3:2",
    "LANDSCAPE 4:3",
    "WIDESCREEN 16:9",
    "VERTICAL 9:16",
    "ULTRAWIDE 21:9",
)
SIZE_PROFILES = ("STANDARD", "HIGH")

# STANDARD is intentionally centered around the previous CREATE default
# (1024 x 1536 for 2:3) so switching to PRESET does not silently lower the
# established workflow quality. HIGH is an optional, more demanding tier.
PRESET_DIMENSIONS = {
    "STANDARD": {
        "SQUARE 1:1": (1248, 1248),
        "PORTRAIT 4:5": (1152, 1440),
        "PORTRAIT 3:4": (1080, 1440),
        "PORTRAIT 2:3": (1024, 1536),
        "LANDSCAPE 3:2": (1536, 1024),
        "LANDSCAPE 4:3": (1440, 1080),
        "WIDESCREEN 16:9": (1664, 936),
        "VERTICAL 9:16": (936, 1664),
        "ULTRAWIDE 21:9": (2016, 864),
    },
    "HIGH": {
        "SQUARE 1:1": (1536, 1536),
        "PORTRAIT 4:5": (1344, 1680),
        "PORTRAIT 3:4": (1296, 1728),
        "PORTRAIT 2:3": (1280, 1920),
        "LANDSCAPE 3:2": (1920, 1280),
        "LANDSCAPE 4:3": (1728, 1296),
        "WIDESCREEN 16:9": (2048, 1152),
        "VERTICAL 9:16": (1152, 2048),
        "ULTRAWIDE 21:9": (2240, 960),
    },
}


def resolve_dimensions(
    mode: str,
    format_name: str,
    size_profile: str,
    manual_width: int,
    manual_height: int,
) -> tuple[int, int]:
    if mode not in RESOLUTION_MODES:
        raise ValueError(f"Unsupported resolution mode: {mode!r}.")

    if mode == "MANUAL":
        width, height = int(manual_width), int(manual_height)
    else:
        if size_profile not in PRESET_DIMENSIONS:
            raise ValueError(f"Unsupported size profile: {size_profile!r}.")
        try:
            width, height = PRESET_DIMENSIONS[size_profile][format_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported format preset: {format_name!r}.") from exc

    if width < 16 or height < 16:
        raise ValueError("Width and height must both be at least 16 pixels.")
    if width % 8 or height % 8:
        raise ValueError(
            "Width and height must be divisible by 8 for the Krea latent path."
        )
    return width, height


class VelvetViceKreaResolutionSelector:
    """Preset aspect-ratio selector with a preserved manual pixel mode."""

    CATEGORY = "VELVET VICE/KREA 2"
    FUNCTION = "generate"
    RETURN_TYPES = ("LATENT", "INT", "INT", "STRING")
    RETURN_NAMES = ("latent", "width", "height", "status")
    DESCRIPTION = (
        "CREATE-only format selector. PRESET chooses tested aspect-ratio pixel "
        "pairs; MANUAL preserves direct width/height control."
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": (RESOLUTION_MODES, {"default": "PRESET"}),
                "format": (FORMATS, {"default": "PORTRAIT 2:3"}),
                "size": (SIZE_PROFILES, {"default": "STANDARD"}),
                "manual_width": (
                    "INT",
                    {"default": 1024, "min": 16, "max": 16384, "step": 8},
                ),
                "manual_height": (
                    "INT",
                    {"default": 1536, "min": 16, "max": 16384, "step": 8},
                ),
                "batch_size": (
                    "INT",
                    {"default": 1, "min": 1, "max": 64, "step": 1},
                ),
            }
        }

    def generate(
        self,
        mode,
        format,
        size,
        manual_width,
        manual_height,
        batch_size,
    ):
        width, height = resolve_dimensions(
            mode,
            format,
            size,
            manual_width,
            manual_height,
        )
        try:
            from nodes import EmptyLatentImage
        except ImportError as exc:
            raise RuntimeError(
                "VELVET VICE KREA FORMAT & RESOLUTION: ComfyUI's "
                "EmptyLatentImage node is unavailable."
            ) from exc

        result = EmptyLatentImage().generate(
            width=width,
            height=height,
            batch_size=int(batch_size),
        )
        latent = result[0] if isinstance(result, tuple) else result
        status = (
            f"PRESET · {format} · {size} · {width}×{height}"
            if mode == "PRESET"
            else f"MANUAL · {width}×{height}"
        )
        return {
            "ui": {"status": [status], "resolution": [f"{width}×{height}"]},
            "result": (latent, width, height, status),
        }
