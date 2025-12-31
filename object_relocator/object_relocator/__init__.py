if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

import os
import argparse
import importlib
import object_relocator.relocator as relocator
import object_relocator.editor as editor

from mods_base import build_mod, command

from object_relocator.options import options
from object_relocator.keybinds import keybinds

@command(description="Reload the modules that can be reloaded.")
def reload_object_relocator_modules(_:argparse.Namespace):
    _dir = os.path.dirname(__file__)
    for file in os.listdir(_dir):
        if not os.path.isfile(os.path.join(_dir, file)):
            continue

        # Specific files to ignores.
        if file in ["__init__.py", "options.py", "keybinds.py"]:
            continue

        name, suffix = os.path.splitext(file)
        # It's not a python file.
        if suffix != ".py":
            continue
        
        module = importlib.import_module("." + name, __name__)

        if hasattr(module, "on_disabled"):
            module.on_disabled()

        importlib.reload(module)

        if hasattr(module, "on_enabled"):
            module.on_enabled()

def enable():
    relocator.on_enabled()
    editor.on_enabled()

def disable():
    relocator.on_disabled()
    editor.on_disabled()

build_mod(on_enable=enable, on_disable=disable, options=options, keybinds=keybinds)