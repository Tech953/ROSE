"""Original Rose meshes and keyframed prefabs. Run with Blender 4.2 LTS.

blender --background --factory-startup --python tools/render_blender.py -- --output build/art
This developer tool is independent of the game's Python runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / 'art-source/render-settings.json').read_text())
RNG = random.Random(CFG['seed'])
MATERIALS = {}
COLLECTIONS = {}
MODEL_OVERRIDE = None


def material(name, color, metal=0.0, roughness=0.8, grain=0.12, glow=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = roughness
    if name.startswith('skin'):
        shader.inputs['Subsurface Weight'].default_value = .035
        shader.inputs['Subsurface Radius'].default_value = (.9, .4, .2)
    if name in ('cloth','canvas','trousers','olive_coat','slate_coat','ochre_coat','burgundy_coat'):
        shader.inputs['Sheen Weight'].default_value = .22
    if glow:
        shader.inputs['Base Color'].default_value = (*color, 1)
        shader.inputs['Emission Color'].default_value = (*color, 1)
        shader.inputs['Emission Strength'].default_value = glow
    else:
        noise = nodes.new('ShaderNodeTexNoise')
        surface = CFG['materials']
        noise.inputs['Scale'].default_value = surface['grain_scale']
        noise.inputs['Detail'].default_value = 3
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.15
        ramp.color_ramp.elements[0].color = tuple(c * (1 - grain) for c in color) + (1,)
        ramp.color_ramp.elements[1].position = 0.85
        ramp.color_ramp.elements[1].color = tuple(min(1, c * (1 + grain)) for c in color) + (1,)
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = surface['bump_strength']
        bump.inputs['Distance'].default_value = .0015 if name.startswith('skin') else surface['bump_distance']
        weather = nodes.new('ShaderNodeTexNoise')
        weather.label = 'Broad worn surface / fixed object coordinates'
        weather.inputs['Scale'].default_value = surface['weather_scale']
        weather.inputs['Detail'].default_value = 2
        dirt = nodes.new('ShaderNodeMixRGB')
        dirt.blend_type = 'MULTIPLY'
        dirt.inputs[0].default_value = surface['weather_strength']
        links.new(weather.outputs['Color'], dirt.inputs[2])
        links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], dirt.inputs[1])
        links.new(dirt.outputs['Color'], shader.inputs['Base Color'])
        # Broad fabric wear and elongated grain remain visible after downsampling.
        if name=='wood' or name in ('cloth','canvas','trousers','olive_coat','slate_coat','ochre_coat','burgundy_coat','leather'):
            detail=nodes.new('ShaderNodeTexNoise');detail.label='Long wood grain' if name=='wood' else 'Uneven woven and handled cloth'
            detail.inputs['Scale'].default_value=7 if name=='wood' else 11
            detail.inputs['Detail'].default_value=4
            if name=='wood':
                coords=nodes.new('ShaderNodeTexCoord');stretch=nodes.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(5,5,.22)
                links.new(coords.outputs['Generated'],stretch.inputs[0]);links.new(stretch.outputs['Vector'],detail.inputs['Vector'])
            detail_color=nodes.new('ShaderNodeValToRGB');detail_color.color_ramp.elements[0].position=.24;detail_color.color_ramp.elements[0].color=(.45,.40,.33,1);detail_color.color_ramp.elements[1].position=.76;detail_color.color_ramp.elements[1].color=(1,1,1,1)
            textured=nodes.new('ShaderNodeMixRGB');textured.blend_type='MULTIPLY';textured.inputs[0].default_value=.56 if name=='wood' else .45
            links.new(detail.outputs['Fac'],detail_color.inputs['Fac']);links.new(detail_color.outputs['Color'],textured.inputs[2]);links.new(dirt.outputs['Color'],textured.inputs[1]);links.new(textured.outputs['Color'],shader.inputs['Base Color'])
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        if name == 'wood' or name in ('cloth','canvas','trousers','olive_coat','slate_coat','ochre_coat','burgundy_coat'):
            wave=nodes.new('ShaderNodeTexWave');wave.label='Directional wood grain' if name=='wood' else 'Fine woven fabric'
            wave.wave_type='BANDS';wave.bands_direction='Z' if name=='wood' else 'DIAGONAL'
            wave.inputs['Scale'].default_value=12 if name=='wood' else 145
            wave.inputs['Distortion'].default_value=3.4 if name=='wood' else .6
            wave.inputs['Detail'].default_value=3
            relief=nodes.new('ShaderNodeMixRGB');relief.blend_type='MIX';relief.inputs[0].default_value=.38
            links.new(noise.outputs['Fac'],relief.inputs[1]);links.new(wave.outputs['Color'],relief.inputs[2]);links.new(relief.outputs['Color'],bump.inputs['Height'])
        links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    MATERIALS[name] = mat
    return mat


def finish(obj, name, mat, parent=None, bevel=0.0):
    obj.name = name
    if mat:
        obj.data.materials.append(MATERIALS[mat])
    if parent:
        obj.parent = parent
    if bevel:
        modifier = obj.modifiers.new('Worn edges', 'BEVEL')
        modifier.width, modifier.segments = bevel, 3
        obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
    return obj


def cube(name, pos, size, mat, parent=None, bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    obj = finish(bpy.context.object, name, mat, parent, bevel)
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def sphere(name, pos, size, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=pos)
    obj = finish(bpy.context.object, name, mat, parent)
    obj.scale = size
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def cylinder(name, pos, radius, depth, mat, parent=None, vertices=16, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=pos)
    obj = finish(bpy.context.object, name, mat, parent, 0.012)
    if rotation:
        obj.rotation_euler = rotation
    return obj


def beam(name, start, end, radius, mat, parent=None):
    a, b = Vector(start), Vector(end)
    obj = cylinder(name, (a + b) / 2, radius, (b - a).length, mat, parent, vertices=10)
    obj.rotation_euler = (b - a).to_track_quat('Z', 'Y').to_euler()
    return obj


def mesh(name, verts, faces, mat, parent=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, mat, parent, 0.012)


def empty(name, pos=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent, obj.location = parent, pos
    obj.empty_display_type = 'PLAIN_AXES'
    obj.empty_display_size = 0.14
    return obj


def collection(name):
    name = MODEL_OVERRIDE or name
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[name]
    COLLECTIONS[name] = c
    return c


def panel(name, pos, size, mat='metal', parent=None):
    obj = cube(name, pos, size, mat, parent)
    for side in (-1, 1):
        for height in (-1, 1):
            sphere(name + ' rivet', (pos[0] + side * size[0] * 0.37, pos[1] - size[1] / 2 - 0.013,
                                    pos[2] + height * size[2] * 0.34), (0.025, 0.012, 0.025), 'brass', parent)
    return obj


def traveler():
    collection('traveler')
    root = empty('Traveler / facing and foot origin')
    body = empty('Body / breath and lean', (0, 0, 0.99), root)
    cube('Travel coat', (0, 0, 0.27), (0.50, 0.30, 0.54), 'cloth', body, 0.065)
    sphere('Coat hem', (0, 0, -0.03), (0.30, 0.19, 0.15), 'cloth', body)
    panel('Breast plate', (0, -0.165, 0.28), (0.33, 0.05, 0.27), 'metal', body)
    cube('Rose seam', (0.08, -0.206, 0.28), (0.028, 0.017, 0.27), 'rose', body, 0.0)
    cube('Broad belt', (0, -0.01, 0.04), (0.51, 0.35, 0.065), 'leather', body, 0.015)
    for x in (-0.19, 0.02, 0.20):
        cube('Supply pouch', (x, -0.20, 0.015), (0.115, 0.11, 0.14), 'leather', body, 0.025)
        cube('Pouch buckle', (x, -0.26, 0.015), (0.032, 0.016, 0.04), 'brass', body, 0.005)
    cube('Field pack', (0, 0.25, 0.26), (0.42, 0.25, 0.48), 'leather', body, 0.055)
    cylinder('Rolled bed cloth', (0, 0.27, 0.55), 0.09, 0.51, 'canvas', body, rotation=(0, math.pi / 2, 0))
    cylinder('Water flask', (0.25, 0.16, 0.19), 0.075, 0.25, 'metal', body)
    head = empty('Head / conversation', (0, -0.01, 0.67), body)
    sphere('Hood shell', (0, 0.025, 0.04), (0.205, 0.19, 0.235), 'cloth', head)
    sphere('Face', (0, -0.113, 0.025), (0.142, 0.088, 0.16), 'skin', head)
    cube('Dark eyes', (0, -0.195, 0.06), (0.23, 0.021, 0.036), 'dark', head, 0.009)
    cube('Nano visor', (-0.08, -0.212, 0.065), (0.066, 0.015, 0.018), 'cyan', head, 0.004)
    sphere('Nose', (0, -0.211, 0.015), (0.035, 0.037, 0.047), 'skin', head)
    sphere('Chin', (0, -0.135, -0.095), (0.084, 0.08, 0.06), 'skin', head)
    joints = {'root': root, 'body': body, 'head': head}
    for side, x in [('L', -0.31), ('R', 0.31)]:
        shoulder = empty('Shoulder ' + side, (x, 0, 0.44), body)
        sphere('Shoulder armor ' + side, (0, 0, -0.05), (0.14, 0.18, 0.14), 'metal', shoulder)
        cylinder('Sleeve ' + side, (0, 0, -0.19), 0.09, 0.28, 'cloth', shoulder)
        elbow = empty('Elbow ' + side, (0, 0, -0.36), shoulder)
        cylinder('Forearm ' + side, (0, 0, -0.14), 0.075, 0.26, 'leather', elbow)
        sphere('Glove ' + side, (0, 0, -0.30), (0.09, 0.08, 0.10), 'leather', elbow)
        if side == 'R':
            beam('Walking tool', (0.015, -0.08, -0.63), (0.015, -0.08, 0.20), 0.025, 'wood', elbow)
            cube('Tool head', (0.015, -0.08, 0.18), (0.18, 0.065, 0.075), 'metal', elbow, 0.01)
            sphere('Tool core', (0.015, -0.115, 0.19), (0.035, 0.02, 0.027), 'cyan', elbow)
        hip = empty('Hip ' + side, (x * 0.46, 0, -0.08), body)
        cylinder('Thigh ' + side, (0, 0, -0.205), 0.115, 0.38, 'trousers', hip)
        knee = empty('Knee ' + side, (0, 0, -0.40), hip)
        sphere('Knee pad ' + side, (0, -0.035, 0), (0.115, 0.10, 0.10), 'metal', knee)
        cylinder('Boot shaft ' + side, (0, 0, -0.205), 0.105, 0.35, 'leather', knee)
        cube('Boot foot ' + side, (0, -0.075, -0.44), (0.23, 0.36, 0.115), 'leather', knee, 0.03)
        for key, obj in [('arm', shoulder), ('elbow', elbow), ('leg', hip), ('knee', knee)]:
            joints[key + side] = obj
    root['designation'] = 'Provisional traveler body; personal appearance and equipment stats remain separately registered.'
    return joints


def pose(j, name, phase):
    s = math.sin(phase * math.tau)
    j['body'].location = (0, 0, 0.99)
    j['body'].rotation_euler = (0, 0, 0)
    j['head'].rotation_euler = (0, 0, 0)
    for side in ('L', 'R'):
        for key in ('arm', 'elbow', 'leg', 'knee'):
            j[key + side].rotation_euler = (0, 0, 0)
        j['elbow' + side].rotation_euler.x = -0.13
    if name == 'idle':
        j['body'].location.z += 0.009 * s
        j['head'].rotation_euler.z = 0.025 * s
    elif name == 'walk':
        j['body'].location.z += 0.038 * abs(s)
        j['body'].rotation_euler.y = 0.035 * s
        for side, sign in [('L', 1), ('R', -1)]:
            j['leg' + side].rotation_euler.x = -0.43 * s * sign
            j['knee' + side].rotation_euler.x = max(0, s * sign) * 0.48
            j['arm' + side].rotation_euler.x = 0.28 * s * sign
            j['elbow' + side].rotation_euler.x = -0.22
    elif name == 'attack':
        sweep = math.sin(phase * math.pi)
        j['body'].rotation_euler.x = 0.16 * sweep
        j['body'].rotation_euler.z = -0.18 * sweep
        j['armR'].rotation_euler.x = -1.5 * sweep
        j['elbowR'].rotation_euler.x = -0.4 * sweep
        j['armL'].rotation_euler.x = -0.32 * sweep
    elif name == 'guard':
        j['body'].location.z -= 0.06
        j['armL'].rotation_euler.x = -0.7
        j['elbowL'].rotation_euler.x = -0.4
        j['armR'].rotation_euler.x = -0.45 - 0.03 * s
        j['elbowR'].rotation_euler.x = -0.1
    elif name == 'work':
        j['body'].rotation_euler.x = 0.25
        j['body'].location.z -= 0.06
        j['armR'].rotation_euler.x = -0.7 - 0.4 * s
        j['elbowR'].rotation_euler.x = -0.5
        j['armL'].rotation_euler.x = -0.4
    elif name == 'talk':
        j['head'].rotation_euler.z = 0.07 * s
        j['armL'].rotation_euler.x = -0.40 - 0.22 * s
        j['elbowL'].rotation_euler.x = -0.75
    elif name == 'hit':
        amount = math.sin(phase * math.pi)
        j['body'].rotation_euler.x = -0.32 * amount
        j['body'].location.y = 0.09 * amount
        j['armL'].rotation_euler.y = -0.23 * amount
        j['armR'].rotation_euler.y = 0.23 * amount
    elif name == 'down':
        j['body'].location = (0, 0, 0.18)
        j['body'].rotation_euler.x = -math.pi / 2
        j['armL'].rotation_euler.y = -0.5
        j['armR'].rotation_euler.y = 0.5


def base(name, size=(1.6, 1.4), height=0.13):
    cube(name + ' plinth', (0, 0, height / 2), (*size, height), 'concrete', bevel=0.045)
    for x in (-size[0] * 0.4, size[0] * 0.4):
        for y in (-size[1] * 0.4, size[1] * 0.4):
            cylinder('Foundation bolt', (x, y, height + 0.015), 0.033, 0.035, 'brass', vertices=8)


def power():
    collection('power'); base('Wind collector', (1.2, 1.0))
    panel('Battery enclosure', (0.28, 0.05, 0.38), (0.62, 0.55, 0.53))
    for x in (0.12, 0.25, 0.38):
        cube('Battery vent', (x, -0.24, 0.45), (0.05, 0.015, 0.15), 'dark', bevel=0)
    cylinder('Collector tower', (-0.25, 0.08, 1.49), 0.07, 2.72, 'metal')
    for x in (-0.65, 0.5):
        beam('Tower brace', (x, 0, 0.15), (-0.25, 0.08, 1.2), 0.023, 'metal')
    hub = empty('Collector rotor', (-0.25, -0.08, 2.56))
    sphere('Rotor cap', (0, -0.06, 0), (0.15, 0.16, 0.15), 'brass', hub)
    for a in (0, math.tau / 3, math.tau * 2 / 3):
        verts = []
        for r, z in [(0.10, -0.09), (0.98, -0.05), (0.84, 0.15), (0.23, 0.11)]:
            verts.append((r * math.cos(a) - z * math.sin(a), 0, r * math.sin(a) + z * math.cos(a)))
        mesh('Collector blade', verts, [(0, 1, 2, 3)], 'metal', hub)
    cube('Power indicator', (0.28, -0.244, 0.23), (0.12, 0.022, 0.035), 'cyan', bevel=0)
    return hub


def water():
    collection('water'); base('Water apparatus', (1.75, 1.55))
    cylinder('Cistern body', (-0.22, 0.15, 0.77), 0.49, 1.12, 'metal', vertices=32)
    for h in (0.28, 0.75, 1.23):
        cylinder('Cistern band', (-0.22, 0.15, h), 0.515, 0.055, 'brass', vertices=32)
    sphere('Domed cistern lid', (-0.22, 0.15, 1.34), (0.49, 0.49, 0.12), 'metal')
    panel('Filter housing', (0.56, 0.10, 0.48), (0.35, 0.42, 0.66))
    beam('Outlet', (-0.1, -0.25, 0.61), (0.52, -0.25, 0.61), 0.043, 'brass')
    beam('Tap', (0.52, -0.25, 0.61), (0.52, -0.25, 0.32), 0.043, 'brass')
    cube('Tank gauge', (-0.22, -0.346, 0.84), (0.075, 0.017, 0.51), 'dark', bevel=0.01)
    cube('Water gauge level', (-0.22, -0.363, 0.70), (0.04, 0.014, 0.25), 'cyan', bevel=0)
    for h in (0.65, 0.8, 0.95):
        cube('Gauge tick', (-0.14, -0.344, h), (0.025, 0.01, 0.012), 'canvas', bevel=0)


def garden():
    collection('garden'); base('Growing bed', (2.1, 1.6), 0.10)
    cube('Dark soil', (0, 0, 0.18), (1.97, 1.45, 0.16), 'soil')
    for x in (-1, 1):
        cube('Timber edge', (x, 0, 0.25), (0.09, 1.64, 0.32), 'wood')
    for y in (-0.77, 0.77):
        cube('Timber edge', (0, y, 0.25), (2.1, 0.09, 0.32), 'wood')
    for x in (-0.65, 0, 0.65):
        for y in (-0.4, 0.3):
            h = RNG.uniform(0.33, 0.51)
            beam('Living stem', (x, y, 0.24), (x, y, h + 0.25), 0.022, 'leaf')
            for a in (0, 2.1, 4.2):
                leaf = sphere('Broad leaf', (x + math.cos(a) * 0.15, y + math.sin(a) * 0.15, h + 0.22), (0.22, 0.08, 0.038), 'leaf')
                leaf.rotation_euler = (0, 0.4, a)
            sphere('Rose fruit', (x, y, h + 0.27), (0.07, 0.065, 0.07), 'rose')
    beam('Irrigation line', (-0.9, -0.58, 0.3), (0.9, -0.58, 0.3), 0.028, 'brass')


def shelter():
    collection('shelter'); base('Field shelter', (2.25, 1.9))
    # Separate roof faces provide the creased canvas silhouette, with no borrowed textures.
    verts = [(-1, -0.8, 0.18), (1, -0.8, 0.18), (0, -0.8, 1.68),
             (-1, 0.8, 0.18), (1, 0.8, 0.18), (0, 0.8, 1.68)]
    mesh('Tent roof', verts, [(0, 3, 5, 2), (2, 5, 4, 1), (3, 4, 5)], 'canvas')
    mesh('Front flap left', [(-1, -0.805, 0.18), (0, -0.805, 1.68), (-0.18, -0.825, 0.20)], [(0, 1, 2)], 'canvas')
    mesh('Front flap right', [(1, -0.805, 0.18), (0, -0.805, 1.68), (0.30, -0.88, 0.20)], [(0, 1, 2)], 'cloth')
    for y in (-0.81, 0.81):
        beam('Tent ridge support', (0, y, 0.13), (0, y, 1.74), 0.032, 'wood')
        for x in (-1.02, 1.02):
            beam('Canvas seam', (x, y, 0.20), (0, y, 1.71), 0.014, 'leather')
    cube('Rolled front bed', (-0.50, -0.55, 0.23), (0.5, 0.7, 0.12), 'cloth')
    cylinder('Lamp', (0.6, -0.82, 0.33), 0.07, 0.16, 'brass')
    sphere('Lamp light', (0.6, -0.82, 0.45), (0.065, 0.065, 0.06), 'cyan')


def workshop():
    collection('workshop'); base('Repair works', (2.15, 1.85))
    panel('Workshop main shell', (0, 0.25, 0.80), (1.6, 1.0, 1.35))
    cube('Dark open doorway', (0.38, -0.265, 0.55), (0.40, 0.022, 0.91), 'dark', bevel=0.015)
    cube('Door frame', (0.10, -0.30, 0.65), (0.055, 0.07, 1.05), 'brass')
    roof = cube('Corrugated roof', (0, 0.25, 1.50), (1.87, 1.26, 0.11), 'metal')
    for x in (-0.75, -0.45, -0.15, 0.15, 0.45, 0.75):
        beam('Roof rib', (x, -0.4, 1.565), (x, 0.85, 1.565), 0.021, 'brass')
    cube('Workbench', (-0.51, -0.65, 0.51), (0.85, 0.46, 0.12), 'wood')
    for x in (-0.86, -0.17):
        beam('Bench leg', (x, -0.65, 0.12), (x, -0.65, 0.48), 0.04, 'metal')
    cube('Bench vice', (-0.68, -0.65, 0.66), (0.23, 0.20, 0.2), 'metal')
    beam('Hammer', (-0.30, -0.74, 0.59), (-0.17, -0.54, 0.59), 0.022, 'wood')
    cube('Repair lamp', (-0.33, -0.31, 1.03), (0.32, 0.06, 0.075), 'cyan')
    cylinder('Exhaust', (0.55, 0.60, 1.69), 0.09, 0.35, 'dark')


def exchange():
    collection('exchange'); base('Supply exchange', (2.25, 1.85))
    for x in (-0.98, 0.98):
        for y in (-0.73, 0.65):
            beam('Market post', (x, y, 0.1), (x, y, 1.46), 0.045, 'wood')
    mesh('Market awning', [(-1.12, -0.86, 1.28), (1.12, -0.86, 1.28), (-1.12, 0.74, 1.54), (1.12, 0.74, 1.54)], [(0, 1, 3, 2)], 'canvas')
    for x in (-0.8, -0.4, 0, 0.4, 0.8):
        beam('Awning seam', (x, -0.86, 1.29), (x, 0.74, 1.55), 0.025, 'cloth')
    cube('Market counter', (0, -0.54, 0.52), (1.86, 0.55, 0.78), 'wood')
    for x in (-0.62, 0, 0.63):
        cube('Stock crate', (x, 0.14, 0.40), (0.49, 0.51, 0.50), 'wood')
        cube('Crate band', (x, -0.122, 0.4), (0.045, 0.024, 0.5), 'metal')
        cylinder('Goods jar', (x, -0.50, 0.99), 0.12, 0.22, 'metal')
        cylinder('Jar lid', (x, -0.50, 1.11), 0.125, 0.035, 'brass')
    cube('Market rose pennant', (-0.86, -0.74, 1.24), (0.20, 0.04, 0.34), 'rose')


def relay():
    collection('relay'); base('Field relay', (1.2, 1.1))
    panel('Relay console', (0, 0.1, 0.45), (0.65, 0.5, 0.64))
    cube('Relay screen', (0, -0.157, 0.53), (0.4, 0.025, 0.22), 'dark')
    for x in (-0.13, 0, 0.13):
        cube('Signal register', (x, -0.177, 0.53), (0.038, 0.016, 0.12), 'cyan', bevel=0)
    beam('Relay mast', (0, 0.25, 0.76), (0, 0.25, 2.52), 0.045, 'metal')
    for h, w in [(2.4, 0.65), (2.16, 0.5), (1.95, 0.37)]:
        beam('Signal antenna', (-w, 0.25, h), (w, 0.25, h), 0.025, 'brass')
    sphere('Relay beacon', (0, 0.25, 2.56), (0.065, 0.065, 0.10), 'rose')


def rock():
    collection('rock')
    for x, y, r in [(-0.25, 0.12, 0.53), (0.36, 0, 0.37), (-0.53, -0.3, 0.23)]:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=(x, y, r * 0.45))
        obj = finish(bpy.context.object, 'Weathered stone', 'stone')
        obj.scale = (1.2, 1, 0.9)
        obj.rotation_euler = (0.2, 0.5, RNG.random())
    beam('Nano fissure', (-0.38, -0.17, 0.37), (-0.04, -0.30, 0.26), 0.014, 'cyan')


def construct():
    collection('construct')
    root = empty('Construct / facing and foot origin')
    chassis = empty('Construct chassis', (0, 0, 0.74), root)
    panel('Salvaged chassis', (0, 0, 0), (0.75, 0.60, 0.47), 'metal', chassis)
    cube('Construct eye', (0, -0.323, 0.06), (0.19, 0.05, 0.095), 'rose', chassis)
    sphere('Power core', (0, 0, 0.30), (0.21, 0.18, 0.17), 'brass', chassis)
    beam('Sensor stalk', (0.18, 0.05, 0.25), (0.18, 0.05, 0.68), 0.025, 'metal', chassis)
    cube('Sensor', (0.18, -0.01, 0.67), (0.20, 0.14, 0.10), 'dark', chassis)
    legs = []
    for i in range(4):
        a = (i * 90 + 45) * math.pi / 180
        leg = empty('Construct leg ' + str(i), (0, 0, 0), chassis)
        start = (math.cos(a) * 0.3, math.sin(a) * 0.3, -0.12)
        joint = (math.cos(a) * 0.63, math.sin(a) * 0.63, -0.38)
        end = (math.cos(a) * 0.70, math.sin(a) * 0.70, -0.68)
        beam('Leg upper', start, joint, 0.046, 'metal', leg)
        sphere('Leg joint', joint, (0.065, 0.065, 0.065), 'brass', leg)
        beam('Leg lower', joint, end, 0.042, 'metal', leg)
        cube('Construct foot', end, (0.19, 0.17, 0.08), 'dark', leg)
        legs.append(leg)
    return root, chassis, legs


def ground(name, colors):
    collection(name)
    # Ground is rendered from 3D relief, then sampled as an unlit screen-space fill by the game.
    base_mat, debris_mat = colors
    cube('Ground relief', (0, 0, -0.15), (8, 8, 0.3), base_mat, bevel=0)
    for i in range(90):
        x, y = RNG.uniform(-4, 4), RNG.uniform(-4, 4)
        r = RNG.uniform(0.018, 0.17)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=r, location=(x, y, 0.018))
        obj = finish(bpy.context.object, 'Ground fragment', debris_mat)
        obj.scale.z = RNG.uniform(0.12, 0.4)


def setup(samples, supersample):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        if c.name != 'Collection':
            bpy.data.collections.remove(c)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.seed = CFG['render']['seed']
    scene.cycles.use_animated_seed = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = CFG['render']['threads']
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = True
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = (*CFG['light']['ambient_color'], 1)
    bg.inputs['Strength'].default_value = CFG['light']['ambient_strength']
    collection('Studio / fixed camera and light')
    phi = math.radians(CFG['camera']['azimuth_degrees'])
    u = Vector((-math.sin(phi), math.cos(phi), 0))
    v = Vector((math.cos(phi), math.sin(phi), 0))
    light_pos = u * CFG['light']['position_in_screen_basis'][0] + v * CFG['light']['position_in_screen_basis'][1] + Vector((0, 0, CFG['light']['position_in_screen_basis'][2]))
    sun_data = bpy.data.lights.new('Hard fixed sunlight', 'SUN')
    sun_data.energy = CFG['light']['sun_energy']
    sun_data.angle = math.radians(CFG['light']['sun_angle_degrees'])
    sun = bpy.data.objects.new('Hard fixed sunlight', sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = light_pos
    sun.rotation_euler = (-light_pos).to_track_quat('-Z', 'Y').to_euler()
    fill_data=bpy.data.lights.new('Broad neutral bounced fill','AREA')
    fill_data.energy=CFG['light']['fill_energy'];fill_data.shape='DISK';fill_data.size=CFG['light']['fill_size']
    fill=bpy.data.objects.new('Broad neutral bounced fill',fill_data);bpy.context.collection.objects.link(fill)
    fill.location=u*CFG['light']['fill_position_in_screen_basis'][0]+v*CFG['light']['fill_position_in_screen_basis'][1]+Vector((0,0,CFG['light']['fill_position_in_screen_basis'][2]))
    fill.rotation_euler=(-fill.location).to_track_quat('-Z','Y').to_euler()
    cam_data = bpy.data.cameras.new('Registered dimetric camera')
    cam_data.type = 'ORTHO'
    cam = bpy.data.objects.new('Registered dimetric camera', cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam
    bpy.ops.mesh.primitive_plane_add(size=200)
    floor = bpy.context.object
    floor.name = 'Shadow catcher / never changes registration'
    floor.is_shadow_catcher = True
    floor.location.z = -0.015
    for name, settings in CFG['materials']['surfaces'].items():
        material(name, tuple(settings['color']), **{k: v for k, v in settings.items() if k != 'color'})
    floor.data.materials.append(MATERIALS['concrete'])
    return scene, floor


def camera(scene, kind, ss):
    cfg = CFG['camera'][kind]
    w, h = cfg['size']
    scene.render.resolution_x, scene.render.resolution_y = w * ss, h * ss
    scene.camera.data.ortho_scale = cfg['ortho_scale']
    elev = math.asin(CFG['camera']['ground_compression'])
    phi = math.radians(CFG['camera']['azimuth_degrees'])
    target = Vector((0, 0, cfg['target_height']))
    offset = Vector((math.cos(phi) * math.cos(elev), math.sin(phi) * math.cos(elev), math.sin(elev))) * CFG['camera']['distance']
    scene.camera.location = target + offset
    scene.camera.rotation_euler = (-offset).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.view_layer.update()
    uv = world_to_camera_view(scene, scene.camera, Vector((0, 0, 0)))
    return [round(uv.x * w, 6), round((1 - uv.y) * h, 6)]


def visibility(name):
    for key, c in COLLECTIONS.items():
        c.hide_render = key != name and not key.startswith('Studio')


def keyframe(obj, frame):
    obj.keyframe_insert('location', frame=frame)
    obj.keyframe_insert('rotation_euler', frame=frame)
    obj.keyframe_insert('scale', frame=frame)


def main():
    global MODEL_OVERRIDE
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=CFG['render']['samples'])
    parser.add_argument('--supersample', type=int, default=CFG['render']['supersample'])
    parser.add_argument('--only', help='Comma-separated model names; does not overwrite the full catalog.')
    parser.add_argument('--resume', action='store_true', help='Reuse completed raw frames only when settings and source match.')
    parser.add_argument('--build-only', action='store_true')
    parser.add_argument('--frames', help='Comma-separated timeline frames for a partial visual check.')
    opts = parser.parse_args(args)
    if not (1 <= opts.samples <= 4096 and 1 <= opts.supersample <= 8):
        parser.error('samples must be 1–4096; supersample must be 1–8')
    opts.output.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import individual_models
    import fidelity_models
    import reference_models
    designs = json.loads((ROOT / 'static/visual-catalog.json').read_text())
    source_hash = hashlib.sha256(Path(__file__).read_bytes() + (ROOT / 'art-source/render-settings.json').read_bytes()
                                 + Path(individual_models.__file__).read_bytes() + Path(fidelity_models.__file__).read_bytes() + Path(reference_models.__file__).read_bytes() + (ROOT / 'static/visual-catalog.json').read_bytes()).hexdigest()
    identity = {'source_sha256': source_hash, 'blender': bpy.app.version_string, 'samples': opts.samples, 'supersample': opts.supersample}
    identity_path = opts.output / 'render-identity.json'
    if opts.resume and (not identity_path.exists() or json.loads(identity_path.read_text()) != identity):
        parser.error('--resume requires matching Blender, source and render settings; use a fresh output directory')
    identity_path.write_text(json.dumps(identity, indent=2) + '\n')
    scene, floor = setup(opts.samples, opts.supersample)
    studio = sys.modules[__name__]
    humans = {name: individual_models.body(studio, name) for name in designs['profiles']}
    for name,joints in humans.items():fidelity_models.body(studio,name,joints)
    reference_models.materials(studio)
    rotors, worn_objects = {}, {}
    builders = dict(power=power, water=water, garden=garden, shelter=shelter, workshop=workshop, exchange=exchange, relay=relay)
    for region in designs['regions']:
        for kind, builder in builders.items():
            model = kind + '_' + region
            MODEL_OVERRIDE = model
            RNG.seed(CFG['seed'] + sum(map(ord, model)))
            rotor = builder()
            if rotor is not None: rotors[model] = rotor
            worn_objects[model] = individual_models.architecture(studio, region, kind)
            fidelity_models.architecture(studio,region,kind)
            reference_models.architecture(studio,region,kind)
        MODEL_OVERRIDE = 'rock_' + region
        rock()
        individual_models.obstacle(studio, region)
        reference_models.obstacle(studio, region)
    MODEL_OVERRIDE = None
    robot = construct()
    for region in designs['regions']:reference_models.ground(studio,region)
    for region in designs['regions']:reference_models.ground(studio,region,path=True)
    requested = set(opts.only.split(',')) if opts.only else set(COLLECTIONS) - {'Studio / fixed camera and light'}
    unknown = requested - set(COLLECTIONS)
    if unknown:
        parser.error('Unknown models: ' + ', '.join(sorted(unknown)))
    catalog = {'schema': 1, 'settings': CFG, 'provenance': 'Original 3D meshes rendered in Blender Cycles, then downsampled and palette-indexed.',
               'render': identity, 'projection': {'hex': 'pointy axial', 'vertical_scale': 0.52, 'directions': 6,
               'elevation_degrees': math.degrees(math.asin(CFG['camera']['ground_compression'])),
               'camera_azimuth_degrees': CFG['camera']['azimuth_degrees'],
               'facing_yaw_degrees': [(CFG['camera']['azimuth_degrees'] + 180 + i * 60) % 360 for i in range(6)]},
               'animations': CFG['animations'], 'visual_catalog': designs, 'models': {}}
    jobs = []
    frame = 1
    for model in [*humans, 'construct', *worn_objects, *['rock_' + region for region in designs['regions']],
                  *['ground_' + region for region in designs['regions']],
                  *['ground_path_' + region for region in designs['regions']]]:
        kind = 'character' if model in humans or model == 'construct' else 'texture' if model.startswith('ground_') else 'environment'
        anchor = camera(scene, kind, opts.supersample)
        size = CFG['camera'][kind]['size']
        record = {'size': size, 'anchor': anchor, 'frames': [], 'timeline_frames': [], 'clips': {}, 'camera_kind': kind,'supersample':CFG['render'].get('texture_supersample',opts.supersample) if kind=='texture' else opts.supersample,
                  'kind': 'texture' if model.startswith('ground_') else 'sprite'}
        animations = CFG['animations'] if kind == 'character' else {'idle': {'frames': 4 if model in rotors else 1, 'loop': True}}
        if model in worn_objects: animations['worn'] = animations['idle'].copy()
        for direction in range(6 if kind == 'character' else 1):
            yaw = math.radians(catalog['projection']['facing_yaw_degrees'][direction])
            for name, config in animations.items():
                clip = []
                count = config['frames']
                for n in range(count):
                    phase = n / (count if config['loop'] else max(1, count - 1))
                    if model in humans:
                        human = humans[model]
                        human['root'].rotation_euler.z = yaw
                        pose(human, name, phase)
                        for obj in human.values():
                            keyframe(obj, frame)
                    elif model == 'construct':
                        root, body, legs = robot
                        root.rotation_euler.z = yaw
                        body.location = (0, 0, 0.74)
                        body.rotation_euler = (0, 0, 0)
                        wave = math.sin(phase * math.tau)
                        if name == 'walk':
                            body.location.z += 0.035 * abs(wave)
                        elif name in ('attack', 'work'):
                            body.rotation_euler.x = 0.22 * math.sin(phase * math.pi)
                        elif name == 'hit':
                            body.rotation_euler.y = 0.18 * math.sin(phase * math.pi)
                        elif name == 'down':
                            body.location.z = 0.3
                            body.rotation_euler.y = 0.45
                        for i, leg in enumerate(legs):
                            leg.rotation_euler.z = 0.09 * wave * (-1 if i % 2 else 1) if name == 'walk' else 0
                            leg.scale = (1, 1, 0.33 if name == 'down' else 1)
                            keyframe(leg, frame)
                        for obj in (root, body):
                            keyframe(obj, frame)
                    elif model in rotors:
                        rotor = rotors[model]
                        rotor.rotation_euler.y = phase * math.tau / 3
                        keyframe(rotor, frame)
                    for obj in worn_objects.get(model, []):
                        obj.hide_render = name != 'worn'
                        obj.keyframe_insert('hide_render', frame=frame)
                    filename = f'{model}/{name}-{direction}-{n:02d}.png'
                    clip.append(len(record['frames']))
                    record['frames'].append(filename)
                    record['timeline_frames'].append(frame)
                    jobs.append((model, kind, frame, filename))
                    marker = scene.timeline_markers.new(f'{model}/{name}/{direction}/{n}', frame=frame)
                    frame += 1
                record['clips'][f'{name}_{direction}' if kind == 'character' else name] = clip
        catalog['models'][model] = record
    scene.frame_end = frame - 1
    for obj in bpy.data.objects:
        if obj.animation_data and obj.animation_data.action:
            for curve in obj.animation_data.action.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation = 'LINEAR'
    # Collection names, original editable meshes, materials and all keyframed poses survive in the source file.
    visibility('traveler')
    scene.frame_set(1)
    camera(scene, 'character', opts.supersample)
    source_catalog = json.dumps(catalog, indent=2) + '\n'
    text = bpy.data.texts.new('Rose sprite catalog.json')
    text.write(source_catalog)
    (ROOT / 'art-source/render-catalog.json').write_text(source_catalog)
    source_file = ROOT / 'art-source/Rose-prefabs.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(source_file), compress=True)
    selected = {int(n) for n in opts.frames.split(',')} if opts.frames else None
    if selected is not None and not selected.issubset({job[2] for job in jobs}):
        parser.error('Requested frames are not present in the catalog')
    catalog_path = opts.output / ('catalog-partial.json' if opts.only or selected is not None else 'catalog.json')
    if opts.only:
        catalog['models'] = {k: v for k, v in catalog['models'].items() if k in requested}
    catalog_path.write_text(json.dumps(catalog, indent=2) + '\n')
    if opts.build_only:
        print('ROSE: modeled and saved source; rendering skipped', flush=True)
        return
    done = 0
    for model, kind, timeline_frame, filename in jobs:
        if model not in requested:
            continue
        if selected is not None and timeline_frame not in selected:
            continue
        path = opts.output / filename
        visibility(model)
        floor.hide_render = model.startswith('ground_')
        scene.frame_set(timeline_frame)
        camera(scene, kind, catalog['models'][model].get('supersample',opts.supersample))
        path.parent.mkdir(parents=True, exist_ok=True)
        if not (opts.resume and path.exists()):
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
        done += 1
        print(f'ROSE FRAME {done}: {filename}', flush=True)
    print('ROSE COMPLETE:', done, 'frames;', source_file, flush=True)


if __name__ == '__main__':
    main()
