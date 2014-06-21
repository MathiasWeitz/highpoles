# highpoles

find and remove highpoles in a blender mesh

A highpole is a vertice with many adjacent edges. It is a personal matter of definition, when there are to many edges.
For some Programs like Sculptris (12 edges) or Meshmixer (24 edges) have problems importing highpoles.

__max normals diverge__ suppress a flip if the normals of both faces are diverging more than this value, a zero just allows flips on a plane.

__minimum edges__ ending condition, when all vertices have less edges than this value. The script can stop before reaching this value if no flips are possible anymore, in this case all highpoles vertices are selected.

__padding__ distance of a flipped edge from the origin vertices. Main reason for this value, sculptris can handle tainted faces, but they still should be avoided, but sculptris fails on highpoles. A positiv padding may produce more aesthetic, but it is more likely that the script doesn't solve all highpoles.
