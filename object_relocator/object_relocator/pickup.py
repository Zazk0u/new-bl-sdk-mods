from __future__ import annotations  # Ensures type hints are ignored at runtime
import uemath
import os
import sys

from io import TextIOWrapper

from pathlib import Path
from datetime import datetime
from unrealsdk.logging import warning

from typing import TYPE_CHECKING, cast, List

from mods_base import get_pc

from unrealsdk import find_class, make_struct, find_enum, find_all
from unrealsdk.unreal import WeakPointer, UClass

from abc import ABC, abstractmethod


if TYPE_CHECKING:
    from common import *


PARTICLE_SYSTEM_COMPONENT_CLASS: UClass = find_class("ParticleSystemComponent")
PRIMITIVE_COMPONENT_CLASS: UClass = find_class("PrimitiveComponent")
STATIC_MESH_COMPONENT_CLASS: UClass = find_class("StaticMeshComponent")

ECollisionType: Actor.ECollisionType = find_enum("ECollisionType")
FOLDER_PATH = os.path.relpath(Path(__file__).parent / "logs", Path(sys.executable).parent)


def get_vector_as_string(vector: Object.Vector) -> str:
    x = "{:.6f}".format(vector.X)
    y = "{:.6f}".format(vector.Y)
    z = "{:.6f}".format(vector.z)
    return f"(X = {x}, Y = {y}, Z = {z})"


def get_plane_as_string(plane: Object.Plane) -> str:
    w = "{:.6f}".format(plane.W)
    x = "{:.6f}".format(plane.X)
    y = "{:.6f}".format(plane.Y)
    z = "{:.6f}".format(plane.z)
    return f"(W = {w}, X = {x}, Y = {y}, Z = {z})"


def get_matrix_as_string(matrix: Object.Matrix) -> str:
    x_plane = get_plane_as_string(matrix.XPlane)
    y_plane = get_plane_as_string(matrix.YPlane)
    z_plane = get_plane_as_string(matrix.ZPlane)
    w_plane = get_plane_as_string(matrix.WPlane)
    return f"(XPlane = {x_plane}, YPlane = {y_plane}, ZPlane = {z_plane}, WPlane = {w_plane})"


def get_rotation_as_string(rotation: Object.Rotator) -> str:
    return str(rotation).replace(":", " =").replace("{", "(").replace("}", ")")


def change_the_collision_of_all_live_actor_to_allow_trace(actor_class: str, exact_class: bool = True):
    for actor in cast("List[Emitter]", find_all(actor_class, exact_class)):
        if not (is_live_object := actor.WorldInfo and actor.AllComponents):
            continue

        for component in actor.AllComponents:
            if component and component.Class._inherits(PRIMITIVE_COMPONENT_CLASS):
                component: PrimitiveComponent = component
                component.BlockActors = True
                component.CollideActors = True

        actor.SetCollisionType(ECollisionType.COLLIDE_BlockAll)
        actor.bBlockActors = True
        actor.bCollideActors = True
        actor.bCollideWorld = True
        actor.ForceUpdateComponents(True, False)


class PickupManager(ABC):
    distance_from_camera: float = 0
    _hit_location_offset: uemath.Vector = uemath.Vector()
    _debug_tick: int = 0

    def pickup(self, impact_info: Actor.ImpactInfo) -> None:
        self._pickup(impact_info)
        self._hit_location_offset = uemath.Vector(self._get_location()) - uemath.Vector(impact_info.HitLocation)


    def update(self) -> None:
        pc: WillowPlayerController = get_pc()
        player_forward = uemath.Rotator(pc.Rotation).get_axes()[0]
        forward_location = uemath.Vector(pc.CalcViewLocation) + (player_forward * self.distance_from_camera)
        new_location = (forward_location + self._hit_location_offset).to_ue_vector()
        self._set_location(new_location)
        self._debug_tick += 1
        if self._debug_tick > 60:
            self._debug_tick = 0
            self._update_debug()


    def collision_debug(self, start_trace: Object.Vector, impact_info: Actor.ImpactInfo) -> None:
        pc: WillowPlayerController = get_pc()
        pc.DrawDebugLine(start_trace, impact_info.HitLocation, 255, 0, 0, True, 2)
        pc.DrawDebugLine(start_trace, impact_info.HitLocation, 0, 255, 0, True, 2)
        pc.DrawDebugSphere(impact_info.HitLocation, 50, 32, 255, 0, 255, True, 2)
        print(f"Hit Actor: {impact_info.HitActor}")
        print(f"Hit Location: {impact_info.HitLocation}")
        print(f"Hit Normal: {impact_info.HitNormal}")
        print(f"Hit Info: {impact_info.HitInfo}")


    def on_pre_trace(self) -> None:
        pass


    def on_post_trace(self) -> None:
        pass


    def on_enter_editor(self) -> None:
        pass


    def on_exit_editor(self) -> None:
        pass


    def on_map_change(self, map_name: str) -> None:
        pass


    def write_infos_to_file(self):
        if not os.path.exists(FOLDER_PATH):
            warning("[Object Relocator]: To create and read logs, export the sdkmod's folder.")
            return
        
        date = str(datetime.now()).replace(":", "-").replace(" ", "_").split(".")[0]
        path = f"{FOLDER_PATH}\\log_{date}.txt"
        with open(path, "w") as file:
            self._write_infos_to_file(file)


    def _write_infos_to_file(self, file: TextIOWrapper) -> None:
        pass


    def _update_debug(self) -> None:
        print(f"Pickup Location: {self._get_location()}")


    @abstractmethod
    def has_pickup(self) -> bool:
        pass


    @abstractmethod
    def can_pickup(self, impact_info: Actor.ImpactInfo) -> bool:
        pass

    
    @abstractmethod
    def drop(self) -> None:
        pass


    @abstractmethod
    def rotate(self, direction: int, rotation_speed: float, axis: str = "Pitch") -> None:
        pass


    @abstractmethod
    def _pickup(self, impact_info: Actor.ImpactInfo) -> None:
        pass


    @abstractmethod
    def _set_location(self, new_location: Object.Vector) -> None:
        pass


    @abstractmethod
    def _get_location(self) -> Object.Vector:
        pass


class ActorPickupManager(PickupManager, ABC):
    current_pickup: WeakPointer[Actor] = WeakPointer()
    opportunity_point: WeakPointer[PopulationOpportunity] = WeakPointer()

    def has_pickup(self) -> bool:
        return self.current_pickup() is not None


    def can_pickup(self, impact_info: Actor.ImpactInfo) -> bool:
        return impact_info.HitActor is not None


    def rotate(self, rotation_increase: float, rotation_axis: str = "Pitch") -> None:
        match rotation_axis:
            case "Pitch":
                self.current_pickup().Rotation.Pitch += rotation_increase
            case "Yaw":
                self.current_pickup().Rotation.Yaw += rotation_increase
            case "Roll":
                self.current_pickup().Rotation.Roll += rotation_increase


    def collision_debug(self, start_trace: Object.Vector, impact_info: Actor.ImpactInfo) -> None:
        super().collision_debug(start_trace, impact_info)
        opportunity_point = self.opportunity_point()
        if opportunity_point:
            print(f"Opportunity Point: {opportunity_point}")


    def drop(self) -> None:
        self.current_pickup = WeakPointer()
    

    def _update_debug(self):
        super()._update_debug()
        print(f"Pickup Rotation: {self.current_pickup().Rotation}")


    def _pickup(self, impact_info: Actor.ImpactInfo) -> None:
        self.current_pickup = WeakPointer(impact_info.HitActor)
        self.opportunity_point = WeakPointer(self._find_opportunity_point())


    def _set_location(self, new_location: Object.Vector) -> None:
        pickup = self.current_pickup()
        pickup.Location = new_location

        if (opportunity_point := self.opportunity_point()):
            opportunity_point.Location = new_location
    
        for comp in pickup.AllComponents:
            if comp.Class._inherits(PARTICLE_SYSTEM_COMPONENT_CLASS):  
                comp: ParticleSystemComponent = comp
                comp.KillParticlesForced()
                comp.ActivateSystem()

        pickup.ForceUpdateComponents(True, False)


    def _get_location(self) -> Object.Vector:
        return self.current_pickup().Location   


    def _write_infos_to_file(self, file: TextIOWrapper):
        pickup = self.current_pickup()
        opportunity_point = self.opportunity_point()

        obj_location = get_vector_as_string(self._get_location())
        obj_rotation = get_rotation_as_string(pickup.Rotation)

        file.write(f"Object:\n")
        file.write(f"{pickup}\n")
        file.write(f"\n")

        if opportunity_point:
            file.write(f"Opportunity Point:\n")
            file.write(f"{opportunity_point}\n")
            file.write(f"\n")

        if hasattr(pickup, "InstanceState"):
            file.write(f"Instance datas:\n")
            for data in pickup.InstanceState.Data:
                file.write(f"{data}\n")
            file.write(f"\n")
        
        file.write(f"Commands:\n")
        # If there's no opportunity point, then the object was handplaced by the game designer (ie: the customization machine). 
        # The object name will always be the same in that case so you'll want to use the object commands instead.
        if opportunity_point:
            file.write(f"set {opportunity_point} Location {obj_location}\n")
            file.write(f"set {opportunity_point} Rotation {obj_rotation}\n")
        else:
            file.write(f"set {pickup} Location {obj_location}\n")
            file.write(f"set {pickup} Rotation {obj_rotation}\n")
        file.write(f"""\n""")


    def _find_opportunity_point(self) -> PopulationOpportunity:
        gearbox_globals: GearboxGlobals = find_class("GearboxGlobals").ClassDefaultObject
        population_master = gearbox_globals.GetGearboxGlobals().GetPopulationMaster()
        return population_master.GetActorsOpportunity(self.current_pickup())


class WillowInteractiveObjectPickupManager(ActorPickupManager):
    def on_pre_trace(self):
        change_the_collision_of_all_live_actor_to_allow_trace("WillowInteractiveObject", True)


    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("WillowInteractiveObject"))


    def collision_debug(self, start_trace: Object.Vector, impact_info: Actor.ImpactInfo) -> None:
        super().collision_debug(start_trace, impact_info)
        if self.current_pickup():
            print(f"InteractiveObjectDefinition: {cast("WillowInteractiveObject", self.current_pickup()).InteractiveObjectDefinition}")
        
    
    ## Normally its not possible to edit with an hotfixes because you need to call ForceUpdate, this fix that.
    def on_map_change(self, map_name):
        for actor in cast("List[WillowInteractiveObject]", find_all("WillowInteractiveObject", False)):
            if actor.Components and actor.WorldInfo:
                for comp in actor.AllComponents:
                    if comp.Class._inherits(PARTICLE_SYSTEM_COMPONENT_CLASS):  
                        comp: ParticleSystemComponent = comp
                        comp.KillParticlesForced()
                        comp.ActivateSystem()
                            
                actor.ForceUpdateComponents(True, False)


    def _write_infos_to_file(self, file: TextIOWrapper):
        file.write(f"InteractiveObjectDefinition:\n")
        file.write(f"{cast("WillowInteractiveObject", self.current_pickup()).InteractiveObjectDefinition}\n")
        file.write(f"\n")
        super()._write_infos_to_file(file)


class InterpActorPickupManager(ActorPickupManager):
    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("InterpActor"))


    def on_enter_editor(self):
        ## Some collision are tied to the mesh, some mesh have no collision.
        change_the_collision_of_all_live_actor_to_allow_trace("InterpActor", False)
    

    def update(self):
        super().update()
        pickup = self.current_pickup()
        print(pickup)
        print(pickup.Location)


    ## Normally its not possible to edit with an hotfixes because you need to call ForceUpdate, this fix that.
    def on_map_change(self, map_name):
        for actor in cast("List[InterpActor]", find_all("InterpActor", False)):
            if actor.Components and actor.WorldInfo:
                actor.ForceUpdateComponents(True, False)


    def _pickup(self, impact_info: Actor.ImpactInfo):
        super()._pickup(impact_info)
        pickup =  self.current_pickup()
        if pickup.Base and pickup.Base.Class._inherits(find_class("InterpActor")):
            self.current_pickup = WeakPointer(pickup.Base)
            if not self.opportunity_point():
                self.opportunity_point = WeakPointer(self._find_opportunity_point())


    def _write_infos_to_file(self, file: TextIOWrapper):
        try:
            file.write(f"Mesh:\n")
            file.write(f"{cast("InterpActor", self.current_pickup()).StaticMeshComponent.StaticMesh}\n")
            file.write(f"\n")
        except:
            pass
        super()._write_infos_to_file(file)


class StaticMeshActorPickupManager(ActorPickupManager):
    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("StaticMeshActor"))


    def on_enter_editor(self):
        change_the_collision_of_all_live_actor_to_allow_trace("StaticMeshActor", False)

    
    ## Normally its not possible to edit with an hotfixes because you need to call ForceUpdate, this fix that.
    def on_map_change(self, map_name):
        for actor in cast("List[StaticMeshActorBase]", find_all("StaticMeshActorBase", False)):
            if actor.Components and actor.WorldInfo:
                actor.ForceUpdateComponents(True, False)


    def _write_infos_to_file(self, file: TextIOWrapper):
        try:
            file.write(f"StaticMesh:\n")
            file.write(f"{cast("StaticMeshActor", self.current_pickup()).StaticMeshComponent.StaticMesh}\n")
            file.write(f"\n")
        except:
            pass
        super()._write_infos_to_file(file)
        file.write(f"""Notes:\n""")
        file.write(f"""### Those hotfixes only work because of Object Relocator force updating all StaticMeshActor on level change, if you use them for your overhaul mod, you need to add Object Relocator to the list of dependencies.\n""")
        file.write(f"""\n""")


class SkeletalMeshActorPickupManager(ActorPickupManager):
    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("SkeletalMeshActor"))


    def on_enter_editor(self):
        change_the_collision_of_all_live_actor_to_allow_trace("SkeletalMeshActor", False)

    
    ## Normally its not possible to edit with an hotfixes because you need to call ForceUpdate, this fix that.
    def on_map_change(self, map_name):
        for actor in cast("List[SkeletalMeshActor]", find_all("SkeletalMeshActor", False)):
            if actor.Components and actor.WorldInfo:
                actor.ForceUpdateComponents(True, False)


    def _write_infos_to_file(self, file: TextIOWrapper):
        try:
            file.write(f"SkeletalMesh:\n")
            file.write(f"{cast("SkeletalMeshActor", self.current_pickup()).SkeletalMeshComponent.SkeletalMesh}\n")
            file.write(f"\n")
        except:
            pass
        super()._write_infos_to_file(file)


class WillowPickupPickupManager(ActorPickupManager):
    base_WIO: WeakPointer[WillowInteractiveObject] = WeakPointer()

    def on_pre_trace(self):
        change_the_collision_of_all_live_actor_to_allow_trace("WillowPickup", False)


    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("WillowPickup"))
    
    
    def drop(self):
        super().drop()
        self.base_WIO = WeakPointer()


    def _pickup(self, impact_info):
        super()._pickup(impact_info)
        pickup = self.current_pickup()
        if pickup.Base and pickup.Base.Class._inherits(find_class("WillowInteractiveObject")):
            self.base_WIO = WeakPointer(pickup.Base)


    def collision_debug(self, start_trace: Object.Vector, impact_info: Actor.ImpactInfo) -> None:
        super().collision_debug(start_trace, impact_info)
        base = self.base_WIO()
        if base:
            print(f"Base: {base}")
            print(f"Base's InteractiveObjectDefinition: {base.InteractiveObjectDefinition}")

    
    ## Normally its not possible to edit with an hotfixes because you need to call ForceUpdate, this fix that.
    def on_map_change(self, map_name):
        for actor in cast("List[WillowPickup]", find_all("WillowPickup", False)):
            if actor.Components and actor.WorldInfo:
                actor.ForceUpdateComponents(True, False)


    def _write_infos_to_file(self, file: TextIOWrapper):
        base = self.base_WIO()
        if base:
            file.write(f"Base:\n")
            file.write(f"{base}\n")
            file.write(f"\n")
            file.write(f"Base's InteractiveObjectDefinition:\n")
            file.write(f"{base.InteractiveObjectDefinition}\n")
            file.write(f"\n")
        super()._write_infos_to_file(file)


class PrimitiveComponentPickupManager(PickupManager, ABC):
    current_pickup: WeakPointer[PrimitiveComponent] = WeakPointer()

    def has_pickup(self) -> bool:
        return self.current_pickup() is not None


    def rotate(self, rotation_increase: float, rotation_axis: str = "Pitch") -> None:
        match rotation_axis:
            case "Pitch":
                self.current_pickup().Rotation.Pitch += rotation_increase
            case "Yaw":
                self.current_pickup().Rotation.Yaw += rotation_increase
            case "Roll":
                self.current_pickup().Rotation.Roll += rotation_increase
    

    def drop(self):
        self.current_pickup = WeakPointer()


    def collision_debug(self, start_trace: Object.Vector, impact_info: Actor.ImpactInfo) -> None:
        super().collision_debug(start_trace, impact_info)
        if self.current_pickup():
            print(f"Owner: {self.current_pickup().Owner}")


    def _update_debug(self):
        super()._update_debug()
        print(f"Pickup Rotation: {self.current_pickup().Rotation}")
        print(f"Pickup CachedParentToWorld Matrix: {self._get_matrix()}")


    def _pickup(self, impact_info: Actor.ImpactInfo) -> None:
        self.current_pickup = WeakPointer(impact_info.HitInfo.HitComponent)


    def _get_location(self) -> Object.Vector:
        plane = self.current_pickup().CachedParentToWorld.WPlane
        return make_struct("Vector", X=plane.X, Y=plane.Y, Z=plane.Z)
    

    def _set_location(self, new_location: Object.Vector) -> None:
        pickup = self.current_pickup()
        pickup.CachedParentToWorld.WPlane.X = new_location.X
        pickup.CachedParentToWorld.WPlane.Y = new_location.Y
        pickup.CachedParentToWorld.WPlane.Z = new_location.Z
        pickup.ForceUpdate(False)
    

    def _get_matrix(self) -> Object.Matrix:
        pickup = self.current_pickup()
        return pickup.CachedParentToWorld


    def _write_infos_to_file(self, file: TextIOWrapper):
        pickup = self.current_pickup()   
        file.write(f"Object:\n")
        file.write(f"{pickup}\n")
        file.write(f"\n")
        file.write(f"Owner:\n")
        file.write(f"{pickup.Owner}\n")
        file.write(f"\n")

        obj_location = get_matrix_as_string(self._get_matrix())
        obj_rotation = get_rotation_as_string(pickup.Rotation)
        
        file.write(f"""Commands:\n""")
        file.write(f"set {pickup} CachedParentToWorld {obj_location}\n")
        file.write(f"set {pickup} Rotation {obj_rotation}\n")


class ActorMeshCollectionPickupManager(PrimitiveComponentPickupManager):
    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("StaticMeshCollectionActor")) and impact_info.HitInfo.HitComponent
    

    def on_enter_editor(self):
        change_the_collision_of_all_live_actor_to_allow_trace("StaticMeshCollectionActor", False)
    
    ## Normally its not possible to edit with an hotfixes because you need to call ForceUpdate, this fix that.
    def on_map_change(self, map_name):
        for actor in cast("List[StaticMeshCollectionActor]", find_all("StaticMeshCollectionActor", False)):
            if actor.Components and actor.WorldInfo:
                actor.ForceUpdateComponents(True, False)


    def _write_infos_to_file(self, file: TextIOWrapper):
        pickup = self.current_pickup()
        try:
            file.write(f"Mesh:\n")
            file.write(f"{cast("StaticMeshComponent", pickup).StaticMesh}\n")
            file.write(f"\n")
        except ValueError:
            pass
        super()._write_infos_to_file(file)
        file.write(f"""\nNotes:\n""")
        file.write(f"""### Those hotfixes only work because of Object Relocator force updating all StaticMeshCollectionActor on level change, if you use them for your overhaul mod, you need to add Object Relocator to the list of dependencies.\n""")
        file.write(f"""### CachedParentToWorld's WPlane control the location.\n""")
        file.write(f"""\n""")


class ForcePickupPrimitiveComponentPickupManager(PrimitiveComponentPickupManager):
    is_mesh_component: bool = False
    is_particle_component: bool = False
    is_owned_by_collection_actor: bool = False

    def can_pickup(self, impact_info):
        return False
    

    def can_force_pickup(self, pickup_object: Object) -> bool:
        return True if pickup_object and pickup_object.Class._inherits("PrimitiveComponent") else False
    

    def force_pickup(self, pickup_object: Object) -> None:
        self.current_pickup = WeakPointer(pickup_object)
        pc: WillowPlayerController = get_pc()
        player_forward = uemath.Rotator(pc.Rotation).get_axes()[0]    
        forward_location = uemath.Vector(pc.CalcViewLocation) + (player_forward * self.distance_from_camera)
        self._hit_location_offset = uemath.Vector(self._get_location()) - forward_location

        if pickup_object.Class._inherits(STATIC_MESH_COMPONENT_CLASS):
            self.is_mesh_component = True

        elif pickup_object.Class._inherits(PARTICLE_SYSTEM_COMPONENT_CLASS):
            self.is_particle_component = True
        
        owner = cast("PrimitiveComponent", pickup_object).Owner
        if owner:
            if owner.Class._inherits(find_class("StaticMeshCollectionActor")):
                self.is_owned_by_collection_actor = True

    
    def rotate(self, rotation_increase, rotation_axis = "Pitch"):
        if self.is_particle_component:
            super().rotate(rotation_increase, rotation_axis)
        elif self.is_mesh_component:
            if self.is_owned_by_collection_actor:
                super().rotate(rotation_increase, rotation_axis)
            else:
                owner = self.current_pickup().Owner
                match rotation_axis:
                    case "Pitch":
                        owner.Rotation.Pitch += rotation_increase
                    case "Yaw":
                        owner.Rotation.Yaw += rotation_increase
                    case "Roll":
                        owner.Rotation.Roll += rotation_increase  
    

    def drop(self):
        super().drop()
        self.is_mesh_component = False
        self.is_particle_component = False
        self.is_owned_by_collection_actor = False


    def _set_location(self, new_location):
        pickup = self.current_pickup()
        if self.is_mesh_component:
            if self.is_owned_by_collection_actor:
                super()._set_location(new_location)
            else:
                pickup.Owner.Location = new_location
                for comp in pickup.Owner.AllComponents:
                    if comp.Class._inherits(PARTICLE_SYSTEM_COMPONENT_CLASS):  
                        comp: ParticleSystemComponent = comp
                        comp.KillParticlesForced()
                        comp.ActivateSystem()
                        
                pickup.Owner.ForceUpdateComponents(True, False)

        elif self.is_particle_component and pickup.Owner:
            pickup.Owner.Location = new_location
            pickup.Owner.ForceUpdateComponents(True, False)


    def _update_debug(self):
        if self.is_particle_component:
            super()._update_debug()

        elif self.is_mesh_component:
            if self.is_owned_by_collection_actor:
                super()._update_debug()
            else:
                owner = self.current_pickup().Owner
                print(f"Owner Rotation: {owner.Rotation}")
                print(f"Owner Location: {owner.Location}")


    def _write_infos_to_file(self, file: TextIOWrapper):
        pickup = self.current_pickup()
        file.write(f"Object:\n")
        file.write(f"{pickup}\n")
        file.write(f"\n")
        file.write(f"Owner:\n")
        file.write(f"{pickup.Owner}\n")
        file.write(f"\n")

        if self.is_mesh_component:
            file.write(f"Mesh:\n")
            file.write(f"{cast("StaticMeshComponent", pickup).StaticMesh}\n")
            file.write(f"\n")

            if self.is_owned_by_collection_actor:
                file.write(f"""Commands:\n""")
                file.write(f"set {pickup} CachedParentToWorld {get_matrix_as_string(self._get_matrix())}\n")
                file.write(f"set {pickup} Rotation {get_rotation_as_string(pickup.Rotation)}\n")
                file.write(f"""\nNotes:\n""")
                file.write(f"""### Those hotfixes only work because of Object Relocator force updating all StaticMeshCollectionActor on level change, if you use them for your overhaul mod, you need to add Object Relocator to the list of dependencies.\n""")
                file.write(f"""### CachedParentToWorld's WPlane control the location.\n""")
                file.write(f"""\n""")
            else:
                file.write(f"""Commands:\n""")
                file.write(f"set {pickup.Owner} Location {get_vector_as_string(pickup.Owner.Location)}\n")
                file.write(f"set {pickup.Owner} Rotation {get_rotation_as_string(pickup.Owner.Rotation)}\n")

        elif self.is_particle_component:
            file.write(f"Particle Template:\n")
            file.write(f"{cast("ParticleSystemComponent", pickup).Template}\n")
            file.write(f"\n")
            file.write(f"""Commands:\n""")
            file.write(f"set {pickup.Owner} Location {get_vector_as_string(self._get_location())}\n")
            file.write(f"set {pickup} Rotation {get_rotation_as_string(pickup.Rotation)}\n")