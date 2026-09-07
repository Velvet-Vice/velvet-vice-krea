"""ComfyUI-Manager install helper for VELVET VICE — KREA.

This script is intentionally dependency-free. It only migrates exact legacy
Velvet Vice KREA install folders out of custom_nodes so duplicate packages
cannot survive a Registry/Manager installation.
"""

from __future__ import annotations

import os
import shutil
import stat
from datetime import datetime
from pathlib import Path

LEGACY_KREA_DIRS = (
    "ComfyUI-Velvet-Vice-KREA",
    "ComfyUI-Velvet-Vice-KREA-main",
    "velvet-vice-krea-main",
    "ComfyUI-ILLUMINATE-AI-KREA",
)
PROTECTED_LTX_DIR = "ComfyUI-Velvet-Vice-LTX"


def _custom_nodes_root(package_root: Path) -> Path:
    parent = package_root.parent
    if parent.name == ".disabled":
        return parent.parent
    return parent


def _make_writable(path: Path) -> None:
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    except OSError:
        pass


def _make_tree_writable(path: Path) -> None:
    if not path.exists():
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            _make_writable(Path(root) / name)
        for name in dirs:
            _make_writable(Path(root) / name)
    _make_writable(path)


def migrate_legacy_installs(package_root: Path | None = None) -> list[tuple[Path, Path]]:
    package_root = (package_root or Path(__file__).resolve().parent).resolve()
    custom_nodes = _custom_nodes_root(package_root).resolve()
    comfy_root = custom_nodes.parent

    if package_root.name == PROTECTED_LTX_DIR:
        raise RuntimeError("Safety guard: KREA lifecycle helper must never target the LTX package.")

    backup_root = comfy_root / "VelvetVice_Backups" / "KREA" / (
        "manager-migration-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    )

    moved: list[tuple[Path, Path]] = []
    candidates: list[Path] = []
    for name in LEGACY_KREA_DIRS:
        candidates.extend(
            (
                custom_nodes / name,
                custom_nodes / f"{name}.disabled",
                custom_nodes / ".disabled" / name,
                custom_nodes / ".disabled" / f"{name}.disabled",
            )
        )

    for source in candidates:
        try:
            source_resolved = source.resolve()
        except OSError:
            source_resolved = source

        if not source.exists() or source_resolved == package_root:
            continue
        if source.name == PROTECTED_LTX_DIR or PROTECTED_LTX_DIR in source.parts:
            continue

        backup_root.mkdir(parents=True, exist_ok=True)
        destination = backup_root / source.name
        suffix = 1
        while destination.exists():
            destination = backup_root / f"{source.name}-{suffix}"
            suffix += 1

        try:
            _make_tree_writable(source)
            shutil.move(str(source), str(destination))
            moved.append((source, destination))
            print(f"[VELVET VICE KREA] Legacy duplicate moved out of custom_nodes: {source} -> {destination}")
        except Exception as exc:
            print(f"[VELVET VICE KREA] WARNING: Could not migrate legacy duplicate {source}: {exc}")

    return moved


def main() -> int:
    moved = migrate_legacy_installs()
    if moved:
        print(f"[VELVET VICE KREA] Migrated {len(moved)} legacy KREA install(s).")
    else:
        print("[VELVET VICE KREA] No legacy KREA duplicates detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
