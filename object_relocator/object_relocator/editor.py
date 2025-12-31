from __future__ import annotations  # Ensures type hints are ignored at runtime
from typing import TYPE_CHECKING, Any

from unrealsdk import make_struct
from unrealsdk.unreal import WeakPointer, BoundFunction

from mods_base import get_pc, hook, SliderOption
from mods_base.hook import Type

from object_relocator.options import editor_fly_speed
from object_relocator.keybinds import editor

if TYPE_CHECKING:
    from bl2 import WillowPlayerController
    from bl2 import WillowPlayerPawn

_current_player_pawn: WeakPointer[WillowPlayerPawn] = WeakPointer()
_editor_is_active: bool = False

@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST) 
def _deactive_editor_on_map_change(this: WillowPlayerController, args: WillowPlayerController.WillowClientDisableLoadingMovie.args, ret: Any, func: BoundFunction) -> None:
    if is_editor_active():
        _set_current_player_pawn(None)
        _set_editor_is_active(False)

def toggle_editor():
    if not is_editor_active():
        _activate_editor()
    else:
        _deativate_editor()

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

def _set_current_player_pawn(pp: WillowPlayerPawn):
    global _current_player_pawn
    _current_player_pawn = WeakPointer(pp)

def _set_editor_is_active(value: bool):
    global _editor_is_active
    _editor_is_active = value

def is_editor_active() -> bool:
    return _editor_is_active

def get_pawn_reference() -> WillowPlayerPawn:
    return _current_player_pawn()

def _set_keybinds_callbacks():
    editor.callback = toggle_editor

def fly_speed_changed(slider: SliderOption, new_value: float):
    pc: WillowPlayerController = get_pc()
    pc.SpectatorCameraSpeed = new_value

def _set_editor_options_callbacks():
    editor_fly_speed.on_change = fly_speed_changed
...
def on_enabled():
    _deactive_editor_on_map_change.enable()
    _set_keybinds_callbacks()
    _set_editor_options_callbacks()

def on_disabled():
    _deactive_editor_on_map_change.disable()
    if is_editor_active():
        _deativate_editor()