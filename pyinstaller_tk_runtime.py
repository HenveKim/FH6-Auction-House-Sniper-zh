"""Runtime hook for bundled tkinter on pyenv-win/PyInstaller builds."""
from __future__ import annotations

import os
import sys


def _first_dir(parent: str, prefix: str) -> str | None:
    if not os.path.isdir(parent):
        return None
    for name in os.listdir(parent):
        path = os.path.join(parent, name)
        if name.startswith(prefix) and os.path.isdir(path):
            return path
    return None


base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
if base not in sys.path:
    sys.path.insert(0, base)

tcl_root = os.path.join(base, "tcl")

tcl_library = _first_dir(tcl_root, "tcl8.")
tk_library = _first_dir(tcl_root, "tk8.")

if tcl_library:
    os.environ.setdefault("TCL_LIBRARY", tcl_library)
if tk_library:
    os.environ.setdefault("TK_LIBRARY", tk_library)
