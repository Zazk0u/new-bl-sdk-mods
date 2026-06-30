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
Doing this will generate a log text file within object_relocator/logs containing informations on the object that was picked up and its new location/rotation values.<br/>
You want to export the sdkmod folder to read the logs.


New Console Commands:

force_pickup StaticMeshComponent
# force_pickup StaticMeshComponent'SouthpawFactory_P.TheWorld:PersistentLevel.StaticMeshCollectionActor_91.StaticMeshActor_SMC_500'
# Force a StaticMeshComponent to be picked up, bypassing collision, use this if you can't pickup a StaticMeshComponent via tracing, usefull with get_mesh_components_in_radius/get_closest_mesh_component.

force_pickup ParticleSystemComponent
# force_pickup ParticleSystemComponent'SouthpawFactory_P.TheWorld:PersistentLevel.Emitter_60.ParticleSystemComponent_139'
# Force a ParticleSystemComponent to be picked up, pretty much need to use this anytime you want to move a ParticleSystemComponent, usefull with get_particle_components_in_radius/get_closest_particle_component.
# Some particles can't be rotated.

get_mesh_components_in_radius Radius
# get_mesh_components_in_radius 300
# Print all the StaticMeshComponents within radius of you + their distance to the console.

get_particle_components_in_radius Radius
# get_particle_components_in_radius 300
# Print all the ParticleSystemComponents within radius of you + their distance to the console.

get_closest_mesh_component
# get_closest_mesh_component
# Search for the closest StaticMeshComponent and write its name to the console input, also print its mesh.

get_closest_particle_component
# get_closeget_closest_particle_componentst_mesh_component
# Search for the closest ParticleSystemComponent and write its name to the console input, also print its template.