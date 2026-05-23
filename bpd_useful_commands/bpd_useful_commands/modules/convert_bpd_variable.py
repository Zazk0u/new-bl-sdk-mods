from __future__ import annotations  # Ensures Type hints are ignored at runtime
from typing import TYPE_CHECKING, Dict, Callable, List
import argparse

from functools import cache

from unrealsdk.logging import error

from mods_base import ArgParseCommand

from unrealsdk import find_object, find_class

from command_extensions import register, command
from command_extensions.builtins import obj_name_splitter, parse_object

from .structs import BehaviorVariableData
from .utils import keep_alive

if TYPE_CHECKING:
    from common import *


class PendingVariable:
    @cache
    def OBJECT_VAR() -> BehaviorProviderDefinition.BehaviorVariableData:
        return BehaviorVariableData("", 5)

    @cache
    def BOOL_VAR() -> BehaviorProviderDefinition.BehaviorVariableData:
        return BehaviorVariableData("", 1)

    @cache
    def INT_VAR() -> BehaviorProviderDefinition.BehaviorVariableData:
        return BehaviorVariableData("", 2)

    @cache
    def FLOAT_VAR() -> BehaviorProviderDefinition.BehaviorVariableData:
        return BehaviorVariableData("", 3)

    @cache
    def ALL_PLAYERS_VAR() -> BehaviorProviderDefinition.BehaviorVariableData:
        return BehaviorVariableData("", 6)
    
    @cache
    def NAMED_VARIABLE() -> BehaviorProviderDefinition.BehaviorVariableData:
        return BehaviorVariableData("", 9)

    @cache
    def VECTOR_VAR() -> BehaviorProviderDefinition.BehaviorVariableData:
        # We can't create a BVAR_Vector, it will crash the game because its dummy pointer is invalid but we can copy an existing one and use it instead.
        # Change to the BVAR_Vector won't affect the BVAR_Vector it copied.
        bpd: BehaviorProviderDefinition = keep_alive(find_object(
            "BehaviorProviderDefinition", 
            # This object exist in both BL2/TPS and doesn't change.
            "GD_Shields.Projectiles.Projectile_StandardLegendaryShield:BehaviorProviderDefinition_0"
        ))
        return bpd.BehaviorSequences[0].VariableData[10]
    
    @cache
    def DIRECTION_VECTOR_VAR() -> BehaviorProviderDefinition.BehaviorVariableData:
        # We can't create a BVAR_DirectionVector, it will crash the game because its dummy pointer is invalid but we can copy an existing one and use it instead.
        # Change to the BVAR_DirectionVector won't affect the BVAR_DirectionVector it copied.
        bpd: BehaviorProviderDefinition = keep_alive(find_object(
            "BehaviorProviderDefinition", 
            # This object exist in both BL2/TPS and doesn't change.
            "GD_Weap_Shotgun.Projectiles.Projectile_TedioreReloadShotgun_Legendary:BehaviorProviderDefinition_0"
        ))
        return bpd.BehaviorSequences[0].VariableData[43]
    
    BPD_VARIABLE_CONSTRUCTOR: Dict[str, Callable[..., (BehaviorProviderDefinition.BehaviorVariableData)]] = {
        "object": OBJECT_VAR,
        "bool": BOOL_VAR,
        "int": INT_VAR,
        "float": FLOAT_VAR,
        "all_players": ALL_PLAYERS_VAR,
        "named_variable": NAMED_VARIABLE,
        "vector": VECTOR_VAR,
        "direction_vector": DIRECTION_VECTOR_VAR,
    }

    def __init__(self, name:str, type_for_constructor:str, bpd_to_edit:BehaviorProviderDefinition, bpd_sequence_index_to_edit:int, variable_data_index_to_edit: int):
        self.name = name
        self.type_for_constructor = type_for_constructor
        self.bpd_to_edit = bpd_to_edit
        self.bpd_sequence_index_to_edit = bpd_sequence_index_to_edit
        self.variable_data_index_to_edit = variable_data_index_to_edit

    def _can_add_variable(self):
        if not self.bpd_to_edit.BehaviorSequences or self.bpd_sequence_index_to_edit > len(self.bpd_to_edit.BehaviorSequences):
            return False
        
        if self.variable_data_index_to_edit != -1:
            if self.variable_data_index_to_edit > len(self.bpd_to_edit.BehaviorSequences[self.bpd_sequence_index_to_edit].VariableData):
                return False
            return True
        
        for variable_data_variable in self.bpd_to_edit.BehaviorSequences[self.bpd_sequence_index_to_edit].VariableData:
            if variable_data_variable.Name and variable_data_variable.Name == self.name:
                return False
        return True
    
    def set_bpd_variable(self):
        if not self._can_add_variable():
            return
        
        variable_template = self.BPD_VARIABLE_CONSTRUCTOR.get(self.type_for_constructor, None)
        if not variable_template:
            return
        
        variable = variable_template()
        variable.Name = self.name
        # Setting the index or appending the VariableData array doesn't cause issues, the pointer of other variables will remain unchanged.
        # Normally it you try to edit the VariableData array with blcm, all pointers get reset to 0 and that can cause a game crash in 90% of case.
        # When you create a new BPD from the default template, you are allowed to use BVAR_Object/BVAR_Bool/BVAR_Int/BVAR_Float/BVAR_AllPlayers/BVAR_NamedVariable, it won't cause crashes.
        # However you can't do that for BVAR_Vector/BVAR_DirectionVector, you need to create a BVAR_Object and use the convert_bpd_variable to convert the BVAR_Object to a copied BVAR_Vector/BVAR_DirectionVector instead.
        # BVAR_Attribute/BVAR_InstanceData/BVAR_NamedKismetVariable/BVAR_AttachmentLocation/BVAR_UnaryMath/BVAR_BinaryMath/BVAR_Flag are lost causes, they are very linked to the original BPD using them and are prone to crashes.
        if self.variable_data_index_to_edit != -1:
            self.bpd_to_edit.BehaviorSequences[self.bpd_sequence_index_to_edit].VariableData[self.variable_data_index_to_edit] = variable
        else:
            self.bpd_to_edit.BehaviorSequences[self.bpd_sequence_index_to_edit].VariableData.append(variable)


BEHAVIOR_PROVIDER_DEFINITION_CLASS: BehaviorProviderDefinition = find_class("BehaviorProviderDefinition")

_all_pending_variables: List[PendingVariable] = []  
_cached_bpds_by_name: Dict[str, BehaviorProviderDefinition] = {}


# Use after the mod file has been executed to edit BPD's VariableData.
def apply_pending_bpd_variables():
    for pending_variable in _all_pending_variables:
        pending_variable.set_bpd_variable()

    _all_pending_variables.clear()
    _cached_bpds_by_name.clear()


@command(splitter=obj_name_splitter, description="Convert a BPD variable of a BPD Sequence VariableData array to another type.")
def convert_bpd_variable(args:argparse.Namespace) -> None:
    """
    Commands:\n
        convert_bpd_variable VariableTypeForConstructor VariableName BPDToEdit BehaviorSequenceIndexToEdit VariableDataIndexToEdit
        VariableTypeForConstructor: object / bool / int / float / float / all_players / vector
        Exemple where i convert a BVAR_Object at index 7 of the first bpd sequence to a BVAR_Vector:
            convert_bpd_variable vector HitLocation BehaviorProviderDefiniton'GD_Globals.SkillExemple:BehaviorProviderDefiniton_0' 0 7
    """
    bpd_name = args.BPDToEdit
    bpd = _cached_bpds_by_name.get(bpd_name, None)

    if not bpd:
        bpd = parse_object(bpd_name)
        if not bpd:
            error(f"BehaviorProviderDefinition '{bpd_name}' does not exist!")
            return
        
        if not bpd.Class._inherits(BEHAVIOR_PROVIDER_DEFINITION_CLASS):
            error(f"Object {bpd} must be a 'BehaviorProviderDefinition'!")
            return
        
        _cached_bpds_by_name[bpd_name] = bpd

    _all_pending_variables.append(PendingVariable(args.VariableName, args.VariableTypeForConstructor, bpd, int(args.BehaviorSequenceIndexToEdit), int(args.VariableDataIndexToEdit)))


def get_bpd_variable_commands() -> List[ArgParseCommand]:
    return [convert_bpd_variable]


register(convert_bpd_variable)
convert_bpd_variable.add_argument("VariableTypeForConstructor", help="The variable type name, case doesn't matter.")
convert_bpd_variable.add_argument("VariableName", help="The variable name.")
convert_bpd_variable.add_argument("BPDToEdit", help="The BehaviorProviderDefinition to set variable for.")
convert_bpd_variable.add_argument("BehaviorSequenceIndexToEdit", help="The BehaviorSequence Index where we gonna add the variable, default to 0.", default=0)
convert_bpd_variable.add_argument("VariableDataIndexToEdit", help="The index of the BehaviorVariableData we gonna switch to our variable, if left as -1, we're appending instead.", default=-1)