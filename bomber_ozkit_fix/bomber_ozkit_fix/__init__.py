from __future__ import annotations  # Ensures type hints are ignored at runtime
if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from typing import TYPE_CHECKING, Any

from mods_base import build_mod, hook, Library

from unrealsdk import find_object, make_struct

from unrealsdk.hooks import Type

from unrealsdk.unreal import BoundFunction

if TYPE_CHECKING:
    from common import *

@hook("WillowGame.WillowPlayerController:SpawningProcessComplete", Type.PRE)
def fix_throw_skills(this:WillowPlayerController, args:WillowPlayerController.SpawningProcessComplete, ret:Any, func:BoundFunction) -> None:
    player_throw_bpd: BehaviorProviderDefinition = find_object("BehaviorProviderDefinition", "GD_PlayerShared.Anims.WeaponAnim_ThrowGrenade:BehaviorProviderDefinition_2")

    try:
        marginal_benefit_throw_anim: SpecialMove_FirstAndThirdPersonAnimation = find_object("SpecialMove_FirstAndThirdPersonAnimation", "Quince_Doppel_Skills.SpecialMoves.SpecialMove_GrenadeThrow")
        marginal_benefit_throw_anim.BehaviorProviderDefinition = player_throw_bpd
    except:
        pass

    try:
        grenade_vent_throw_anim: SpecialMove_FirstAndThirdPersonAnimation = find_object("SpecialMove_FirstAndThirdPersonAnimation", "GD_Prototype_Streaming.Anims.SpecialMove_ThrowGrenade")
        grenade_vent_throw_anim.BehaviorProviderDefinition = player_throw_bpd
        grenade_vent_throw_anim.SMNotifies = []
        grenade_vent_throw_anim.TimedBehaviorEvents = [ make_struct("TimedAnimBehaviorEvent", Time=0.5, bServerOnly=False, EventName="SpawnGrenade") ]
    except:
        pass


build_mod(hooks=[fix_throw_skills], cls=Library)