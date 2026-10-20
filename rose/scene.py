"""Persistent local scenes shared by exploration, infrastructure and combat."""
import copy
import hexgrid as hx
import infrastructure
import visuals
import materials
import animations

PALETTES = {
    'WN_TOWER': {'ground': '#26332e', 'edge': '#52604f', 'accent': '#a4c892', 'material': 'darkwood'},
    'CITY_CLOUD_S': {'ground': '#2b3642', 'edge': '#536979', 'accent': '#acd9db', 'material': 'metal'},
    'ENACT_HILLS': {'ground': '#3a352b', 'edge': '#736348', 'accent': '#e0c397', 'material': 'earth'},
    'AETHERGALE': {'ground': '#3c3038', 'edge': '#78606c', 'accent': '#d9acbd', 'material': 'crystal'},
}


def ensure(w, c, engine):
    if 'scene' in c:
        for tile in c['scene']['tiles'].values():
            if tile['prefab']=='rock':materials.ensure(tile,'stone',w['tick'],2)
        return c['scene']
    rules = w['rules']['generation']
    radius = rules['scene_radius']
    infrastructure.ensure(w, c, engine)
    g = engine.rng(w['seed'], 'rose-scene-v1', c['x'], c['y'])
    tiles = {}
    for pos in hx.disk(radius):
        rock = g.randrange(100) < rules['obstacle_density'] and hx.distance(pos) > 1
        tiles[hx.key(pos)] = dict(pos=pos, passable=not rock, opaque=rock, cover=0,
                                  elevation=g.randrange(3), prefab='rock' if rock else 'ground',
                                  variant=g.randrange(4))
    protected = set()
    for direction in hx.DIRS:
        for pos in hx.line([0, 0], [direction[0] * radius, direction[1] * radius]):
            protected.add(hx.key(pos))
    nodes = c['infrastructure']['nodes']
    building_keys = {hx.key(node['pos']) for node in nodes}
    for node in nodes:
        # An accessible apron is part of every prefab. Preserve the central walk network.
        apron = min((p for p in hx.neighbors(node['pos']) if hx.key(p) in tiles and hx.key(p) not in building_keys), key=hx.distance)
        for pos in hx.line([0, 0], apron):
            protected.add(hx.key(pos))
        for pos in hx.neighbors(node['pos']):
            if hx.key(pos) in tiles and hx.key(pos) not in building_keys:
                protected.add(hx.key(pos))
    for key in protected:
        tiles[key].update(passable=True, opaque=False, prefab='path', elevation=0)
    for node in nodes:
        tiles[hx.key(node['pos'])].update(passable=False, opaque=True, prefab=node['kind'], elevation=0)
    for tile in tiles.values():
        if tile['prefab']=='rock':materials.ensure(tile,'stone',w['tick'],2)
        if tile['passable']:
            tile['cover'] = min(2, sum(not tiles[hx.key(p)]['passable'] for p in hx.neighbors(tile['pos']) if hx.key(p) in tiles))
    c['scene'] = dict(id=engine.key(c['x'], c['y']), schema=1, radius=radius, tiles=tiles,
                      palette=PALETTES[c['region']].copy(), encounter=None, events=[], serial=0)
    return c['scene']


def at(w, p, engine):
    return ensure(w, engine.local(w, p), engine)


def locals_here(w, c):
    players = [p for p in w['players'] if p['pos'] == [c['x'], c['y']]]
    npcs = [a for a in [*w['actors'], *w.get('residents', {}).values()]
            if [a['x'], a['y']] == [c['x'], c['y']]]
    return players, npcs


def sync(w, c, engine):
    s = ensure(w, c, engine)
    players, npcs = locals_here(w, c)
    subjects = [*players, *npcs]
    used = set()
    ordered_tiles = sorted((t for t in s['tiles'].values() if t['passable']), key=lambda t: (hx.distance(t['pos']), hx.key(t['pos'])))
    # Preserve saved positions first, so spawning another NPC never displaces a player.
    for subject in subjects:
        local = subject.get('local')
        if local and local['sector'] == s['id'] and hx.key(local['pos']) in s['tiles'] and s['tiles'][hx.key(local['pos'])]['passable']:
            used.add(hx.key(local['pos']))
    for subject in subjects:
        if subject.get('local', {}).get('sector') == s['id']:
            continue
        free = next(t['pos'] for t in ordered_tiles if hx.key(t['pos']) not in used)
        subject['local'] = dict(sector=s['id'], pos=free[:], pose='idle', serial=0)
        used.add(hx.key(free))
    threat = c.get('threat')
    if threat and 'local_pos' not in threat:
        free = [t['pos'] for t in ordered_tiles if hx.distance(t['pos']) >= s['radius'] - 2 and hx.key(t['pos']) not in used]
        threat['local_pos'] = max(free, key=lambda pos: (pos[0], pos[1]))[:]
    return s


def occupied(w, c, ignore=None):
    players, npcs = locals_here(w, c)
    positions = [a['local']['pos'] for a in [*players, *npcs] if a['id'] != ignore and a.get('health', 100) > 0 and a.get('local', {}).get('sector') == c['scene']['id']]
    t = c.get('threat')
    if t and not t['resolved'] and t['health'] > 0 and ignore != 'threat':
        positions.append(t['local_pos'])
    return positions


def face(subject, destination):
    subject['local']['facing']=animations.facing(subject['local']['pos'],destination)


def pose(s, subject, animation, dest=None, trail=None, animate=True):
    path=None
    if dest is not None:
        subject['local']['trail'] = copy.deepcopy(trail or [subject['local']['pos'], list(dest)])
        direction = [dest[i] - subject['local']['trail'][-2][i] for i in range(2)] if len(subject['local']['trail'])>1 else [0,0]
        if tuple(direction) in hx.DIRS:subject['local']['facing']=hx.DIRS.index(tuple(direction))
        subject['local']['pos'] = list(dest)
        path=subject['local']['trail']
    subject['local']['pose'] = animation
    subject['local']['serial'] += 1
    s['serial'] += 1
    if animate:animations.pose(s,subject,animation,path)


def event(w, c, text):
    c['scene']['events'].append(dict(tick=w['tick'], text=text))
    c['scene']['events'] = c['scene']['events'][-24:]


def follow(w, c, p, engine):
    for a in w['actors']:
        if a.get('owner') != p['id'] or [a['x'],a['y']] != p['pos'] or a['health']<35 or a['energy']<15 or a['attitude']<30:
            continue
        if hx.distance(a['local']['pos'],p['local']['pos'])<=1:continue
        candidates=[hx.path(c['scene']['tiles'],a['local']['pos'],pos,occupied(w,c,a['id'])) for pos in hx.neighbors(p['local']['pos'])]
        routes=[r for r in candidates if r]
        if routes:
            route=min(routes,key=lambda r:len(r))
            if len(route)>1:
                pose(c['scene'],a,'walk',route[1]);a['energy']=max(0,a['energy']-1)


def public(w, p, engine):
    c = engine.local(w, p)
    s = sync(w, c, engine)
    players, npcs = locals_here(w, c)
    units = []
    for a in [*players, *npcs]:
        is_player = a in players
        visual = visuals.ensure_actor(w, a)
        units.append(dict(id=a['id'], name=a['name'], pos=a['local']['pos'][:],
                          kind='player' if is_player else 'companion' if a.get('owner') else 'npc',
                          mine=a['id'] == p['id'], health=a.get('health', 100), pose=a['local']['pose'],
                          pose_serial=a['local']['serial'], owner=a.get('owner'),
                          trail=copy.deepcopy(a['local'].get('trail',[])),facing=a['local'].get('facing',0),
                          task=a.get('engagement', {}).get('task', 'local duties'),
                          visual=copy.deepcopy(visual), visual_label=visuals.designation(visual)))
    t = c.get('threat')
    if t:
        units.append(dict(id='threat', name=t['name'], pos=t['local_pos'][:], kind='threat',
                          health=t['health'], mine=False, pose='down' if t['health'] <= 0 else 'guard' if not t['resolved'] else 'idle',
                          pose_serial=t.get('pose_serial', 0), resolved=t['resolved']))
        units[-1]['trail']=copy.deepcopy(t.get('trail',[]));units[-1]['facing']=t.get('facing',0)
    result = {k: copy.deepcopy(v) for k, v in s.items() if k != 'encounter'}
    result['units'] = units
    result['animation'] = animations.public(s)
    result['infrastructure'] = infrastructure.public(w, c, p)
    result['lifecycle'] = engine.lifecycle.public(w,c,p,engine)
    result['weather'] = engine.weathering.public(w,c,p)
    for node in result['infrastructure']['nodes']:
        original = next(n for n in c['infrastructure']['nodes'] if n['id']==node['id'])
        node['visual'] = copy.deepcopy(visuals.ensure_node(w, c, original))
        node['visual_label'] = visuals.designation(node['visual'])
        node['surface_view'] = engine.weathering.public_object(original)
    for project in result['lifecycle']['projects']:
        original=next((n for n in c['lifecycle']['projects'] if n['id']==project['id']),None)
        project['surface_view']=engine.weathering.public_object(original) if original else None
    for tile in result['tiles'].values():
        if tile['prefab']=='rock':
            tile['visual']={'model':'rock_'+c['region'], 'tone':tile['variant']%3}
            tile['surface_view']=engine.weathering.public_object(c['scene']['tiles'][hx.key(tile['pos'])])
    result['combat'] = copy.deepcopy(s.get('encounter'))
    result['ap_rules'] = w['rules']['combat'].copy()
    result['action_availability'] = engine.tactical.availability(w, c, p, engine)
    result['interaction_options'] = engine.interactions.public(w, c, p, units, engine)
    result['reachable'] = []
    encounter = s.get('encounter')
    own_turn = encounter and encounter['active'] and encounter['current'] == p['id']
    budget = encounter['ap'].get(p['id'], 0) // w['rules']['combat']['move_ap'] if own_turn else None
    if not encounter or not encounter['active'] or own_turn:
        for tile in s['tiles'].values():
            if not tile['passable']:
                continue
            path = hx.path(s['tiles'], p['local']['pos'], tile['pos'], occupied(w, c, p['id']))
            if path and (budget is None or len(path) - 1 <= budget):
                result['reachable'].append(tile['pos'])
    return result
