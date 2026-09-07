"""ComfyUI-Manager uninstall helper for VELVET VICE — KREA.

Manager executes this script before removing the package. The helper makes the
current package writable so Windows can delete it, and removes exact historical
KREA duplicate folders that could otherwise make the node pack appear to remain
installed after a successful Manager uninstall.

The Velvet Vice LTX package is explicitly protected and is never touched.
"""

from __future__ import annotations

import os
import shutil
import stat
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


def make_tree_writable(path: Path) -> None:
    if not path.exists():
        return
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            _make_writable(Path(root) / name)
        for name in dirs:
            _make_writable(Path(root) / name)
    _make_writable(path)


def _rmtree_writable(path: Path) -> None:
    def onerror(func, failed_path, _exc_info):
        failed = Path(failed_path)
        _make_writable(failed)
        func(failed_path)

    make_tree_writable(path)
    shutil.rmtree(path, onerror=onerror)


def cleanup_legacy_installs(package_root: Path | None = None) -> list[Path]:
    package_root = (package_root or Path(__file__).resolve().parent).resolve()
    custom_nodes = _custom_nodes_root(package_root).resolve()

    if package_root.name == PROTECTED_LTX_DIR:
        raise RuntimeError("Safety guard: KREA lifecycle helper must never target the LTX package.")

    removed: list[Path] = []
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

    for candidate in candidates:
        if not candidate.exists():
            continue

        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate

        if resolved == package_root:
            continue
        if candidate.name == PROTECTED_LTX_DIR or PROTECTED_LTX_DIR in candidate.parts:
            continue

        try:
            _rmtree_writable(candidate)
            removed.append(candidate)
            print(f"[VELVET VICE KREA] Removed legacy duplicate during uninstall: {candidate}")
        except Exception as exc:
            print(f"[VELVET VICE KREA] WARNING: Could not remove legacy duplicate {candidate}: {exc}")

    make_tree_writable(package_root)
    return removed


def main() -> int:
    removed = cleanup_legacy_installs()
    print(
        "[VELVET VICE KREA] Uninstall preparation complete"
        + (f"; removed {len(removed)} legacy duplicate(s)." if removed else ".")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
