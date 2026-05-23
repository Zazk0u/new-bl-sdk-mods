from __future__ import annotations  # Ensures type hints are ignored at runtime
if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from typing import TYPE_CHECKING, Any, List

from mods_base import Library, build_mod, hook, AbstractCommand

from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction

from .modules.convert_bpd_variable import (
    get_bpd_variable_commands, 
    apply_pending_bpd_variables
)

from .modules.bpd_events import (
    get_bpd_event_commands,
    make_bool_param,
    make_int_param,
    make_float_param,
    make_object_param,
    make_vector_param,
    activate_bpd_event,
    broadcast_bpd_event,
    notify_skills_event
)

from .modules.utils import (
    get_bpd_utils_commands,
    get_bpd_variables_debug_info
)


__all__ = (
    "make_bool_param",
    "make_int_param",
    "make_float_param",
    "make_object_param",
    "make_vector_param",
    "activate_bpd_event",
    "broadcast_bpd_event",
    "notify_skills_event",
    "get_bpd_variables_debug_info"
)


if TYPE_CHECKING:
    from common import *


@hook("Engine.PlayerController:ConsoleCommand", Type.POST)
def react_to_executed_file(this:WillowConsole, args:WillowConsole.ConsoleCommand.args, ret:Any, func:BoundFunction) -> None:
    if args.Command.startswith("exec"):
        apply_pending_bpd_variables()


commands: List[AbstractCommand] = []
commands.extend(get_bpd_variable_commands())
commands.extend(get_bpd_event_commands())
commands.extend(get_bpd_utils_commands())


mod = build_mod(cls=Library, hooks=[react_to_executed_file], commands=commands)