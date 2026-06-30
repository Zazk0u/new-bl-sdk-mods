if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

import object_relocator.relocator as relocator
import object_relocator.editor as editor
import object_relocator.inputs as inputs

from typing import TYPE_CHECKING, Any, List, cast

from unrealsdk import find_all
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction

from mods_base import hook, HookType
from mods_base import build_mod, Library, HookType
from mods_base.options import BaseOption
from mods_base.keybinds import KeybindType
from mods_base.command import ArgParseCommand

if TYPE_CHECKING:
    from common import GameInfo
    from common import StaticMeshCollectionActor
    from common import StaticMeshActorBase


## Normally its not possible to edit a StaticMeshCollectionActor's StaticMeshComponent / StaticMeshActorBase with an hotfixes because you need to call ForceUpdate.
## This hook update all StaticMeshCollectionActor on map change so it's now possible.
@hook("Engine.GameInfo:PostCommitMapChange", Type.PRE)
def update_all_static_mesh_actor_collection_on_map_change(this:GameInfo, args:GameInfo.PostCommitMapChange.args, ret:Any, func:BoundFunction) -> None:
    for actor in cast("List[StaticMeshCollectionActor]", find_all("StaticMeshCollectionActor", False)):
        if actor.Components and actor.WorldInfo:
            actor.ForceUpdateComponents(True, False)

    for actor in cast("List[StaticMeshActorBase]", find_all("StaticMeshActorBase", False)):
        if actor.Components and actor.WorldInfo:
            actor.ForceUpdateComponents(True, False)


def enable():
    relocator.on_enabled()
    editor.on_enabled()


def disable():
    relocator.on_disabled()
    editor.on_disabled()


all_options: List[BaseOption] = []
all_options.extend(editor.all_options)
all_options.extend(relocator.all_options)

all_keybinds: List[KeybindType] = []
all_keybinds.extend(relocator.all_keybinds)
all_keybinds.extend(editor.all_keybinds)
all_keybinds.extend(inputs.all_keybinds)


all_commands: List[ArgParseCommand] = []
all_commands.extend(relocator.all_commands)


all_hooks: List[HookType] = [
    update_all_static_mesh_actor_collection_on_map_change,
]

build_mod(cls=Library, on_enable=enable, on_disable=disable, options=all_options, keybinds=all_keybinds, commands=all_commands, hooks=all_hooks)

# rlm object_relocator object_relocator.relocator object_relocator.pickup
# rlm object_relocator.relocator object_relocator.pickup