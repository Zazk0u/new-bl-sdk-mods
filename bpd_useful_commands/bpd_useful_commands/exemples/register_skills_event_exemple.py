from mods_base import get_pc
from bpd_useful_commands.modules.bpd_events import notify_skills_event

notify_skills_event(get_pc(), "mOnCustomEvent")

# pyexec bpd_useful_commands/exemples/register_skills_event_exemple.py