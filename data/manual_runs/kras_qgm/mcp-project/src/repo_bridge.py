"""Import bridge for the pinned quantum-generative-models checkout.

The repository's ``utils/__init__.py`` and ``models/__init__.py`` import
``orquestra.qml``, which is not installable from any public source (Zapata AI
discontinued Orquestra; both ``orquestra-qml`` and ``orquestra-qml-core`` return
HTTP 404 from PyPI). A plain ``import utils.filter`` therefore fails before it
reaches any of the code we actually want.

``install()`` registers synthetic namespace packages for ``utils``, ``models``,
``models.priors`` and ``models.error`` whose ``__path__`` points at the real
directories, so the modules below resolve their relative imports normally while
the orquestra-importing ``__init__.py`` files never execute.

``repo_cwd()`` is required for ``utils.filter``: it loads
``./database/pains.txt``, ``./database/wehi_pains.csv`` and ``./database/mcf.csv``
at module scope inside a ``try/except FileNotFoundError`` that only warns. From
the wrong working directory the import succeeds and the first call then fails
with ``NameError: name '_filters' is not defined``.

This module does no scientific computation. It only makes the upstream code
importable.
"""

from __future__ import annotations

import contextlib
import os
import sys
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT / "repo" / "quantum-generative-models"

#: Packages whose real ``__init__.py`` must not run, mapped to their directory.
_NAMESPACES = {
    "utils": REPO_ROOT / "utils",
    "models": REPO_ROOT / "models",
    "models.priors": REPO_ROOT / "models" / "priors",
    "models.error": REPO_ROOT / "models" / "error",
}


def _register(name: str, path: Path) -> types.ModuleType:
    existing = sys.modules.get(name)
    if existing is not None and getattr(existing, "__paper2mcp_bridge__", False):
        return existing
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    module.__package__ = name
    module.__paper2mcp_bridge__ = True
    sys.modules[name] = module
    if "." in name:
        parent_name, _, leaf = name.rpartition(".")
        setattr(sys.modules[parent_name], leaf, module)
    return module


def install() -> Path:
    """Make the pinned repository importable. Returns the repository root."""
    if not REPO_ROOT.is_dir():
        raise RuntimeError(f"pinned repository checkout not found at {REPO_ROOT}")
    repo = str(REPO_ROOT)
    if repo not in sys.path:
        sys.path.insert(0, repo)
    for name, path in _NAMESPACES.items():
        _register(name, path)
    return REPO_ROOT


@contextlib.contextmanager
def repo_cwd():
    """Run with the working directory at the repository root.

    ``utils.filter`` resolves its structural-alert catalogues relative to the
    working directory at import time, so it must first be imported under this.
    """
    previous = os.getcwd()
    os.chdir(REPO_ROOT)
    try:
        yield REPO_ROOT
    finally:
        os.chdir(previous)


def load_filter_module():
    """Import ``utils.filter`` with its catalogues actually loaded.

    Raises if the catalogues did not load, instead of leaving the silent-empty
    failure mode the upstream ``except FileNotFoundError`` creates.
    """
    install()
    with repo_cwd():
        import utils.filter as _filter  # noqa: PLC0415

        for attr in ("_filters", "dic"):
            if not hasattr(_filter, attr):
                raise RuntimeError(
                    "utils.filter imported without its structural-alert catalogues "
                    f"(missing {attr!r}). The upstream module swallows a missing "
                    "database/ directory in a try/except that only warns, so any "
                    "call would fail with NameError or silently accept nothing. "
                    f"Expected catalogues under {REPO_ROOT / 'database'}."
                )
    return _filter
