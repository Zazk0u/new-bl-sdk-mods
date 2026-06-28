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


ECollisionType: Actor.ECollisionType = find_enum("ECollisionType")
FOLDER_PATH = os.path.relpath(Path(__file__).parent / "logs", Path(sys.executable).parent)


class PickupManager(ABC):
    distance_from_camera: float
    _hit_location_offset: uemath.Vector

    def pickup(self, impact_info: Actor.ImpactInfo) -> None:
        self._pickup(impact_info)
        self._hit_location_offset = uemath.Vector(self._get_location()) - uemath.Vector(impact_info.HitLocation)


    def update(self) -> None:
        pc: WillowPlayerController = get_pc()
        player_forward = uemath.Rotator(pc.Rotation).get_axes()[0]    
        new_location = (uemath.Vector(pc.CalcViewLocation) + (player_forward * self.distance_from_camera) + self._hit_location_offset).to_ue_vector()
        self._set_location(new_location)


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


    def _pickup(self, impact_info: Actor.ImpactInfo) -> None:
        self.current_pickup = WeakPointer(impact_info.HitActor)
        self.opportunity_point = WeakPointer(self._find_opportunity_point())


    def _set_location(self, new_location: Object.Vector) -> None:
        pickup = self.current_pickup()
        pickup.Location = new_location
        pickup.ForceUpdateComponents(False, False)
        if (opportunity_point := self.opportunity_point()):
            opportunity_point.Location = new_location


    def _get_location(self) -> Object.Vector:
        return self.current_pickup().Location


    def _write_infos_to_file(self, file: TextIOWrapper):
        pickup = self.current_pickup()
        opportunity_point = self.opportunity_point()

        obj_location = str(pickup.Location).replace(":", " =").replace("{", "(").replace("}", ")")
        obj_rotation = str(pickup.Rotation).replace(":", " =").replace("{", "(").replace("}", ")")
        
        file.write(f"Object:\n")
        file.write(f"{pickup}\n")
        file.write(f"\n")

        if opportunity_point:
            file.write(f"Opportunity Point:\n")
            file.write(f"{opportunity_point}\n")
            file.write(f"\n")

        file.write(f"Location:\n")
        file.write(f"{obj_location}\n")
        file.write(f"\n")

        file.write(f"Rotation:\n")
        file.write(f"{obj_rotation}\n")
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


    def _find_opportunity_point(self) -> PopulationOpportunity:
        gearbox_globals: GearboxGlobals = find_class("GearboxGlobals").ClassDefaultObject
        population_master = gearbox_globals.GetGearboxGlobals().GetPopulationMaster()
        return population_master.GetActorsOpportunity(self.current_pickup())


class WillowInteractiveObjectPickupManager(ActorPickupManager):
    def on_pre_trace(self):
        self._change_the_collision_of_all_live_WIO_to_allow_trace()


    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("WillowInteractiveObject"))


    def collision_debug(self, start_trace: Object.Vector, impact_info: Actor.ImpactInfo) -> None:
        super().collision_debug(start_trace, impact_info)
        print(f"InteractiveObjectDefinition: {cast("WillowInteractiveObject", self.current_pickup()).InteractiveObjectDefinition}")


    def _write_infos_to_file(self, file: TextIOWrapper):
        file.write(f"InteractiveObjectDefinition:\n")
        file.write(f"{cast("WillowInteractiveObject", self.current_pickup()).InteractiveObjectDefinition}\n")
        file.write(f"\n")
        super()._write_infos_to_file(file)


    def _change_the_collision_of_all_live_WIO_to_allow_trace(self):
        primitive_component_class: UClass = find_class("PrimitiveComponent")
        for actor in cast("List[WillowInteractiveObject]", find_all("WillowInteractiveObject", True)):
            if not (is_live_object := actor.WorldInfo and actor.AllComponents):
                continue

            actor.SetCollisionType(ECollisionType.COLLIDE_BlockAll)
            actor.bBlockActors = True
            for component in actor.AllComponents:
                if component and component.Class._inherits(primitive_component_class):
                    cast("PrimitiveComponent", component).BlockActors = True


class InterpActorPickupManager(ActorPickupManager):
    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("InterpActor"))
    

    def _pickup(self, impact_info: Actor.ImpactInfo):
        super()._pickup(impact_info)
        pickup =  self.current_pickup()
        if pickup.Base and pickup.Base.Class._inherits(find_class("InterpActor")):
            self.current_pickup = WeakPointer(pickup.Base)
            if not self.opportunity_point():
                self.opportunity_point = WeakPointer(self._find_opportunity_point())


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
        print(f"Owner: {self.current_pickup().Owner}")


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
    

    def _write_infos_to_file(self, file: TextIOWrapper):
        pickup = self.current_pickup()   
        file.write(f"Object:\n")
        file.write(f"{pickup}\n")
        file.write(f"\n")
        file.write(f"Owner:\n")
        file.write(f"{pickup.Owner}\n")
        file.write(f"\n")


class ActorMeshCollectionPickupManager(PrimitiveComponentPickupManager):
    def can_pickup(self, impact_info):
        return impact_info.HitActor and impact_info.HitActor.Class._inherits(find_class("StaticMeshCollectionActor")) and impact_info.HitInfo.HitComponent


    def _write_infos_to_file(self, file: TextIOWrapper):
        super()._write_infos_to_file(file)

        pickup = self.current_pickup()
        obj_location = str(pickup.CachedParentToWorld).replace(":", " =").replace("{", "(").replace("}", ")")
        obj_rotation = str(pickup.Rotation).replace(":", " =").replace("{", "(").replace("}", ")")
        
        file.write(f"""Commands: (CachedParentToWorld control the location)\n""")
        file.write(f"set {pickup} CachedParentToWorld {obj_location}\n")
        file.write(f"set {pickup} Rotation {obj_rotation}\n")