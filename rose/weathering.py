"""Observed-cycle surface weathering and paid care; rates are game-scale adaptations.

Existing climate owns the stimulus. This module never generates resources,
repairs condition, moves a foundation or substitutes for a numerical solver.
"""
import hashlib
import re

import hexgrid as hx

ACTS = {'surface_clean', 'canopy_brace'}
WIND = {'still air': 0., 'dry wind': .38, 'rain': .28,
        'contrail squall': .72, 'particulate storm': .9}


def clamp(value):
    return round(max(0., min(100., value)), 3)


def canopy(obj):
    return obj.get('kind') == 'shelter' and obj.get('material_state', {}).get('material') == 'fabric'


def objects(c):
    yield from c.get('infrastructure', {}).get('nodes', [])
    yield from (p for p in c.get('lifecycle', {}).get('projects', []) if p['stage'] in {'foundation', 'frame', 'finishing'})
    yield from (t for t in c.get('scene', {}).get('tiles', {}).values() if t['prefab'] == 'rock')


def ensure_object(w, c, obj):
    material = obj['material_state']
    if 'surface' not in material:
        identity = obj.get('id', hx.key(obj['pos']))
        digest = hashlib.sha256(f"{w['seed']}|surface|{c['x']},{c['y']}|{identity}".encode()).digest()
        material['surface'] = dict(schema=1, last_tick=w['tick'], wetness=0., dust=0.,
                              lashings=55. if canopy(obj) else 0., phase=int.from_bytes(digest[:2], 'big') / 65536,
                              clean_inputs=0, brace_inputs=0)
    return material['surface']


def surface(obj):
    return obj.get('material_state', {}).get('surface', {})


def signal(w, c, engine, climate=None):
    climate = climate or engine.weather(w, c)
    direction = engine.rng(w['seed'], 'surface-wind', c['region'], w['tick'] // 4).randrange(6)
    return dict(schema=1, tick=w['tick'], climate=climate, strength=WIND[climate], direction=direction)


def ensure(w, c, engine):
    # Cold saves start at the observed time with dry, unsoiled surfaces. No
    # elapsed history, weather damage or previous treatment is fabricated.
    if 'surface_weather' not in c:
        c['surface_weather'] = dict(signal(w, c, engine), last_tick=w['tick'])
    for obj in objects(c):
        ensure_object(w, c, obj)


def advance(w, c, engine, climate):
    ensure(w, c, engine)
    state = c['surface_weather']
    if not w['started'] or w['paused'] or engine.tactical.any_active(w) or w['tick'] <= state['last_tick']:
        return
    # Only an observed host cycle is applied, including after an old save with
    # a clock gap. Repeated reads, old ticks and render frames do no work.
    state.update(signal(w, c, engine, climate), last_tick=w['tick'])
    wind = state['strength']
    rain = climate == 'rain'
    airborne = (2.6 if c['region'] == 'AETHERGALE' else 1.2) * wind * (1 - min(95, c['growth']) / 140)
    for obj in objects(c):
        surface = ensure_object(w, c, obj)
        if w['tick'] <= surface['last_tick']:
            continue
        surface['last_tick'] = w['tick']
        if obj.get('material_state', {}).get('destroyed'):
            continue
        surface['wetness'] = clamp(surface['wetness'] + (16 if rain else -3 - wind * 4))
        surface['dust'] = clamp(surface['dust'] - 8 if rain else surface['dust'] + airborne * (1 - surface['wetness'] / 120))
        if canopy(obj) and wind >= .6:
            strain = wind ** 2 * (1 + (100 - obj.get('condition', 100)) / 100) * 1.2
            surface['lashings'] = clamp(surface['lashings'] - strain)


def braced(obj):
    return canopy(obj) and obj.get('condition', 0) > 0 and surface(obj).get('lashings', 0) >= 70


def protection(obj):
    return .72 if braced(obj) else 1.


def public_object(obj):
    value = surface(obj)
    if not value:
        return None
    return dict(wetness=value['wetness'] / 100, dust=value['dust'] / 100,
                restraint=value['lashings'] / 100 if canopy(obj) else 1.,
                phase=value['phase'], fabric=canopy(obj), braced=braced(obj))


def public(w, c, p):
    state = c.get('surface_weather')
    if not state or p['remote'] or p.get('percept', {}).get('address'):
        return None
    return {k: state[k] for k in ('schema', 'tick', 'climate', 'strength', 'direction')}


def summary(obj):
    s = surface(obj)
    parts = []
    if s.get('wetness', 0) >= 35:
        parts.append('Damp surfaces retain moisture.')
    if s.get('dust', 0) >= 20:
        parts.append('Settled dust softens the handled surfaces.')
    if canopy(obj):
        parts.append('The canopy lashings hold firm.' if braced(obj) else
                     'The canopy lashings are slack.' if s.get('lashings', 55) < 35 else
                     'The canopy fabric is held between fixed anchors.')
    return ' '.join(parts)


def prose(c):
    nodes = [n for n in c.get('infrastructure', {}).get('nodes', [])
             if n.get('condition', 0) > 0 and not n.get('material_state', {}).get('destroyed')]
    if not nodes:
        return ''
    target = next((n for n in nodes if canopy(n)), nodes[0])
    return summary(target)


def parse(text):
    value = text.lower().strip()
    m = re.fullmatch(r'clean surface (structure|project|hex) ([\w,-]{1,50})', value)
    if m:
        return dict(action='surface_clean', target=m[1] + ':' + m[2])
    m = re.fullmatch(r'brace canopy (?:structure )?([\w,-]{1,50})', value)
    if m:
        return dict(action='canopy_brace', target='structure:' + m[1])
    return None


def reason(w, c, p, kind, obj, op, engine):
    blocked = engine.materials.work_reason(w, c, p, engine)
    if blocked:
        return blocked
    owner = obj.get('owner')
    if kind in {'project', 'structure'} and owner and owner != p['id'] and any(q['id'] == owner for q in w['players']):
        return 'Only the commissioning player can care for this private surface.'
    if hx.distance(p['local']['pos'], obj['pos']) != 1:
        return 'Approach an adjacent hex before working on the surface.'
    if obj.get('material_state', {}).get('destroyed') or obj.get('condition', 0) <= 0:
        return 'Clear the collapsed material before preparing a new surface.'
    if op == 'canopy_brace':
        return ('Choose a completed fabric canopy.' if kind != 'structure' or not canopy(obj) else
                'The canopy lashings are already tight.' if surface(obj).get('lashings', 55) >= 90 else
                'Bracing requires one personal scrap.' if p['inventory']['scrap'] < 1 else '')
    return ('No settled dust needs washing here.' if surface(obj).get('dust', 0) < 5 else
            'Cleaning requires one personal water.' if p['inventory']['water'] < 1 else '')


def actions(w, c, p, kind, obj, engine):
    selector = kind + ':' + (hx.key(obj['pos']) if kind == 'hex' else obj['id'])
    ops = [('surface_clean', 'CLEAN SURFACE / 1 WATER', 'resource', 9, 'One personal water; one survival cycle. Does not repair condition.')]
    if kind == 'structure' and canopy(obj):
        ops.append(('canopy_brace', 'BRACE CANOPY / 1 SCRAP', 'seamllurgy', 11, 'One personal scrap; one survival cycle. Tightens fixed lashings; does not repair condition.'))
    return [dict(group='skill', label=label, intent=dict(action=op, target=selector), skill=skill,
                 training=p['character']['skills'].get(skill, 0), stat='tech', dc=dc, cost=cost,
                 reason=reason(w, c, p, kind, obj, op, engine)) for op, label, skill, dc, cost in ops]


def handle(w, p, intent, raw, engine):
    c = engine.local(w, p)
    kind, obj = engine.materials.target_object(c, intent.get('target', ''), engine)
    op = intent['action']
    blocked = reason(w, c, p, kind, obj, op, engine)
    engine.require(not blocked, blocked)
    s = ensure_object(w, c, obj)
    resource = 'scrap' if op == 'canopy_brace' else 'water'
    p['inventory'][resource] -= 1
    s['brace_inputs' if op == 'canopy_brace' else 'clean_inputs'] += 1
    skill, dc = ('seamllurgy', 11) if op == 'canopy_brace' else ('resource', 9)
    context = dict(action=op, faction=obj.get('faction', engine.REGIONS[c['region']]['faction']))
    ok, roll = engine.check(w, p, 'tech', dc, skill, context)
    if op == 'canopy_brace':
        if ok:
            s['lashings'] = clamp(s['lashings'] + 35)
        text = ('The lashings tighten against the fixed canopy anchors.' if ok else
                'The new binding fails to hold; one scrap was used and the lashings remain unchanged.')
    else:
        s['wetness'] = clamp(s['wetness'] + 35)
        if ok:
            s['dust'] = clamp(s['dust'] - 50)
        text = ('The water lifts settled dust; the surface remains wet.' if ok else
                'The water wets the surface but fails to lift the settled dust.')
    engine.scene.face(p, obj['pos'])
    engine.scene.pose(c['scene'], p, 'work')
    engine.materials.cell_record(w, c, p['name'] + ': ' + text, source=obj.get('id', hx.key(obj['pos'])))
    return dict(text=text, mechanics=roll, time_spent=True)
