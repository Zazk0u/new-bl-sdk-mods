from __future__ import annotations  # Ensures type hints are ignored at runtime
if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from typing import TYPE_CHECKING, Any

from mods_base import build_mod, hook, BoolOption, Game

from unrealsdk import find_class

from unrealsdk.hooks import Type

from unrealsdk.unreal import BoundFunction

if TYPE_CHECKING:
    from common import *
    from tps import OzWillowDmgSource_Slam


IS_TPS: bool = Game.get_current() == Game.TPS


WILLOW_INTERACTIVE_OBJECT_CLASS: WillowInteractiveObject = find_class("WillowInteractiveObject")
WILLOW_PROJECTILE_CLASS: WillowProjectile = find_class("WillowProjectile")
WILLOW_WEAPON_CLASS: WillowWeapon = find_class("WillowWeapon")
WILLOW_GRENADE_MOD_CLASS: WillowGrenadeMod = find_class("WillowGrenadeMod")
BULLET_DAMAGESOURCE_CLASS: WillowDmgSource_Bullet = find_class("WillowDmgSource_Bullet") # OzWillowDmgSource_Laser inherit from this.
MELEE_DAMAGESOURCE_CLASS: WillowDmgSource_Melee = find_class("WillowDmgSource_Melee")


if IS_TPS:
    SLAM_DAMAGESOURCE_CLASS: OzWillowDmgSource_Slam = find_class("OzWillowDmgSource_Slam")


allow_bullets_option = BoolOption(f"{"Bullets/Lasers" if IS_TPS else "Bullets"}", True, "Open containers", "Don't open containers")
allow_projectiles_option = BoolOption("Projectiles", True, "Open containers", "Don't open containers")
allow_grenades_option = BoolOption("Grenades", True, "Open containers", "Don't open containers")
allow_melee_option = BoolOption("Melee", True, "Open containers", "Don't open containers")
allow_slam_option = BoolOption("Slam", True, "Open containers", "Don't open containers", is_hidden=not IS_TPS)


def _wio_is_a_container(wio: WillowInteractiveObject)-> bool:
    return wio and wio.Loot and len(wio.Loot) > 0 and wio.Class is WILLOW_INTERACTIVE_OBJECT_CLASS


def _can_use_wio(wio: WillowInteractiveObject, damage_controller: Controller, damage_causer: IDamageCauser, damage_type: DamageType)-> bool:
    return (
        wio.bCanBeUsed[0] == 1 # 1 mean it can be used, the game set this to 0 once the WIO is used.
        and wio.bCostsToUse[0] == 0 # Shouldn't be opened if the container has a cost, it would be cheaty.
        and damage_controller 
        and damage_controller.Pawn 
        and damage_controller.bIsPlayer
        and _wio_is_a_container(wio) 
        and damage_causer
        and damage_type
        and _pass_damage_filter_options(damage_causer, damage_type)
    )


def _pass_damage_filter_options(damage_causer: IDamageCauser, damage_type: DamageType) -> bool:
    if allow_bullets_option.value and damage_type._inherits(BULLET_DAMAGESOURCE_CLASS):
        return True
    
    if allow_melee_option.value and damage_type._inherits(MELEE_DAMAGESOURCE_CLASS):
        return True
    
    if IS_TPS and allow_slam_option.value and damage_type._inherits(SLAM_DAMAGESOURCE_CLASS):
        return True
        
    if damage_causer.Class._inherits(WILLOW_PROJECTILE_CLASS):
        damage_projectile: WillowProjectile = damage_causer

        # A projectile spawned from a grenade mod won't store the grenade mod reference on its childs projectile. 
        # That mean there is now way of knowing if the child originate from a grenade mod, we basically have to check that owner is None and assume its a grenade.
        # Could store the grenade mod owner into a WeakRef/InstanceData with an on projectile spawn hook and then evaluate it, but it's good enough.
        if allow_grenades_option.value and (damage_projectile.Owner is None or damage_projectile.Owner.Class._inherits(WILLOW_GRENADE_MOD_CLASS)):
            return True
        
        if allow_projectiles_option.value:
            return True


@hook("WillowGame.WillowInteractiveObject:InitializeFromDefinition", Type.POST)
def on_wio_initialize(this:WillowInteractiveObject, args:WillowInteractiveObject.InitializeFromDefinition.args, ret:Any, func:BoundFunction) -> None:
    definition = this.InteractiveObjectDefinition
    if definition and _wio_is_a_container(this):
        # This does allow damaging skills (ie: anarchy) from procing with more interactive objects.
        this.bCanBeDamaged = True
        this.bTakeDamageCausedByRadiusDamage = True


@hook("WillowGame.WillowInteractiveObject:TakeDamage", Type.PRE)
def on_wio_take_damage(this:WillowInteractiveObject, args:WillowInteractiveObject.TakeDamage.args, ret:Any, func:BoundFunction) -> None:
    damage_controller = args.EventInstigator
    if _can_use_wio(this, damage_controller, args.DamageCauser, args.DamageType):
        this.UseObject(damage_controller.Pawn, None, 0)


@hook("WillowGame.WillowInteractiveObject:TakeRadiusDamage", Type.PRE)
def on_wio_take_radius_damage(this:WillowInteractiveObject, args:WillowInteractiveObject.TakeRadiusDamage.args, ret:Any, func:BoundFunction) -> None:
    damage_controller = args.InstigatedBy
    if _can_use_wio(this, damage_controller, args.DamageCauser, args.DamageType):
        this.UseObject(damage_controller.Pawn, None, 0)


build_mod(
    options=[
        allow_bullets_option, 
        allow_projectiles_option, 
        allow_grenades_option,
        allow_melee_option,
        allow_slam_option
    ],
    hooks=[
        on_wio_initialize,
        on_wio_take_damage,
        on_wio_take_radius_damage,
    ]
)