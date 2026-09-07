# VELVET VICE — KREA

Velvet Vice custom nodes and interface styling for the Krea 2 Vision Prompter workflow.

Version `2.0.5` keeps the complete v2.0.4 rendering/edit architecture and adds a ComfyUI Manager / Comfy Registry lifecycle hotfix focused on clean install and uninstall behavior.

## What changed in v2.0.5

- Added `install.py` lifecycle migration for exact historical KREA duplicate folders.
- Added `uninstall.py` lifecycle cleanup for ComfyUI Manager / Comfy Registry uninstalls.
- Before Manager removes the active package, the uninstall helper recursively clears read-only attributes to reduce Windows `PermissionError / WinError 5` deletion failures.
- Exact legacy KREA folders are removed so an old duplicate cannot make the nodes appear to remain installed after a successful Manager uninstall.
- `ComfyUI-Velvet-Vice-LTX` is explicitly protected and is never touched.
- Registry identity remains `velvet-vice-krea`.
- All v2.0.4 fixes remain: Prompt-First branch isolation, Native Edit 768 px grounding, SeedVR2 output isolation, Classic Img2Img denoise 0.40 neutral default, separate `04A / 04B / 04C` edit groups, and Missing Custom Nodes Registry metadata.

## Complete Image Edit Guide

For detailed setup, mode selection, Native Edit Original/Custom, Classic Img2Img denoise behavior, example prompts and troubleshooting, see [`IMAGE_EDIT_GUIDE.md`](IMAGE_EDIT_GUIDE.md).

## Installation

### ComfyUI-Manager / Comfy Registry (recommended)

Install **VELVET VICE — KREA** through ComfyUI-Manager / the Comfy Registry. The canonical package ID and install folder are:

`velvet-vice-krea`

Then restart ComfyUI completely and hard-refresh the browser with `Ctrl+F5`.

The v2.0.5 Registry package now includes lifecycle helpers that migrate/remove the following exact historical KREA duplicates:

- `ComfyUI-Velvet-Vice-KREA`
- `ComfyUI-Velvet-Vice-KREA-main`
- `velvet-vice-krea-main`
- `ComfyUI-ILLUMINATE-AI-KREA`

The Velvet Vice LTX package is not targeted by these helpers.

### Civitai package

The Civitai v2.0.5 ZIP includes the full workflow, the canonical `velvet-vice-krea` custom-node package, the Qwen3.5 Autoprompt installer BAT, the Windows Portable launch example, documentation and the isolated fallback installer.

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

Classic Img2Img is a traditional denoise-based image-to-image path. The source image is normalized, resized, VAE encoded and connected to the KSampler `latent_image` input. Stable public defaults remain:

- Denoise: `0.40`
- Optional creative LoRAs: OFF
- SeedVR2: optional / bypassed for the first base test

## Registry

- Publisher: `velvet-vice`
- Node ID: `velvet-vice-krea`
- Version: `2.0.5`
- Display name: `VELVET VICE — KREA`
