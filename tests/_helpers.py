from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def install_anki_stubs() -> None:
    if "aqt" in sys.modules:
        return

    aqt = types.ModuleType("aqt")
    aqt.mw = types.SimpleNamespace(col=None, pm=None)
    sys.modules["aqt"] = aqt

    utils = types.ModuleType("aqt.utils")

    def showWarning(_msg):
        return None

    utils.showWarning = showWarning
    sys.modules["aqt.utils"] = utils

    importing = types.ModuleType("aqt.importing")

    def importFile(_mw, _path):
        return None

    importing.importFile = importFile
    sys.modules["aqt.importing"] = importing

    import_export = types.ModuleType("aqt.import_export")
    import_export_importing = types.ModuleType("aqt.import_export.importing")

    def import_file(_mw, _path):
        return None

    import_export_importing.import_file = import_file
    sys.modules["aqt.import_export"] = import_export
    sys.modules["aqt.import_export.importing"] = import_export_importing

    anki = types.ModuleType("anki")
    hooks = types.ModuleType("anki.hooks")

    def wrap(func, wrapper, pos="after"):
        def inner(*args, **kwargs):
            if pos == "before":
                wrapper(*args, **kwargs)
                return func(*args, **kwargs)
            result = func(*args, **kwargs)
            wrapper(*args, **kwargs)
            return result

        return inner

    hooks.wrap = wrap
    sys.modules["anki"] = anki
    sys.modules["anki.hooks"] = hooks


def load_addon_module(module_name: str):
    addon_dir = Path(__file__).resolve().parents[1] / "addon"
    if "addon" not in sys.modules:
        pkg = types.ModuleType("addon")
        pkg.__path__ = [str(addon_dir)]
        sys.modules["addon"] = pkg

    module_path = addon_dir / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"addon.{module_name}", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load addon module {module_name}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[f"addon.{module_name}"] = module
    spec.loader.exec_module(module)
    return module
