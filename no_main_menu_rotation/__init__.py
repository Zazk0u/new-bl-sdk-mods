if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from typing import Any, List

from mods_base import build_mod, hook, HookType

from unrealsdk import find_object
from unrealsdk.hooks import Type
from unrealsdk.unreal import UObject, WrappedStruct, BoundFunction, WeakPointer

_interp_menu_cache: WeakPointer = WeakPointer()

def _set_input_time(time: float):
    global _interp_menu_cache
    try:
        if not _interp_menu_cache():
            _interp_menu_cache = WeakPointer(find_object("WillowSeqAct_InterpMenu", "menumap.TheWorld:PersistentLevel.Main_Sequence.WillowSeqAct_InterpMenu_0"))
        _interp_menu_cache().InputTime = time
    except ValueError:
        pass

def _disable_main_menu_rotation():
    _set_input_time(999999)

def _enable_main_menu_rotation():
    _set_input_time(0)

@hook("WillowGame.FrontendGFxMovie:OnTick", Type.PRE)
def disable_rotation_on_tick(this:UObject, args:WrappedStruct, ret:Any, func:BoundFunction) -> None:
    _disable_main_menu_rotation()
 
def enable():
    _disable_main_menu_rotation()

def disable():
    _enable_main_menu_rotation()

build_mod(on_enable=enable, on_disable=disable, hooks=[disable_rotation_on_tick])
