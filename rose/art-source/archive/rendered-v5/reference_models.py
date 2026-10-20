"""Original Rose environment refinements guided by the supplied prefab indexes.

No pixels or meshes are imported from the reference sheets. Body materials and
studio lights are deliberately independent of these environment materials.
"""
import math
import random


REGIONS=('WN_TOWER','CITY_CLOUD_S','ENACT_HILLS','AETHERGALE')


class FastStudio:
    """Build repeated scenery directly; avoid whole-scene operator updates."""
    def __init__(self,source):self.source=source;self.templates={}
    def __getattr__(self,name):return getattr(self.source,name)
    def object(self,name,vertices,faces,pos,mat,parent=None,bevel=0):
        data=self.bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
        obj=self.bpy.data.objects.new(name,data);self.bpy.context.collection.objects.link(obj);obj.location=pos
        return self.finish(obj,name,mat,parent,bevel)
    def cube(self,name,pos,size,mat,parent=None,bevel=.025):
        x,y,z=[v/2 for v in size]
        return self.object(name,[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],pos,mat,parent,bevel)
    def template(self,kind):
        if kind not in self.templates:
            if kind=='sphere':self.bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1)
            else:self.bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1)
            obj=self.bpy.context.object;self.templates[kind]=obj.data
            self.bpy.data.objects.remove(obj,do_unlink=True)
        return self.templates[kind]
    def rounded(self,kind,name,pos,size,mat,parent=None):
        data=self.template(kind).copy();obj=self.bpy.data.objects.new(name,data);self.bpy.context.collection.objects.link(obj)
        obj.location=pos;obj.scale=size
        for face in data.polygons:face.use_smooth=True
        return self.finish(obj,name,mat,parent)
    def sphere(self,name,pos,size,mat,parent=None):return self.rounded('sphere',name,pos,size,mat,parent)
    def cylinder(self,name,pos,radius,depth,mat,parent=None,vertices=16,rotation=None):
        pts=[(radius*math.cos(i*math.tau/vertices),radius*math.sin(i*math.tau/vertices),z) for z in [-depth/2,depth/2] for i in range(vertices)]
        faces=[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]+[tuple(reversed(range(vertices))),tuple(range(vertices,2*vertices))]
        obj=self.object(name,pts,faces,pos,mat,parent,.012)
        if rotation:obj.rotation_euler=rotation
        return obj
    def beam(self,name,start,end,radius,mat,parent=None):
        from mathutils import Vector
        a,b=Vector(start),Vector(end);obj=self.cylinder(name,(a+b)/2,radius,(b-a).length,mat,parent,vertices=10)
        obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return obj


_FAST={}
def fast(s):
    if isinstance(s,FastStudio):return s
    if id(s) not in _FAST:_FAST[id(s)]=FastStudio(s)
    return _FAST[id(s)]


def materials(s):
    recipes={'ref_wood':((.22,.165,.10),0,.84),'ref_metal':((.19,.205,.18),.58,.49),
             'ref_stone':((.24,.235,.195),0,.95),'ref_plaster':((.40,.355,.265),0,.94),
             'ref_canvas':((.32,.275,.20),0,.94),'ref_rust':((.23,.11,.055),.15,.89),
             'ref_clay':((.285,.205,.12),0,.94),'ref_glass':((.055,.08,.073),.35,.26)}
    for name,(color,metal,roughness) in recipes.items():
        mat=s.material(name,color,metal=metal,roughness=roughness,grain=.25)
        nodes,links=mat.node_tree.nodes,mat.node_tree.links;shader=nodes.get('Principled BSDF')
        coord=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY'
        mapping.inputs[1].default_value=(1.4,1.4,.10) if name=='ref_wood' else (1,1,.55)
        links.new(coord.outputs['Generated'],mapping.inputs[0])
        noise=nodes.new('ShaderNodeTexNoise');noise.label='Localized handled wear and moisture';noise.inputs['Scale'].default_value=17 if name=='ref_wood' else 7;noise.inputs['Detail'].default_value=5
        links.new(mapping.outputs['Vector'],noise.inputs['Vector'])
        ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.23;ramp.color_ramp.elements[0].color=tuple(c*.38 for c in color)+(1,)
        ramp.color_ramp.elements[1].position=.76;ramp.color_ramp.elements[1].color=tuple(min(1,c*1.45) for c in color)+(1,)
        links.new(noise.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
        bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.30;bump.inputs['Distance'].default_value=.010 if name!='ref_glass' else .001
        links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])


def activate(s,name):
    col=s.COLLECTIONS[name];s.bpy.context.view_layer.active_layer_collection=s.bpy.context.view_layer.layer_collection.children[col.name]
    return col


def broken_stone(s,name,pos,size,rng,material='ref_stone',parent=None):
    s=fast(s);obj=s.rounded('ico',name,pos,size,material,parent)
    for v in obj.data.vertices:v.co*=rng.uniform(.87,1.10)
    obj.scale=size;obj.rotation_euler=(rng.uniform(-.15,.15),rng.uniform(-.15,.15),rng.random()*math.tau)
    for f in obj.data.polygons:f.use_smooth=True
    return obj


def architecture(s,region,kind):
    s=fast(s)
    col=activate(s,kind+'_'+region);rng=random.Random(902+sum(map(ord,region+kind)))
    swaps={'metal':'ref_metal','brass':'ref_metal','wood':'ref_wood','plaster':'ref_plaster','stone':'ref_stone','concrete':'ref_stone','canvas':'ref_canvas','rust':'ref_rust'}
    for obj in list(col.objects):
        if obj.type!='MESH':continue
        for slot in obj.material_slots:
            if slot.material and slot.material.name in swaps:slot.material=s.MATERIALS[swaps[slot.material.name]]
        # Break the perfectly regular platform perimeter into an eroded apron.
        if 'plinth' in obj.name.lower():
            if len(obj.data.vertices)==8:
                for v in obj.data.vertices:
                    v.co.x+=rng.uniform(-.027,.027);v.co.y+=rng.uniform(-.027,.027)
    if kind in ('workshop','shelter','exchange'):
        if kind=='workshop':
            # Individual cladding projects in front of the existing shell.
            for side in ('front','side'):
                for row in range(6):
                    for column in range(5 if side=='front' else 3):
                        if side=='front' and column>=3 and row<4:continue
                        z=.20+row*.19
                        if region=='WN_TOWER':
                            size=(.30,.033,.165) if side=='front' else (.033,.30,.165);mat='ref_wood'
                        elif region=='CITY_CLOUD_S':
                            size=(.29,.023,.17) if side=='front' else (.023,.29,.17);mat='ref_metal'
                        else:
                            size=(.30,.035,.16) if side=='front' else (.035,.30,.16);mat='ref_plaster' if region=='ENACT_HILLS' else 'ref_stone'
                        pos=(-.63+column*.30+(.06 if row%2 else 0),-.274,z) if side=='front' else (.815,-.07+column*.29,z)
                        obj=s.cube('Reference / fitted weathered cladding',pos,size,mat,bevel=.009)
                        obj.rotation_euler.y=rng.uniform(-.012,.012)
            # Window glass, recess, upper hood and independent sill.
            s.cube('Reference / smoked window pane',(-.41,-.383,.96),(.36,.012,.27),'ref_glass',bevel=.003)
            s.beam('Reference / window rain hood',(-.67,-.39,1.16),(-.15,-.39,1.16),.026,'ref_metal')
            for i in range(4):s.cube('Reference / roof repair patch',(-.71+i*.39,.50,1.568),(.32,.29,.014),'ref_rust',bevel=.006)
            s.cylinder('Reference / service drum',(-.92,.45,.38),.16,.48,'ref_metal',vertices=24)
            for z in [.20,.44,.62]:s.cylinder('Reference / drum hoop',(-.92,.45,z),.167,.025,'ref_rust',vertices=24)
            for i in range(3):s.cube('Reference / loose bench tools',(-.40+i*.08,-.69,.59),(.055,.18,.023),'ref_metal',bevel=.006)
        elif kind=='exchange':
            for i in range(9):
                x=-.84+i*.21;s.cube('Reference / counter face boards',(x,-.835,.48),(.19,.026,.68),'ref_wood',bevel=.009)
                for z in [.21,.74]:s.sphere('Reference / counter nail',(x,-.854,z),(.007,.005,.007),'ref_metal')
            for x in [-.65,.05,.68]:
                s.cube('Reference / labeled stock wrapping',(x,-.51,1.16),(.22,.15,.085),'ref_canvas',bevel=.012)
                s.beam('Reference / binding twine',(x,-.585,1.17),(x,-.44,1.17),.008,'ref_wood')
        else:
            for i in range(5):
                y=-.57+i*.27;s.beam('Reference / hand repaired shelter batten',(-.92,y,.29),(-.92,y,1.07),.018,'ref_wood')
            s.cube('Reference / folded entrance blanket',(.55,-.73,.18),(.35,.25,.085),'ref_canvas',bevel=.035)
        # Scuffs and irregular rubble belong to the registered building apron.
        for i in range(11):
            x=rng.uniform(-.92,.92);y=rng.choice([rng.uniform(-.91,-.76),rng.uniform(.63,.76)])
            broken_stone(s,'Reference / apron aggregate',(x,y,.11),(rng.uniform(.025,.065),rng.uniform(.022,.055),.015),rng,'ref_clay' if region=='ENACT_HILLS' else 'ref_stone')
    elif kind=='water':
        for z in [.33,.71,1.09]:
            for i in range(12):
                a=i*math.tau/12
                s.sphere('Reference / flaked tank finish',(math.cos(a)*.49,math.sin(a)*.35,z),(.018,.009,.037),'ref_rust')
        s.beam('Reference / external tank pipe',(-.44,-.25,.30),(-.44,-.25,.78),.025,'ref_metal')
    elif kind in ('relay','power'):
        for i in range(4):s.cube('Reference / service grille',(-.15+i*.095,-.265,.36),(.037,.014,.15),'dark',bevel=.003)
        for i in range(4):s.beam('Reference / bolted service seam',(-.25,-.282,.23+i*.04),(.24,-.282,.23+i*.04),.004,'ref_rust')
    elif kind=='garden':
        for i in range(16):
            x,y=rng.uniform(-.85,.85),rng.uniform(-.5,.5)
            broken_stone(s,'Reference / dark cultivated soil',(x,y,.20),(.03,.04,.01),rng,'ref_wood')


def obstacle(s,region):
    s=fast(s)
    col=activate(s,'rock_'+region);rng=random.Random(781+sum(map(ord,region)))
    for obj in list(col.objects):
        if obj.name.startswith('Weathered stone'):s.bpy.data.objects.remove(obj,do_unlink=True)
    for x,y,r in [(-.24,.10,.49),(.31,.04,.33),(-.50,-.26,.21)]:
        broken_stone(s,'Reference / eroded stone',(x,y,r*.38),(r*1.21,r,r*.70),rng)
    for i in range(10):
        x,y=rng.uniform(-.63,.65),rng.uniform(-.38,.36)
        broken_stone(s,'Reference / stone scree',(x,y,.035),(.055,.035,.018),rng)


def floor_material(s,region,path=False):
    color={'WN_TOWER':(.145,.155,.10),'CITY_CLOUD_S':(.145,.145,.13),'ENACT_HILLS':(.215,.17,.108),'AETHERGALE':(.185,.19,.17)}[region]
    if path:color=tuple(c*1.22 for c in color)
    name='ref_floor_'+('path_' if path else '')+region;mat=s.material(name,color,roughness=.97,grain=.16)
    nodes,links=mat.node_tree.nodes,mat.node_tree.links;shader=nodes.get('Principled BSDF')
    coord=nodes.new('ShaderNodeTexCoord')
    def trig(vector,period,operation):
        dot=nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=vector;links.new(coord.outputs['Object'],dot.inputs[0])
        mul=nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=math.tau/period;links.new(dot.outputs['Value'],mul.inputs[0])
        node=nodes.new('ShaderNodeMath');node.operation=operation;links.new(mul.outputs[0],node.inputs[0]);return node.outputs[0]
    u=(math.sqrt(.5),math.sqrt(.5),0);v=(math.sqrt(.5),-math.sqrt(.5),0)
    xyz=nodes.new('ShaderNodeCombineXYZ')
    links.new(trig(u,2,'SINE'),xyz.inputs[0]);links.new(trig(u,2,'COSINE'),xyz.inputs[1]);links.new(trig(v,2.5/.52,'SINE'),xyz.inputs[2])
    noise=nodes.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=18;noise.inputs['Detail'].default_value=4
    links.new(xyz.outputs[0],noise.inputs['Vector']);links.new(trig(v,2.5/.52,'COSINE'),noise.inputs['W'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=tuple(c*.53 for c in color)+(1,)
    ramp.color_ramp.elements[1].position=.84;ramp.color_ramp.elements[1].color=tuple(c*1.27 for c in color)+(1,)
    links.new(noise.outputs['Fac'],ramp.inputs['Fac']);links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.006
    links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    return name


def ground(s,region,path=False,replace=False):
    s=fast(s)
    name='ground_'+('path_' if path else '')+region
    if replace:
        col=activate(s,name)
        for obj in list(col.objects):s.bpy.data.objects.remove(obj,do_unlink=True)
    else:s.collection(name)
    mat=floor_material(s,region,path);s.cube('Reference / continuous terrain relief',(0,0,-.10),(14,14,.20),mat,bevel=0)
    rng=random.Random(443+sum(map(ord,region))+int(path)*191)
    # Repeat physical grit in the camera's screen basis, matching its sample
    # period. Details are small enough to support actors rather than compete.
    for i in range(18 if not path else 12):
        u,v=rng.uniform(-1,1),rng.uniform(-2.5/.52/2,2.5/.52/2)
        for du in [-2,0,2]:
            for dv in [-2.5/.52,0,2.5/.52]:
                x=(u+du+v+dv)*math.sqrt(.5);y=(u+du-v-dv)*math.sqrt(.5)
                if region=='WN_TOWER' and not path and i%3==0:
                    leaf=s.sphere('Reference / fine decomposing leaf',(x,y,.009),(.055,.025,.005),'ref_wood');leaf.rotation_euler.z=i*.89
                elif region=='CITY_CLOUD_S' and path:
                    s.cube('Reference / worn paving fragment',(x,y,.006),(.10,.075,.011),'ref_stone',bevel=.006)
                else:s.sphere('Reference / mineral aggregate',(x,y,.007),(.017+i%3*.006,.014,.005),'ref_clay' if region=='ENACT_HILLS' else 'ref_stone')
