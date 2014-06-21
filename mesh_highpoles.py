# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
	'name': "Mesh Highpoles",
	'author': "Mathias Weitz",
	'version': (0, 0, 1),
	'blender': (2, 7, 0),
	'location': "View3D > Tools",
	'description': "find and eleminate highpoles",
	'category': 'Mesh'}

import bpy
from bpy.props import *
import math, time, logging
import mathutils
from math import pi,sin,cos,sqrt
from mathutils import Vector, Matrix

def distanceBetweenLines(p0,p1,q0,q1):
	''' Lines are given by Points (Vector) on the Line '''
	r0, r1, d = 0, 0, 0
	w = p0-q0
	u,v = p1 - p0, q1 - q0
	uu, vv, uv = u.dot(u), v.dot(v), u.dot(v)
	uw, vw = u.dot(w), v.dot(w)
	denom = uu * vv - uv * uv
	if 1e-7 < abs(denom):
		r0 = (uv * vw - vv * uw) / denom 
		r1 = (uu * vw - uv * uw) / denom 
	return r0, r1, d
		
class MeshFindhighpoles(bpy.types.Operator):
	'''reduces highpole verts by flipping an edge connected to the highpole'''
	bl_idname = 'mesh.findhighpoles'
	bl_label = 'MeshFindHighpoles'
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		obj = context.active_object
		return (obj and obj.type == 'MESH')

	def execute(self, context):
		#global logging
		#logging.info("\n************************* Start")
		activeMesh = context.active_object
		bpy.ops.object.mode_set(mode='EDIT')		
		bpy.ops.mesh.select_mode(type="VERT", action='TOGGLE')
		bpy.ops.mesh.select_all(action='SELECT')		
		bpy.ops.mesh.quads_convert_to_tris()
		diverge = cos(context.scene.highPoint_facediverge * pi / 180)
		padding = context.scene.highPoint_flippadding
		hist = []
		b = True
		while b:
			#hist = hist[-50:]
			b = False
			bpy.ops.object.mode_set(mode='OBJECT')		
			highPoleScore = 0
			for edge in activeMesh.data.edges:
				edge.select = False
			for poly in activeMesh.data.polygons:
				# todo - testing if every polygon is a triangle
				poly.select = False
			for verts in activeMesh.data.vertices:
				verts.select = False
				
			verts_to_edges = {}
			for edges in activeMesh.data.edge_keys:
				for i in range(len(edges)):
					if not edges[i] in verts_to_edges:
						verts_to_edges[edges[i]] = []
					verts_to_edges[edges[i]].append(edges)
			
			edge_to_opvert = {}
			for poly in activeMesh.data.polygons:
				for i in range(len(poly.vertices)):
					p1,p2,p3 = poly.vertices[i], poly.vertices[(i + 1) % len(poly.vertices)], poly.vertices[(i + 2) % len(poly.vertices)]
					if p2 < p1:
						p1,p2 = p2,p1
					if (p1,p2) not in edge_to_opvert:
						edge_to_opvert[(p1,p2)] = {'op':[], 'no':[]}
					edge_to_opvert[(p1,p2)]['op'].append(p3)
					edge_to_opvert[(p1,p2)]['no'].append(poly.normal)
					
			highPoleScore = 0
			for i,vs in verts_to_edges.items():
				if highPoleScore < len(vs):
					highPoleScore = len(vs)
			#print ("highPoleScore", highPoleScore)
			if context.scene.highPoint_minedges <= highPoleScore:
				bestGain, bestEdge = 0.0, (0,0)
				for i,vs in verts_to_edges.items():
					#activeMesh.data.vertices[i].select = highPoleScore == len(vs)
					if highPoleScore == len(vs):
						# if Highpole, go through all 
						for v in vs:
							#print (v,hist, v in hist)
							if 2 == len(edge_to_opvert[v]['no']) and v not in hist:
								dotnormal = abs(edge_to_opvert[v]['no'][0].dot(edge_to_opvert[v]['no'][1]))
								#print (i,v, edge_to_opvert[v], dotnormal)
								# gain is the number of edges which will be reduced overall by flipping this edge
								p0 = activeMesh.data.vertices[v[0]].co
								p1 = activeMesh.data.vertices[v[1]].co
								q0 = activeMesh.data.vertices[edge_to_opvert[v]['op'][0]].co
								q1 = activeMesh.data.vertices[edge_to_opvert[v]['op'][1]].co
								#print ('p0, p1, q0, q1', p0, p1, q0, q1)
								r0, r1, d = distanceBetweenLines(p0,p1,q0,q1)
								gain = highPoleScore + r0 - 1 - (max(len(verts_to_edges[edge_to_opvert[v]['op'][0]]), len(verts_to_edges[edge_to_opvert[v]['op'][1]])))
								if bestGain < gain and diverge < dotnormal:
									if 0.0+padding < r0 and r0 < 1.0-padding:
										bestGain = gain
										bestEdge = v
								
				print ("HighPole, Gain", "%3d" % highPoleScore, "%3.2f" % bestGain, bestEdge)
				if 0 < bestGain:
					hist.append(bestEdge)
					b = True
					activeMesh.data.vertices[bestEdge[0]].select = True
					activeMesh.data.vertices[bestEdge[1]].select = True
					bpy.ops.object.mode_set(mode='EDIT')
					bpy.ops.mesh.edge_rotate()
		
		# show the verts that are still highpoles
		for i,vs in verts_to_edges.items():
			if context.scene.highPoint_minedges <= len(vs):
				activeMesh.data.vertices[i].select = True
		bpy.ops.object.mode_set(mode='EDIT')
		return {'FINISHED'}
		
class VIEW3D_PT_tools_HighPoles(bpy.types.Panel):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_context = "mesh_edit"
	bl_idname = 'MeshHighPoles'
	bl_label = "HighPoles"
	bl_category = "Tools"
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		active_obj = context.active_object
		layout = self.layout

		col1 = layout.column(align=True)
		col1.prop(context.scene, "highPoint_minedges")
		col1.prop(context.scene, "highPoint_facediverge")
		col1.prop(context.scene, "highPoint_flippadding")
		row = col1.row(align=True)
		row.operator("mesh.findhighpoles", text="Eleminate Highpoles")
		
classes = [VIEW3D_PT_tools_HighPoles,
	MeshFindhighpoles,]

def register():
	#bpy.utils.register_module(__name__)
	for c in classes:
		bpy.utils.register_class(c)
	bpy.types.Scene.highPoint_facediverge = FloatProperty(name = "max normals diverge",
		description = "maximum diverge of face normals for flipping edge in grad",
		default = 1.0,
		min = 0.0,
		max = 90.0,
		precision = 0)
	bpy.types.Scene.highPoint_minedges = IntProperty(
		name="minimum edges",
		description="stops if minimum of edges per vert is achieved",
		default = 12,
		min = 7,
		max = 24)
	bpy.types.Scene.highPoint_flippadding = FloatProperty(name = "padding",
		description = "aesthetic distance a edge should keep after a flip, the smaller the value the more likely a flip will be done. Negative values allow defect flips.",
		default = 0.0,
		min = -0.4,
		max = 0.4,
		precision = 1)
	
def unregister():
	#bpy.utils.unregister_module(__name__)
	for c in classes:
		bpy.utils.unregister_class(c)

if __name__ == "__main__":
	register()
	logging.basicConfig(filename='c:\\tmp\\python.txt', format='%(message)s', level=logging.DEBUG)