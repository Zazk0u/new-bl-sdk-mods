Utility library for BPDs.

- Run custom BPD events from python with custom outputs.
- Converts VariableData's variable to another type, like a BVAR_Object to a BVAR_Vector using the new convert_bpd_variable command.
- Debug a BPD's VariableData using the new log_bpd / log_path_bpd commands on a live object to log all its variables in the console.

New console commands:
- log_bpd LiveObjectName <br/>
log_bpd WillowProjectile_0 <br/>
Log all the variables from the object's first registered BPD using the live object's name.

- log_bpd_path LiveObjectPathName <br/>
log_bpd_path BackBurner_P.TheWorld:PersistentLevel.WillowProjectile_0 <br/>
Log all the variables from the object's first registered BPD using the live object's path name.
