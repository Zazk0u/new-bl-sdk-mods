from __future__ import annotations  # Ensures type hints are ignored at runtime
if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from typing import TYPE_CHECKING, Any, cast

from mods_base import build_mod, get_pc, hook, SliderOption, Game

from unrealsdk import find_object

from unrealsdk.hooks import Type, Block
from unrealsdk.unreal import WrappedStruct, BoundFunction

if TYPE_CHECKING:
    from common import *

_mod_enabled: bool = False

_is_bl2: bool = Game.get_current() == Game.BL2

# TPS doesn't have the bl2 function to get the maximum level cap,
# instead used 70 for the max level and the user will have to change it themself with the max slider if they don't match it.
MAX_POSSIBLE_LEVEL_CAP: int = get_pc().GetMaximumPossiblePlayerLevelCap() if _is_bl2 else 70

VANILLA_MIN_LEVEL_TO_GAIN_SKILL_POINTS: int = 5 if _is_bl2 else 3

# Calculate the difference and use it to cap the max slider to prevent the user to go nut with its minimum value, only for bl2.
LEVEL_OFFSET_FOR_MAX_SLIDER_MIN_VALUE: int = (MAX_POSSIBLE_LEVEL_CAP - VANILLA_MIN_LEVEL_TO_GAIN_SKILL_POINTS) if _is_bl2 else 50

SKILL_POINTS_PER_LEVEL_UP_AID: AttributeInitializationDefinition = find_object(
    "AttributeInitializationDefinition", 
    "GD_Globals.Skills.INI_SkillPointsPerLevelUp"
)

min_level_for_skill_points: SliderOption = SliderOption(
    identifier="Minimum level", 
    value=VANILLA_MIN_LEVEL_TO_GAIN_SKILL_POINTS, 
    min_value=1, 
    max_value=VANILLA_MIN_LEVEL_TO_GAIN_SKILL_POINTS,
    description_title="Minimum level to start gaining skill points, a level of 1 make you start with 1 skill point.", 
    on_change=lambda x, y: _set_minimum_level_for_skill_points_gain(y) if _mod_enabled else None
)

max_level_for_skill_points: SliderOption = SliderOption(
    identifier="Maximum level",
    value=MAX_POSSIBLE_LEVEL_CAP, 
    min_value=LEVEL_OFFSET_FOR_MAX_SLIDER_MIN_VALUE, 
    max_value=MAX_POSSIBLE_LEVEL_CAP, 
    description_title=f"""Maximum level after which you no longer gain skills points if you want to offset early skill points gain.""",
)

def _set_minimum_level_for_skill_points_gain(value:float) -> None:
    global SKILL_POINTS_PER_LEVEL_UP_AID
    expression_list = SKILL_POINTS_PER_LEVEL_UP_AID.ConditionalInitialization.ConditionalExpressionList
    if expression_list:
        expression = expression_list[0].Expressions
        if expression:
            expression[0].ConstantOperand2 = value


@hook("WillowGame.WillowPlayerController:LoadTheBank", Type.PRE)
def recompute_skill_points_on_spawn(this:WillowPlayerController, args:WillowPlayerController.LoadTheBank.args, ret:Any, func:BoundFunction) -> None:
    global max_level_for_skill_points, min_level_for_skill_points

    current_level = cast("WillowPlayerPawn", this.Pawn).GetGameStage()
    clamped_level = current_level if current_level <= max_level_for_skill_points.value else max_level_for_skill_points.value
    max_points = clamped_level - (min_level_for_skill_points.value - 1)
    spent_points = this.PlayerSkillTree.GetSkillPointsSpentInTree() if this.PlayerSkillTree is not None else 0
    
    replication_info: WillowPlayerReplicationInfo = this.PlayerReplicationInfo
    if max_points != (replication_info.GeneralSkillPoints + spent_points):
        replication_info.GeneralSkillPoints = max_points - spent_points


@hook("WillowGame.SkillTreeGFxObject:RequestSkillUpgrade", Type.PRE)
def request_skill_upgrade(this:SkillTreeGFxObject, args:SkillTreeGFxObject.RequestSkillUpgrade.args, ret:Any, func:BoundFunction) -> None:
    result = this.CanUpgradeSkill()
    no_failure = 4
    skill_locked = 1
    result = no_failure if result == skill_locked else result
    if result == no_failure:
        this.ProgressionMaskSpeed = this.MovieDef.BranchProgressionMaskSpeed
        this.WPCOwner.ServerUpgradeSkill(this.CurrentSkill)
        this.WPCOwner.PlayerSkillTree.UpdateBranchProgression(this)
    else:
        this.Movie.PlaySpecialUISound("ResultFailure")
    return Block


@hook("WillowGame.SkillTreeGFxObject:UpdateTooltips", Type.PRE)
@hook("WillowGame.SkillTreeGFxObject:UpdateInfoBox", Type.PRE)
@hook("WillowGame.SkillTreeGFxObject:UpdateAllSkillIcons", Type.PRE)
@hook("WillowGame.SkillTreeGFxObject:CalculateBranchProgression", Type.PRE)
def fake_level_five(this:FrontendGFxMovie, args:WrappedStruct, ret:Any, func:BoundFunction) -> None:
    func = getattr(this, func.func.Name)
    replication_info: WillowPlayerReplicationInfo = this.WPCOwner.PlayerReplicationInfo
    if replication_info.ExpLevel < 5:
        lvl = replication_info.ExpLevel
        replication_info.ExpLevel = 5
        func()
        replication_info.ExpLevel = lvl
        return Block


def enable() -> None:
    global _mod_enabled
    _mod_enabled = True
    _set_minimum_level_for_skill_points_gain(min_level_for_skill_points.value)


def disable() -> None:
    global _mod_enabled
    _mod_enabled = False
    _set_minimum_level_for_skill_points_gain(VANILLA_MIN_LEVEL_TO_GAIN_SKILL_POINTS)


build_mod(
    on_enable=enable,
    on_disable=disable,
    hooks=[
        recompute_skill_points_on_spawn,
        request_skill_upgrade, 
        fake_level_five
    ],
    options=[
        min_level_for_skill_points,
        max_level_for_skill_points
    ]
)