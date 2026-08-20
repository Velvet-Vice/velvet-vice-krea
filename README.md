# ComfyUI-Velvet-Vice-KREA

Velvet Vice custom nodes and interface styling for the Krea 2 Vision Prompter workflow.

Version `2.0.0` accompanies the public **VELVET VICE KREA 2 VISION PROMPTER v2.0** workflow. It keeps the independent CREATE / Native Edit / Classic Img2Img architecture and adds the Prompt Director v2, verified prompt-first Ollama release gate, CREATE Format & Resolution selector, Render This Stage controller, safe interrupt recovery, Krea-only Emerald + Violet theme isolation, PowerLoRA theme auto-adoption, layout-safety fixes, and model-neutral Krea diffusion-model selectors.

## Installation

### ComfyUI-Manager / Comfy Registry (recommended)

Install **VELVET VICE — KREA** through ComfyUI-Manager / the Comfy Registry, then restart ComfyUI. The registered package provides all `VelvetViceKrea...` node classes used by the public workflow.

### Civitai release installer

The complete Civitai release also includes the isolated Velvet Vice KREA installer. It backs up and replaces only the dedicated Velvet Vice KREA custom-node installation and does not modify the separate Velvet Vice LTX custom-node pack.

### Manual fallback

1. Remove an older `ComfyUI-ILLUMINATE-AI-KREA` folder if it is still installed.
2. Place this repository in `ComfyUI/custom_nodes/`.
3. Restart ComfyUI completely.
4. Load `VELVET_VICE_KREA2_VISION_PROMPTER_v2.0.json`.

No additional `pip install` is required by this node pack.

## Model-neutral Krea loader

The public v2.0 workflow does not store a creator-specific diffusion-model filename. CREATE, Native Edit and Classic Img2Img each keep their own independent `VelvetViceKreaModelLoader`. The saved value is `SELECT KREA 2 MODEL`; at runtime the dropdown lists models available in the user's ComfyUI `diffusion_models` folder.

Only the branch being executed needs a valid Krea 2-compatible model selection. The loader delegates the actual load to ComfyUI's core UNET loader so its weight-dtype behavior remains unchanged.

## Vision Prompt Director v2

- MANUAL returns `manual_prompt` unchanged and never creates or contacts an Ollama client.
- ASSISTED sends `short_idea` exactly once to the configured Qwen3.5 9B model.
- Adaptive Krea-specific expansion, explicit constraint locking and STRICT / BALANCED / CREATIVE Director Freedom are included.
- A release barrier verifies the Ollama model is gone before the selected Krea render branch may resolve its heavy inputs.

## Independent image architecture

| Branch | Local model/decode | Local SeedVR2 | Local preview | Local save |
|---|---:|---:|---:|---:|
| CREATE | Yes | Yes | Yes | Yes |
| Native Edit — Original | Yes | Yes | Yes | Yes |
| Native Edit — Custom | Yes | Yes | Yes | Yes |
| Classic Img2Img | Yes | Yes | Yes | Yes |

Only enable the required branch with the existing Fast Groups Bypasser controls. All other branches should remain bypassed.

## Velvet Vice interface

The browser extension applies the private Krea-only Emerald + Violet visual system and retains the established Velvet Vice execution animation. Newly created, pasted or duplicated `Power Lora Loader (rgthree)` nodes are adopted only when the graph is already identified as a Velvet Vice KREA workflow. LTX graphs remain outside the Krea namespace.

## Render This Stage

The CREATE studio includes BASE, REFINEMENT, DETAILER and SEEDVR2 / FINAL partial-execution controls targeting the existing preview outputs. Normal full-workflow execution is not rewired.

## Format & Resolution

CREATE offers PRESET aspect ratios and STANDARD/HIGH profiles while MANUAL preserves direct width/height control. Switching away from MANUAL does not overwrite the saved manual values.

## Validation

The runtime files in this Registry package are byte-identical to the validated KREA v2.0 Civitai runtime. Release-level workflow, layout and installer tests are maintained with the full Civitai release package.
