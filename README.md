# VELVET VICE — KREA

Velvet Vice custom nodes and interface styling for the Krea 2 Vision Prompter workflow.

Version `2.0.4` accompanies the stable **VELVET VICE KREA 2 VISION PROMPTER v2.0.4** workflow. It retains the independent CREATE / Native Edit / Classic Img2Img architecture and promotes the tested branch-isolation fixes to the public runtime.

## What changed in v2.0.4

- Prompt-First inactive branches now return ComfyUI `ExecutionBlocker` objects instead of raw `None`, preventing inactive VAEDecode, CLIP and sampler paths from dereferencing invalid resources.
- Lazy branch resolution is graph-aware, so optional inputs removed by bypassed groups are never incorrectly strengthened into missing links.
- Native Edit requests `native_original_latent` only for `NATIVE EDIT — ORIGINAL`; the Custom target keeps its own target latent.
- Native Original, Native Custom and Classic Img2Img SeedVR2 finish paths use a workflow-mode-aware output gate.
- SeedVR2 can receive a dedicated memory handoff before loading its large models.
- Native Edit keeps its corrected 768 px grounded-reference path.
- The public Classic Img2Img workflow uses neutral defaults: optional creative LoRAs OFF, denoise 0.40 and SeedVR2 bypassed during base testing.

## Complete Image Edit Guide

For detailed setup, mode selection, Native Edit Original/Custom, Classic Img2Img denoise behavior, example prompts and troubleshooting, see [`IMAGE_EDIT_GUIDE.md`](IMAGE_EDIT_GUIDE.md).

## Installation

### ComfyUI-Manager / Comfy Registry (recommended)

Install **VELVET VICE — KREA** through ComfyUI-Manager / the Comfy Registry. The canonical package ID and install folder are:

`velvet-vice-krea`

Then restart ComfyUI completely and hard-refresh the browser with `Ctrl+F5`.

Keep only one Velvet Vice KREA copy in `ComfyUI/custom_nodes`. Legacy folders such as `ComfyUI-Velvet-Vice-KREA`, `ComfyUI-Velvet-Vice-KREA-main`, `velvet-vice-krea-main` or `ComfyUI-ILLUMINATE-AI-KREA` can load the same nodes twice and cause confusing UI or uninstall behavior. The repository includes `_CLEAN_LEGACY_KREA_DUPLICATES.cmd` for one-time cleanup.

### Civitai package

The Civitai v2.0.4 ZIP includes an isolated installer and the full workflow. The installer targets the same canonical folder:

`ComfyUI/custom_nodes/velvet-vice-krea`

Close ComfyUI before running the installer. It uses a staged copy, backs up the previous KREA folder and never targets the Velvet Vice LTX node pack.

## Vision Prompt Director v2

- MANUAL returns `manual_prompt` unchanged and never contacts Ollama.
- ASSISTED sends `short_idea` once to the configured Qwen3.5 9B model.
- A release barrier verifies Ollama is released before the selected Krea render branch resolves heavy inputs.
- The workflow-mode selector keeps CREATE, Native Edit and Classic Img2Img prompt behavior separate.

## Independent image architecture

| Branch | Local model/decode | Local SeedVR2 | Local preview | Local save |
|---|---:|---:|---:|---:|
| CREATE | Yes | Yes | Yes | Yes |
| Native Edit — Original | Yes | Yes | Yes | Yes |
| Native Edit — Custom | Yes | Yes | Yes | Yes |
| Classic Img2Img | Yes | Yes | Yes | Yes |

Inactive branches are isolated server-side rather than being allowed to emit `None` into normal ComfyUI nodes.

## Native Edit

Native Edit is the source-faithful editing path. The source image is preprocessed and grounded before the sampler. Use it for targeted edits where identity, pose, camera and composition should remain close to the original.

## Classic Img2Img

Classic Img2Img is a traditional denoise-based image-to-image path. The source image is normalized, resized, VAE encoded and connected to the KSampler `latent_image` input. The stable public defaults are deliberately neutral:

- Denoise: `0.40`
- Optional creative LoRAs: OFF
- SeedVR2: optional / bypassed for the first base test

Raise denoise only when stronger reinterpretation is intended.

## Velvet Vice interface

The browser extension applies the private KREA-only Emerald + Violet visual system and retains the established Velvet Vice execution animation. Newly created or pasted `Power Lora Loader (rgthree)` nodes are adopted only when the graph is already identified as a Velvet Vice KREA workflow. LTX graphs remain outside the KREA namespace.

## Registry

- Publisher: `velvet-vice`
- Node ID: `velvet-vice-krea`
- Version: `2.0.4`
- Display name: `VELVET VICE — KREA`
