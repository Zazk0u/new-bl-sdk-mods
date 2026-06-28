from __future__ import annotations  # Ensures type hints are ignored at runtime
from typing import TYPE_CHECKING, Any, cast, List
from mods_base import hook, get_pc
from mods_base.options import BaseOption, SliderOption, BoolOption, SpinnerOption
from mods_base.keybinds import KeybindType, EInputEvent

from unrealsdk import find_class, find_enum
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction
from unrealsdk.unreal import IGNORE_STRUCT

from .inputs import is_shift_enabled, is_alt_enabled
from .editor import is_editor_active, get_pawn_reference
from .pickup import PickupManager, WillowInteractiveObjectPickupManager, InterpActorPickupManager, ActorMeshCollectionPickupManager

import uemath

if TYPE_CHECKING:
    from common import *


DegreeToURot: float = 182.044449
EButtonState: WillowPlayerInput.EButtonState = find_enum("EButtonState")
MinObjectDistanceAllowedFromCamera: float = 200
MaxObjectDistanceAllowedFromCamera: float = 3000
MaxDistanceIncreaseMultiplier: float = 100
DistanceIncreasePerMouseWheelInput: float = 5
AdditionalTimeSecondsBeforeResetingDistanceIncreaseMultiplier: float = 0.5

_last_distance_change_from_camera_time: float = 0
_distance_from_camera_multiplier: float = 1

_wio_pickup_manager: PickupManager = WillowInteractiveObjectPickupManager()
_mesh_collection_pickup_manager: PickupManager = ActorMeshCollectionPickupManager()
_interp_actor_collection_pickup_manager: PickupManager = InterpActorPickupManager()
_current_pickup_manager: PickupManager = _wio_pickup_manager


def _do_pickup_object():
    if not is_editor_active():
        return
    
    if not _current_pickup_manager.has_pickup():
        _try_to_pickup_object()
        _update_current_pickup_manager.enable()
    else:
        _current_pickup_manager.write_infos_to_file()
        _current_pickup_manager.drop()
        _update_current_pickup_manager.disable()


def _try_to_pickup_object():
    weapon, destroy_spawned_weapon = _get_weapon()
    if not weapon:
        return
    
    _wio_pickup_manager.on_pre_trace()
    _mesh_collection_pickup_manager.on_pre_trace()
    _interp_actor_collection_pickup_manager.on_pre_trace()

    pc: WillowPlayerController = get_pc()
    start_trace = pc.CalcViewLocation
    player_forward = uemath.Rotator(pc.Rotation).get_axes()[0]
    end_trace = (uemath.Vector(start_trace) + (player_forward * pickup_max_range.value)).to_ue_vector()
    impact_info = weapon.CalcWeaponFire(start_trace, end_trace, [], IGNORE_STRUCT, True)[1][0]
    
    _wio_pickup_manager.on_post_trace()
    _mesh_collection_pickup_manager.on_post_trace()
    _interp_actor_collection_pickup_manager.on_post_trace()
    
    if _evaluate_pickup_manager(impact_info):
        _current_pickup_manager.distance_from_camera = uemath.Vector(pc.CalcViewLocation).distance(uemath.Vector(impact_info.HitLocation))
        _current_pickup_manager.pickup(impact_info)

    if debug_mode.value is True:
        _current_pickup_manager.collision_debug(start_trace, impact_info)

    if destroy_spawned_weapon:
        weapon.Destroy()


def _get_weapon() -> tuple[WillowWeapon, bool]:
    pawn = get_pawn_reference()
    weapon: WillowWeapon = None
    destroy_spawned_weapon: bool = False
    if not pawn:
        return [weapon, destroy_spawned_weapon]
    
    weapon = pawn.Weapon
    if not weapon:
        weapon = pawn.Spawn(find_class("WillowWeapon"))
        destroy_spawned_weapon = True
    return [weapon, destroy_spawned_weapon]


def _evaluate_pickup_manager(impact_info: Actor.ImpactInfo):
    global _current_pickup_manager
    if _wio_pickup_manager.can_pickup(impact_info):
        _current_pickup_manager = _wio_pickup_manager
        return True

    if _mesh_collection_pickup_manager.can_pickup(impact_info):
        _current_pickup_manager = _mesh_collection_pickup_manager
        return True
    
    if _interp_actor_collection_pickup_manager.can_pickup(impact_info):
        _current_pickup_manager = _interp_actor_collection_pickup_manager
        return True
    
    return False


def _reset():
    _update_current_pickup_manager.disable()
    if _current_pickup_manager.has_pickup():
        _current_pickup_manager.drop()


def _rotate_object(direction: int):
    if not _current_pickup_manager.has_pickup():
        return
    
    rotation_increase = int(direction * DegreeToURot * (rotation_multiplier.value * 0.01))
    if is_shift_enabled():
        _current_pickup_manager.rotate(rotation_increase, shift_rotation.value)
    elif is_alt_enabled():
        _current_pickup_manager.rotate(rotation_increase, alt_rotation.value)
    else:
        _current_pickup_manager.rotate(rotation_increase, mouse_rotation.value)


def _change_pickup_distance_from_camera(direction: int):
    global _last_distance_change_from_camera_time, _distance_from_camera_multiplier
    if not _current_pickup_manager.has_pickup():
        return
    
    world_info = cast("WillowPlayerController", get_pc()).WorldInfo
    current_time = world_info.TimeSeconds
    next_time = _last_distance_change_from_camera_time + AdditionalTimeSecondsBeforeResetingDistanceIncreaseMultiplier
    _last_distance_change_from_camera_time = current_time

    # Check if the mouse wheel was pressed within a small laps of time.
    # If so, increase the distance multiplier which will make the object move toward/away from you faster.
    # There prolly is a smoother way to to it with tick hook when i have some time.
    if next_time >= current_time:
        _distance_from_camera_multiplier += DistanceIncreasePerMouseWheelInput
        if _distance_from_camera_multiplier > MaxDistanceIncreaseMultiplier:
            _distance_from_camera_multiplier = MaxDistanceIncreaseMultiplier
    else:
        _distance_from_camera_multiplier = 1
    
    _current_pickup_manager.distance_from_camera += direction * _distance_from_camera_multiplier
    _current_pickup_manager.distance_from_camera = min(max(_current_pickup_manager.distance_from_camera, MinObjectDistanceAllowedFromCamera), MaxObjectDistanceAllowedFromCamera)


@hook("WillowGame.WillowPlayerController:PlayerTick", Type.POST)
def _update_current_pickup_manager(this: WillowPlayerController, args: WillowPlayerController.PlayerTick.args, ret: Any, func: BoundFunction) -> None:
    if _current_pickup_manager.has_pickup():
        _current_pickup_manager.update()


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST) 
def _reset_on_loading_game_session(obj:WillowPlayerController, _args:WillowPlayerController.WillowClientDisableLoadingMovie.args, _ret:Any, _func:BoundFunction) -> None:
    _reset()


...
debug_mode = BoolOption("Debug mode", False, description="Print debug messages and draw when attempting to pickup an object for better visualization.")
pickup_max_range = SliderOption("Max pickup range", MaxObjectDistanceAllowedFromCamera, MinObjectDistanceAllowedFromCamera, MaxObjectDistanceAllowedFromCamera, description="The range at which you can pickup the object.")
mouse_rotation = SpinnerOption("Mouse rotation axis", "Roll", ["Pitch", "Yaw", "Roll"], description="Which of the object rotation axis is affected by holding the input.")
alt_rotation = SpinnerOption("Left Alt rotation axis", "Yaw", ["Pitch", "Yaw", "Roll"], description="Which of the object rotation axis is affected by holding the input.")
shift_rotation = SpinnerOption("Left Shift rotation axis", "Pitch", ["Pitch", "Yaw", "Roll"], description="Which of the object rotation axis is affected by holding the input.")
rotation_multiplier = SliderOption("Rotation multiplier", 50, 1, 100, description="Multiplier when rotating the picked object, decrease for slower rotation.")


all_options: List[BaseOption]  = [
    debug_mode,
    pickup_max_range, 
    mouse_rotation,
    alt_rotation,
    shift_rotation,
    rotation_multiplier
]


pickup_object = KeybindType("Pickup/Release object in editor", "E", event_filter=EInputEvent.IE_Pressed, callback=_do_pickup_object)
rotate_object_increase = KeybindType("Rotation increase", "LeftMouseButton", event_filter=EInputEvent.IE_Repeat, is_hidden=True, callback=lambda: _rotate_object(1))
rotate_object_decrease = KeybindType("Rotation decrease", "RightMouseButton", event_filter=EInputEvent.IE_Repeat, is_hidden=True, callback=lambda: _rotate_object(-1))
move_object_toward = KeybindType("Move toward", "MouseScrollDown", is_hidden=True, callback=lambda: _change_pickup_distance_from_camera(-1))
move_object_away = KeybindType("Move away", "MouseScrollUp", is_hidden=True, callback=lambda: _change_pickup_distance_from_camera(1))


all_keybinds: List[KeybindType]  = [
    pickup_object,
    rotate_object_increase,
    rotate_object_decrease,
    move_object_toward,
    move_object_away,
]


def on_enabled():
    _reset_on_loading_game_session.enable()


def on_disabled():
    _reset_on_loading_game_session.disable()
    _reset()