# VELVET VICE KREA 2 — Missing Nodes Registry Metadata Hotfix (v2.0.4)

The public workflow now embeds Comfy Registry metadata on every `VelvetViceKrea*` workflow node:

- `cnr_id`: `velvet-vice-krea`
- `ver`: `2.0.4`

This allows ComfyUI Manager / **Missing Custom Nodes** to map missing Velvet Vice KREA nodes directly to the canonical Registry package:

`velvet-vice-krea`

The Registry package itself already exposes the public Velvet Vice KREA node classes through `node_list.json`. This hotfix corrects the workflow-side metadata used by clean installations and Missing Custom Nodes detection.

For a clean-install verification, temporarily remove or rename the installed `velvet-vice-krea` folder, restart ComfyUI completely, load the current v2.0.4 workflow and open **Missing Custom Nodes**.
