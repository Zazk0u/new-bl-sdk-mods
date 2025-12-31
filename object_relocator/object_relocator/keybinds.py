from mods_base.keybinds import KeybindType, EInputEvent
from typing import List

_is_shift_enabled: bool = False
_is_alt_enabled: bool = False

def _check_shift_input(input_event: EInputEvent):
    global _is_shift_enabled
    _is_shift_enabled = False
    if input_event == EInputEvent.IE_Pressed:
        _is_shift_enabled = True
    elif input_event == EInputEvent.IE_Repeat:
        _is_shift_enabled = True

def _check_alt_input(input_event: EInputEvent):
    global _is_alt_enabled
    _is_alt_enabled = False
    if input_event == EInputEvent.IE_Pressed:
        _is_alt_enabled = True
    elif input_event == EInputEvent.IE_Repeat:
        _is_alt_enabled = True

def is_shift_enabled():
    return _is_shift_enabled

def is_alt_enabled():
    return _is_alt_enabled

editor = KeybindType("Toggle editor", "F3", event_filter=EInputEvent.IE_Pressed)
pickup_object = KeybindType("Pickup/Release object in editor", "E", event_filter=EInputEvent.IE_Pressed)
rotate_object_increase = KeybindType("Rotation increase", "LeftMouseButton", event_filter=EInputEvent.IE_Repeat, is_hidden=True)
rotate_object_decrease = KeybindType("Rotation decrease", "RightMouseButton", event_filter=EInputEvent.IE_Repeat, is_hidden=True)
move_object_toward = KeybindType("Move toward", "MouseScrollDown", is_hidden=True)
move_object_away = KeybindType("Move away", "MouseScrollUp", is_hidden=True)
_shift = KeybindType("Shift rotation", "LeftShift", event_filter=None, is_hidden=True, callback=_check_shift_input)
_alt = KeybindType("Alt rotation", "LeftAlt", event_filter=None, is_hidden=True, callback=_check_alt_input)

keybinds: List[KeybindType]  = [
    editor,
    pickup_object,
    rotate_object_increase,
    rotate_object_decrease,
    move_object_toward,
    move_object_away,
    _shift,
    _alt
]