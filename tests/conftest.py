"""Test setup.

Loads the integration's ``ndbc`` module directly from its file so the parser
can be tested without installing Home Assistant. The package's ``__init__.py``
(which imports Home Assistant) is deliberately never executed.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "ndbc_buoy"


def _load_ndbc() -> types.ModuleType:
    if "ndbc_buoy" not in sys.modules:
        pkg = types.ModuleType("ndbc_buoy")
        pkg.__path__ = [str(PKG_DIR)]
        sys.modules["ndbc_buoy"] = pkg

    for name in ("const", "ndbc"):
        full = f"ndbc_buoy.{name}"
        if full not in sys.modules:
            spec = importlib.util.spec_from_file_location(full, PKG_DIR / f"{name}.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[full] = module
            spec.loader.exec_module(module)

    return sys.modules["ndbc_buoy.ndbc"]


@pytest.fixture(scope="session")
def ndbc() -> types.ModuleType:
    return _load_ndbc()


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"
