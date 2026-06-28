from __future__ import annotations  # Ensures type hints are ignored at runtime
from typing import TYPE_CHECKING, List, Any

from unrealsdk import make_struct, find_enum, find_class
from unrealsdk.unreal import WeakPointer, UClass, BoundFunction

from mods_base import get_pc, hook
from mods_base.hook import Type
from mods_base.options import BaseOption, SliderOption
from mods_base.keybinds import KeybindType, EInputEvent

if TYPE_CHECKING:
    from common import *

PRIMITIVE_COMPONENT_CLASS: UClass = find_class("PrimitiveComponent")
ECollisionType: Actor.ECollisionType = find_enum("ECollisionType")

_current_player_pawn: WeakPointer[WillowPlayerPawn] = WeakPointer()
_editor_is_active: bool = False


def toggle_editor():
    if not is_editor_active():
        _activate_editor()
    else:
        _deativate_editor()


def is_editor_active() -> bool:
    return _editor_is_active


def get_pawn_reference() -> WillowPlayerPawn:
    return _current_player_pawn()


def _set_current_player_pawn(pp: WillowPlayerPawn):
    global _current_player_pawn
    _current_player_pawn = WeakPointer(pp)


def _set_editor_is_active(value: bool):
    global _editor_is_active
    _editor_is_active = value


def _activate_editor():
    pc: WillowPlayerController = get_pc()
    pawn: WillowPlayerPawn = pc.Pawn

    pc.ServerSpectate()
    pc.bCollideWorld = False
    pc.SpectatorCameraSpeed = editor_fly_speed.value

    pawn.Behavior_ChangeVisibility(False)
    pawn.bCanTarget = False
    _set_current_player_pawn(pawn)
    _set_editor_is_active(True)



def _deativate_editor():
    pawn = _current_player_pawn()
    if not pawn:
        return
    
    pc: WillowPlayerController = get_pc()
    pawn.Location = make_struct("Vector", X=pc.Location.X, Y=pc.Location.Y, Z=pc.Location.Z)
    pawn.Behavior_ChangeVisibility(True)
    pawn.bCanTarget = True

    pc.Possess(pawn, True)
    _set_current_player_pawn(None)
    _set_editor_is_active(False)


def _fly_speed_changed(slider: SliderOption, new_value: float):
    pc: WillowPlayerController = get_pc()
    pc.SpectatorCameraSpeed = new_value


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.PRE) 
def _reset_on_loading_game_session(obj:WillowPlayerController, _args:WillowPlayerController._WillowClientDisableLoadingMovie.args, _ret:Any, _func:BoundFunction) -> None:
    _set_current_player_pawn(None)
    _set_editor_is_active(False)

...
editor_fly_speed = SliderOption("Editor fly speed", 2000, 1000, 10000, description="Speed at which you fly in editor mode.", on_change_anytime=_fly_speed_changed)


all_options: List[BaseOption]  = [
    editor_fly_speed,
]


editor = KeybindType("Toggle editor", "F3", event_filter=EInputEvent.IE_Pressed, callback=toggle_editor)


all_keybinds: List[KeybindType]  = [
    editor,
]


def on_enabled():
    _reset_on_loading_game_session.enable()


def on_disabled():
    _reset_on_loading_game_session.disable()
    if is_editor_active():
        _deativate_editor()