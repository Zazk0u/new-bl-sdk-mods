from __future__ import annotations  # Ensures type hints are ignored at runtime
from typing import TYPE_CHECKING, Any, cast
from mods_base import hook, get_pc

from unrealsdk import find_class, find_enum
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction
from unrealsdk.unreal import WeakPointer, IGNORE_STRUCT

from object_relocator.options import pickup_max_range, debug_mode, rotation_multiplier, mouse_rotation, alt_rotation, shift_rotation
from object_relocator.keybinds import pickup_object, rotate_object_decrease, rotate_object_increase, move_object_away, move_object_toward, is_shift_enabled, is_alt_enabled
from object_relocator.write import write_object_infos_to_file
from object_relocator.editor import is_editor_active, get_pawn_reference

import uemath

if TYPE_CHECKING:
    from common import *

DegreeToURot: float = 182.044449
EButtonState: WillowPlayerInput.EButtonState = find_enum("EButtonState")
MinObjectDistanceAllowedFromCamera: float = 200
MaxObjectDistanceAllowedFromCamera: float = 2000
MaxDistanceChangeMultiplier: float = 100
DistanceIncreasePerMouseWheelInput: float = 5
AdditionalTimeSecondsBeforeResetingDistanceChangeMultiplier: float = 0.5

_current_object: WeakPointer[WillowInteractiveObject] = WeakPointer()
_current_opportunity_point: WeakPointer[PopulationOpportunity] = WeakPointer()
_hit_location_offset: uemath.Vector = uemath.Vector()
_object_distance_from_camera: float = 0
_last_distance_change_time: float = 0
_distance_change_multiplier: float = 1

@hook("WillowGame.WillowPlayerController:PlayerTick", Type.POST)
def _place_object_in_front_of_camera_each_tick(this: WillowPlayerController, args: WillowPlayerController.PlayerTick.args, ret: Any, func: BoundFunction) -> None:
    if not (obj := _current_object()):
        return
    
    # Importing remove_object in the editor module gave me circular cyclic issues, fuck my life.
    # I'm putting it in the tick hook because i don't care to solve that issues right now.
    if not is_editor_active():
        remove_object()
        return

    player_forward = uemath.Rotator(this.Rotation).get_axes()[0]    
    new_location = (uemath.Vector(this.CalcViewLocation) + (player_forward * _object_distance_from_camera) + _hit_location_offset).to_ue_vector()
    obj.Location = new_location
    obj.ForceUpdateComponents(False, False)

    if (opportunity_point := _current_opportunity_point()):
        opportunity_point.Location = new_location

def do_pickup_object():
    if not is_editor_active():
        return
    
    if not _current_object():
        _try_to_pickup_object()
    else:
        remove_object()

def _try_to_pickup_object():
    weapon, destroy_spawned_weapon = _get_weapon()
    if not weapon:
        return
    
    pc: WillowPlayerController = get_pc()
    start_trace = pc.CalcViewLocation
    player_forward = uemath.Rotator(pc.Rotation).get_axes()[0]
    end_trace = (uemath.Vector(start_trace) + (player_forward * pickup_max_range.value)).to_ue_vector()
    impact_info = weapon.CalcWeaponFire(start_trace, end_trace, [], IGNORE_STRUCT, True)[1][0]
    
    if debug_mode.value is True:
        _trace_debug(pc, start_trace, impact_info)

    if (obj := cast("WillowInteractiveObject", impact_info.HitActor)) and obj.Class._inherits(find_class("WillowInteractiveObject")):
        _set_current_object(obj)
        _set_hit_location_offset(obj, impact_info.HitLocation)
        _set_object_distance_from_camera(pc, impact_info.HitLocation)
        _set_current_opportunity_point(_get_opportunity_point(obj))

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

def _trace_debug(pc: WillowPlayerController, start_trace: Actor.Vector, impact_info: Actor.ImpactInfo):
    print(f"Hit Actor: {impact_info.HitActor}")
    print(f"Hit Location: {impact_info.HitLocation}")
    print(f"Hit Normal: {impact_info.HitNormal}")
    print(f"Hit Info: {impact_info.HitInfo}")
    pc.DrawDebugLine(start_trace, impact_info.HitLocation, 255, 0, 0, True, 2)
    pc.DrawDebugLine(start_trace, impact_info.HitLocation, 0, 255, 0, True, 2)
    pc.DrawDebugSphere(impact_info.HitLocation, 50, 32, 255, 0, 255, True, 2)

def _set_current_object(obj: WillowInteractiveObject):
    global _current_object
    _current_object = WeakPointer(obj)

def _set_hit_location_offset(obj: WillowInteractiveObject, hit_location: Actor.Vector):
    global _hit_location_offset
    _hit_location_offset = uemath.Vector(obj.Location) - uemath.Vector(hit_location)

def _set_object_distance_from_camera(pc: WillowPlayerController, hit_location: Actor.Vector):
    global _object_distance_from_camera
    _object_distance_from_camera = uemath.Vector(pc.CalcViewLocation).distance(uemath.Vector(hit_location))

def _get_opportunity_point(obj: WillowInteractiveObject) -> PopulationOpportunity:
    gearbox_globals: GearboxGlobals = find_class("GearboxGlobals").ClassDefaultObject
    population_master = gearbox_globals.GetGearboxGlobals().GetPopulationMaster()
    return population_master.GetActorsOpportunity(obj)

def _set_current_opportunity_point(opportunity_point: PopulationOpportunity):
    global _current_opportunity_point
    _current_opportunity_point = WeakPointer(opportunity_point)

def remove_object():
    obj = _current_object()
    opportunity_point = _current_opportunity_point()
    _set_current_object(None)
    _set_current_opportunity_point(None)
    write_object_infos_to_file(obj, opportunity_point)

def rotate_object(direction: int):
    if not (obj := _current_object()):
        return
    
    rotation_increase = int(direction * DegreeToURot * (rotation_multiplier.value * 0.01))
    if is_shift_enabled():
        _rotate_axis(obj, rotation_increase, shift_rotation.value)
    elif is_alt_enabled():
        _rotate_axis(obj, rotation_increase, alt_rotation.value)
    else:
        _rotate_axis(obj, rotation_increase, mouse_rotation.value)

def _rotate_axis(obj: WillowInteractiveObject, rotation_increase: int, rotation_axis: str):
    match rotation_axis:
        case "Pitch":
            obj.Rotation.Pitch += rotation_increase
        case "Yaw":
            obj.Rotation.Yaw += rotation_increase
        case "Roll":
            obj.Rotation.Roll += rotation_increase

def change_object_distance_from_camera(direction: int):
    global _object_distance_from_camera, _last_distance_change_time, _distance_change_multiplier
    if not _current_object():
        return
    
    world_info = cast("WillowPlayerController", get_pc()).WorldInfo
    current_time = world_info.TimeSeconds
    next_time = _last_distance_change_time + AdditionalTimeSecondsBeforeResetingDistanceChangeMultiplier
    _last_distance_change_time = current_time

    if next_time >= current_time:
        _distance_change_multiplier += DistanceIncreasePerMouseWheelInput
        if _distance_change_multiplier > MaxDistanceChangeMultiplier:
            _distance_change_multiplier = MaxDistanceChangeMultiplier
    else:
        _distance_change_multiplier = 1
    
    _object_distance_from_camera += direction * _distance_change_multiplier
    _clamp_object_distance_from_camera()

def _clamp_object_distance_from_camera():
    global _object_distance_from_camera
    if _object_distance_from_camera < MinObjectDistanceAllowedFromCamera:
        _object_distance_from_camera = MinObjectDistanceAllowedFromCamera
    elif _object_distance_from_camera > MaxObjectDistanceAllowedFromCamera:
        _object_distance_from_camera = MaxObjectDistanceAllowedFromCamera

def _set_keybinds_callbacks():
    pickup_object.callback = do_pickup_object
    rotate_object_increase.callback = lambda: rotate_object(1)
    rotate_object_decrease.callback = lambda: rotate_object(-1)
    move_object_toward.callback = lambda: change_object_distance_from_camera(-1)
    move_object_away.callback = lambda: change_object_distance_from_camera(1)

...
def on_enabled():
    _place_object_in_front_of_camera_each_tick.enable()
    _set_keybinds_callbacks()

def on_disabled():
    _place_object_in_front_of_camera_each_tick.disable()
    if _current_object():
        remove_object()