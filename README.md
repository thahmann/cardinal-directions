# cardinal-directions
This repository is where code is being collected for the project to enable precise reasoning on cardinal direction information

MapDataCollection.py contains a small library of functions for collecting and dealing with relations between polygons in ArcGis. It was originally made for counties, but should work for any shapefile containing polygons.
The library can be used to collect the centers of the polygons, the shared borders between each pair of polygons,  and the sector relations between those two sets of objects.
The library also contains a function designed to take the sector relations and assign at least one directional label to each object, and exactly one object to each directional label.
