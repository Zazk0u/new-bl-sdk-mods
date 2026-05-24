Utility library for BPDs.

- Run custom BPD events from python with custom outputs.
- Converts VariableData's variable to another type, like a BVAR_Object to a BVAR_Vector using the new convert_bpd_variable command.
- Debug a BPD's VariableData using the new log_bpd / log_path_bpd commands on a live object to log all its variables in the console.

# New console commands:
- `log_bpd LiveObjectName` <br/>
IE:  `log_bpd WillowProjectile_0` <br/>
_Log all the variables from the object's first registered BPD using the live object's name._

- `log_bpd_path LiveObjectPathName` <br/>
IE:  `log_bpd_path BackBurner_P.TheWorld:PersistentLevel.WillowProjectile_0` <br/>
_Log all the variables from the object's first registered BPD using the live object's path name._

![](https://github.com/Zazk0u/new-bl-sdk-mods/blob/main/bpd_useful_commands/bpd_useful_commands/exemples/log_bpd_exemple.png)

- `log_registered_skills_event` <br/>
_Log the registered skills event that you've set using the register_skills_event file command to the console._

# New file commands:
- `register_skills_event EventName SkillDefinition` <br/>
IE:  `register_skills_event mOnDamagedEnemy GD_Globals.SkillDefinition_DamagedEnemy` <br/>
_Register an event name for a SkillDefinition, allowing it to get notified by any notify_skills_event call from python that match the event name._

- `convert_bpd_variable VariableTypeForConstructor VariableName BPDToEdit BehaviorSequenceIndexToEdit VariableDataIndexToEdit`<br/>
IE:  `convert_bpd_variable vector HitLocation BehaviorProviderDefiniton'GD_Globals.SkillExemple:BehaviorProviderDefiniton_0' 0 7` <br/>
_Convert a BPD variable of a BPD Sequence VariableData array to another type._<br/>
_This is usefull when you want to convert a BVAR_Object into a BVAR_Vector, it won't cause a game crash._<br/><br/>
Here the arguments for the VariableTypeForConstructor, you really only care for vector and direction_vector:<br/>
`object, bool, int, float, all_players, named_variable, vector, direction_vector`

# Troubleshooting:
_Why log_bpd/log_bpd_path has empty variables or show me uncorrect variables._
![](https://github.com/Zazk0u/new-bl-sdk-mods/blob/main/bpd_useful_commands/WhyLogBPDNotWorkOnPawnOrWeapon.png)
![](https://github.com/Zazk0u/new-bl-sdk-mods/blob/main/bpd_useful_commands/WhyLogBPDNotWorkOnPawnOrWeapon_2.png)
![](https://github.com/Zazk0u/new-bl-sdk-mods/blob/main/bpd_useful_commands/WhyLogBPDNotWorkOnPawnOrWeapon_3.png)
![](https://github.com/Zazk0u/new-bl-sdk-mods/blob/main/bpd_useful_commands/WhyLogBPDNotWorkOnPawnOrWeapon_4.png)

# Changelog:
V1: Released.
