# Object Relocator
Tool for editing map, allow you to pick up, move and rotate an interactive object.

### v1.0
Initial Release.
### v1.1
Fixed quitting while in editor causing the editor keybind to no longer work.
### v1.2
Now should work on all interactive objects, activating the editor will iterate trought all objects and change their collision to allow my trace function to work.
### v1.42
Updated for the new Python SDK v3.8 release.
Can now pickup static map meshes and interp actors (which is pretty much 90% of the map).
Now update all StaticMeshCollectionActor on map change which allow them you to modify their StaticMeshComponents with hotfixes (you couldn't before).
