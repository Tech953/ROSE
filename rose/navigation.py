"""Continuous world-map travel; local hexes remain a separate bodily scale."""
import copy
import heapq
import math
import re
import geography as geo
import tactical

ACTS = {'goto', 'travel', 'world_map', 'enter_location', 'stop_travel', 'resume_travel'}
SECONDS_PER_UNIT = 2.4


def sector(point):
    return [math.floor(v + .5) for v in point]


def point(value):
    if not isinstance(value, str) or not re.fullmatch(r'-?\d{1,3}(?:\.\d{1,4})?\s*,\s*-?\d{1,3}(?:\.\d{1,4})?', value.strip()):
        raise ValueError('Choose a named destination or a world point written as x,y.')
    result = [float(v) for v in value.split(',')]
    if not all(math.isfinite(v) for v in result) or not (geo.MIN_X-.49 <= result[0] <= geo.MAX_X+.49 and geo.MIN_Y-.49 <= result[1] <= geo.MAX_Y+.49):
        raise ValueError('That point lies outside the interpreted world map.')
    if not geo.info(*sector(result))['passable']:
        raise ValueError('That point is water or a closed border. Choose land or a bridge.')
    return result


def route(start, goal):
    """Eight world directions, weighted terrain, no diagonal cuts through barriers."""
    start, goal = tuple(start), tuple(goal)
    if not geo.info(*goal)['passable']:
        raise ValueError('That destination is not physically accessible.')
    queue, costs, previous = [(0, start)], {start: 0}, {start: None}
    while queue:
        cost, current = heapq.heappop(queue)
        if current == goal:
            break
        if cost > costs[current]:
            continue
        for dx, dy in ((0,-1),(1,0),(0,1),(-1,0),(1,-1),(1,1),(-1,1),(-1,-1)):
            next_pos = (current[0]+dx, current[1]+dy)
            terrain = geo.info(*next_pos)
            if not terrain['passable']:
                continue
            if dx and dy and (not geo.info(current[0]+dx, current[1])['passable'] or not geo.info(current[0], current[1]+dy)['passable']):
                continue
            new_cost = cost + math.hypot(dx, dy) * terrain['cost']
            if new_cost < costs.get(next_pos, math.inf):
                costs[next_pos], previous[next_pos] = new_cost, current
                heapq.heappush(queue, (new_cost, next_pos))
    if goal not in previous:
        raise ValueError('No traversable route was found within the interpreted map.')
    path, current = [], goal
    while previous[current] is not None:
        path.append(list(current))
        current = previous[current]
    return path[::-1]


def ensure(p):
    nav = p.setdefault('overworld', dict(schema=1, mode='local', status='idle', point=p['pos'][:],
        target=(p.get('route') or [None])[-1], body_sector=p['pos'][:], serial=0, reason='', visited=[p['pos'][:]], seen=[]))
    # Migration and field-station recovery keep the two coordinate scales aligned.
    if nav.get('body_sector',p['pos']) != p['pos']:
        p['route'], p['destination'] = [], None
        nav.update(point=p['pos'][:], target=None, mode='local', status='stopped',
                   reason='Position changed in the field. Choose a new destination.', serial=nav['serial']+1)
    nav['body_sector']=p['pos'][:]
    if p['pos'] not in nav['visited']:
        nav['visited'].append(p['pos'][:])
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            pos = [p['pos'][0]+dx, p['pos'][1]+dy]
            if geo.MIN_X <= pos[0] <= geo.MAX_X and geo.MIN_Y <= pos[1] <= geo.MAX_Y and pos not in nav['seen']:
                nav['seen'].append(pos)
    return nav


def parse(text):
    value = text.lower().strip()
    for action, pattern in [('world_map', r'(?:world map|overworld|leave location|leave the field)'),
                            ('enter_location', r'(?:enter location|enter the field|visit location)'),
                            ('stop_travel', r'(?:stop travel|stop traveling|halt travel)'),
                            ('resume_travel', r'(?:resume travel|continue journey)')]:
        if re.fullmatch(pattern, value):
            return dict(action=action, target='')
    match = re.fullmatch(r'(?:go to|route to|navigate to|travel to|head to)\s+(-?\d{1,3}(?:\.\d{1,4})?\s*,\s*-?\d{1,3}(?:\.\d{1,4})?)', value)
    if match:
        return dict(action='goto', target=match.group(1))
    return None


def stop(p, status='stopped', reason='Travel stopped.'):
    nav = ensure(p)
    nav.update(status=status, reason=reason, serial=nav['serial']+1)
    return nav


def recover(p):
    """Recovery can occur at the spawn itself; do not rely on a changed sector."""
    nav = stop(p, 'recovery', 'Field-station recovery interrupted the journey. Choose a new destination.')
    p['route'], p['destination'] = [], None
    nav.update(point=p['pos'][:], target=None, mode='local', body_sector=p['pos'][:])


def hazard(p):
    if p['health'] <= 30 or p['energy'] <= 15 or any(p[k] >= 80 for k in ('thirst', 'food_need', 'sleep')):
        return 'Travel stopped for survival needs. Enter this location to drink, eat, rest or seek care.'
    return None


def handle(w, p, intent, raw, engine):
    op, target = intent['action'], intent.get('target', '')
    engine.require(w.get('layout') == 'atlas', 'World-map travel is available in atlas worlds.')
    nav, roll, out = ensure(p), '', ''
    if op == 'goto':
        if geo.norm(target) == 'commitment':
            engine.require(p.get('contract'), 'Accept a commitment before routing to its target.')
            destination, name = p['contract']['target'][:], p['contract']['destination']
        else:
            landmark_id = geo.resolve(target)
            if landmark_id:
                lm = geo.LANDMARKS[landmark_id]
                destination, name = lm['pos'][:], lm['name']
            else:
                destination = point(target)
                lm = geo.landmark(*sector(destination))
                name = lm['name'] if lm else f'Open terrain [{destination[0]:g},{destination[1]:g}]'
        path = route(p['pos'], sector(destination))
        # Validate everything before replacing an existing journey.
        p['route'], p['destination'] = path, name
        nav.update(mode='world', target=destination, status='traveling', reason='', serial=nav['serial']+1)
        if nav['point'] == destination:
            nav.update(status='arrived', reason='Already at the selected point. Enter this location or choose another destination.')
        ok, roll = engine.check(w, p, 'percept', 9, 'fieldcraft')
        out = f'Journey set to {name}. Travel continues on the world map; select another point to redirect, or Stop to halt.'
        out += ' Your route reading is clear.' if ok else 'The route is registered; changing conditions still need observation.'
    elif op == 'world_map':
        nav['mode'] = 'world'
        out = 'You unfold the world map. Click any land point, including unexplored ground, or choose a named destination.'
    elif op == 'enter_location':
        stop(p, reason='You entered the local field. Your onward route is retained.')
        nav['mode'] = 'local'
        out = 'You enter '+engine.local(w, p)['title']+'. Exploration, dialogue and combat use this local isometric scene.'
    elif op == 'stop_travel':
        stop(p)
        out = 'Journey stopped at the current world point. Enter this location, redirect the route, or resume.'
    elif op == 'resume_travel':
        engine.require(nav.get('target') is not None and (p.get('route') or nav['point'] != nav['target']), 'Choose a new destination on the world map.')
        engine.require(not hazard(p), hazard(p) or '')
        # Revalidate an interrupted or older saved journey from its actual sector.
        path = route(p['pos'], sector(nav['target']))
        p['route'] = path
        nav.update(mode='world', status='traveling', reason='', serial=nav['serial']+1)
        out = 'The journey resumes from your current point.'
    elif op == 'travel':
        # Compatibility with typed "travel next" and earlier Rose journals.
        engine.require(p.get('route'), 'Choose a destination on the world map first.')
        destination = p['route'][0][:]
        if nav.get('target') is None:
            nav['target'] = p['route'][-1][:]
        if destination==p['pos']:
            p['route']=p['route'][1:];nav['point']=destination[:]
            if not p['route'] and nav['point']==nav['target']:stop(p,'arrived','Destination reached. Enter this location or choose another world point.')
            return dict(text='You reach the next route marker inside the current sector.',mechanics='',time_spent=False)
        result = cross(w, p, destination, engine)
        result['already_finalized'] = True
        return result
    return dict(text=out, mechanics=roll, time_spent=False)


def cross(w, p, destination, engine, consume=True, at_point=None):
    nav = ensure(p)
    result = engine.cross_sector(w, p, destination)
    if p['pos'] != destination:
        recover(p)
        return result
    if consume:p['route'] = p['route'][1:]
    nav['point'] = (at_point or destination)[:]
    nav['body_sector']=p['pos'][:]
    ensure(p)
    c = engine.local(w, p)
    if c.get('threat') and not c['threat']['resolved'] and c['threat']['health'] > 0:
        stop(p, 'encounter', 'A hostile construct interrupted your journey. Resolve it in the local field, then resume or redirect.')
        nav['mode'] = 'local'
        tactical.begin(w, c, p, engine)
        engine.emit(w, nav['reason'], 'encounter', p['pos'][:])
    elif hazard(p):
        stop(p, 'needs', hazard(p))
    elif not p['route'] and nav['point'] == nav['target']:
        stop(p, 'arrived', 'Destination reached. Enter this location or choose another world point.')
        result['text'] += ' You have reached the registered route destination.'
        p['last_result'] = result['text']
    return result


def advance(w, p, engine, seconds=1):
    """One bounded host-clock update. No movement while paused, idle or in combat."""
    nav = ensure(p)
    if nav['status'] != 'traveling' or not w['started'] or w['paused'] or p['remote'] or tactical.any_active(w):
        return False
    if hazard(p):
        stop(p, 'needs', hazard(p)); w['revision'] += 1
        return True
    next_point = (p.get('route') or [nav['target']])[0]
    if next_point is None:
        stop(p); w['revision'] += 1
        return True
    distance = math.dist(nav['point'], next_point)
    travel = max(0, min(float(seconds), 1)) / (SECONDS_PER_UNIT * geo.info(*sector(next_point))['cost'])
    new_point = [round(a+(b-a)*min(1,travel/distance),6) for a,b in zip(nav['point'],next_point)] if distance else next_point[:]
    if sector(new_point) != p['pos']:
        cross(w,p,sector(new_point),engine,consume=False,at_point=new_point)
    else:nav['point']=new_point
    if nav['status']=='traveling' and distance <= travel:
        if p.get('route'):p['route']=p['route'][1:]
        if not p.get('route') and nav['point']==nav['target']:
            stop(p,'arrived','Destination reached. Enter this location or choose another world point.')
    nav['serial'] += 1
    w['revision'] += 1
    return True


def public(p):
    result = copy.deepcopy(ensure(p))
    result['seconds_per_unit'] = SECONDS_PER_UNIT
    return result
