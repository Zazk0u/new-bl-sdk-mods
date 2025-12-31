from mods_base.options import BaseOption, SliderOption, BoolOption, SpinnerOption
from typing import List

debug_mode = BoolOption("Debug mode", False, description="Print debug messages and draw when attempting to pickup an picked object for better visualization.")
pickup_max_range = SliderOption("Max pickup range", 2000, 200, 2000, description="The range at which you can pickup the object.")
editor_fly_speed = SliderOption("Editor fly speed", 2000, 1000, 10000, description="Speed at which you fly in editor mode.")
mouse_rotation = SpinnerOption("Mouse rotation axis", "Roll", ["Pitch", "Yaw", "Roll"], description="Which of the object rotation axis is affected by holding the input.")
alt_rotation = SpinnerOption("Left Alt rotation axis", "Yaw", ["Pitch", "Yaw", "Roll"], description="Which of the object rotation axis is affected by holding the input.")
shift_rotation = SpinnerOption("Left Shift rotation axis", "Pitch", ["Pitch", "Yaw", "Roll"], description="Which of the object rotation axis is affected by holding the input.")
rotation_multiplier = SliderOption("Rotation multiplier", 50, 1, 100, description="Multiplier when rotating the picked object, decrease for slower rotation.")

options: List[BaseOption]  = [
    debug_mode,
    pickup_max_range, 
    editor_fly_speed,
    mouse_rotation,
    alt_rotation,
    shift_rotation,
    rotation_multiplier
]