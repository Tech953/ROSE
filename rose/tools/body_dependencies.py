"""Fail-closed fingerprint of the saved body bake and its studio dependencies."""
import hashlib
import json
import bpy


def value(v):
    if isinstance(v,(str,bool,int,float)) or v is None:return v
    return [value(x) for x in v]


def material_record(mat):
    nodes=[]
    allowed={'BSDF_PRINCIPLED','OUTPUT_MATERIAL','TEX_NOISE','VALTORGB','BUMP','MIX_RGB','TEX_COORD','VECT_MATH','TEX_WAVE'}
    for node in mat.node_tree.nodes:
        if node.type not in allowed:raise ValueError('Unsupported body material node: '+node.type)
        r=dict(name=node.name,type=node.type,inputs={i.identifier:value(i.default_value) for i in node.inputs if hasattr(i,'default_value')})
        for attr in ['noise_dimensions','normalize','blend_type','use_clamp','distribution','subsurface_method','operation','wave_type','wave_profile','bands_direction','rings_direction','from_instancer']:
            if hasattr(node,attr):r[attr]=value(getattr(node,attr))
        if node.type=='TEX_COORD' and node.object:raise ValueError('External texture coordinates require a fresh bake')
        if hasattr(node,'color_ramp'):
            a=node.color_ramp;r['ramp']=[a.color_mode,a.interpolation,a.hue_interpolation,[(e.position,list(e.color)) for e in a.elements]]
        nodes.append(r)
    return dict(nodes=sorted(nodes,key=lambda n:n['name']),links=sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in mat.node_tree.links))


def object_record(obj):
    r=dict(name=obj.name,type=obj.type,parent=obj.parent.name if obj.parent else None,location=list(obj.location),rotation=list(obj.rotation_euler),scale=list(obj.scale),parent_inverse=[list(row) for row in obj.matrix_parent_inverse],modifiers=[])
    for mod in obj.modifiers:
        if mod.type not in {'BEVEL','WEIGHTED_NORMAL'}:raise ValueError('Unsupported body modifier: '+mod.type)
        r['modifiers'].append({a:value(getattr(mod,a)) for a in ['type','width','segments','limit_method','angle_limit','weight','keep_sharp','mode','show_render'] if hasattr(mod,a)})
    if obj.type=='MESH':
        r.update(vertices=[list(v.co) for v in obj.data.vertices],polygons=[(list(p.vertices),p.material_index,p.use_smooth) for p in obj.data.polygons],materials=[material_record(m) for m in obj.data.materials])
    animation=obj.animation_data
    if animation and animation.drivers:raise ValueError('Body drivers require a fresh bake')
    if animation and animation.action:
        r['curves']=[dict(path=c.data_path,index=c.array_index,extrapolation=c.extrapolation,keys=[(list(k.co),k.interpolation,list(k.handle_left),list(k.handle_right),k.handle_left_type,k.handle_right_type) for k in c.keyframe_points]) for c in animation.action.fcurves]
    return r


def fingerprint(model,catalog):
    cfg=catalog['settings'];scene=bpy.context.scene
    lights=[]
    for light in sorted((o for o in bpy.data.collections['Studio / fixed camera and light'].objects if o.type=='LIGHT'),key=lambda o:o.name):
        d=light.data;lights.append(dict(object=object_record(light),data={a:value(getattr(d,a)) for a in ['type','energy','angle','color','shape','size','size_y','use_shadow'] if hasattr(d,a)}))
    floor=bpy.data.objects['Shadow catcher / never changes registration']
    r=dict(objects=[object_record(o) for o in sorted(bpy.data.collections[model].objects,key=lambda o:o.name)],camera={**cfg['camera']['character'],'azimuth':cfg['camera']['azimuth_degrees'],'compression':cfg['camera']['ground_compression'],'distance':cfg['camera']['distance']},render=cfg['render'],animations=cfg['animations'],projection=catalog['projection'],lights=lights,ambient=[value(i.default_value) for i in scene.world.node_tree.nodes['Background'].inputs],floor=object_record(floor),floor_is_shadow_catcher=floor.is_shadow_catcher,view=[scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure,scene.view_settings.gamma])
    return hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest()
