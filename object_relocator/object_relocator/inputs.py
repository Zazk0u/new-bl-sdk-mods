from mods_base.keybinds import KeybindType, EInputEvent
from typing import List

_is_shift_enabled: bool = False
_is_alt_enabled: bool = False


def is_shift_enabled():
    return _is_shift_enabled


def is_alt_enabled():
    return _is_alt_enabled


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


_shift = KeybindType("Shift rotation", "LeftShift", event_filter=None, is_hidden=True, callback=_check_shift_input)
_alt = KeybindType("Alt rotation", "LeftAlt", event_filter=None, is_hidden=True, callback=_check_alt_input)


all_keybinds: List[KeybindType]  = [
    _shift,
    _alt
]