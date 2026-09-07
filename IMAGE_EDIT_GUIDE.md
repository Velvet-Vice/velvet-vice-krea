# VELVET VICE — KREA 2 VISION PROMPTER v2.0.4
## Complete Image Edit Guide

This guide explains the two image-editing systems included in the workflow:

1. **KREA 2 Native Edit** — precise, instruction-based editing designed to preserve the source image.
2. **Classic Img2Img** — traditional denoise-based image-to-image for more creative reinterpretation.

Native Edit also contains two target modes:

- **NATIVE EDIT — ORIGINAL** — keeps the source image dimensions/latent as the edit target.
- **NATIVE EDIT — CUSTOM** — uses the same source image for visual grounding but generates into a separately defined target format/latent.

---

# 1. Before using any Edit mode

The most important control is **00 — WORKFLOW MODE / PROMPT PROFILE**.

Select the mode you actually want to run before changing the edit controls:

- `NATIVE EDIT — ORIGINAL`
- `NATIVE EDIT — CUSTOM`
- `CLASSIC IMG2IMG`

The workflow mode determines which model/CLIP/VAE branch is allowed to resolve through the Prompt-First Gate. The other branches are blocked so they cannot accidentally run with invalid resources.

In the group controls, keep the common workflow sections available and make sure the edit section/output section required for your mode is enabled.

For normal editing, the important groups are:

- `00 — VELVET VICE CONTROL HUB · MODE / FORMAT / SEED`
- `01 — VELVET VICE CORE LOADOUT · MODEL / ENCODER / VAE / LORAS`
- `02 — VELVET VICE VISION PROMPT STUDIO · MANUAL / ASSISTED`
- `04 — IMAGE EDIT STUDIO · THREE INDEPENDENT MODES`
- `06 — INDEPENDENT OUTPUT STUDIO · FOUR LOCAL FINISH PATHS`

For Native Edit, also enable:

- `INTERNAL B — NATIVE EDIT ENGINE`

For Classic Img2Img, also enable:

- `INTERNAL C — CLASSIC IMG2IMG ENGINE`

You do **not** need to enable optional detailers, concept batch or SeedVR2 just to test whether editing works.

---

# 2. Prompt Mode: MANUAL vs ASSISTED

`workflow_mode` and `prompt_mode` are different controls.

The **workflow mode** chooses the branch: CREATE, Native Edit or Classic Img2Img.

The **Prompt Director mode** chooses how the text prompt is produced:

### MANUAL
Write the final instruction yourself. Ollama is not contacted.

### ASSISTED
Write a short idea. The Prompt Director uses the configured Qwen model to expand the instruction and releases Ollama before the Krea render branch is allowed to load.

For troubleshooting, **MANUAL is recommended first** because it removes the prompt-enhancement step from the test.

---

# 3. KREA 2 NATIVE EDIT

## When should I use Native Edit?

Use Native Edit when the source image should remain recognizable and you want a targeted change.

Typical examples:

- change clothing while preserving the face and pose
- replace or modify an object
- alter lighting or color
- change part of the background
- preserve identity and composition
- make a controlled instruction-based edit

If your goal is "change this specific thing, but keep the rest of the image", Native Edit is usually the correct choice.

---

## Native Edit — ORIGINAL: Quick Start

### Step 1 — Select the mode
In **00 — WORKFLOW MODE / PROMPT PROFILE**, choose:

`NATIVE EDIT — ORIGINAL`

### Step 2 — Enable the correct groups
Make sure these are enabled:

- `04 — IMAGE EDIT STUDIO`
- `06 — INDEPENDENT OUTPUT STUDIO`
- `INTERNAL B — NATIVE EDIT ENGINE`

### Step 3 — Load the source image
Go to:

`NATIVE EDIT — SOURCE IMAGE`

Load the image you want to edit.

This is the reference image used by the Native Edit preprocessing and grounded image-conditioning path.

### Step 4 — Write the edit instruction
Use a direct editing instruction. Describe both:

- what should change
- what should stay unchanged

Example:

> Replace her black jacket with a dark red leather jacket. Keep her face, hairstyle, pose, body proportions, camera angle, lighting and background unchanged.

This usually works better than a short keyword prompt such as:

> red leather jacket

### Step 5 — Render the base edit first
Leave optional SeedVR2 disabled/bypassed for the first test.

Check:

`KREA 2 EDIT — ORIGINAL TARGET BASE RESULT PREVIEW`

Only after the base edit looks correct should you enable optional final-resolution processing.

---

# 4. What Native Edit does internally

The source image is not simply passed into a normal Text-to-Image sampler.

The Native Edit path performs dedicated preprocessing and reference grounding. In v2.0.4 the source/reference path is connected through the Native Edit preprocessing/model-patch stage and the grounded edit conditioning uses the corrected **768 px** reference resolution.

The Prompt-First Gate keeps the Native model, CLIP, VAE and Native preprocessing behind the selected workflow mode so CREATE or Classic resources cannot cross into this branch.

For `NATIVE EDIT — ORIGINAL`, the original source latent is also used as the target latent.

---

# 5. Native Edit — CUSTOM

Choose:

`NATIVE EDIT — CUSTOM`

when you want Native Edit's source-image grounding but want the generated target to use a separately defined target format/latent instead of strictly using the original source latent.

The source image still matters. It is used for the Native Edit reference/grounding path, while the target latent comes from the Custom Target setup.

This is useful when you need to change the output canvas or target format while retaining visual guidance from the source.

Important difference:

- **ORIGINAL** uses `native_original_latent`.
- **CUSTOM** does not require `native_original_latent`; it uses its own target latent.

Check the Custom result at:

`KREA 2 EDIT — CUSTOM TARGET BASE RESULT PREVIEW`

Again, test the base result before enabling SeedVR2.

---

# 6. Native Edit prompt examples

### Clothing edit
> Change her white shirt into a fitted black leather jacket. Preserve her face, hair, pose, body proportions, camera angle and background.

### Background edit
> Replace the plain wall behind the subject with a dim industrial laboratory. Keep the person, pose, clothing, face and camera perspective unchanged.

### Lighting edit
> Change the lighting to warm golden-hour light coming from the left. Preserve the subject, clothing, pose, facial features and background structure.

### Object replacement
> Replace the cup in his right hand with a small glass bottle. Keep the hand position, body pose, face, clothing and scene composition unchanged.

The more important preservation is, the more explicitly you should state what must remain unchanged.

---

# 7. CLASSIC IMG2IMG

## When should I use Classic Img2Img?

Classic Img2Img is the more traditional denoise-based workflow.

Use it when you want:

- stronger style changes
- creative reinterpretation
- more freedom from the source
- a normal denoise control
- traditional positive/optional negative conditioning
- to preserve the basic source structure while allowing the model to redesign more of the image

Classic Img2Img is intentionally less strict than Native Edit.

---

## Classic Img2Img: Quick Start

### Step 1 — Select the mode
In **00 — WORKFLOW MODE / PROMPT PROFILE**, choose:

`CLASSIC IMG2IMG`

### Step 2 — Enable the correct groups
Make sure these are enabled:

- `04 — IMAGE EDIT STUDIO`
- `06 — INDEPENDENT OUTPUT STUDIO`
- `INTERNAL C — CLASSIC IMG2IMG ENGINE`

### Step 3 — Load the source image
Load your image into:

`CLASSIC IMG2IMG SOURCE`

The source image is then processed through:

`SOURCE → NORMALIZATION → RESIZE → VAE ENCODE → KSampler latent_image`

So Classic Img2Img is **not** a hidden Text-to-Image branch. The source image really becomes the starting latent for the sampler.

### Step 4 — Write the transformation prompt
Classic Img2Img accepts a more result-oriented prompt than Native Edit.

Example:

> Transform the source into a cinematic dark-fantasy portrait with dramatic rim lighting, richer shadows, detailed fabric and a moody gothic atmosphere while keeping the overall pose and composition recognizable.

### Step 5 — Start at denoise 0.40
v2.0.4 ships with:

`Denoise = 0.40`

This is deliberately more source-faithful than the earlier test value.

### Step 6 — Keep optional creative LoRAs OFF initially
All optional creative LoRAs in the Classic Img2Img Power LoRA Loader are OFF by default in v2.0.4.

This is important for troubleshooting. First confirm that the source image behaves correctly, then enable creative LoRAs one at a time.

### Step 7 — Check the Base Preview
Use:

`CLASSIC IMG2IMG PREVIEW`

before enabling SeedVR2.

---

# 8. Classic Img2Img denoise guide

Denoise is the most important control for how strongly Classic Img2Img follows the source image.

### 0.20–0.30 — very conservative
The source image dominates. Useful for small texture/style adjustments.

### 0.30–0.45 — source-faithful / balanced
Good starting range when the original image should still clearly drive composition and subject structure.

**v2.0.4 default: 0.40**

### 0.45–0.60 — stronger reinterpretation
The prompt gains more influence. Identity, small structures and clothing can change more noticeably.

### 0.60–0.75 — creative transformation
The source still provides a latent starting point, but the model has considerably more freedom.

### 0.75+ — very strong transformation
At this point the result can feel much closer to a re-generation than a conservative image edit.

If Classic Img2Img appears to "ignore" the source image, first lower denoise before changing anything else.

---

# 9. Optional negative prompt in Classic Img2Img

Classic Img2Img includes an optional traditional negative-conditioning path.

Keep it short and focused, for example:

> blurry, low detail, distorted hands, extra fingers, text artifacts

Do not assume a huge negative keyword list will improve the result. Test the zero-negative/default path first.

---

# 10. SeedVR2: use it after the edit works

Native Edit and Classic Img2Img each have their own isolated SeedVR2 finish path.

SeedVR2 is a **final stage**, not the editing engine itself.

Recommended test order:

1. Run the edit without SeedVR2.
2. Inspect the base preview.
3. Confirm the source image and prompt behavior are correct.
4. Only then enable SeedVR2.
5. Compare the base result with the final upscaled result.

SeedVR2 can improve final presentation/resolution, but it can also reinterpret small details. Do not diagnose the base edit by looking only at the SeedVR2 output.

v2.0.4 includes workflow-mode-aware SeedVR2 output gates so inactive Native/Classic finish paths do not produce missing `image`, `dit` or `vae` connection errors.

---

# 11. Native Edit vs Classic Img2Img — which one should I choose?

| Goal | Recommended mode |
|---|---|
| Change one specific thing and preserve the rest | Native Edit |
| Preserve face/identity as much as possible | Native Edit |
| Preserve pose and camera composition | Native Edit |
| Targeted clothing/background/object edit | Native Edit |
| Change output target/canvas while keeping Native grounding | Native Edit — Custom |
| Creative style transformation | Classic Img2Img |
| Strong reinterpretation | Classic Img2Img |
| Traditional denoise workflow | Classic Img2Img |
| Want direct control over source-vs-prompt strength | Classic Img2Img |

A simple rule:

**Native Edit = "edit this image."**

**Classic Img2Img = "reinterpret this image."**

---

# 12. Troubleshooting

## The edit looks like Text-to-Image

### Native Edit
Check that:

- workflow mode is `NATIVE EDIT — ORIGINAL` or `NATIVE EDIT — CUSTOM`
- the source image is loaded in `NATIVE EDIT — SOURCE IMAGE`
- `04 — IMAGE EDIT STUDIO` is enabled
- `INTERNAL B — NATIVE EDIT ENGINE` is enabled
- you are inspecting the Native base preview, not a different branch output

### Classic Img2Img
Check that:

- workflow mode is `CLASSIC IMG2IMG`
- the image is loaded in `CLASSIC IMG2IMG SOURCE`
- `INTERNAL C — CLASSIC IMG2IMG ENGINE` is enabled
- denoise is around `0.40` for the first test
- creative LoRAs remain OFF
- SeedVR2 is bypassed while troubleshooting

The Classic branch's source is physically wired through VAE Encode into the sampler latent, so excessive drift is normally a denoise/prompt/LoRA issue rather than a missing source connection.

---

## Error: `NoneType object has no attribute decode`

This was addressed in v2.0.4 by blocking inactive Prompt-First outputs with `ExecutionBlocker` instead of sending raw `None` into normal ComfyUI nodes.

If you still see it after upgrading:

- make sure only one Velvet Vice KREA custom-node copy is installed
- restart ComfyUI completely
- reload the v2.0.4 workflow

---

## Error: `there is no input to that node at all`

v2.0.4 uses graph-aware lazy input resolution so the Prompt-First Gate does not request optional inputs that ComfyUI removed because their source group was bypassed.

If the selected branch itself is genuinely disabled, the workflow should now provide a more readable Velvet Vice error telling you which internal engine must be enabled.

---

## SeedVR2 says `Required input is missing: image / dit / vae`

The v2.0.4 workflow contains separate mode-aware output gates for Native Original, Native Custom and Classic Img2Img.

If this error appears after upgrading, verify that:

- you loaded the v2.0.4 workflow, not an older JSON
- the matching internal edit engine is enabled
- the source image is loaded
- the current `workflow_mode` matches the output branch you are trying to use

---

## The source image loader gives a permission error

If ComfyUI reports `Permission denied` for the `input` directory, make sure an actual image file is selected in the Load Image node. The input directory itself must not be treated as the selected image file.

---

# 13. Recommended first test for every new installation

Use a clearly recognizable source image and perform one simple edit.

### Native Edit test

Mode:

`NATIVE EDIT — ORIGINAL`

Prompt:

> Change the jacket from black to red. Keep everything else unchanged.

SeedVR2:

OFF / bypassed

Expected result:

The person, pose, framing and scene should remain close to the source, with the requested targeted change.

### Classic Img2Img test

Mode:

`CLASSIC IMG2IMG`

Denoise:

`0.40`

Creative LoRAs:

OFF

Prompt:

> Reinterpret the image as a cinematic portrait with dramatic lighting while keeping the subject and composition recognizable.

SeedVR2:

OFF / bypassed

Expected result:

The source structure should remain recognizable, while the prompt has more freedom than Native Edit.

---

# 14. Safe workflow for advanced experimentation

Once the base edit works:

1. Change only one setting at a time.
2. Increase Classic denoise gradually.
3. Add one LoRA at a time.
4. Compare Native Edit and Classic Img2Img using the same source.
5. Enable SeedVR2 only after the base result is good.
6. Keep separate previews as checkpoints so you know which stage introduced a change.

This makes it much easier to distinguish an actual workflow problem from a creative setting that intentionally gives the model more freedom.

---

## Summary

### KREA 2 Native Edit
Best for controlled, source-faithful edits.

**Basic path:**

`Select Native mode → Load NATIVE EDIT source → Write direct edit instruction → Base Preview → optional SeedVR2`

### Classic Img2Img
Best for traditional denoise-based reinterpretation.

**Basic path:**

`Select CLASSIC IMG2IMG → Load CLASSIC source → Denoise 0.40 → Base Preview → optional LoRAs / SeedVR2`

When troubleshooting, always test the simplest base path first.
