# VELVET VICE KREA 2 — Image Edit Group Split (v2.0.4)

The Image Edit Studio uses separate bypassable front-end groups so Native Edit and Classic Img2Img cannot be activated together by one shared group toggle.

- `04A — NATIVE EDIT STUDIO • ORIGINAL / CUSTOM`
  - Native source image
  - Native Original sampler
  - Native Custom target latent and sampler
  - Native edit seed
- `04B — CLASSIC IMG2IMG STUDIO • SOURCE / DENOISE`
  - Classic source image
  - Classic KSampler
  - Classic negative switcher
- `04C — IMAGE EDIT BRANCH CONTROL • ENABLE / GUIDE`
  - Native and Classic Fast Groups Bypasser controls
  - activation guide
  - should remain active

## Native Edit
Enable `04A` + `INTERNAL B — NATIVE EDIT ENGINE` and keep `04B` bypassed.

## Classic Img2Img
Enable `04B` + `INTERNAL C — CLASSIC IMG2IMG ENGINE` and keep `04A` bypassed.

This prevents both source/sampler front ends from running sequentially when only one image-edit method is intended.
