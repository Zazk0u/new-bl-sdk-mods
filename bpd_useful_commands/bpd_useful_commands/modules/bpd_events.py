from __future__ import annotations  # Ensures type hints are ignored at runtime
from typing import TYPE_CHECKING, List, Dict
import argparse

from mods_base import ArgParseCommand

from unrealsdk import find_class
from unrealsdk.logging import error

from command_extensions import register, command
from command_extensions.builtins import obj_name_splitter, parse_object

from .structs import BehaviorVariableValue, Vector
from .utils import keep_alive, GEARBOX_GLOBALS

if TYPE_CHECKING:
    from common import *


SKILL_DEFINITION_CLASS: SkillDefinition = find_class("SkillDefinition")

_registered_skill_definitions_by_event_name: Dict[str, List[SkillDefinition]] = {}


def make_bool_param(value:bool=0):
    return BehaviorVariableValue(IntValue=int(value), VariableType=1)


def make_int_param(value:int=0):
    return BehaviorVariableValue(IntValue=value, VariableType=2)


def make_float_param(value:float=0.00):
    return BehaviorVariableValue(FloatValue=value, VariableType=3)


def make_object_param(value:Object=None):
    return BehaviorVariableValue(ObjectValue=value, VariableType=5)


def make_vector_param(value:Object.Vector=Vector()):
    return BehaviorVariableValue(VectorValue=value, VariableType=4)


def activate_bpd_event(
        consumer_handle:IBehaviorConsumer.BehaviorConsumerHandle,
        event_name:str,
        bpd:BehaviorProviderDefinition,  
        parameters:List[BehaviorProviderDefinition.BehaviorVariableValue] = [],
        linkid:int = 0,
    ):
    """
    Call a custom event on a BPD of the consumer, the parameters are used for the event's outputed variables.\n
    Exemple:\n
        parameters = [
                make_object_param(projectile.InstigatorController),
                make_object_param(projectile.Instigator),
                make_object_param(projectile.Owner),
                make_object_param(weapon_reloaded),
                make_float_param(current_time),
                make_bool_param(should_explode)
            ]
        activate_bpd_event(projectile.GetBehaviorConsumerHandle(), "mOnPlayerReloadGun", projectile.Definition.BehaviorProviderDefinition, parameters)
    """

    if consumer_handle:
        behavior_kernel = GEARBOX_GLOBALS.GetBehaviorKernel()
        behavior_kernel.ActivateBehaviorEventFromScript(consumer_handle, bpd, event_name, linkid, parameters)


def broadcast_bpd_event(
        consumer_handle:IBehaviorConsumer.BehaviorConsumerHandle, 
        event_name:str,
        bpds:List[BehaviorProviderDefinition] = [],  
        parameters:List[BehaviorProviderDefinition.BehaviorVariableValue] = [],
        linkid:int = 0,
    ):
    """
    Call a custom event on all BPDs given of the consumer, the parameters are used for the event's outputed variables.\n
    If no BPD is given, it will automatically find every BPDs used by the consumer and call the event on each one.
    """

    if consumer_handle:
        behavior_kernel = GEARBOX_GLOBALS.GetBehaviorKernel()
        behavior_kernel.BroadcastBehaviorEventFromScript(consumer_handle, event_name, bpds, linkid, parameters)


def notify_skills_event(controller:Controller, event_name:str, parameters:List[BehaviorProviderDefinition.BehaviorVariableValue] = [], skill_states_to_ignore: List[SkillDefinition.ESkillState] = []):
    """
    Call a custom event on the BPD of all skills owned by the controller if the skill's state is not within the skill_states_to_ignore.\n
    The parameters are used for the event's outputed variables.\n
    Exemple:\n
        parameters = [
                make_object_param(skill_instigator),
                make_object_param(skill_instigator.Pawn),
                make_object_param(damaged_instigator),
                make_object_param(damaged_instigator.Pawn),
                make_object_param(damage_causer),
                make_float_param(damage_dealt),
                make_vector_param(hit_location)
            ]
        notify_skills_event(controller, "mOnDamagedEnemy", parameters, [ESKillState.SKILL_Paused])\n
    Warning: For performance reason, you must use the register_skills_event command to allow a SkillDefinition to get notified by notify_skills_event.
    """

    if not controller:
        return
    
    game_info: WillowGameInfo = controller.WorldInfo.Game
    skill_manager = game_info.GetSkillManager()
    if not skill_manager:
        return
    
    for skill_definition in _registered_skill_definitions_by_event_name.get(event_name, []):
        skill = skill_manager.GetActiveSkillForInstigatorByDefinition(controller, skill_definition)
        if not skill or (skill_states_to_ignore and skill.SkillState in skill_states_to_ignore):
            continue

        consumer_handle = skill.GetBehaviorConsumerHandle()
        bpd = skill.Definition.GetBehaviorProviderDefinition()
        activate_bpd_event(consumer_handle, event_name, bpd, parameters)


@command(splitter=obj_name_splitter, description="Register an event name for a SkillDefinition, allowing it to get notified by any notify_skills_event call that match the event name.")
def register_skills_event(args:argparse.Namespace) -> None:
    """
    Commands:\n
        register_skills_event event_name skill_definition_to_run_even_on
        Exemple:
            register_skills_event mOnDamagedEnemy GD_Globals.SkillDefinition_DamagedEnemy
    """

    skill_def = parse_object(args.SkillDefinition)
    if not skill_def:
        return
    
    if not skill_def.Class._inherits(SKILL_DEFINITION_CLASS):
        error(f"Object {skill_def} must be a 'SkillDefinition'!")
        return
    
    keep_alive(skill_def)
    skills_list = _registered_skill_definitions_by_event_name.get(args.EventName, [])
    if skill_def not in skills_list:
        skills_list.append(skill_def)
        _registered_skill_definitions_by_event_name[args.EventName] = skills_list


register(register_skills_event)
register_skills_event.add_argument("EventName", help="The event name.")
register_skills_event.add_argument("SkillDefinition", help="The SkillDefinition to notify.")


@command(splitter=obj_name_splitter, description="Log the registered skills event to the console.")
def log_registered_skills_event(args:argparse.Namespace) -> None:
    for event in _registered_skill_definitions_by_event_name:
        print(f"{event}: {_registered_skill_definitions_by_event_name[event]}")


def get_bpd_event_commands() -> List[ArgParseCommand]:
    return [register_skills_event, log_registered_skills_event]