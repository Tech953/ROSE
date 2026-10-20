"""Local object observation and a read-only catalogue of concrete field actions."""
import copy
import re
import characters
import companions
import hexgrid as hx
import infrastructure
import photonics
import machines
import materials
import scene

ACTS = {'field_look', 'field_dialogue', 'companion_yield'}
RESIDENT_TOPICS = {'place', 'history', 'needs'}
TEXTURES = {
    'power': 'Broad blades hang above a braced mast. Wear polishes the edges where wind and grit meet.',
    'water': 'A collector folds toward the cistern lip; mineral traces mark the seams of its holding vessel.',
    'garden': 'Cultivation beds hold a close weave of stems, worked soil and carefully fastened support ribs.',
    'shelter': 'A low canopy pulls taut over its frame. Patched seams divide the weathered surface into a history of repairs.',
    'workshop': 'The reclamation bench carries scored work surfaces and fitted salvage. Its stock belongs to the public works ledger.',
    'exchange': 'A broad awning covers the exchange counter. Supplies and prices are accounted for in the local business ledger.',
    'relay': 'A slender relay rises from its service housing. Small fittings interrupt the long, deliberate silhouette.',
    'rock': 'A heavy mineral shoulder breaks the walking surface. Its rough planes shelter a narrow margin of ground.',
    'path': 'Repeated passage has pressed a route through the ground; its edges retain the surrounding material.',
    'ground': 'The surface changes under the fixed light: small ridges, worn patches and sheltered depressions remain distinct.',
}


def parse(text):
    value = text.strip()
    match = re.fullmatch(r'look (?:at )?(structure|unit|hex)\s+(.+)', value, re.I)
    if match:
        return dict(action='field_look', target=match[1].lower() + ':' + match[2])
    match = re.fullmatch(r'ask (.+?) to (?:make room|step aside)', value, re.I)
    return dict(action='companion_yield', target=match[1]) if match else None


def target(w, c, selector, engine):
    kind, _, identity = selector.partition(':')
    if kind == 'structure':
        found = next((n for n in c['infrastructure']['nodes'] if identity in {n['id'], n['kind'], n['name']}), None)
    elif kind == 'unit':
        players, npcs = scene.locals_here(w, c)
        found = next((a for a in [*players, *npcs] if a['id'] == identity), None)
        if identity == 'threat':
            found = c.get('threat')
    elif kind == 'hex':
        found = c['scene']['tiles'].get(hx.key(hx.parse(identity)))
    else:
        found = None
    engine.require(found is not None, 'Choose a registered object, person or hex in this local field.')
    return kind, found


def yield_destinations(w, c, p, ally):
    """One physical step that preserves solid tiles and every living occupant."""
    blocked = {hx.key(pos) for pos in scene.occupied(w, c, ally['id'])}
    options = [pos for pos in hx.neighbors(ally['local']['pos'])
               if c['scene']['tiles'].get(hx.key(pos), {}).get('passable') and hx.key(pos) not in blocked]
    # Moving away from the player's feet clears a corridor before choosing a side.
    return sorted(options, key=lambda pos: (-hx.distance(pos, p['local']['pos']), hx.key(pos)))


def yield_reason(w, c, p, ally):
    if ally.get('owner') != p['id']:
        return 'Only your own companion can be asked to make room.'
    if hx.distance(p['local']['pos'], ally['local']['pos']) != 1:
        return 'Stand one hex beside this companion.'
    if ally['health'] < 35 or ally['energy'] < 15 or ally['attitude'] < 30 or ally['engagement']['phase'] == 'recover':
        return 'This companion needs care, rest or a willing agreement first.'
    if not yield_destinations(w, c, p, ally):
        return 'No free adjacent hex is available; clear another approach.'
    return ''


def handle(w, p, intent, raw, engine):
    c = engine.local(w, p)
    s = scene.sync(w, c, engine)
    op, selector = intent['action'], intent.get('target', '')
    if op == 'field_look':
        kind, obj = target(w, c, selector, engine)
        context = dict(action=op)
        if kind == 'structure':
            context['faction'] = obj['faction']
            text = f"{obj['name']} [{obj['id']}]. {TEXTURES[obj['kind']]} "
            text += f"Its registered material is {obj['material']}; condition {obj['condition']}/100, {obj['status']}. "
            if obj.get('material_state'):text+=f"Its surface is {materials.phase(obj)}; {obj['material_state']['salvage_remaining']} scrap remain recoverable from any registered collapse. "
            if obj.get('machine'):text+='Its fitted '+obj['machine']['label']+' is '+obj['machine']['status']+'. '
            detail = 'The arrangement of the service fittings becomes legible against the wear.'
        elif kind == 'hex':
            text = f"Axial hex {obj['pos']}. {TEXTURES.get(obj['prefab'], TEXTURES['ground'])} "
            text += f"The field record marks it {'walkable' if obj['passable'] else 'solid'}, with cover +{obj['cover']}. "
            if obj.get('material_state'):text+=f"The rock is {materials.phase(obj)}, condition {obj['condition']}/100. "
            detail = 'You distinguish the protected edges from the exposed walking surface.'
        elif obj is c.get('threat'):
            text = f"{obj['name']}. A low mechanical body stands over articulated supports. "
            text += f"The field record marks health {obj['health']} and state {obj['state']}. "
            detail = 'You separate the exposed frame from the surrounding cover.'
        else:
            ch = obj['character']
            context['npc'] = obj['id'] if obj not in w['players'] else None
            import visuals
            design = visuals.ensure_actor(w,obj)
            appearance = ch['appearance'] or visuals.CATALOG['profiles'][design['model']]['description']
            text = f"{obj['name']} / {ch['pronouns']}. {appearance}" + ('' if appearance.endswith(('.', '!', '?')) else '.') + ' '
            if ch['mannerisms']:
                text += ch['mannerisms'].rstrip('.') + '. '
            text += f"Recorded health {obj.get('health', 100)}/100. "
            detail = 'The details of their registered appearance remain recognizable in this light.'
        region = engine.REGIONS[c['region']]
        text += f"Around the subject: {region['scent']}; {region['sound']}. "
        if p['remote']:
            text = 'UNVERIFIED REMOTE PROJECTION. ' + text
        ok, mechanics = engine.check(w, p, 'percept', 9, 'percept', context)
        text += detail if ok else 'The public record remains readable; the finer sensory interpretation is uncertain.'
        return dict(text=text, mechanics=mechanics, intent=intent, time_spent=False)
    if op == 'field_dialogue':
        identity, _, topic = selector.partition('|')
        obj = next((a for a in w.get('residents', {}).values() if a['id'] == identity), None)
        engine.require(obj and [obj['x'], obj['y']] == p['pos'], 'Choose the resident present in this field.')
        engine.require(hx.distance(p['local']['pos'], obj['local']['pos']) <= 2, 'Approach within two hexes of this resident.')
        engine.require(obj['health'] > 0 and topic in RESIDENT_TOPICS, 'Choose place, history or needs for a living resident.')
        # The mapped dialogue system records the actual source resident and character voice.
        engine.require(engine.adventure.resident(w, p) is obj, 'This resident is not the current mapped encounter.')
        result = engine.adventure.handle(w, p, dict(action='dialogue', target=topic), raw, engine)
        result['intent'] = intent
        return result
    ally = companions.find(w, selector)
    engine.require(ally and [ally['x'], ally['y']] == p['pos'], 'Choose your companion in this field.')
    engine.require(not engine.tactical.active(c), 'Make-room requests are available outside combat.')
    engine.require(not yield_reason(w, c, p, ally), yield_reason(w, c, p, ally))
    ok, mechanics = engine.check(w, p, 'rapport', 9, 'community', dict(action=op, npc=ally['id']))
    if ok:
        destination = yield_destinations(w, c, p, ally)[0]
        scene.pose(s, ally, 'walk', destination)
        ally['energy'] -= 1
        companions.event(w, ally, 'Made room for ' + p['name'] + ' with one physical step.')
        text = ally['name'] + f" steps to hex {destination}, clearing their previous position."
    else:
        text = ally['name'] + ' asks for a clearer direction and keeps their position.'
    return dict(text=text, mechanics=mechanics, intent=intent, time_spent=False)


def public(w, c, p, units, engine):
    """No rolls, mutations or hidden automatic movement while constructing menus."""
    common = ('The host must begin the expedition.' if not w['started'] else
              'The host has paused this world.' if w['paused'] else '')
    work = common or ('Return from remote observation before physical work.' if p['remote'] else
                      'Resolve this encounter before ordinary field work.' if engine.tactical.active(c) else '')
    result = {}

    def option(group, label, action, selector, stat, skill, dc, reason='', cost='', default=False):
        return dict(group=group, label=label, intent=dict(action=action, target=selector),
                    skill=characters.SKILLS[skill]['label'], training=p['character']['skills'].get(skill, 0),
                    stat=stat, dc=dc, reason=reason, cost=cost, default=default)

    def look(selector):
        return option('look', 'LOOK', 'field_look', selector, 'percept', 'percept', 9, common, 'No AP or survival cycle')

    for node in c['infrastructure']['nodes']:
        selector = 'structure:' + node['id']
        adjacent = work or ('Approach an adjacent hex before physical work.' if hx.distance(p['local']['pos'], node['pos']) != 1 else '')
        repair = adjacent or ('Already maintained.' if node['condition'] >= 95 else 'Repair needs one scrap.' if not p['inventory']['scrap'] else '')
        actions = [look(selector)]
        actions[0]['default'] = True
        actions += [option('skill', 'INSPECT', 'structure_inspect', node['id'], 'percept', 'fractech', 10, work, 'No survival cycle'),
                    option('item', 'REPAIR / 1 SCRAP', 'structure_repair', node['id'], 'tech', infrastructure.TYPES[node['kind']]['skill'],
                           w['rules']['infrastructure']['repair_dc'], repair, '1 scrap; 1 survival cycle, including on setback'),
                    option('use', 'TOGGLE SCOPE', 'structure_toggle', node['id'], 'tech', 'fractech', 10, adjacent, '1 survival cycle')]
        if node['kind'] == 'workshop':
            fields = w.get('substrate', {}).get('fields', {})
            f = fields.get('base:' + engine.key(c['x'], c['y']), {})
            ph = f.get('photonics', {})
            baseline = ('Return through the recorded trace for baseline optical work.' if p.get('percept', {}).get('address') else '')
            unresolved = f.get('unresolved_reason', '') or (engine.particles.UNRESOLVED_REASON if not f and len(fields) >= engine.particles.MAX_FIELDS else '')
            optical = work or baseline or unresolved
            read = option('look', 'READ RESONANCE', 'particle_survey', node['id'], 'percept', 'light', 10,
                          common or baseline, 'No AP, supplies or survival cycle')
            tune = option('skill', 'TUNE SPECTRUM', 'particle_tune', node['id'] + '|' + ph.get('band', 'cyan') + ':' + ph.get('mode', 'steady'),
                          'tech', 'light', 12, optical or photonics.control_reason(f, c, p, 'particle_tune', node),
                          '1 survival cycle, including on setback; no public power')
            tune['settings'] = dict(bands=list(photonics.BANDS), modes=list(photonics.MODES),
                                    band=ph.get('band', 'cyan'), mode=ph.get('mode', 'steady'), workshop=node['id'])
            actions += [read, tune,
                        option('use', 'EXCITE / 1 PUBLIC POWER', 'particle_excite', node['id'], 'tech', 'light', 11,
                               optical or photonics.control_reason(f, c, p, 'particle_excite', node),
                               '1 public power + 1 survival cycle, including on setback'),
                        option('use', 'QUENCH RESONANCE', 'particle_quench', node['id'], 'tech', 'light', 10,
                               optical or photonics.control_reason(f, c, p, 'particle_quench', node),
                               '1 survival cycle, including on setback; stored energy becomes heat on success; no refund')]
            for kind,definition in machines.APPLICATIONS.items():
                actions.append(option('item','FIT '+kind.upper()+' / 2 SCRAP','machine_fit',node['id']+'|'+kind,
                    'tech','metallurgy',12,optical or machines.reason(w,c,p,f,node,'machine_fit',kind),
                    '2 personal scrap + 1 survival cycle, including on setback'))
            if f.get('mechanism',{}).get('node')==node['id']:
                actions += [option('use','OPERATE MACHINE / 1 PUBLIC POWER','machine_operate',node['id'],
                    'tech','fractech',11,optical or machines.reason(w,c,p,f,node,'machine_operate'),
                    '1 public power + 1 survival cycle, including on setback'),
                    option('use','DISENGAGE MACHINE','machine_stop',node['id'],'tech','fractech',11,
                    optical or machines.reason(w,c,p,f,node,'machine_stop'),'1 survival cycle; remaining motion dissipates')]
        resource = {'water': 'water', 'garden': 'food', 'workshop': 'scrap'}.get(node['kind'])
        if resource:
            reason = adjacent or ('Restore and enable this apparatus first.' if not node['enabled'] or node['condition'] < 30 else
                                 'The public store is empty.' if not c['infrastructure']['stores'][resource] else
                                 'Your pack is full.' if p['inventory'][resource] >= 99 else '')
            actions.append(option('use', 'DRAW ONE SUPPLY', 'structure_draw', node['id'], 'tech', 'resource', 11, reason, 'One public ' + resource + '; 1 survival cycle'))
        if node['kind'] == 'exchange':
            actions.append(option('use', 'REVIEW EXCHANGE', 'business', '', 'percept', 'resource', 10, work, 'No survival cycle'))
        if not p.get('contract') and node['condition'] < 85:
            actions.append(option('skill', 'ACCEPT MAINTENANCE', 'structure_contract', node['id'], 'rapport', 'contracts', 11, work, 'No survival cycle; review commitment terms'))
        commitment = p.get('contract') or {}
        if commitment.get('kind') == 'infrastructure' and commitment.get('node') == node['id']:
            repaired = any(e.get('actor') == p['id'] and e.get('work_serial', 0) > commitment['accepted_serial'] for e in node['ledger'])
            reason = adjacent or ('Restore condition to 85 first.' if node['condition'] < commitment['goal'] else
                                 'Record your own successful repair after accepting.' if p['id'] not in node['repaired_by'] or not repaired else
                                 'Make room for three scrap.' if p['inventory']['scrap'] > 96 else '')
            actions.append(option('skill', 'FULFILL MAINTENANCE', 'structure_fulfill', node['id'], 'rapport', 'contracts', 10, reason, '1 survival cycle; reward on success'))
        if node.get('ruin_registered'):actions=[actions[0]]
        actions+=materials.object_actions(w,c,p,'structure',node,engine)
        result[selector] = dict(name=node['name'], pos=node['pos'][:], actions=actions)
    for unit in units:
        selector = 'unit:' + unit['id']
        actions = [look(selector)]
        actions[0]['default'] = True
        ally = next((a for a in [*w['actors'], *w.get('residents', {}).values()] if a['id'] == unit['id']), None)
        approach = work or ('Approach within two hexes to interact.' if hx.distance(p['local']['pos'], unit['pos']) > 2 else
                           'This person cannot presently respond.' if unit['health'] <= 0 else '')
        if ally:
            if unit['id'].startswith('resident:'):
                actions.append(option('use', 'ASK ABOUT PLACE', 'field_dialogue', ally['id'] + '|place', 'rapport', 'community', 10, approach, 'No survival cycle', True))
                actions.append(option('skill', 'ASK ABOUT HISTORY', 'field_dialogue', ally['id'] + '|history', 'rapport', 'teaching', 10, approach, 'No survival cycle'))
            else:
                agreement = approach or ('This NPC is engaged with another expedition.' if ally.get('owner') not in {None, p['id']} else '')
                actions.append(option('use', 'ASK ABOUT PLANS', 'npc_talk', ally['id'] + '|plans', 'rapport', 'community', 10, agreement, 'No survival cycle', True))
                actions.append(option('skill', 'ASK ABOUT LORE', 'npc_talk', ally['id'] + '|lore', 'percept', 'history', 10, agreement, 'No survival cycle'))
                if ally.get('owner') is None:
                    reason = approach or ('Your expedition already has two companions.' if len(p['companions']) >= 2 else
                                          'This NPC needs care or a willing agreement first.' if ally['attitude'] < 30 or ally['health'] < 35 else
                                          'An agreement offers one food and one water.' if not p['inventory']['food'] or not p['inventory']['water'] else
                                          'Give this NPC four cycles before proposing again.' if w['tick'] < ally.get('recruit_after', 0) else
                                          'The NPC pack needs room for provisions.' if ally['inventory']['food'] >= 99 or ally['inventory']['water'] >= 99 else '')
                    actions.append(option('skill', 'PROPOSE COMPANIONSHIP', 'recruit', ally['id'], 'rapport', 'community', 11, reason, '1 food + 1 water on agreement; 1 survival cycle'))
                if ally.get('owner') == p['id']:
                    actions.append(option('use', 'ASK TO MAKE ROOM', 'companion_yield', ally['id'], 'rapport', 'community', 9, work or yield_reason(w, c, p, ally), 'One companion step and 1 companion energy on success'))
                    for supply in ['food', 'water', 'scrap', 'seed']:
                        reason = approach or ('Your pack has no ' + supply + '.' if not p['inventory'][supply] else 'The companion pack is full.' if ally['inventory'][supply] >= 99 else '')
                        actions.append(option('item', 'GIVE ONE ' + supply.upper(), 'share', ally['id'] + '|' + supply, 'rapport', 'community', 9, reason, '1 ' + supply + ' transferred; 1 survival cycle'))
                    reason = approach or ('Care requires one medkit.' if not p['inventory']['medkit'] else 'No treatment is needed.' if ally['health'] == 100 and not ally['injuries'] and not ally['ailments'] else '')
                    actions.append(option('item', 'MEDKIT / FIELD CARE', 'companion_treat', ally['id'], 'tech', 'medtech', 10, reason, '1 medkit; 1 survival cycle, including on setback'))
            if len(actions) > 1:
                actions[0]['default'] = False
        if unit['mine']:
            reason = engine.tactical.availability(w, c, p, engine)['combat_care']['reason']
            if engine.tactical.active(c):
                actions.append(option('item', 'MEDKIT / 3 AP', 'combat_care', '', 'tech', 'medtech', 10, reason, '1 medkit + 3 AP, including on setback'))
        if unit['kind'] == 'threat' and not unit.get('resolved'):
            avail = engine.tactical.availability(w, c, p, engine)
            for action, label, stat, skill, dc, cost in [('attack', 'STRIKE', 'body', 'transversal', c['threat']['defense'], str(w['rules']['combat']['melee_ap']) + ' AP'),
                                                     ('shoot', 'CRYSTALLIN SHOT', 'body', 'ballistics', c['threat']['defense'], str(w['rules']['combat']['ranged_ap']) + ' AP + 1 scrap'),
                                                     ('parley', 'PARLEY', 'rapport', 'memetic', 13, str(w['rules']['combat']['parley_ap']) + ' AP')]:
                actions.append(option('skill', label, action, 'threat', stat, skill, dc, avail[action]['reason'], cost + ', including on setback'))
        result[selector] = dict(name=unit['name'], pos=unit['pos'][:], actions=actions)
    for tile in c['scene']['tiles'].values():
        if tile['prefab']=='rock':
            selector='hex:'+hx.key(tile['pos'])
            actions=[look(selector)]+materials.object_actions(w,c,p,'hex',tile,engine)
            actions[0]['default']=True
            result[selector]=dict(name='Rock / '+materials.phase(tile),pos=tile['pos'][:],actions=actions)
    result['hex'] = dict(actions=[look('')])
    return copy.deepcopy(result)
