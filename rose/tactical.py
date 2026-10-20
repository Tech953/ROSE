"""Action points and ordered turns in the same persistent hex scene as exploration."""
import re
import hexgrid as hx
import scene
import survival
import materials
import animations

ACTS = {'hex_move', 'engage', 'end_turn', 'attack', 'shoot', 'guard', 'parley', 'flee', 'combat_care'}


def any_active(w):
    return any((c.get('scene', {}).get('encounter') or {}).get('active') for c in w['cells'].values())


def active(c):
    return (c.get('scene', {}).get('encounter') or {}).get('active', False)


def availability(w, c, p, engine):
    """Read-only prerequisites for controls; action handlers remain authoritative."""
    s, t, rules = c['scene'], c.get('threat'), w['rules']['combat']
    enc = s.get('encounter') or {}
    common = ('The host must begin the expedition.' if not w['started'] else
              'The host has paused this world.' if w['paused'] else
              'Return from remote observation before acting in the field.' if p['remote'] else '')
    result = {}
    costs = dict(hex_move=rules['move_ap'], attack=rules['melee_ap'], shoot=rules['ranged_ap'],
                 guard=rules['guard_ap'], parley=rules['parley_ap'], combat_care=3, flee=rules['move_ap'])
    for op in ACTS:
        reason = common
        if not reason:
            if op == 'engage':
                reason = ('This encounter is already active.' if enc.get('active') else
                          'No unresolved hostile construct is present.' if not t or t['resolved'] or t['health'] <= 0 else '')
            elif op == 'end_turn':
                reason = ('No encounter is active.' if not enc.get('active') else
                          'Only the current player or host can advance this turn.' if enc['current'] != p['id'] and p['id'] != w['host'] else '')
            elif enc.get('active'):
                reason = ('Wait for your turn.' if enc['current'] != p['id'] else
                          'Not enough AP; end your turn or choose a cheaper action.' if enc['ap'].get(p['id'], 0) < costs[op] else '')
            elif op != 'hex_move':
                reason = 'Begin an encounter before using combat actions.'
        if not reason and op in {'attack', 'shoot', 'parley'}:
            distance = hx.distance(p['local']['pos'], t['local_pos'])
            limit = {'attack': 1, 'shoot': 6, 'parley': 4}[op]
            if distance > limit or (op != 'parley' and distance < 1):
                reason = f'Approach within {limit} visible hexes.'
            elif not hx.visible(s['tiles'], p['local']['pos'], t['local_pos']):
                reason = 'A solid object blocks line of sight.'
            elif op == 'shoot' and ('black.dot' not in p['credentials'] or 'crystallin' not in p['loadout']):
                reason = 'Equip a registered crystallin before shooting.'
            elif op == 'shoot' and p['inventory']['scrap'] < 1:
                reason = 'A shot requires one scrap charge.'
            elif op in {'attack','shoot'} and not materials.operable(p,'crystallin' if op=='shoot' else 'field_staff'):
                reason = 'Repair or replace the worn weapon before attacking.'
        if not reason and op == 'combat_care':
            if p['health'] == 100 and not p['injuries'] and not p['ailments']:
                reason = 'No care is currently needed.'
            elif not p['inventory']['medkit']:
                reason = 'Care requires one medkit.'
        if not reason and op == 'flee':
            if hx.distance(p['local']['pos']) < s['radius'] - 1:
                reason = 'Reach an outer hex before disengaging.'
            elif w['layout'] == 'atlas' and not any(engine.geography.info(p['pos'][0]+dx,p['pos'][1]+dy)['passable'] for dx,dy in engine.DIRS.values()):
                reason = 'No neighboring land sector is available.'
        result[op] = dict(allowed=not reason, reason=reason)
    return result


def parse(text):
    value = text.lower().strip()
    match = re.fullmatch(r'(?:hex|move hex|walk hex)\s+(-?\d{1,3},-?\d{1,3})', value)
    if match:
        return dict(action='hex_move', target=match.group(1))
    exact = {'engage': 'engage', 'begin combat': 'engage', 'end turn': 'end_turn',
             'pass turn': 'end_turn', 'combat care': 'combat_care'}
    return dict(action=exact[value], target='') if value in exact else None


def subjects(w, c, enc):
    live = {p['id']: p for p in w['players'] if p['id'] in enc['participants'] and p['pos'] == [c['x'], c['y']]
            and p['id'] not in enc['withdrawn'] and p['health'] > 0}
    for a in w['actors']:
        if a['id'] in enc['participants'] and a.get('owner') in live and a['health'] > 0:
            live[a['id']] = a
    return live


def log(w, c, text):
    scene.event(w, c, text)
    enc = c['scene']['encounter']
    enc['log'].append(text)
    enc['log'] = enc['log'][-24:]


def points(w, subject, enemy=False):
    rules = w['rules']['combat']
    return rules['enemy_ap'] if enemy else rules['base_ap'] + min(2, subject['character']['attributes']['body'] // 2)


def close(w, c, outcome, engine, beneficiary=None):
    enc = c['scene']['encounter']
    if not enc or not enc['active']:
        return
    enc['active'] = False
    enc['outcome'] = outcome
    enc['current'] = None
    t = c['threat']
    t['state'] = {'disabled': 'disabled', 'truce': 'truce'}.get(outcome, 'watchful')
    if outcome in {'disabled', 'truce'}:
        t['resolved'] = True
        if beneficiary:
            beneficiary['xp'] += 1
            engine.standing(w, beneficiary, engine.REGIONS[c['region']]['faction'], 1)
            if outcome == 'disabled' and not t.get('cache_paid'):
                quantity = min(2, 99 - beneficiary['inventory']['scrap'])
                beneficiary['inventory']['scrap'] += quantity
                t['cache_paid'] = True
                log(w, c, f'{beneficiary["name"]} recovers {quantity} scrap from the disabled construct. The cache is closed.')
    log(w, c, 'Encounter ends: ' + outcome + '. Exploration resumes in the existing scene.')
    # A finished encounter advances one shared ecological cycle. The clock stays fixed during turns.
    engine.tick(w, 'encounter concluded')


def begin(w, c, p, engine):
    t = c.get('threat')
    engine.require(t and not t['resolved'] and t['health'] > 0, 'No unresolved hostile construct is present in this scene.')
    engine.require(not p['remote'], 'Lower the remote apparatus before engaging.')
    scene.sync(w, c, engine)
    humans = [a for a in w['players'] if a['pos'] == p['pos'] and not a['remote'] and a['health'] > 0]
    allies = [a for a in w['actors'] if a.get('owner') in {h['id'] for h in humans} and [a['x'], a['y']] == p['pos']
              and a['health'] >= 35 and a['energy'] >= 15 and a['attitude'] >= 30]
    initiative = {}
    for a in [*humans, *allies]:
        attr = a['character']['attributes']
        initiative[a['id']] = attr['percept'] + attr['body'] + engine.rng(w['seed'], 'initiative', w['tick'], a['id']).randrange(6)
    initiative['threat'] = 5 + engine.rng(w['seed'], 'enemy initiative', c['x'], c['y'], w['tick']).randrange(6)
    ok, roll = engine.check(w, p, 'percept', 10, 'percept', dict(action='engage'))
    if ok:
        initiative[p['id']] += 2
    order = sorted(initiative, key=lambda identity: (-initiative[identity], identity))
    enc = dict(active=True, round=1, order=order, index=0, current=order[0],
               initiative=initiative, participants=[a['id'] for a in [*humans, *allies]],
               humans=[a['id'] for a in humans], withdrawn=[], ap={}, log=[], outcome=None)
    c['scene']['encounter'] = enc
    for a in [*humans, *allies]:
        enc['ap'][a['id']] = points(w, a)
        a['local_guard'] = 0
    enc['ap']['threat'] = points(w, None, True)
    t['state'] = 'engaged'
    log(w, c, 'Combat begins on the current hex scene; sequence follows perception, body and initiative. ' + ', '.join(order))
    run_ai(w, c, engine)
    return roll


def next_turn(w, c, engine):
    enc = c['scene']['encounter']
    if not enc['active']:
        return
    for _ in range(len(enc['order']) + 1):
        enc['index'] = (enc['index'] + 1) % len(enc['order'])
        if enc['index'] == 0:
            enc['round'] += 1
        who = enc['order'][enc['index']]
        live = subjects(w, c, enc)
        if not any(identity in live for identity in enc['humans']):
            close(w, c, 'withdrawn', engine)
            return
        if who == 'threat' or who in live:
            enc['current'] = who
            enc['ap'][who] = points(w, live.get(who), who == 'threat')
            if who in live:
                live[who]['local_guard'] = 0
            return


def spend(w, c, p, cost, engine):
    enc = c['scene']['encounter']
    engine.require(enc and enc['active'] and enc['current'] == p['id'], 'Wait for your turn in the encounter sequence.')
    engine.require(enc['ap'][p['id']] >= cost, 'Not enough action points. End your turn or choose a cheaper action.')
    enc['ap'][p['id']] -= cost


def chase(w, c, actor, target, budget, engine, enemy=False):
    s = c['scene']
    start = c['threat']['local_pos'] if enemy else actor['local']['pos']
    occupied = scene.occupied(w, c, 'threat' if enemy else actor['id'])
    candidates = []
    for pos in hx.neighbors(target['local']['pos']):
        route = hx.path(s['tiles'], start, pos, occupied)
        if route:
            candidates.append(route)
    if not candidates:
        return budget
    route = min(candidates, key=lambda r: (len(r), hx.key(r[-1])))
    steps = min(len(route) - 1, budget // w['rules']['combat']['move_ap'])
    if steps:
        destination = route[steps]
        if enemy:
            c['threat']['local_pos'] = destination[:]
            c['threat']['trail'] = route[:steps+1]
            c['threat']['pose_serial'] = c['threat'].get('pose_serial', 0) + 1
            t=c['threat'];t['facing']=animations.facing(route[steps-1],destination)
            animations.emit(s,'move','threat',steps*animations.STEP_MS,pose='walk',path=route[:steps+1],facing=t['facing'])
        else:
            scene.pose(s, actor, 'walk', destination,route[:steps+1])
        log(w, c, actor['name'] + ' moves ' + str(steps) + ' hexes.')
    return budget - steps * w['rules']['combat']['move_ap']


def companion_turn(w, c, ally, engine):
    enc, t = c['scene']['encounter'], c['threat']
    materials.ensure_gear(ally,w['tick'])
    if ally['health'] < 35 or ally['energy'] < 15 or ally['attitude'] < 30:
        log(w, c, ally['name'] + ' holds back: care, energy or consent is insufficient.')
        return
    task = ally['engagement']['task']
    if task in {'rest', 'guard'} or ally['engagement']['phase'] == 'recover':
        ok, roll = engine.check(w, ally, 'body', 9, 'fieldcraft', dict(action='guard'))
        ally['local_guard'] = 2 if ok and task == 'guard' else 0
        scene.pose(c['scene'], ally, 'guard' if task == 'guard' else 'idle')
        log(w, c, ally['name'] + ' holds their ' + task + ' assignment. ' + roll)
        return
    # Companion movement is physical and respects every occupied hex.
    target = {'local': {'pos': t['local_pos']}}
    budget = chase(w, c, ally, target, enc['ap'][ally['id']], engine)
    cost = w['rules']['combat']['melee_ap']
    if hx.distance(ally['local']['pos'], t['local_pos']) == 1 and budget >= cost and materials.operable(ally,'field_staff'):
        ok, roll = engine.check(w, ally, 'body', t['defense'], 'transversal', dict(action='attack'))
        factor=materials.weapon_use(w,ally)
        if ok:
            damage = max(1,int((5 + ally['character']['attributes']['body'])*factor))
            t['health'] = max(0, t['health'] - damage)
            ally['energy'] = max(0, ally['energy'] - 2)
            log(w, c, ally['name'] + ' deals ' + str(damage) + ' construct damage. ' + roll)
        else:
            log(w, c, ally['name'] + ' cannot find an opening. ' + roll)
        scene.face(ally,t['local_pos']);scene.pose(c['scene'],ally,'attack',animate=False)
        animations.strike(c['scene'],ally['id'],ally['local']['pos'],'unit:threat',t['local_pos'],damage if ok else 0)
        if not t['health']:
            owner = next((p for p in w['players'] if p['id'] == ally['owner']), None)
            close(w, c, 'disabled', engine, owner)
        budget -= cost
    enc['ap'][ally['id']] = budget


def enemy_turn(w, c, engine):
    enc, t = c['scene']['encounter'], c['threat']
    live = subjects(w, c, enc)
    if not live:
        close(w, c, 'withdrawn', engine)
        return
    target = min(live.values(), key=lambda a: (hx.distance(a['local']['pos'], t['local_pos']), a['id']))
    budget = chase(w, c, t, target, enc['ap']['threat'], engine, True)
    cost = w['rules']['combat']['melee_ap']
    if hx.distance(target['local']['pos'], t['local_pos']) == 1 and budget >= cost:
        cover = c['scene']['tiles'][hx.key(target['local']['pos'])]['cover']
        guard = target.get('local_guard', 0)
        ok, roll = engine.check(w, target, 'body', t['attack'], 'fieldcraft',
                                dict(action='guard', modifier=cover + guard, reason=f'hex cover +{cover}, guarded stance +{guard}'))
        damage = 0 if ok else max(1, t['damage'] - (2 if guard else 0))
        defenders = [a for a in live.values() if a.get('owner') == target['id'] and a['health'] >= 35
                     and a.get('local_guard', 0) and hx.distance(a['local']['pos'], target['local']['pos']) <= 1]
        reactions=[]
        if damage and defenders:
            guard_npc = defenders[0]
            share = min(3, damage)
            guard_npc['health'] = max(0, guard_npc['health'] - share)
            damage -= share
            reactions=[dict(target='unit:'+guard_npc['id'],destination=guard_npc['local']['pos'][:],damage=share)]
            log(w, c, guard_npc['name'] + ' shares ' + str(share) + ' health of this adjacent guard action.')
        target['health'] = max(0, target['health'] - damage)
        t['facing']=animations.facing(t['local_pos'],target['local']['pos']);t['pose_serial']=t.get('pose_serial',0)+1
        animations.strike(c['scene'],'threat',t['local_pos'],'unit:'+target['id'],target['local']['pos'],damage,reactions=reactions)
        scene.pose(c['scene'], target, 'hit' if damage else 'guard',animate=not damage)
        log(w, c, t['name'] + ' costs ' + target['name'] + ' ' + str(damage) + ' health. ' + roll)
        if not target['health']:
            if target['id'] in enc['humans']:
                enc['withdrawn'].append(target['id'])
                survival.harm(target, 'impact strain')
                survival.advance(w, target, 1)
                engine.visit(w, *target['pos'])
                log(w, c, target['name'] + ' is recovered to the field station; inventory and injuries remain.')
            else:
                scene.pose(c['scene'], target, 'down')
        budget -= cost
    enc['ap']['threat'] = budget


def run_ai(w, c, engine):
    enc = c['scene']['encounter']
    for _ in range(40):
        if not enc['active']:
            return
        live = subjects(w, c, enc)
        who = enc['current']
        if who in enc['humans'] and who in live:
            return
        if who == 'threat':
            enemy_turn(w, c, engine)
        elif who in live:
            companion_turn(w, c, live[who], engine)
        next_turn(w, c, engine)
    raise ValueError('Encounter sequence could not reach a living player turn.')


def handle(w, p, intent, raw, engine):
    c = engine.local(w, p)
    s = scene.sync(w, c, engine)
    op, target = intent['action'], intent.get('target', '')
    enc, t, rules = s.get('encounter'), c.get('threat'), w['rules']['combat']
    out, mechanics, timing = '', '', False
    if op == 'hex_move':
        destination = hx.parse(target)
        tile = s['tiles'].get(hx.key(destination))
        engine.require(tile and tile['passable'], 'Choose a walkable hex in this scene.')
        engine.require(hx.distance(p['local']['pos'], destination) == 1, 'Movement commits one adjacent hex at a time.')
        engine.require(destination not in scene.occupied(w, c, p['id']), 'That hex is occupied.')
        if active(c):
            spend(w, c, p, rules['move_ap'], engine)
        ok, mechanics = engine.check(w, p, 'body', 8, 'transversal', dict(action='hex_move'))
        scene.pose(s, p, 'walk', destination)
        p['energy'] = max(0, p['energy'] - (1 if ok else 2))
        out = f"You move to axial hex {destination}." + ('' if ok else ' Awkward footing costs one extra energy.')
        if not active(c):
            scene.follow(w,c,p,engine)
            p['local_steps'] = p.get('local_steps', 0) + 1
            timing = p['local_steps'] % 6 == 0
            if t and not t['resolved'] and hx.distance(destination, t['local_pos']) <= rules['trigger_distance'] and hx.visible(s['tiles'], destination, t['local_pos']):
                mechanics += '\n' + begin(w, c, p, engine)
                out += ' The construct reacts; this same scene enters turn-based combat.'
                timing = False
    elif op == 'engage':
        engine.require(not active(c), 'This encounter is already active.')
        mechanics = begin(w, c, p, engine)
        out = 'The scene enters turn-based combat. Review the sequence and your action points.'
    else:
        engine.require(active(c), 'Begin this encounter with Engage, or approach the construct on the local hex scene.')
        engine.require(target in {'', 'threat', t['name']}, 'Combat targets the displayed hostile construct.')
        if op == 'end_turn':
            current = enc['current']
            engine.require(current == p['id'] or p['id'] == w['host'], 'Only the current player or host can advance this turn.')
            _, mechanics = engine.check(w, p, 'percept', 8, 'percept', dict(action='end_turn'))
            enc['ap'][current] = 0
            if current == p['id']:
                recovered = survival.advance(w, p, 1)
                if recovered:
                    engine.navigation.recover(p)
                    enc['withdrawn'].append(p['id'])
            log(w, c, p['name'] + ' ends ' + ('their' if current == p['id'] else 'the waiting player’s') + ' turn.')
            next_turn(w, c, engine)
            run_ai(w, c, engine)
            out = 'The next living participant receives a refreshed AP budget.'
        elif op in {'attack', 'shoot'}:
            ranged = op == 'shoot'
            distance = hx.distance(p['local']['pos'], t['local_pos'])
            engine.require(1 <= distance <= (6 if ranged else 1), 'Move into weapon range: melee 1 hex; crystallin 6 hexes.')
            engine.require(hx.visible(s['tiles'], p['local']['pos'], t['local_pos']), 'A solid structure or terrain prop blocks line of sight.')
            engine.require(materials.operable(p,'crystallin' if ranged else 'field_staff'),'Repair or replace the weapon before attacking.')
            if ranged:
                engine.require('black.dot' in p['credentials'] and 'crystallin' in p['loadout'], 'A crystallin shot requires active registered equipment.')
                engine.require(p['inventory']['scrap'] >= 1, 'A shot consumes one scrap charge.')
            spend(w, c, p, rules['ranged_ap'] if ranged else rules['melee_ap'], engine)
            if ranged:
                p['inventory']['scrap'] -= 1
            cover = s['tiles'][hx.key(t['local_pos'])]['cover'] if ranged else 0
            ok, mechanics = engine.check(w, p, 'body', t['defense'], 'ballistics' if ranged else 'transversal',
                                          dict(action=op, modifier=-cover, reason=f'target hex cover −{cover}'))
            factor=materials.weapon_use(w,p,ranged)
            if ok:
                damage = max(1,int(((9 if ranged else 6) + p['character']['attributes']['body'])*factor))
                t['health'] = max(0, t['health'] - damage)
                out = f"Your {'shot' if ranged else 'field-staff strike'} deals {damage} construct damage."
            else:
                out = 'Your attack fails to find an opening; its action points are spent.'
            scene.face(p,t['local_pos']);scene.pose(s, p, 'attack',animate=False)
            animations.strike(s,p['id'],p['local']['pos'],'unit:threat',t['local_pos'],damage if ok else 0,ranged)
            t['pose_serial'] = t.get('pose_serial', 0) + 1
            if not t['health']:
                close(w, c, 'disabled', engine, p)
                out += ' The construct is disabled and the encounter cache is closed.'
            log(w, c, p['name'] + ': ' + out)
        elif op == 'guard':
            spend(w, c, p, rules['guard_ap'], engine)
            ok, mechanics = engine.check(w, p, 'body', 10, 'fieldcraft', dict(action='guard'))
            p['local_guard'] = 2 if ok else 0
            scene.pose(s, p, 'guard')
            out = 'You hold a guarded stance until your next turn.' if ok else 'The stance does not settle; its AP is spent.'
        elif op == 'parley':
            engine.require(hx.distance(p['local']['pos'], t['local_pos']) <= 4 and hx.visible(s['tiles'], p['local']['pos'], t['local_pos']), 'Approach within four visible hexes to negotiate a transit protocol.')
            spend(w, c, p, rules['parley_ap'], engine)
            ok, mechanics = engine.check(w, p, 'rapport', 13, 'memetic', dict(action='parley'))
            scene.pose(s, p, 'talk')
            out = 'The transit protocol is accepted; exploration resumes without a cache reward.' if ok else 'The proposed protocol is refused; AP is spent.'
            if ok:
                close(w, c, 'truce', engine, p)
        elif op == 'combat_care':
            engine.require(p['health'] < 100 or p['injuries'] or p['ailments'], 'No care is currently needed.')
            engine.require(p['inventory']['medkit'] > 0, 'A combat treatment needs one medkit.')
            spend(w, c, p, 3, engine)
            p['inventory']['medkit'] -= 1
            ok, mechanics = engine.check(w, p, 'tech', 10, 'medtech', dict(action='combat_care'))
            if ok:
                p['health'] = min(100, p['health'] + 25)
                if p['injuries']:
                    p['injuries'].pop(0)
                elif p['ailments']:
                    p['ailments'].pop(0)
            out = 'Field care restores 25 health and one condition.' if ok else 'The treatment fails; one medkit is spent.'
            scene.pose(s, p, 'work')
        elif op == 'flee':
            engine.require(hx.distance(p['local']['pos']) >= s['radius'] - 1, 'Reach an outer hex before disengaging to the next survey sector.')
            candidates = []
            for direction, (dx, dy) in engine.DIRS.items():
                x, y = p['pos'][0] + dx, p['pos'][1] + dy
                if w['layout'] == 'atlas' and not engine.geography.info(x, y)['passable']:
                    continue
                candidates.append((direction, x, y))
            engine.require(candidates, 'No physical neighboring sector is available for withdrawal.')
            spend(w, c, p, rules['move_ap'], engine)
            ok, mechanics = engine.check(w, p, 'body', 11, 'transversal', dict(action='flee'))
            if ok:
                direction, x, y = candidates[0]
                enc['withdrawn'].append(p['id'])
                engine.visit(w, x, y)
                p['pos'], p['route'], p['destination'] = [x, y], [], None
                out = 'You disengage ' + direction + ' into the next physical survey sector.'
                next_turn(w, c, engine)
                run_ai(w, c, engine)
            else:
                out = 'The withdrawal does not open; AP is spent.'
        else:
            raise ValueError('Unsupported tactical action.')
    return dict(text=out, mechanics=mechanics, intent=intent, time_spent=timing)
