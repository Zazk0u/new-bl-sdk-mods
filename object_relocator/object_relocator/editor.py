from __future__ import annotations  # Ensures type hints are ignored at runtime
from typing import TYPE_CHECKING, cast, List

from unrealsdk import make_struct, find_all, find_enum, find_class
from unrealsdk.unreal import WeakPointer, UClass

from mods_base import get_pc, SliderOption


from object_relocator.options import editor_fly_speed
from object_relocator.keybinds import editor

if TYPE_CHECKING:
    from common import *

ECollisionType: Actor.ECollisionType = find_enum("ECollisionType")
PRIMITIVE_COMPONENT: UClass = find_class("PrimitiveComponent")

_current_player_pawn: WeakPointer[WillowPlayerPawn] = WeakPointer()
_editor_is_active: bool = False

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
    _change_the_collision_of_all_live_objects_to_allow_trace()

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
    _reset_the_collision_of_all_live_objects()

def _change_the_collision_of_all_live_objects_to_allow_trace():
    for obj in cast("List[WillowInteractiveObject]", find_all("WillowInteractiveObject")):
        if not (is_live_object := obj.WorldInfo and obj.AllComponents):
            continue

        obj.SetCollisionType(ECollisionType.COLLIDE_BlockAll)
        obj.bBlockActors = True
        for component in obj.AllComponents:
            primitive_component: PrimitiveComponent = component
            if primitive_component.Class._inherits(PRIMITIVE_COMPONENT):
                primitive_component.BlockActors = True

def _reset_the_collision_of_all_live_objects():
    for obj in cast("List[WillowInteractiveObject]", find_all("WillowInteractiveObject")):
        if not (is_live_object := obj.WorldInfo and obj.AllComponents):
            continue

        for instance_data in obj.InstanceState.Data:
            collision_type = instance_data.ComponentData.CollisionType
            component: PrimitiveComponent = instance_data.ComponentData.Component
            if not component or not component.Class._inherits(PRIMITIVE_COMPONENT):
                continue

            if collision_type in [ECollisionType.COLLIDE_TouchAll, ECollisionType.COLLIDE_TouchAllButWeapons, ECollisionType.COLLIDE_TouchWeapons]:
                component.BlockActors = False
            else:
                component.BlockActors = True

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
    _set_keybinds_callbacks()
    _set_editor_options_callbacks()

def on_disabled():
    if is_editor_active():
        _deativate_editor()