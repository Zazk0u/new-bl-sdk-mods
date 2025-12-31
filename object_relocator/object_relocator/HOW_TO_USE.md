Requirements:
https://bl-sdk.github.io/willow2-mod-db/mods/uemath/

1:<br/>
Activate the editor mode, then press the pick up object keybind while looking at an interactive object.<br/>
The object will now be held in front of you.

2:<br/>
Rotate the picked up object's Roll rotation by holding your Left/Right mouse. (you can edit which input rotate which axis in the mod settings)<br/>
- hold Left Alt + Mouse to rotate the Yawn rotation instead.
- hold Left Shift + Mouse to rotate the Pitch rotation instead.

Roll your mouse wheel to move the object toward/away from you.

3:<br/>
Press the pick up keybind again to release the object.<br/>
Doing this will generate a log text file within object_relocator/logs containing informations on the object that was picked up.<br/>
You want to export the sdkmod folder to read the files.

Logged informations:
- Object's name
- Object's definition
- Object's opportunity point if it has one
- Object's new location
- Object's new rotation
- Object's instance datas
- Location/Rotation set commands for the Opportunity Point/Object, to use for text mods

Known limitations: 
- Object might no longer pickable if broken, like a bullymong pile after being shot, this happen because the game designer set its collision to None, preventing traces function to affect it.



