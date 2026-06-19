"""Path resolution that works in both source and frozen (PyInstaller) builds."""
from __future__ import annotations
import sys
from pathlib import Path


def app_dir() -> Path:
    """Directory holding user-writable config and logs.

    Frozen exe: the folder containing the exe.
    Source: the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def resource_dir() -> Path:
    """Directory holding bundled read-only resources such as templates.

    Frozen exe: PyInstaller's internal resource directory.
    Source: the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent
