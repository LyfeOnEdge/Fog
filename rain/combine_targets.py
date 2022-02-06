from ursina import *
#Based on convert.py from ursina
from ursina import destroy

temp_entity = None

def get_vertices(entity, relative_to=None):
    global temp_entity
    if relative_to is None:
        return entity.model.vertices

    vertices = list()
    if not temp_entity:
        temp_entity = Entity(ignore=True)

    temp_entity.parent = entity.model

    for v in entity.model.vertices:
        temp_entity.position = v
        vertices.append(temp_entity.get_position(relative_to))

    return vertices

def combine_targets(entities, destroy_after = False):
    parent = Entity(color=color.white)

    verts = []
    tris = []
    norms = []
    uvs = []
    cols = []
    to_destroy = []
    o = 0


    for e in entities:
        if not hasattr(e, 'model') or e.model == None or e.scripts or e.eternal:
            continue
        if not hasattr(e.model, 'vertices') or not e.model.vertices:
            e.model = load_model(e.model.name, use_deepcopy=True)
            e.origin = e.origin

        verts += get_vertices(e, parent)

        if not e.model.triangles:
            new_tris = [i for i in range(len(e.model.vertices))]

        else:
            new_tris = list()
            for t in e.model.triangles:
                if isinstance(t, int):
                    new_tris.append(t)
                elif len(t) == 3:
                    new_tris.extend(t)
                elif len(t) == 4: # turn quad into tris
                    new_tris.extend([t[0], t[1], t[2], t[2], t[3], t[0]])

        new_tris = [t+o for t in new_tris]
        new_tris = [(new_tris[i], new_tris[i+1], new_tris[i+2]) for i in range(0, len(new_tris), 3)]

        o += len(e.model.vertices)
        tris += new_tris

        if e.model.uvs: uvs += e.model.uvs

        if e.model.colors: # if has vertex colors
            cols.extend(e.model.colors)
        else:
            cols.extend((e.color, ) * len(e.model.vertices))

        to_destroy.append(e)

    if destroy_after:
        [destroy(e) for e in to_destroy]

    parent.model = Mesh(vertices=verts, triangles=tris, normals=norms, uvs=uvs, colors=cols, mode='triangle')
    print('combined')

    return parent