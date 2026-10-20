"""Add transparent scenery margin and prove the six body sources are unchanged."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parent))
import render_blender as studio


def value(v):
    if isinstance(v,(str,bool,int,float)) or v is None:return v
    return [value(x) for x in v]


def material_record(mat):
    nodes=[]
    allowed={'BSDF_PRINCIPLED','OUTPUT_MATERIAL','TEX_NOISE','VALTORGB','BUMP','MIX_RGB'}
    for node in mat.node_tree.nodes:
        if node.type not in allowed:raise ValueError('Reuse fingerprint does not support '+node.type)
        record=dict(name=node.name,type=node.type,inputs={i.identifier:value(i.default_value) for i in node.inputs if hasattr(i,'default_value')})
        for attr in ['noise_dimensions','normalize','blend_type','use_clamp','distribution','subsurface_method']:
            if hasattr(node,attr):record[attr]=value(getattr(node,attr))
        if hasattr(node,'color_ramp'):
            ramp=node.color_ramp;record['ramp']=[ramp.color_mode,ramp.interpolation,ramp.hue_interpolation,[(e.position,list(e.color)) for e in ramp.elements]]
        nodes.append(record)
    links=[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in mat.node_tree.links]
    return dict(nodes=sorted(nodes,key=lambda n:n['name']),links=sorted(links))


def fingerprint(model,catalog):
    objects=[]
    for obj in sorted(bpy.data.collections[model].objects,key=lambda o:o.name):
        r=dict(name=obj.name,type=obj.type,parent=obj.parent.name if obj.parent else None,
               location=list(obj.location),rotation=list(obj.rotation_euler),scale=list(obj.scale),
               parent_inverse=[list(row) for row in obj.matrix_parent_inverse],modifiers=[])
        for mod in obj.modifiers:
            if mod.type not in {'BEVEL','WEIGHTED_NORMAL'}:raise ValueError('Unsupported reuse modifier')
            r['modifiers'].append({a:value(getattr(mod,a)) for a in ['type','width','segments','limit_method','angle_limit','weight','keep_sharp','mode'] if hasattr(mod,a)})
        if obj.type=='MESH':
            r['vertices']=[list(v.co) for v in obj.data.vertices]
            r['polygons']=[(list(p.vertices),p.material_index,p.use_smooth) for p in obj.data.polygons]
            r['materials']=[material_record(m) for m in obj.data.materials]
        animation=obj.animation_data
        if animation and animation.drivers:raise ValueError('Drivers require a fresh bake')
        if animation and animation.action:
            r['curves']=[dict(path=c.data_path,index=c.array_index,extrapolation=c.extrapolation,
                              keys=[(list(k.co),k.interpolation,list(k.handle_left),list(k.handle_right),k.handle_left_type,k.handle_right_type) for k in c.keyframe_points]) for c in animation.action.fcurves]
        objects.append(r)
    cfg=catalog['settings'];scene=bpy.context.scene
    light=bpy.data.objects['Hard fixed sunlight'];floor=bpy.data.objects['Shadow catcher / never changes registration']
    record=dict(objects=objects,camera={**cfg['camera']['character'],'azimuth':cfg['camera']['azimuth_degrees'],'compression':cfg['camera']['ground_compression'],'distance':cfg['camera']['distance']},
                render=cfg['render'],animations=cfg['animations'],projection=catalog['projection'],
                light=[list(light.location),list(light.rotation_euler),light.data.energy,light.data.angle,list(light.data.color)],
                ambient=[value(i.default_value) for i in scene.world.node_tree.nodes['Background'].inputs],
                floor=[list(floor.location),material_record(floor.data.materials[0])],
                view=[scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure,scene.view_settings.gamma])
    return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def main():
    source=studio.ROOT/'art-source/Rose-prefabs.blend';old=studio.ROOT/'art-source/body-bake-v3.blend'
    if old.exists():raise ValueError('Body bake archive already exists; do not overwrite it')
    shutil.copy2(source,old);old_sha=hashlib.sha256(old.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1)
    catalog=json.loads(bpy.data.texts['Rose sprite catalog.json'].as_string())
    bodies=[k for k,r in catalog['models'].items() if r['camera_kind']=='character']
    before={k:fingerprint(k,catalog) for k in bodies}
    cfg=catalog['settings'];cfg['camera']['texture']=dict(cfg['camera']['environment'])
    cfg['camera']['environment']={**cfg['camera']['environment'],'size':[192,224],'ortho_scale':7.0}
    studio.CFG=cfg
    for model,record in catalog['models'].items():
        kind='texture' if model.startswith('ground_') else record['camera_kind']
        record['camera_kind']=kind;record['size']=cfg['camera'][kind]['size'];record['anchor']=studio.camera(scene,kind,cfg['render']['supersample'])
    studio.camera(scene,'character',cfg['render']['supersample'])
    after={k:fingerprint(k,catalog) for k in bodies}
    if before!=after:raise ValueError('Reframing changed a body render dependency')
    for k in bodies:catalog['models'][k]['dependency_sha256']=after[k]
    text=json.dumps(catalog,indent=2)+'\n';bpy.data.texts['Rose sprite catalog.json'].clear();bpy.data.texts['Rose sprite catalog.json'].write(text)
    bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
    (studio.ROOT/'art-source/render-catalog.json').write_text(text)
    (studio.ROOT/'art-source/render-settings.json').write_text(json.dumps(cfg,indent=2)+'\n')
    proof=dict(schema=1,original_body_source_sha256=old_sha,current_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               comparison='Mesh vertices/faces, transforms, modifiers, material nodes/links, pose curves, body camera, sampling, light, ambient, shadow floor and color management.',
               models={k:dict(before=before[k],after=after[k]) for k in bodies})
    (studio.ROOT/'art-source/body-reuse-proof-v3.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('ROSE: expanded scenery margins at the original 32 pixels per world unit; six body dependencies unchanged.',flush=True)


if __name__=='__main__':main()
