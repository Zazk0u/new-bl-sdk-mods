from __future__ import annotations  # Ensures type hints are ignored at runtime
from typing import TYPE_CHECKING
from pathlib import Path
from datetime import datetime
from unrealsdk import find_class

import os
import sys

if TYPE_CHECKING:
    from common import WillowInteractiveObject
    from common import PopulationOpportunity

_folder_path = os.path.relpath(Path(__file__).parent / "logs", Path(sys.executable).parent)

def write_object_infos_to_file(obj: WillowInteractiveObject, opportunity_point: PopulationOpportunity):
    date = str(datetime.now()).replace(":", "-").replace(" ", "_").split(".")[0]
    path = f"{_folder_path}\log_{date}.txt"
    obj_location = str(obj.Location).replace(":", " =").replace("{", "(").replace("}", ")")
    obj_rotation = str(obj.Rotation).replace(":", " =").replace("{", "(").replace("}", ")")

    with open(path, "w") as f:
        f.write(f"Object:\n")
        f.write(f"{obj}\n")
        f.write(f"\n")

        f.write(f"Definition:\n")
        f.write(f"{obj.InteractiveObjectDefinition}\n")
        f.write(f"\n")

        f.write(f"Opportunity Point:\n")
        f.write(f"{opportunity_point}\n")
        f.write(f"\n")

        f.write(f"Location:\n")
        f.write(f"{obj_location}\n")
        f.write(f"\n")

        f.write(f"Rotation:\n")
        f.write(f"{obj_rotation}\n")
        f.write(f"\n")

        f.write(f"Instance datas:\n")
        for data in obj.InstanceState.Data:
            f.write(f"{data}\n")
        f.write(f"\n")
        
        f.write(f"Commands:\n")
        # If there's no opportunity point, then the object was handplaced by the game designer (ie: the customization machine). 
        # The object name will always be the same in that case so you'll want to use the object commands instead.
        if opportunity_point:
            f.write(f"set {opportunity_point} Location {obj_location}\n")
            f.write(f"set {opportunity_point} Rotation {obj_rotation}\n")
        else:
            f.write(f"set {obj} Location {obj_location}\n")
            f.write(f"set {obj} Rotation {obj_rotation}\n")