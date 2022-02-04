#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 13 20:26:52 2022

format conversions for gmsh

@author: benoit




field_data:
    {'physName1':[tag,dim],
     'physName2':[tag,dim]...}
    
point_data:
    {'gmsh:dim_tags': [
        [entDim,entTag],
        [entDim,entTag],
        ...]}



cell_data:
    {'gmsh:physical':
     element physical group tag}






"""

fd={'Source':[1,3],
'Space':[2,3],
'Boundary':[3,2]}

for el in sim.elements:
    elIdx=el.globalNodeIndices
    inSrc=np.all(sim.nodeRoleTable==2)
    
    
msh=meshio.Mesh(
    sim.mesh.nodeCoords,
    mioElems)