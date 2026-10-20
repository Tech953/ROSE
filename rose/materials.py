"""Persistent, bounded material wear and finite recovery for registered objects.

Condition is the object's existing 0..100 authority. Material clocks and
receipts never produce public stock, numerical energy or a second salvage.
"""
import copy
import math
import re

import hexgrid as hx
import animations
import weathering

ACTS = {'material_inspect', 'material_strike', 'material_clear',
        'gear_inspect', 'gear_repair', 'gear_replace', 'gear_reclaim'}
PROFILES = {
    'wood': dict(label='mineralized wood', hardness=2, dry=.012, wet=.09, storm=.10, recovery=.4),
    'metal': dict(label='worked metal', hardness=6, dry=.005, wet=.06, storm=.025, recovery=.6),
    'stone': dict(label='stone and earth composite', hardness=8, dry=.002, wet=.005, storm=.01, recovery=.5),
    'crystal': dict(label='faceted crystal', hardness=4, dry=.006, wet=.01, storm=.10, recovery=.4),
    'fabric': dict(label='woven canopy fabric', hardness=1, dry=.025, wet=.07, storm=.18, recovery=.2),
    'polymer': dict(label='bio-polymer', hardness=3, dry=.015, wet=.025, storm=.06, recovery=.4),
}
GEAR = {'field_staff': ('Field staff', 'wood'), 'crystallin': ('Crystallin< retrofit', 'crystal'),
        'leg_spikes': ('LEG|SPIKES', 'metal'), 'meta_fingers': ('Meta-Fingers', 'metal'),
        'bio_glass': ('Corded Bio-Glass', 'polymer'), 'survey_lens': ('Survey lens', 'crystal'),
        'filter_graft': ('Filter graft', 'polymer'), 'rest_regulator': ('Rest regulator', 'polymer'),
        'resonance_link': ('Resonance link', 'crystal')}
BUILD_COST = {'garden': 4, 'shelter': 5, 'water': 6, 'power': 7, 'workshop': 7, 'exchange': 7, 'relay': 6}


def phase(obj):
    if obj.get('material_state', {}).get('destroyed') or obj.get('condition', 100) <= 0: return 'ruined'
    return 'fractured' if obj.get('condition', 100) < 30 else 'worn' if obj.get('condition', 100) < 60 else 'sound'


def profile_for(c, kind):
    if c['region'] == 'AETHERGALE' and kind in {'shelter', 'exchange'}: return 'fabric'
    return {'WN_TOWER': 'wood', 'CITY_CLOUD_S': 'metal', 'ENACT_HILLS': 'stone', 'AETHERGALE': 'crystal'}[c['region']]


def ensure(obj, material, tick, budget=0):
    if 'material_state' not in obj:
        obj.setdefault('condition', 100)
        obj['material_state'] = dict(schema=1, material=material, age=0, last_tick=tick, exposure=0.,
            weather_loss=0, damage_loss=0, repair_inputs=0, destroyed=False, destroyed_at=None,
            embodied_scrap=budget, salvage_remaining=0, recovered_scrap=0, lost_scrap=0)
    if obj['condition']<=0 and not obj['material_state']['destroyed']:
        damage(obj,1,tick,'recorded zero condition')
    return obj['material_state']


def ensure_node(w, c, node):
    return ensure(node, profile_for(c, node['kind']), w['tick'], node.get('embodied_scrap', BUILD_COST.get(node['kind'], 0)))


def ensure_gear(p, tick):
    records = p.setdefault('gear', {})
    for key in ['field_staff', *p.get('loadout', [])]:
        if key not in GEAR: continue
        if key not in records:
            records[key] = dict(id=p['id'] + ':' + key + ':0', key=key, name=GEAR[key][0], condition=100, generation=0)
        ensure(records[key], GEAR[key][1], tick, 1 if key == 'field_staff' else 2)
    return records


def operable(p, key):
    item = p.get('gear', {}).get(key)
    return item is None or (item['condition'] >= (20 if key == 'crystallin' else 1 if key == 'field_staff' else 30)
                           and not item['material_state']['destroyed'])


def damage(obj, amount, tick, cause='impact'):
    if type(amount) is not int or not 0 <= amount <= 100: raise ValueError('Material damage must be an integer from 0 to 100.')
    state = obj['material_state']
    if state['destroyed'] or not amount: return False
    before = obj['condition']; obj['condition'] = max(0, before - amount)
    state['weather_loss' if cause == 'weather' else 'damage_loss'] += before - obj['condition']
    if not obj['condition']:
        state['last_intact_condition'] = before
        state['destroyed'] = True; state['destroyed_at'] = tick; state['cause'] = cause
        recoverable = math.floor(state['embodied_scrap'] * PROFILES[state['material']]['recovery'])
        state['salvage_remaining'] = recoverable
        state['lost_scrap'] = state['embodied_scrap'] - recoverable
        return True
    return False


def age(obj, tick, moisture, climate, protection=1.):
    state = obj['material_state']; elapsed = max(0, tick - state['last_tick'])
    if not elapsed: return False
    state['last_tick'] = tick; state['age'] += elapsed
    if state['destroyed']: return False
    spec = PROFILES[state['material']]
    rate = spec['dry'] + (spec['wet'] if moisture >= 70 or climate == 'rain' else 0)
    rate += spec['storm'] if climate in {'particulate storm', 'contrail squall'} else 0
    state['exposure'] += elapsed * rate * protection
    loss = min(100, math.floor(state['exposure'])); state['exposure'] -= loss
    return damage(obj, loss, tick, 'weather')


def cell_record(w, c, text, **details):
    data = c.setdefault('material_record', dict(schema=1, history=[], cleared=[]))
    data['history'].append(dict(tick=w['tick'], text=text, **details)); data['history'] = data['history'][-48:]


def collapse_node(w, c, node, engine):
    if node.get('ruin_registered'): return
    node.update(condition=0, enabled=False, status='ruined', ruin_registered=True)
    for edge in c['infrastructure']['links']:
        if node['id'] in [edge['a'], edge['b']]: edge['condition'] = 0
    tile = c.get('scene', {}).get('tiles', {}).get(hx.key(node['pos']))
    if tile: tile.update(passable=False, opaque=False, elevation=0)
    if node.get('shelter_contribution'): c['shelter'] = max(0, c['shelter'] - node['shelter_contribution'])
    engine.lifecycle.cover(c['scene']); engine.infrastructure.refresh_support(c)
    animations.collapse(c['scene'],'structure:'+node['id'],node)
    cell_record(w, c, node.get('name', node['kind']) + ' collapses; its connections fail and rubble occupies the foundation.',
                source=node['id'], salvage=node['material_state']['salvage_remaining'])
    # Reconcile only; never run another mechanism step or refund stored energy.
    engine.particles.reconcile_sources(w)
    for address, field in w.get('substrate', {}).get('fields', {}).items():
        if address == 'base:' + engine.key(c['x'], c['y']): engine.machines.reconcile(field, c)


def collapse_project(w, c, project, engine):
    if project['stage'] == 'ruined': return
    project['stage'] = 'ruined'
    c['scene']['tiles'][hx.key(project['pos'])].update(opaque=False, passable=False)
    engine.lifecycle.cover(c['scene'])
    animations.collapse(c['scene'],'project:'+project['id'],project)
    cell_record(w, c, project['id'] + ' collapses. Its remaining physical materials are recoverable once.', source=project['id'])


def collapse_rock(w, c, tile, engine):
    if tile.get('ruin_registered'): return
    tile.update(opaque=False,elevation=0,ruin_registered=True)
    engine.lifecycle.cover(c['scene'])
    animations.collapse(c['scene'],'hex:'+hx.key(tile['pos']),tile)
    cell_record(w,c,'A stone prop collapses into persistent debris.',source='hex:'+hx.key(tile['pos']))


def advance(w, engine):
    for c in w['cells'].values():
        climate = engine.weather(w, c)
        for node in c['infrastructure']['nodes']:
            ensure_node(w, c, node)
            if age(node, w['tick'], c['moisture'], climate,weathering.protection(node)) or node['material_state']['destroyed']:
                collapse_node(w, c, node, engine)
        for project in engine.lifecycle.ensure(w, c)['projects']:
            if project['stage'] not in engine.lifecycle.LIVE: continue
            ensure(project, profile_for(c, project['kind']), w['tick'], project['escrow'])
            if age(project, w['tick'], c['moisture'], climate) or project['material_state']['destroyed']:
                collapse_project(w, c, project, engine)
        for tile in c['scene']['tiles'].values():
            if tile['prefab'] != 'rock': continue
            ensure(tile, 'stone', w['tick'], 2)
            if age(tile, w['tick'], c['moisture'], climate) or tile['material_state']['destroyed']:
                collapse_rock(w,c,tile,engine)
    people = [*w['players'], *w['actors'], *w.get('residents', {}).values()]
    for p in people:
        c = w['cells'].get(hx.key(p['pos'] if 'pos' in p else [p['x'], p['y']]))
        if not c: continue
        for item in ensure_gear(p, w['tick']).values():
            if age(item, w['tick'], c['moisture'], engine.weather(w, c), .25):
                p.setdefault('gear_log', []).append(dict(tick=w['tick'], text=item['name'] + ' fails after prolonged exposure.'))
                p['gear_log'] = p['gear_log'][-24:]


def weapon_use(w, p, ranged=False):
    key = 'crystallin' if ranged else 'field_staff'; item = ensure_gear(p, w['tick'])[key]
    factor = 1. if item['condition'] >= 60 else .8 if item['condition'] >= 30 else .55
    damage(item, 2, w['tick'], 'weapon use')
    return factor


def replace_record(p, key, tick):
    item = p['gear'][key]; old = copy.deepcopy(item)
    old['material_state']['retired'] = True
    old['material_state']['lost_scrap'] = old['material_state']['embodied_scrap'] - old['material_state']['recovered_scrap']
    old['material_state']['salvage_remaining'] = 0
    p.setdefault('gear_history', []).append(old); p['gear_history'] = p['gear_history'][-16:]
    serial = item['generation'] + 1
    fresh = dict(id=p['id']+':'+key+':'+str(serial),key=key,name=item['name'],condition=100,generation=serial)
    ensure(fresh,GEAR[key][1],tick,2); p['gear'][key] = fresh


def after_action(w, p, intent, timing, equipment):
    if not timing and intent['action'] not in {'hex_move', 'guard', 'combat_care'}: return
    skills = {r['skill'] for r in p.get('_checks', [])}
    for key in p.get('loadout', []):
        if key in equipment and equipment[key]['skill'] in skills and operable(p, key):
            item = ensure_gear(p, w['tick'])[key]; damage(item, 1, w['tick'], 'equipment use')


def parse(text):
    value = text.lower().strip()
    match = re.fullmatch(r'(inspect|repair|replace|reclaim) (?:gear|weapon) ([\w_]{1,30})', value)
    if match: return dict(action='gear_' + match[1], target=match[2])
    match = re.fullmatch(r'(inspect|strike|clear) material (structure|project|hex) ([\w,-]{1,50})', value)
    if match: return dict(action='material_' + match[1], target=match[2] + ':' + match[3])
    return None


def target_object(c, target, engine):
    kind, _, identity = target.partition(':')
    if kind == 'structure': obj = next((n for n in c['infrastructure']['nodes'] if identity in [n['id'], n['kind']]), None)
    elif kind == 'project': obj = next((n for n in c['lifecycle']['projects'] if n['id'] == identity and n['stage'] in engine.lifecycle.LIVE | {'ruined'}), None)
    elif kind == 'hex':
        pos = hx.parse(identity); obj = c['scene']['tiles'].get(hx.key(pos))
        if obj and obj['prefab'] != 'rock': obj = None
    else: obj = None
    engine.require(obj is not None, 'Choose an existing structure, active project or rock in this field.')
    return kind, obj


def ownership_reason(w, p, kind, obj):
    owner = obj.get('owner')
    if kind in {'project', 'structure'} and owner and owner != p['id'] and any(q['id'] == owner for q in w['players']):
        return 'Only the commissioning player can destroy or recover this private foundation.'
    return ''


def clear(w, c, kind, obj, p, engine):
    state = obj['material_state']; amount = state['salvage_remaining']
    engine.require(state['destroyed'] and 'cleared_at' not in state, 'Only uncleared collapsed debris can be recovered.')
    engine.require(p['inventory']['scrap'] + amount <= 99, 'Make room for the recoverable scrap before clearing.')
    animations.clear(c['scene'],kind+':'+(hx.key(obj['pos']) if kind=='hex' else obj['id']),obj)
    p['inventory']['scrap'] += amount; state['recovered_scrap'] += amount; state['salvage_remaining'] = 0; state['cleared_at'] = w['tick']
    pos = obj['pos']; tile = c['scene']['tiles'][hx.key(pos)]
    if kind == 'structure':
        c['infrastructure']['nodes'].remove(obj)
        c['infrastructure']['links'] = [e for e in c['infrastructure']['links'] if obj['id'] not in [e['a'], e['b']]]
    elif kind == 'project': obj['stage'] = 'cleared'
    # The cleared footprint is physically traversable and can be surveyed anew.
    tile.update(passable=True, opaque=False, prefab='ground', elevation=0, material_scar=True)
    engine.lifecycle.cover(c['scene']); engine.infrastructure.refresh_support(c)
    record = c.setdefault('material_record', dict(schema=1, history=[], cleared=[]))
    record['cleared'].append(dict(source=obj.get('id', hx.key(pos)), kind=kind, pos=pos[:], material_state=copy.deepcopy(state)))
    record['cleared'] = record['cleared'][-32:]
    totals = record.setdefault('totals', dict(embodied_cleared=0,recovered=0,lost=0))
    totals['embodied_cleared'] += state['embodied_scrap']; totals['recovered'] += amount; totals['lost'] += state['lost_scrap']
    cell_record(w, c, f'Cleared {kind} debris; {amount} existing scrap recovered.', source=obj.get('id', hx.key(pos)))
    return amount


def work_reason(w, c, p, engine):
    return ('Begin the expedition first.' if not w['started'] else 'The world is paused.' if w['paused'] else
        'Return through the recorded void trace.' if p.get('percept', {}).get('address') else
        'Return from remote observation.' if p['remote'] else 'Resolve the encounter first.' if engine.tactical.active(c) else '')


def gear_reason(w, c, p, item, op, engine):
    if op == 'gear_inspect': return 'Begin the expedition first.' if not w['started'] else 'The world is paused.' if w['paused'] else ''
    reason = work_reason(w, c, p, engine)
    if reason: return reason
    key = item['key']
    if op == 'gear_repair':
        return 'Destroyed gear needs replacement.' if item['condition'] <= 0 else 'Already maintained.' if item['condition'] >= 95 else 'Repair requires one scrap.' if not p['inventory']['scrap'] else ''
    if op == 'gear_reclaim':
        return 'Only destroyed gear can be reclaimed.' if item['condition'] > 0 else 'This shell has already been reclaimed.' if item['material_state'].get('reclaimed') else 'Make room for recovered scrap.' if p['inventory']['scrap'] + item['material_state']['salvage_remaining'] > 99 else ''
    if item['condition'] >= 30: return 'Replace only fractured or destroyed gear; sound items can be repaired.'
    if p['inventory']['scrap'] < 2: return 'Replacement requires two scrap.'
    if key != 'field_staff':
        if key not in p['loadout'] or 'black.dot' not in p['credentials']: return 'Install and register this equipment before replacing its parts.'
        if not any(n['kind'] == 'workshop' and n['enabled'] and n['condition'] >= 30 and hx.distance(p['local']['pos'], n['pos']) == 1 for n in c['infrastructure']['nodes']): return 'Approach a maintained workshop to replace regulated equipment.'
    return ''


def object_actions(w, c, p, kind, obj, engine):
    selector = kind + ':' + (hx.key(obj['pos']) if kind == 'hex' else obj['id'])
    common = 'Begin the expedition first.' if not w['started'] else 'The world is paused.' if w['paused'] else ''
    reason = work_reason(w,c,p,engine)
    strike_reason = '' if engine.tactical.active(c) and reason == 'Resolve the encounter first.' else reason
    adjacent = '' if hx.distance(p['local']['pos'],obj['pos']) == 1 else 'Approach an adjacent hex before material work.'
    state = obj.get('material_state', {})
    broken = state.get('destroyed', False)
    ownership = ownership_reason(w,p,kind,obj)
    strike_reason = strike_reason or ownership or adjacent or ('Already rubble; clear its materials.' if broken else 'Repair or replace your field staff first.' if not operable(p,'field_staff') else '')
    if engine.tactical.active(c):
        enc = c['scene']['encounter']
        strike_reason = strike_reason or ('Wait for your combat turn.' if enc['current'] != p['id'] else 'Not enough AP.' if enc['ap'].get(p['id'],0) < w['rules']['combat']['melee_ap'] else '')
    clear_reason = reason or ownership or adjacent or ('Collapse the object before clearing it.' if not broken else 'Make room for recovered scrap.' if p['inventory']['scrap'] + state.get('salvage_remaining',0) > 99 else '')
    cost = str(w['rules']['combat']['melee_ap'])+' AP' if engine.tactical.active(c) else '1 survival cycle'
    public = kind == 'structure' and not obj.get('owner')
    spec = PROFILES[state.get('material','stone')]
    return [dict(group=group,label=label,intent=dict(action=op,target=selector),skill='Material craft',training=p['character']['skills'].get('metallurgy',0),stat=stat,dc=dc,reason=blocked,cost=note)
        for group,label,op,stat,dc,blocked,note in [
        ('look','INSPECT MATERIAL','material_inspect','percept',9,common,'No AP or survival cycle'),
        ('skill','STRIKE PUBLIC WORKS' if public else 'STRIKE MATERIAL','material_strike','body',10+spec['hardness']//2,strike_reason,cost+'; 2 staff condition'+('; −1 faction standing' if public else '')),
        ('use','CLEAR RUBBLE / RECOVER '+str(state.get('salvage_remaining',0))+' SCRAP','material_clear','tech',10,clear_reason,'1 survival cycle; existing material only')]]+weathering.actions(w,c,p,kind,obj,engine)


def public(w, c, p, engine):
    items = copy.deepcopy(ensure_gear(p, w['tick']))
    for key, item in items.items():
        item['state'] = phase(item); item['material_label'] = PROFILES[item['material_state']['material']]['label']
        item['installed'] = key == 'field_staff' or key in p['loadout']
        item['actions'] = [dict(label=label, intent=dict(action=op, target=key), reason=gear_reason(w,c,p,item,op,engine))
            for op,label in [('gear_inspect','INSPECT'),('gear_repair','REPAIR / 1 SCRAP'),('gear_replace','REPLACE / 2 SCRAP'),('gear_reclaim','RECLAIM BROKEN SHELL')]]
    return dict(items=list(items.values()), history=copy.deepcopy(p.get('gear_log', [])[-24:]),
                local_record=copy.deepcopy(c.get('material_record', dict(history=[], cleared=[]))))


def handle(w, p, intent, raw, engine):
    c = engine.local(w, p); op = intent['action']; target = intent.get('target', '')
    context = dict(action=op, faction=engine.REGIONS[c['region']]['faction'])
    if op.startswith('gear_'):
        item = ensure_gear(p, w['tick']).get(target); engine.require(item is not None, 'Choose gear registered to this character.')
        reason = gear_reason(w,c,p,item,op,engine); engine.require(not reason,reason)
        if op == 'gear_inspect':
            ok, roll = engine.check(w,p,'percept',9,'metallurgy',context)
            text = f"{item['name']}: {phase(item)}, condition {item['condition']}/100; {PROFILES[item['material_state']['material']]['label']}."
            return dict(text=text,mechanics=roll,time_spent=False)
        cost = 1 if op == 'gear_repair' else 2 if op == 'gear_replace' else 0
        p['inventory']['scrap'] -= cost
        ok, roll = engine.check(w,p,'tech',11 if op != 'gear_reclaim' else 9,'metallurgy',context)
        if ok:
            state = item['material_state']
            if op == 'gear_repair':
                item['condition'] = min(100,item['condition']+25); state['repair_inputs'] += 1
                text = item['name'] + ' is repaired to ' + str(item['condition']) + '/100.'
            elif op == 'gear_replace':
                replace_record(p,target,w['tick'])
                text = item['name'] + ' receives paid replacement parts; its prior shell is retired.'
            else:
                amount = state['salvage_remaining']; p['inventory']['scrap'] += amount
                state['salvage_remaining'] = 0; state['recovered_scrap'] += amount; state['reclaimed'] = True
                text = f'{amount} existing scrap recovered from the broken shell; this receipt is closed.'
        else: text = 'The material work fails; its reserved scrap is spent and no gear is restored or recovered.'
        p.setdefault('gear_log', []).append(dict(tick=w['tick'],text=text)); p['gear_log'] = p['gear_log'][-24:]
        engine.scene.pose(c['scene'],p,'work')
        return dict(text=text,mechanics=roll,time_spent=True)
    kind, obj = target_object(c,target,engine)
    if kind == 'structure': ensure_node(w,c,obj); context['faction'] = obj['faction']
    else: ensure(obj,'stone' if kind == 'hex' else profile_for(c,obj['kind']),w['tick'],2 if kind == 'hex' else obj['escrow'])
    if op == 'material_inspect':
        ok, roll = engine.check(w,p,'percept',9,'metallurgy',context)
        text = f"{PROFILES[obj['material_state']['material']]['label']}: {phase(obj)}, condition {obj['condition']}/100; age {obj['material_state']['age']} cycles. "+weathering.summary(obj)
        return dict(text=text,mechanics=roll,time_spent=False)
    reason = work_reason(w,c,p,engine)
    if op == 'material_strike' and engine.tactical.active(c) and reason == 'Resolve the encounter first.': reason = ''
    engine.require(not reason,reason)
    engine.require(not ownership_reason(w,p,kind,obj),ownership_reason(w,p,kind,obj))
    engine.require(hx.distance(p['local']['pos'],obj['pos']) == 1,'Approach an adjacent hex before material work.')
    if op == 'material_clear':
        engine.require(obj['material_state']['destroyed'],'Only collapsed debris can be cleared.')
        engine.require(p['inventory']['scrap']+obj['material_state']['salvage_remaining'] <= 99,'Make room for recovered scrap.')
        ok, roll = engine.check(w,p,'tech',10,'metallurgy',context)
        text = f'Cleared the debris and recovered {clear(w,c,kind,obj,p,engine)} existing scrap. The footprint is open for travel or construction.' if ok else 'The safe recovery attempt fails; debris and its recoverable material remain.'
    else:
        engine.require(not obj['material_state']['destroyed'],'The object is already rubble; clear its remaining materials.')
        engine.require(operable(p,'field_staff'),'Repair or replace your field staff before striking material.')
        if engine.tactical.active(c):engine.tactical.spend(w,c,p,w['rules']['combat']['melee_ap'],engine)
        factor = weapon_use(w,p); spec = PROFILES[obj['material_state']['material']]
        ok, roll = engine.check(w,p,'body',10+spec['hardness']//2,'metallurgy',context)
        public_work = kind == 'structure' and not obj.get('owner')
        if public_work: engine.standing(w,p,context['faction'],-1)
        loss = max(1,round((20+3*p['character']['attributes']['body']-spec['hardness'])*factor)) if ok else 0
        engine.scene.face(p,obj['pos']);engine.scene.pose(c['scene'],p,'attack',animate=False)
        animations.strike(c['scene'],p['id'],p['local']['pos'],target,obj['pos'],loss,material=obj['material_state']['material'])
        destroyed = damage(obj,loss,w['tick'],'deliberate impact')
        if destroyed:
            if kind == 'structure': collapse_node(w,c,obj,engine)
            elif kind == 'project': collapse_project(w,c,obj,engine)
            else: collapse_rock(w,c,obj,engine)
        text = f"The impact costs {loss} condition. " + ('The object collapses into persistent debris.' if destroyed else 'Its remaining condition is '+str(obj['condition'])+'/100.')
        if public_work: text += ' Damaging public works costs one faction standing.'
        cell_record(w,c,text,source=target,actor=p['id'])
    if op!='material_strike':engine.scene.face(p,obj['pos']);engine.scene.pose(c['scene'],p,'work')
    return dict(text=text,mechanics=roll,time_spent=not engine.tactical.active(c))
