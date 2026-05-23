from __future__ import annotations  # Ensures Type hints are ignored at runtime

import argparse

from typing import TYPE_CHECKING, List

from mods_base import command, ArgParseCommand

from unrealsdk import find_class, find_all, find_object
from unrealsdk.unreal import UObject


if TYPE_CHECKING:
    from common import *


GEARBOX_GLOBALS: GearboxGlobals = find_class("GearboxGlobals").ClassDefaultObject
IBEHAVIOR_CONSUMER_CLASS: IBehaviorConsumer = find_class("IBehaviorConsumer")


def keep_alive(object:UObject, undo:bool=False) -> UObject:
    """Set an object to stay alive.""" 
    try:
        if undo:
            object.ObjectFlags &= ~0x4000
        else:
            object.ObjectFlags |= 0x4000
        return object
    except AttributeError:
        return object


def find_live_object_by_name(name: str) -> UObject:
    """Find a a live object by its name, any live object has an int at the end of its name, ie: WillowProjectile_0.""" 
    if not name or not name[-1].isdigit():
        print(f"{name} is not a live object.")
        return
    
    name = name.lower()
    class_name = name.rsplit("_")[0]
    for live_object in find_all(class_name, True):
        if not live_object.Name.lower() == name:
            continue
        return live_object


def get_bpd_variables_debug_info(consumer_handle:IBehaviorConsumer.BehaviorConsumerHandle) -> str:
    """
    Log all the variable from the consummer bpd's variable data.\n
    Doesn't seems to work with BVAR_UnaryMath and BVAR_BinaryMath.\n
    If an actor has multiple BPD, it can only show variables for the first BPD that was registered.
    """ 

    if not consumer_handle or consumer_handle.PID == -1:
        return ""
    
    kernel = GEARBOX_GLOBALS.GetBehaviorKernel()
    behavior_sequence_idx = 0
    debug_text = ""

    while True:
        _, variables_list = kernel.GetVariableStateSummaryForSequence(consumer_handle.PID, behavior_sequence_idx, [])
        if not variables_list:
            break
        
        debug_text += f"BehaviorSequences {behavior_sequence_idx}:\n"
        idx = 0
        for var in variables_list:
            debug_text += f"VariableData Index[{idx}]: {var}\n"
            idx += 1

        behavior_sequence_idx += 1
        
    return debug_text


@command(description="Log all BPD variable of a live object using its name.")
def log_bpd(_:argparse.Namespace) -> None:
    """
    Commands:\n
        log_bpd LiveObjectName
        Exemple:
            log_bpd WillowProjectile_0
    """
    live_object: IBehaviorConsumer = find_live_object_by_name(_.LiveObjectName)
    if live_object and live_object.Class._implements(IBEHAVIOR_CONSUMER_CLASS):
        print(get_bpd_variables_debug_info(live_object.GetBehaviorConsumerHandle()))


@command(description="Log all BPD variable of a live object using its path name.")
def log_bpd_path(_:argparse.Namespace) -> None:
    """
    Commands:\n
        log_bpd_path LiveObjectPathName
        Exemple:
            log_bpd_path BackBurner_P.TheWorld:PersistentLevel.WillowProjectile_0
    """
    live_object: IBehaviorConsumer = find_object("Object", _.LiveObjectPathName)
    if live_object and live_object.Class._implements(IBEHAVIOR_CONSUMER_CLASS):
        print(get_bpd_variables_debug_info(live_object.GetBehaviorConsumerHandle()))


log_bpd.add_argument("LiveObjectName")
log_bpd_path.add_argument("LiveObjectPathName")


def get_bpd_utils_commands() -> List[ArgParseCommand]:
    return [log_bpd, log_bpd_path]