"""Original practical fixtures, contact detail and regional RGB lighting.

Blender authoring only. The baseline character studio is restored between
models; regional material copies never modify the shared body datablocks.
"""
import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

import reference_models

ROOT = Path(__file__).resolve().parents[1]


def signatures():
    return json.loads((ROOT / 'static/lighting-signatures.json').read_text())


def configure(scene, settings, region=None):
    """Use the same projection and light direction for every regional bake."""
    base = settings['light']
    profile = settings.get('lighting_signatures', {}).get('profiles', {}).get(region)
    sun = bpy.data.objects['Hard fixed sunlight'].data
    fill = bpy.data.objects['Broad neutral bounced fill'].data
    background = scene.world.node_tree.nodes['Background']
    sun.energy = profile['sun']['energy'] if profile else base['sun_energy']
    sun.color = profile['sun']['color'] if profile else (1, 1, 1)
    fill.energy = profile['fill']['energy'] if profile else base['fill_energy']
    fill.color = profile['fill']['color'] if profile else (1, 1, 1)
    background.inputs['Color'].default_value = (*(profile['ambient']['color'] if profile else base['ambient_color']), 1)
    background.inputs['Strength'].default_value = profile['ambient']['strength'] if profile else base['ambient_strength']


def surface(source, region, texture=False):
    """Keep actual roughness, microrelief and recess shading in the baked art."""
    material = source.copy()
    material.name = 'Spectrum / ' + region + ' / ' + source.name
    if not material.use_nodes:
        return material
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get('Principled BSDF')
    if not shader:
        return material
    name = source.name.lower()
    metal = shader.inputs['Metallic'].default_value > .25
    glass = 'glass' in name
    timber = 'wood' in name
    cloth = any(n in name for n in ('cloth', 'canvas', 'coat'))
    rough = .29 if glass else .42 if metal else .76 if timber else .91
    if cloth:
        rough = .90
    shader.inputs['Roughness'].default_value = rough
    shader.inputs['Coat Weight'].default_value = .26 if glass else .16 if metal and region == 'CITY_CLOUD_S' else .04 if timber else 0
    shader.inputs['Coat Roughness'].default_value = .24
    if texture:
        # Terrain already uses periodic object-coordinate noise. Preserve its
        # period instead of adding a new nonperiodic moisture pattern.
        noise = next((n for n in nodes if n.type == 'TEX_NOISE'), None)
    else:
        noise = nodes.new('ShaderNodeTexNoise')
        noise.label = 'Pitted metal / handled timber / mineral microrelief'
        noise.inputs['Scale'].default_value = 72 if metal else 48
        noise.inputs['Detail'].default_value = 4
        coords = nodes.new('ShaderNodeTexCoord')
        links.new(coords.outputs['Generated'], noise.inputs['Vector'])
    if noise:
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.label = 'Physical roughness variation'
        ramp.color_ramp.elements[0].position = .25
        ramp.color_ramp.elements[0].color = (max(.15, rough - .17),) * 3 + (1,)
        ramp.color_ramp.elements[1].position = .75
        ramp.color_ramp.elements[1].color = (min(.98, rough + .12),) * 3 + (1,)
        links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], shader.inputs['Roughness'])
        if not texture and not glass:
            bump = nodes.new('ShaderNodeBump')
            bump.label = 'Secondary physical surface relief'
            bump.inputs['Strength'].default_value = .16
            bump.inputs['Distance'].default_value = .002 if metal else .004
            if shader.inputs['Normal'].is_linked:
                links.new(shader.inputs['Normal'].links[0].from_socket, bump.inputs['Normal'])
            links.new(noise.outputs['Fac'], bump.inputs['Height'])
            links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    if not texture and shader.inputs['Base Color'].is_linked:
        original = shader.inputs['Base Color'].links[0].from_socket
        ao = nodes.new('ShaderNodeAmbientOcclusion')
        ao.label = 'Recesses and construction contacts'
        ao.inputs['Distance'].default_value = .15
        ao.samples = 8
        mix = nodes.new('ShaderNodeMixRGB')
        mix.blend_type = 'MULTIPLY'
        mix.inputs[0].default_value = .20
        links.new(original, mix.inputs[1])
        links.new(ao.outputs['Color'], mix.inputs[2])
        links.new(mix.outputs['Color'], shader.inputs['Base Color'])
    return material


def emitter_material(studio, region, kind, color, secondary=False):
    name = 'Spectrum emitter / ' + region + ' / ' + kind + (' / secondary' if secondary else ' / primary')
    if name not in studio.MATERIALS:
        studio.material(name, color, metal=.12, roughness=.24, glow=5.5)
    return name


def practical(studio, region, kind, pos, secondary=False):
    """A physical shield, lens and casting point light share one position."""
    s = reference_models.fast(studio)
    profile = studio.CFG['lighting_signatures']['profiles'][region]
    color = profile['secondary' if secondary else 'primary']
    mat = emitter_material(studio, region, kind, color, secondary)
    x, y, z = pos
    if region in ('WN_TOWER', 'ENACT_HILLS'):
        s.cube('Spectrum / shielded hearth housing', (x, y + .028, z), (.16, .09, .20), 'ref_metal', bevel=.018)
        s.sphere('Spectrum / frosted practical lens', (x, y - .027, z), (.050, .028, .065), mat)
        for dz in [-.075, .075]:
            s.beam('Spectrum / lens guard', (x-.067, y-.046, z+dz), (x+.067, y-.046, z+dz), .008, 'ref_metal')
    elif region == 'CITY_CLOUD_S':
        s.cube('Spectrum / replaceable node housing', (x, y+.022, z), (.22, .08, .14), 'ref_metal', bevel=.012)
        for dx in [-.070, -.023, .023, .070]:
            s.cube('Spectrum / isolated luminous register', (x+dx, y-.029, z), (.022, .014, .082), mat, bevel=.005)
        for dx in [-.097, .097]:
            s.sphere('Spectrum / housing fastener', (x+dx, y-.033, z), (.007, .006, .007), 'ref_metal')
    else:
        s.cylinder('Spectrum / crystal socket', (x, y, z-.045), .058, .05, 'ref_metal')
        obj=s.object('Spectrum / prismatic lightPROKT lens', [(-.055,-.035,-.05),(.055,-.035,-.05),(0,.045,-.05),(0,0,.13)], [(0,1,2),(0,3,1),(1,3,2),(2,3,0)], pos, mat, bevel=.006)
    data = bpy.data.lights.new('Spectrum / ' + kind + ' / practical', 'POINT')
    data.energy = profile['practical_energy'] * (.62 if secondary else 1)
    data.color = color
    data.shadow_soft_size = .08
    lamp = bpy.data.objects.new(data.name, data)
    bpy.context.collection.objects.link(lamp)
    lamp.location = (x, y-.09, z)
    lamp['emission_material'] = mat
    return {'position': [x, y-.04, z], 'color': color, 'radius': 57 if secondary else 74,
            'intensity': .66 if secondary else 1, 'portable': region in ('WN_TOWER', 'ENACT_HILLS') and kind in ('shelter', 'exchange')}, lamp


def refine(studio, catalog):
    """Apply once to a complete source catalog; no body or camera edits."""
    if any('lighting_signature' in r for r in catalog['models'].values()):
        raise ValueError('Spectrum refinements already exist in this source')
    studio.CFG['lighting_signatures'] = signatures()
    cache = {}
    scene = bpy.context.scene
    placements = {'workshop': (-.70,-.43,.93), 'shelter': (-.42,-.59,.68),
                  'exchange': (-.79,-.88,.99), 'water': (-.25,-.38,.83),
                  'power': (-.14,-.30,.49), 'relay': (-.31,-.19,.64), 'garden': (-.51,-.37,.31)}
    for name, record in catalog['models'].items():
        if record['camera_kind'] == 'character':
            continue
        region = next(r for r in catalog['visual_catalog']['regions'] if name.endswith('_'+r))
        col = reference_models.activate(studio, name)
        for obj in list(col.objects):
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                if not slot.material:
                    continue
                key = (slot.material.name, region, record['kind']=='texture')
                if key not in cache:
                    cache[key] = surface(slot.material, region, record['kind']=='texture')
                slot.material = cache[key]
        record.update(lighting_signature=region, samples=96, supersample=2, adaptive_threshold=.035, adaptive_min_samples=24)
        record['practicals'] = []
        kind = name.rsplit('_'+region,1)[0]
        if kind not in placements:
            continue
        fixture, lamp = practical(studio, region, kind, placements[kind])
        fixtures = [(fixture, lamp)]
        if kind in ('workshop','exchange','relay') and region in ('CITY_CLOUD_S','AETHERGALE'):
            fixtures.append(practical(studio, region, kind, (.64,-.29,.68 if kind=='relay' else 1.03), secondary=True))
        studio.camera(scene, record['camera_kind'], record['supersample'])
        w, h = record['size']
        scale = studio.CFG['camera'][record['camera_kind']]['runtime_scale']
        for fixture, lamp in fixtures:
            uv=world_to_camera_view(scene,scene.camera,Vector(fixture.pop('position')))
            fixture['offset']=[round((uv.x*w-record['anchor'][0])*scale,4), round(((1-uv.y)*h-record['anchor'][1])*scale,4)]
            fixture['ground_offset']=[fixture['offset'][0],3]
            record['practicals'].append(fixture)
            # Baked light is deliberately weaker on a damaged/isolate frame.
            idle=set(record['clips']['idle'])
            energy=lamp.data.energy
            emission=bpy.data.materials[lamp['emission_material']].node_tree.nodes['Principled BSDF'].inputs['Emission Strength']
            for i,frame in enumerate(record['timeline_frames']):
                lamp.data.energy=energy if i in idle else energy*.12
                lamp.data.keyframe_insert('energy',frame=frame)
                emission.default_value=5.5 if i in idle else .30
                emission.keyframe_insert('default_value',frame=frame)
            for curve in lamp.data.animation_data.action.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation='CONSTANT'
    configure(scene, studio.CFG)
    studio.camera(scene,'character',studio.CFG['render']['supersample'])
    scene.frame_set(1)
