"""Seeded public works, physical access, finite utility stores and maintenance contracts."""
import copy
import visuals
import re
import hexgrid as hx
import materials
import weathering

ACTS = {'structure_inspect', 'structure_repair', 'structure_toggle', 'structure_draw',
        'structure_contract', 'structure_fulfill'}
TYPES = {
    'power': dict(label='wind collector', skill='fractech', role='producer', output='power', demand=0),
    'water': dict(label='condensation cistern', skill='resource', role='producer', output='water', demand=1),
    'garden': dict(label='cultivation frame', skill='druid', role='producer', output='food', demand=1),
    'shelter': dict(label='shared refuge', skill='metallurgy', role='service', output='shelter', demand=0),
    'workshop': dict(label='reclamation workshop', skill='metallurgy', role='producer', output='scrap', demand=1),
    'exchange': dict(label='field exchange', skill='metallurgy', role='business', output='trade', demand=0),
    'relay': dict(label='route relay', skill='fractech', role='service', output='context', demand=1),
}
POSITIONS = [[2, -1], [-2, 1], [0, -3], [-3, 0], [3, -2], [0, 3], [-2, 3]]


def ensure(w, c, engine):
    if 'infrastructure' in c:
        for node in c['infrastructure']['nodes']:
            visuals.ensure_node(w,c,node);materials.ensure_node(w,c,node)
        return c['infrastructure']
    rules = w['rules']['generation']
    g = engine.rng(w['seed'], 'rose-infrastructure-v1', c['x'], c['y'])
    landmark = c.get('landmark') or {}
    services = landmark.get('services', [])
    opening = [c['x'], c['y']] == w.get('spawn', [0, 0])
    chosen = ['power', 'water']
    for kind in ['garden', 'shelter', 'workshop', 'exchange', 'relay']:
        required = (opening and kind in {'garden', 'shelter', 'workshop', 'exchange'}) or (kind == 'shelter' and 'shelter' in services) or (kind == 'exchange' and any(x in services for x in ['trade', 'craft', 'mods', 'register']))
        if required or g.randrange(100) < rules['infrastructure_density']:
            chosen.append(kind)
    nodes = []
    positions = copy.deepcopy(POSITIONS)
    g.shuffle(positions)
    material = {'WN_TOWER': 'darkwood and bio-plast', 'CITY_CLOUD_S': 'salvaged metal',
                'ENACT_HILLS': 'worked metal and earth', 'AETHERGALE': 'crystal and tent fabric'}[c['region']]
    for i, kind in enumerate(chosen):
        nodes.append(dict(id=f'{kind}-{i}', kind=kind, name=TYPES[kind]['label'],
                          pos=positions[i][:], condition=max(30, min(95, rules['starting_condition'] + g.randint(-14, 14))),
                          enabled=True, material=material, faction=engine.REGIONS[c['region']]['faction'],
                          capacity=2 + g.randrange(3), status='awaiting cycle', repaired_by=[], work_serial=0, ledger=[]))
        visuals.ensure_node(w,c,nodes[-1])
        materials.ensure_node(w,c,nodes[-1])
    links = []
    connected = [nodes[0]]
    for node in nodes[1:]:
        parent = min(connected, key=lambda a: hx.distance(a['pos'], node['pos']))
        links.append(dict(a=parent['id'], b=node['id'], condition=80,
                          path=hx.line(parent['pos'], node['pos'])))
        connected.append(node)
    cap = w['rules']['infrastructure']['storage_cap']
    c['infrastructure'] = dict(schema=1, nodes=nodes, links=links,
                               population=rules['population'] if landmark or opening else max(2, rules['population'] // 2),
                               stores=dict(power=0, water=min(4, cap), food=min(3, cap), scrap=min(2, cap)),
                               cap=cap, last_cycle=-1, generation=copy.deepcopy(rules),
                               metrics=dict(power_generated=0, power_spent=0, water_produced=0, food_produced=0,
                                            water_consumed=0, food_consumed=0, cultivation_water_used=0, unmet_water=0, unmet_food=0), ledger=[])
    return c['infrastructure']


def network(data):
    working = {n['id'] for n in data['nodes'] if n['enabled'] and n['condition'] >= 30}
    roots = [n['id'] for n in data['nodes'] if n['kind'] == 'power' and n['id'] in working]
    powered = set(roots)
    for _ in data['nodes']:
        for edge in data['links']:
            if edge['condition'] < 30 or edge['a'] not in working or edge['b'] not in working:
                continue
            if edge['a'] in powered or edge['b'] in powered:
                powered.update([edge['a'], edge['b']])
    return powered


def record(w, data, message, node=None, subject=None):
    item = dict(tick=w['tick'], text=message)
    if subject:item.update(actor=subject['id'],work_serial=node['work_serial'])
    data['ledger'].append(item)
    data['ledger'] = data['ledger'][-30:]
    if node:
        node['ledger'].append(item.copy())
        node['ledger'] = node['ledger'][-10:]


def refresh_support(c):
    data=c['infrastructure'];powered=network(data)
    c['network_bonus']=int(any(n['kind']=='relay' and n['status']=='working' and n['id'] in powered for n in data['nodes']))


def public(w, c, p):
    data = copy.deepcopy(c['infrastructure'])
    connected = network(data)
    for node in data['nodes']:
        node['connected'] = node['id'] in connected
        node['adjacent'] = hx.distance(p['local']['pos'], node['pos']) == 1
        node['definition'] = TYPES[node['kind']].copy()
        if node['kind']=='garden':node['growth']=c['growth'];node['moisture']=c['moisture']
    return data


def cycle(w, engine):
    rules = w['rules']['infrastructure']
    if w['tick'] % rules['cycle_ticks']:
        return
    for c in w['cells'].values():
        data = ensure(w, c, engine)
        if data['last_cycle'] == w['tick']:
            continue
        data['last_cycle'] = w['tick']
        storm = engine.weather(w, c) in {'particulate storm', 'contrail squall'}
        for node in data['nodes']:
            damp=c['moisture']>=75
            organic=c['region']=='WN_TOWER' and node['kind'] in {'shelter','workshop','exchange'}
            corrosion=c['region']=='CITY_CLOUD_S' and damp and w['tick']%12==0
            fabric=c['region']=='AETHERGALE' and storm and node['kind'] in {'shelter','exchange'} and not weathering.braced(node)
            extra=int((organic and damp) or corrosion or fabric or (node['kind']=='garden' and c['moisture']<20))
            materials.ensure_node(w,c,node)
            if materials.damage(node,rules['wear']+int(storm)+extra,w['tick'],'weather'):
                materials.collapse_node(w,c,node,engine)
        if storm:
            for edge in data['links']:
                edge['condition'] = max(0, edge['condition'] - 1)
        powered = network(data)
        stores, metrics = data['stores'], data['metrics']
        cap = data['cap']
        metrics.update(power_generated=0, power_spent=0, water_produced=0, food_produced=0,
                       water_consumed=0, food_consumed=0, cultivation_water_used=0)
        for node in data['nodes']:
            if node['kind'] == 'power' and node['id'] in powered:
                gain = min(cap - stores['power'], rules['power_output'] + int(storm))
                stores['power'] += gain
                metrics['power_generated'] += gain
        for node in sorted(data['nodes'], key=lambda n: {'water': 0, 'garden': 1, 'relay': 2}.get(n['kind'], 3)):
            if node.get('ruin_registered'):
                node['status']='ruined';continue
            node['status'] = 'disconnected' if node['id'] not in powered else 'working'
            if node['condition'] < 30 or not node['enabled']:
                node['status'] = 'offline'
                continue
            demand = TYPES[node['kind']]['demand']
            if demand and (node['id'] not in powered or stores['power'] < demand):
                node['status'] = 'power deficit'
                continue
            if node['kind'] == 'water':
                quantity = min(node['capacity'], cap - stores['water'], c['water'])
                if not quantity:
                    node['status'] = 'no source water or full store'
                    continue
                c['water'] -= quantity
                stores['water'] += quantity
                metrics['water_produced'] += quantity
            elif node['kind'] == 'garden':
                quantity = min(node['capacity'], cap - stores['food'], c['food'], stores['water'])
                if not quantity or c['growth'] < 20:
                    node['status'] = 'cultivation input deficit'
                    continue
                c['food'] -= quantity
                stores['food'] += quantity
                stores['water'] -= quantity
                metrics['cultivation_water_used'] += quantity
                metrics['food_produced'] += quantity
                c['growth'] = max(0, c['growth'] - 1)
            elif node['kind'] == 'workshop':
                quantity = min(1, cap - stores['scrap'], c['scrap'])
                if not quantity:
                    node['status'] = 'no salvage or full store'
                    continue
                c['scrap'] -= quantity
                stores['scrap'] += quantity
            if demand:
                stores['power'] -= demand
                metrics['power_spent'] += demand
        # Residents consume public stores; players and recruited companions keep their own packs.
        water_need = max(1, (data['population'] + 7) // 8)
        food_need = max(1, (data['population'] + 11) // 12)
        for resource, need in [('water', water_need), ('food', food_need)]:
            used = min(stores[resource], need)
            stores[resource] -= used
            metrics[resource + '_consumed'] = used
            metrics['unmet_' + resource] = need - used
        refresh_support(c)
        record(w, data, f"Generated {metrics['power_generated']} wind power; transferred {metrics['water_produced']} source water and {metrics['food_produced']} local food; cultivation used {metrics['cultivation_water_used']} water. Resident demand used {metrics['water_consumed']} water and {metrics['food_consumed']} food; unmet water {metrics['unmet_water']}, food {metrics['unmet_food']}.")


def parse(text):
    patterns = {
        'structure_inspect': r'(?:inspect|survey) structure(?:\s+(.+))?',
        'structure_repair': r'(?:repair|maintain) structure\s+(.+)',
        'structure_toggle': r'toggle structure\s+(.+)',
        'structure_draw': r'draw (?:from )?structure\s+(.+)',
        'structure_contract': r'(?:accept (?:an? )?infrastructure contract|commission structure)(?:\s+(.+))?',
        'structure_fulfill': r'complete infrastructure contract',
    }
    for action, pattern in patterns.items():
        match = re.fullmatch(pattern, text.lower().strip())
        if match:
            return dict(action=action, target=(match.group(1) or '') if match.lastindex else '')
    return None


def autonomous_repair(w, a, c, engine):
    import scene
    import lifecycle
    scene.sync(w,c,engine)
    building=lifecycle.autonomous_build(w,a,c,engine)
    if building:return building
    item=materials.ensure_gear(a,w['tick'])['field_staff']
    cost=2 if item['condition']<=0 else 1
    if item['condition']<60 and a['inventory']['scrap']>=cost:
        a['inventory']['scrap']-=cost
        if cost==2:materials.replace_record(a,'field_staff',w['tick'])
        else:item['condition']=min(100,item['condition']+25);item['material_state']['repair_inputs']+=1
        scene.pose(c['scene'],a,'work')
        return 'Spent '+str(cost)+' personal scrap maintaining a worn field staff before further infrastructure work.'
    candidates=[n for n in c['infrastructure']['nodes'] if n['condition']<85 and not n.get('ruin_registered')]
    if not candidates:return None
    node=min(candidates,key=lambda n:n['condition'])
    if hx.distance(a['local']['pos'],node['pos'])>1:
        routes=[hx.path(c['scene']['tiles'],a['local']['pos'],pos,scene.occupied(w,c,a['id'])) for pos in hx.neighbors(node['pos'])]
        routes=[r for r in routes if r]
        if not routes:return 'No physical approach to the planned structure was available.'
        route=min(routes,key=len)
        if len(route)>1:scene.pose(c['scene'],a,'walk',route[1])
        return 'Moved one actual hex toward '+node['name']+' for a later work cycle.'
    if not a['inventory']['scrap']:return 'Deferred infrastructure work until personal scrap is available.'
    a['inventory']['scrap']-=1;node['condition']=min(100,node['condition']+15)
    materials.ensure_node(w,c,node)['repair_inputs']+=1
    node['work_serial']+=1
    refresh_support(c)
    record(w,c['infrastructure'],a['name']+' spent one NPC scrap to repair '+node['id']+'.',node)
    scene.pose(c['scene'],a,'work')
    return 'Spent one personal scrap to restore 15 structure condition at '+node['name']+'.'


def handle(w, p, intent, raw, engine):
    import scene
    c = engine.local(w, p)
    s = scene.sync(w, c, engine)
    data = c['infrastructure']
    op, target = intent['action'], intent.get('target', '')
    if op == 'structure_fulfill' or (op == 'fulfill' and (p.get('contract') or {}).get('kind') == 'infrastructure'):
        commitment = p.get('contract') or {}
        engine.require(commitment.get('kind') == 'infrastructure' and commitment['target'] == p['pos'], 'Return to your commissioned structure.')
        target = commitment['node']
        op = 'structure_fulfill'
    node = next((n for n in data['nodes'] if target in [n['id'], n['kind'], n['name']]), None)
    if not target:
        candidates=[n for n in data['nodes'] if op=='structure_inspect' or not n.get('ruin_registered')]
        node = min(candidates, key=lambda n: n['condition']) if candidates else None
    engine.require(node is not None, 'Choose a structure ID from the local infrastructure panel.')
    if op!='structure_inspect':engine.require(not node.get('ruin_registered'),'This structure is rubble. Clear its materials and commission a new foundation.')
    context = dict(faction=node['faction'], action=op)
    timing = op not in {'structure_inspect', 'structure_contract'}
    if op in {'structure_repair', 'structure_toggle', 'structure_draw', 'structure_fulfill'}:
        engine.require(hx.distance(p['local']['pos'], node['pos']) == 1, 'Approach an adjacent hex beside this structure first.')
    if op == 'structure_inspect':
        ok, mechanics = engine.check(w, p, 'percept', 10, 'fractech', context)
        out = f"{node['name']} [{node['id']}] at hex {node['pos']}: {node['material']}, condition {node['condition']}, {node['status']}; public stores {data['stores']}. "
        out += 'The local operating limits are distinguishable.' if ok else 'The public ledger remains visible; fault interpretation is uncertain.'
    elif op == 'structure_repair':
        engine.require(node['condition'] < 95, 'The structure is already maintained.')
        engine.require(p['inventory']['scrap'] >= 1, 'This repair consumes one scrap.')
        p['inventory']['scrap'] -= 1
        ok, mechanics = engine.check(w, p, 'tech', w['rules']['infrastructure']['repair_dc'], TYPES[node['kind']]['skill'], context)
        if ok:
            node['condition'] = min(100, node['condition'] + 25)
            materials.ensure_node(w,c,node)['repair_inputs']+=1
            node['work_serial'] += 1
            node['repaired_by'] = list(dict.fromkeys([*node['repaired_by'], p['id']]))[-6:]
            for edge in data['links']:
                if node['id'] in [edge['a'], edge['b']]:
                    edge['condition'] = min(100, edge['condition'] + 10)
            c['stability'] = engine.clamp(c['stability'] + 5)
            refresh_support(c)
            p['xp'] += 1
            engine.standing(w, p, node['faction'], 1)
            engine.adventure.after_work(w, p, 'restore', True)
            out = f"You restore {node['name']} to condition {node['condition']} and reinforce its adjoining connections."
            record(w, data, p['name'] + ' repaired ' + node['id'] + ' with one personal scrap.', node, p)
            scene.pose(s, p, 'work')
        else:
            out = 'The repair fails to hold; one scrap is spent and the structure retains its prior condition.'
    elif op == 'structure_toggle':
        ok, mechanics = engine.check(w, p, 'tech', 10, 'fractech', context)
        if ok:
            node['enabled'] = not node['enabled']
            node['status'] = 'awaiting cycle' if node['enabled'] else 'offline'
            refresh_support(c)
            out = node['name'] + (' is enabled for the next utility cycle.' if node['enabled'] else ' is isolated from the operating network.')
            record(w, data, p['name'] + ' changed ' + node['id'] + ' operating scope.', node)
        else:
            out = 'The parameter check fails; operating scope is unchanged.'
    elif op == 'structure_draw':
        resource = {'water': 'water', 'garden': 'food', 'workshop': 'scrap'}.get(node['kind'])
        engine.require(resource is not None, 'Draw supplies from a cistern, cultivation frame or workshop.')
        engine.require(node['enabled'] and node['condition'] >= 30, 'Restore and enable this apparatus first.')
        engine.require(data['stores'][resource] > 0 and p['inventory'][resource] < 99, 'The public store needs actual stock and your pack needs space.')
        ok, mechanics = engine.check(w, p, 'tech', 11, 'resource', context)
        if ok:
            data['stores'][resource] -= 1
            p['inventory'][resource] += 1
            out = 'You transfer one public ' + resource + ' into your pack.'
            record(w, data, p['name'] + ' drew one actual ' + resource + '.', node)
        else:
            out = 'The safe transfer check fails; no supply moves.'
    elif op == 'structure_contract':
        engine.require(p.get('contract') is None, 'Complete or abandon your current commitment first.')
        engine.require(node['condition'] < 85, 'Choose a structure below its maintenance target of 85.')
        ok, mechanics = engine.check(w, p, 'rapport', 11, 'contracts', context)
        if ok:
            p['contract'] = dict(kind='infrastructure', target=p['pos'][:], destination=c['title'], node=node['id'],
                                 faction=node['faction'], goal=85, accepted_serial=node['work_serial'],
                                 reward='3 scrap, 2 XP, +2 standing', accepted_tick=w['tick'])
            out = f"You commit to repair {node['name']} [{node['id']}] to condition 85, then fulfill beside it. Your own recorded repair is required."
        else:
            out = 'The maintenance terms remain unsigned; no commitment is accepted.'
    else:
        commitment = p['contract']
        engine.require(node['condition'] >= commitment['goal'], 'The commissioned structure has not reached condition 85.')
        repaired = any(e.get('actor')==p['id'] and e.get('work_serial',0)>commitment['accepted_serial'] for e in node['ledger'])
        engine.require(p['id'] in node['repaired_by'] and repaired, 'Record your own successful repair after accepting this commitment.')
        engine.require(p['inventory']['scrap'] <= 96, 'Make room for three scrap.')
        ok, mechanics = engine.check(w, p, 'rapport', 10, 'contracts', context)
        if ok:
            p['inventory']['scrap'] += 3
            p['xp'] += 2
            engine.standing(w, p, node['faction'], 2)
            w['contracts_completed'] += 1
            p['contract_history'].append(dict(**copy.deepcopy(commitment),completed_tick=w['tick']))
            p['contract_history']=p['contract_history'][-60:]
            p['contract'] = None
            out = 'The maintenance record is accepted: three scrap, two XP and two standing. This commitment is closed.'
            record(w, data, p['name'] + ' closed the maintenance commitment.', node)
        else:
            out = 'The maintenance record needs another review; your commitment remains open.'
    return dict(text=out, mechanics=mechanics, intent=intent, time_spent=timing)
