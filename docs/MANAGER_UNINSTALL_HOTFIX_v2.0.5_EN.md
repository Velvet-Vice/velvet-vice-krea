# VELVET VICE KREA — ComfyUI Manager Uninstall Hotfix v2.0.5

This release adds explicit ComfyUI-Manager lifecycle helpers to the Registry package.

## What is fixed

- `install.py` migrates known historical Velvet Vice KREA duplicate folders out of `custom_nodes`.
- `uninstall.py` removes known legacy KREA duplicates when the user chooses Uninstall in ComfyUI Manager.
- Before Manager removes the active package, `uninstall.py` clears read-only attributes recursively to reduce Windows `PermissionError / WinError 5` deletion failures.
- The helper never deletes or modifies `ComfyUI-Velvet-Vice-LTX`.
- Registry identity remains `velvet-vice-krea`.

## Known historical KREA names handled

- `ComfyUI-Velvet-Vice-KREA`
- `ComfyUI-Velvet-Vice-KREA-main`
- `velvet-vice-krea-main`
- `ComfyUI-ILLUMINATE-AI-KREA`

The canonical Manager/Registry package remains:

`ComfyUI/custom_nodes/velvet-vice-krea`

A Manager uninstall should remove the canonical package and clean the exact historical KREA duplicates above, without touching LTX.
