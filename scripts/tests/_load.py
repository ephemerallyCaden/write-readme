"""Load a hyphenated script from scripts/ as a module for testing."""
from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType

SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(SCRIPTS)

# The scripts import _mdlib, which sits next to them.
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def script_path(filename: str) -> str:
    return os.path.join(SCRIPTS, filename)


def load_script(filename: str) -> ModuleType:
    name = filename.removesuffix(".py").replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, script_path(filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses look the module up by name
    spec.loader.exec_module(module)
    return module
