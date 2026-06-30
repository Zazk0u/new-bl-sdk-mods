from __future__ import annotations  # Ensures type hints are ignored at runtime
from typing import TYPE_CHECKING, Any, cast, List, Callable, Dict

from mods_base import hook, get_pc, ENGINE, HookType
from mods_base.options import BaseOption, SliderOption, BoolOption, SpinnerOption
from mods_base.keybinds import KeybindType, EInputEvent
from mods_base.command import command, ArgParseCommand

from unrealsdk import find_class, find_enum, find_all, make_struct, find_object
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, IGNORE_STRUCT

from .inputs import is_shift_enabled, is_alt_enabled
from .editor import is_editor_active, get_pawn_reference
from .pickup import (
    PickupManager, 
    WillowInteractiveObjectPickupManager, 
    InterpActorPickupManager, 
    StaticMeshActorPickupManager, 
    ActorMeshCollectionPickupManager, 
    WillowPickupPickupManager, 
    SkeletalMeshActorPickupManager, 
    ForcePickupPrimitiveComponentPickupManager
)

import uemath
import argparse

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

_all_standard_pickup_managers: List[PickupManager] = [
    WillowInteractiveObjectPickupManager(),
    ActorMeshCollectionPickupManager(),
    InterpActorPickupManager(),
    StaticMeshActorPickupManager(),
    WillowPickupPickupManager(),
    SkeletalMeshActorPickupManager()
]

_force_pickup_primitive_component_manager: ForcePickupPrimitiveComponentPickupManager = ForcePickupPrimitiveComponentPickupManager()

_current_pickup_manager: PickupManager = _force_pickup_primitive_component_manager

def notify_enter_editor():
    _force_pickup_primitive_component_manager.on_enter_editor()
    for manager in _all_standard_pickup_managers:
        manager.on_enter_editor()


def notify_exit_editor():
    _force_pickup_primitive_component_manager.on_exit_editor()
    for manager in _all_standard_pickup_managers:
        manager.on_exit_editor()
    _reset()


def _do_pickup_object():
    if not is_editor_active():
        return
    
    if not _current_pickup_manager.has_pickup():
        sucess = _try_to_pickup_object()
        if sucess:
            _update_current_pickup_manager.enable()
    else:
        _current_pickup_manager.write_infos_to_file()
        _current_pickup_manager.drop()
        _update_current_pickup_manager.disable()


def _try_to_pickup_object() -> bool:
    sucess = False
    weapon, destroy_spawned_weapon = _get_weapon()
    if not weapon:
        return sucess
    
    for manager in _all_standard_pickup_managers:
        manager.on_pre_trace()

    pc: WillowPlayerController = get_pc()
    start_trace = pc.CalcViewLocation
    player_forward = uemath.Rotator(pc.Rotation).get_axes()[0]
    end_trace = (uemath.Vector(start_trace) + (player_forward * pickup_max_range.value)).to_ue_vector()
    impact_info = weapon.CalcWeaponFire(start_trace, end_trace, [], IGNORE_STRUCT, True)[1][0]
    
    for manager in _all_standard_pickup_managers:
        manager.on_post_trace()
    
    if _evaluate_pickup_manager(impact_info):
        _current_pickup_manager.distance_from_camera = uemath.Vector(pc.CalcViewLocation).distance(uemath.Vector(impact_info.HitLocation))
        _current_pickup_manager.pickup(impact_info)
        sucess = True

    if debug_mode.value is True:
        _current_pickup_manager.collision_debug(start_trace, impact_info)

    if destroy_spawned_weapon:
        weapon.Destroy()
    
    return sucess


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
    for manager in _all_standard_pickup_managers:
        if manager.can_pickup(impact_info):
            _current_pickup_manager = manager
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


def _force_pickup_primitive_component(component: PrimitiveComponent):
    global _current_pickup_manager
    if not is_editor_active():
        print("Must be in the editor!")
        return

    if _current_pickup_manager.has_pickup():
        _current_pickup_manager.drop()
    
    if component.Owner:
        _current_pickup_manager = _force_pickup_primitive_component_manager
        smc_location = uemath.Vector(make_struct("Vector", X=component.CachedParentToWorld.WPlane.X, Y=component.CachedParentToWorld.WPlane.Y, Z=component.CachedParentToWorld.WPlane.Z))
        _current_pickup_manager.distance_from_camera = uemath.Vector(cast("WillowPlayerController", get_pc()).CalcViewLocation).distance(smc_location)
        _current_pickup_manager.force_pickup(component)
        _update_current_pickup_manager.enable()


def _for_all_primitive_component_in_radius(primitive_class: str, radius: float, callback: Callable[[PrimitiveComponent, float], None], condition: Callable[[PrimitiveComponent], bool] = None):
    pc: WillowPlayerController = get_pc()
    player_location = uemath.Vector(pc.Location if not pc.Pawn else pc.Pawn.Location)

    for primitive in cast("List[StaticMeshComponent]", find_all(primitive_class, False)):
        if not (is_live_object := primitive.Owner):
            continue

        primitive_location = uemath.Vector(make_struct("Vector", X=primitive.CachedParentToWorld.WPlane.X, Y=primitive.CachedParentToWorld.WPlane.Y, Z=primitive.CachedParentToWorld.WPlane.Z))
        distance = primitive_location.distance(player_location)
        if distance <= radius and (not condition or condition(primitive)):
            callback(primitive, distance)


def _get_closest_primitive_component(primitive_class: str, condition: Callable[[PrimitiveComponent], bool] = None) -> PrimitiveComponent:
    closest_distance: float = 0
    found_comp: StaticMeshComponent = None
    def find_closest_primitive(primitive: PrimitiveComponent, distance: float):
        nonlocal found_comp, closest_distance
        if not found_comp:
            found_comp = primitive
            closest_distance = distance
        elif distance < closest_distance:
            found_comp = primitive
            closest_distance = distance

    _for_all_primitive_component_in_radius(primitive_class, 999999999999999999, find_closest_primitive, condition)
    return found_comp


@hook("WillowGame.WillowPlayerController:PlayerTick", Type.POST)
def _update_current_pickup_manager(this: WillowPlayerController, args: WillowPlayerController.PlayerTick.args, ret: Any, func: BoundFunction) -> None:
    if _current_pickup_manager.has_pickup():
        _current_pickup_manager.update()


@hook("WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie", Type.POST) 
def _reset_on_loading_game_session(obj:WillowPlayerController, _args:WillowPlayerController.WillowClientDisableLoadingMovie.args, _ret:Any, _func:BoundFunction) -> None:
    _reset()


@hook("Engine.GameInfo:PostCommitMapChange", Type.PRE)
def notify_all_pickup_managers_of_map_change(this:GameInfo, args:GameInfo.PostCommitMapChange.args, ret:Any, func:BoundFunction) -> None:
    for pickup_manager in _all_standard_pickup_managers:
        pickup_manager.on_map_change(this.WorldInfo.GetMapName(True))


@command(description="Print all the live StaticMeshComponents in radius.")
def get_mesh_components_in_radius(args:argparse.Namespace) -> None:
    all_distance_by_mesh_component: Dict[StaticMeshComponent, float] = {}
    def callback(comp: StaticMeshComponent, distance: float):
        nonlocal all_distance_by_mesh_component
        all_distance_by_mesh_component[comp] = distance
    _for_all_primitive_component_in_radius("StaticMeshComponent", float(args.Radius), callback, lambda x: x and cast("StaticMeshComponent", x).StaticMesh)
    for key in sorted(all_distance_by_mesh_component, key=all_distance_by_mesh_component.get):
        distance = "{:.6f}".format(all_distance_by_mesh_component[key])
        print(f"{distance}  {key}   {cast("StaticMeshComponent", key).StaticMesh}")


@command(description="Print all the live ParticleSystemComponent in radius.")
def get_particle_components_in_radius(args:argparse.Namespace) -> None:
    all_distance_by_particle_component: Dict[ParticleSystemComponent, float] = {}
    def callback(comp: ParticleSystemComponent, distance: float):
        nonlocal all_distance_by_particle_component
        all_distance_by_particle_component[comp] = distance
    _for_all_primitive_component_in_radius("ParticleSystemComponent", float(args.Radius), callback, lambda x: x and cast("ParticleSystemComponent", x).Template)
    for key in sorted(all_distance_by_particle_component, key=all_distance_by_particle_component.get):
        distance = "{:.6f}".format(all_distance_by_particle_component[key])
        print(f"{distance} {key}    {cast("ParticleSystemComponent", key).Template}")


# force_pickup StaticMeshComponent'SouthpawFactory_P.TheWorld:PersistentLevel.StaticMeshCollectionActor_91.StaticMeshActor_SMC_500'
# force_pickup ParticleSystemComponent'SouthpawFactory_P.TheWorld:PersistentLevel.Emitter_60.ParticleSystemComponent_139'
@command(description="Force a StaticMeshComponent/ParticleSystemComponent to be pickup, mostly usefull if the trace can't affect it.")
def force_pickup(args:argparse.Namespace) -> None:
    primitive_name: str = args.PrimitiveComponentName
    if primitive_name.startswith("ParticleSystemComponent"):
        primitive_name = primitive_name.replace("ParticleSystemComponent", "")
    elif primitive_name.startswith("StaticMeshComponent"):
        primitive_name = primitive_name.replace("StaticMeshComponent", "")
    
    try:
        primitive: PrimitiveComponent = find_object("PrimitiveComponent", primitive_name)
    except:
        return
    
    if primitive and (primitive.Class._inherits(find_class("StaticMeshComponent")) or primitive.Class._inherits(find_class("ParticleSystemComponent"))):
        _force_pickup_primitive_component(primitive)


@command(description="Write the closest StaticMeshComponents in the console input.")
def get_closest_mesh_component(args:argparse.Namespace) -> None:
    found_comp: StaticMeshComponent = _get_closest_primitive_component("StaticMeshComponent", lambda x: x and cast("StaticMeshComponent", x).StaticMesh)
    if found_comp:
        print(found_comp.StaticMesh)
        cast("WillowConsole", ENGINE.GetEngine().GameViewport.ViewportConsole).SetInputText(found_comp._path_name())


@command(description="Write the closest StaticMeshComponents in the console input.")
def get_closest_particle_component(args:argparse.Namespace) -> None:
    found_comp: ParticleSystemComponent = _get_closest_primitive_component("ParticleSystemComponent", lambda x: x and cast("ParticleSystemComponent", x).Template)
    if found_comp:
        print(found_comp.Template)
        cast("WillowConsole", ENGINE.GetEngine().GameViewport.ViewportConsole).SetInputText(found_comp._path_name())


@command(description="Print all the PopulationOpportunity in radius.")
def get_opportunity_points_in_radius(args:argparse.Namespace) -> None:
    pc: WillowPlayerController = get_pc()
    if not pc:
        return
    
    opportunity_points_by_distance: Dict[float, PopulationOpportunity] = {}
    player_location = uemath.Vector(pc.Location if not pc.Pawn else pc.Pawn.location)
    radius: float = float(args.Radius)

    for opportunity_point in find_all("PopulationOpportunity", False):
        opportunity_point: PopulationOpportunity = opportunity_point
        distance = uemath.Vector(opportunity_point.Location).distance(player_location)
        if distance <= radius:
            opportunity_points_by_distance[distance] = opportunity_point
    
    sorted_list = sorted(opportunity_points_by_distance.items())
    for key, value in sorted_list:
        distance = "{:.6f}".format(key)
        if value.Class._inherits(find_class("PopulationOpportunityArea")):
            all_population_definitions: List[PopulationOpportunityArea.PopulationOptionAreaData] = []
            for spawn_option in cast("PopulationOpportunityArea", value).SpawnOptions:
                for pop_def in spawn_option.PopulationDefinitions:
                    if pop_def.PopulationDef:
                        all_population_definitions.append(pop_def.PopulationDef)

            value = f"{value}   {all_population_definitions}"

        elif value.Class._inherits(find_class("PopulationOpportunityCloner")):
            value = f"{value}   {cast("PopulationOpportunityCloner", value).SpawnFactory}"

        elif value.Class._inherits(find_class("PopulationOpportunityCombat")):
            value = f"{value}   {cast("PopulationOpportunityCombat", value).PopulationDef}"

        elif value.Class._inherits(find_class("PopulationOpportunityPoint")):
            value = f"{value}   {cast("PopulationOpportunityPoint", value).PopulationDef}"

        elif value.Class._inherits(find_class("PopulationOpportunityDen")):
            value = f"{value}   {cast("PopulationOpportunityDen", value).PopulationDef}"

        elif value.Class._inherits(find_class("PopulationOpportunityDen")):
            value = f"{value}   {cast("PopulationOpportunityDen", value).PopulationDef}"
        
        print(f"{distance} {value}")


get_mesh_components_in_radius.add_argument("Radius")
get_particle_components_in_radius.add_argument("Radius")
force_pickup.add_argument("PrimitiveComponentName")
get_opportunity_points_in_radius.add_argument("Radius")


...
debug_mode = BoolOption("Debug mode", True, description="Print debug messages and draw when attempting to pickup an object for better visualization.")
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

## TODO: Add keybinds to scale the pickup.
all_keybinds: List[KeybindType]  = [
    pickup_object,
    rotate_object_increase,
    rotate_object_decrease,
    move_object_toward,
    move_object_away,
]


all_commands: List[ArgParseCommand]  = [
    get_mesh_components_in_radius,
    get_particle_components_in_radius,
    get_closest_mesh_component,
    get_closest_particle_component,
    get_opportunity_points_in_radius,
    force_pickup,
]


all_hooks: List[HookType]  = [
    notify_all_pickup_managers_of_map_change,
]


def on_enabled():
    _reset_on_loading_game_session.enable()


def on_disabled():
    _reset_on_loading_game_session.disable()
    _reset()