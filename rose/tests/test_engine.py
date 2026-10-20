"""Rose engine invariants: topology, conservation, access, turns and persistence."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import engine
import hexgrid as hx
import infrastructure as infra
import scene
import tactical
import world
import server
import companions
import geography


class RoseTest(unittest.TestCase):
    def setUp(self):
        self.dice = patch('world.secrets.randbelow', return_value=19)
        self.dice.start()
        self.addCleanup(self.dice.stop)
        self.w = world.new_world('rose-tests')
        self.p = world.add_player(self.w, 'Beck', 'NanoClad Scout')
        self.w.update(code='ROSETEST', started=True)
        world.snapshot(self.w, self.p)
        self.c = world.local(self.w, self.p)

    def act(self, action, target=None):
        if target is None:
            intent, error = world.parse(action)
            self.assertIsNone(error)
        else:
            intent = dict(action=action, target=target)
        return world.act(self.w, self.p, intent)

    def approach(self, node):
        routes = [hx.path(self.c['scene']['tiles'], self.p['local']['pos'], pos,
                          scene.occupied(self.w, self.c, self.p['id'])) for pos in hx.neighbors(node['pos'])]
        route = min((p for p in routes if p), key=len)
        for pos in route[1:]:
            self.act('hex_move', hx.key(pos))

    def battle(self, health=60, pos=(1, 0)):
        self.c['threat'] = dict(name='test reclamation construct', id='threat', health=health, defense=12,
                               attack=11, damage=7, state='watchful', intent='guarding salvage',
                               lore='Generated test fixture.', resolved=False, local_pos=list(pos))
        self.act('engage', '')
        return self.c['scene']['encounter']


class VariablesAndTopology(RoseTest):
    def test_partial_rules_are_saved_without_mutating_defaults(self):
        baseline = copy.deepcopy(engine.DEFAULTS)
        w = world.new_world('partial', rules={'generation': {'scene_radius': 9}})
        self.assertEqual(w['rules']['generation']['scene_radius'], 9)
        self.assertEqual(w['rules']['combat'], baseline['combat'])
        self.assertEqual(engine.DEFAULTS, baseline)

    def test_rules_reject_unknown_fields_bools_wrong_types_and_bounds(self):
        for invalid in [{'unknown': 1}, {'schema': True}, {'generation': {'scene_radius': True}},
                        {'generation': {'scene_radius': 500}}, {'combat': {'move_ap': 0}},
                        {'infrastructure': {'free_supplies': 1}}, {'combat': []}, []]:
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                engine.validate(invalid)

    def test_profiles_produce_materially_different_public_works(self):
        frontier = world.new_world('profile', profile='frontier')
        settlement = world.new_world('profile', profile='settlement')
        self.assertLess(frontier['rules']['generation']['population'], settlement['rules']['generation']['population'])
        self.assertLess(frontier['rules']['generation']['starting_condition'], settlement['rules']['generation']['starting_condition'])
        with self.assertRaises(ValueError):
            world.new_world('bad', profile='unknown')

    def test_seed_and_rules_reproduce_the_scene_and_network(self):
        a, b = world.new_world('repro'), world.new_world('repro')
        c1, c2 = world.local(a, {'pos': a['spawn']}), world.local(b, {'pos': b['spawn']})
        self.assertEqual(c1['scene'], c2['scene'])
        self.assertEqual(c1['infrastructure'], c2['infrastructure'])
        other = world.new_world('another')
        self.assertNotEqual(c1['scene']['tiles'], world.local(other, {'pos': other['spawn']})['scene']['tiles'])
        self.assertNotEqual([n['pos'] for n in c1['infrastructure']['nodes']], [n['pos'] for n in world.local(other,{'pos':other['spawn']})['infrastructure']['nodes']])

    def test_hexes_have_six_symmetric_neighbors(self):
        for pos in hx.disk(4):
            self.assertEqual(len(hx.neighbors(pos)), 6)
            for neighbor in hx.neighbors(pos):
                self.assertEqual(hx.distance(pos, neighbor), 1)
                self.assertIn(pos, hx.neighbors(neighbor))
        self.assertEqual(len(hx.disk(6)), 127)

    def test_cube_lines_and_bfs_are_contiguous(self):
        for a in hx.disk(3):
            for b in [[3, 0], [-3, 2], [0, -3]]:
                line = hx.line(a, b)
                self.assertEqual(line[0], a)
                self.assertEqual(line[-1], b)
                self.assertEqual(len(line) - 1, hx.distance(a, b))
                self.assertTrue(all(hx.distance(x, y) == 1 for x, y in zip(line, line[1:])))

    def test_bounded_generation_always_leaves_accessible_aprons(self):
        for radius in [5, 9]:
            for density in [0, 100]:
                for obstacles in [0, 28]:
                    for seed in range(12):
                        w = world.new_world(str(seed), rules={'generation': {'scene_radius': radius,
                                             'infrastructure_density': density, 'obstacle_density': obstacles}})
                        c = world.local(w, {'pos': w['spawn']})
                        for node in c['infrastructure']['nodes']:
                            self.assertTrue(any(hx.path(c['scene']['tiles'], [0, 0], p) for p in hx.neighbors(node['pos'])),
                                            (radius, density, obstacles, seed, node['id']))

    def test_density_changes_generated_nonlandmark_module_count(self):
        a = world.new_world('density', rules={'generation': {'infrastructure_density': 0}})
        b = world.new_world('density', rules={'generation': {'infrastructure_density': 100}})
        self.assertEqual(len(world.visit(a, -10, 2)['infrastructure']['nodes']), 2)
        self.assertEqual(len(world.visit(b, -10, 2)['infrastructure']['nodes']), 7)

    def test_landmarks_keep_source_geography_and_regional_materials(self):
        for lm in geography.LANDMARKS.values():
            c = world.visit(self.w, *lm['pos'])
            self.assertEqual(c['region'], lm['region'])
            self.assertTrue(c['scene']['palette']['material'])
            self.assertIn('source', c['landmark'])
        self.assertEqual(len(geography.LANDMARKS), 28)

    def test_six_players_spawn_in_distinct_walkable_hexes(self):
        for i in range(5):
            world.add_player(self.w, 'Player ' + str(i), 'Seam Mediator')
        state = world.snapshot(self.w, self.p)
        positions = [key for key in [hx.key(u['pos']) for u in state['scene']['units']] if key]
        self.assertEqual(len(positions), len(set(positions)))
        with self.assertRaises(ValueError):
            world.add_player(self.w, 'Seventh', 'Seam Mediator')

    def test_nonadjacent_and_occupied_moves_are_rejected_before_spending(self):
        before = self.p['energy']
        for target in ['6,0', hx.key(self.w['actors'][0]['local']['pos']), '100,100']:
            with self.assertRaises(ValueError):
                self.act('hex_move', target)
        self.assertEqual(self.p['energy'], before)

    def test_snapshot_has_hex_scene_and_no_session_tokens(self):
        state = world.snapshot(self.w, self.p)
        self.assertEqual(state['scene']['id'], hx.key(self.p['pos']))
        self.assertNotIn(self.p['token'], json.dumps(state))
        self.assertTrue(state['scene']['reachable'])


class InfrastructureTests(RoseTest):
    def node(self, kind):
        return next(n for n in self.c['infrastructure']['nodes'] if n['kind'] == kind)

    def test_remote_repair_cannot_consume_scrap(self):
        node = self.node('water')
        scrap = self.p['inventory']['scrap']
        with self.assertRaises(ValueError):
            self.act('structure_repair', node['id'])
        self.assertEqual(scrap, self.p['inventory']['scrap'])

    def test_successful_repair_updates_structure_and_connected_wiring(self):
        node = self.node('water')
        self.approach(node)
        node['condition'] = 40
        before = self.p['inventory']['scrap']
        self.act('structure_repair', node['id'])
        self.assertEqual(node['condition'], 65)
        self.assertEqual(self.p['inventory']['scrap'], before - 1)
        self.assertIn(self.p['id'], node['repaired_by'])
        self.assertTrue(any(e['condition'] == 90 for e in self.c['infrastructure']['links'] if node['id'] in [e['a'], e['b']]))
        self.assertEqual(self.p['last_check']['skill'], 'resource')

    def test_failed_repair_spends_material_without_restoring_condition(self):
        node = self.node('power')
        self.approach(node)
        before, scrap = node['condition'], self.p['inventory']['scrap']
        with patch('world.secrets.randbelow', return_value=0):
            self.act('structure_repair', node['id'])
        self.assertEqual(node['condition'], before)
        self.assertEqual(self.p['inventory']['scrap'], scrap - 1)

    def test_drawing_water_conserves_both_ledgers(self):
        node = self.node('water')
        self.approach(node)
        data = self.c['infrastructure']
        total = data['stores']['water'] + self.p['inventory']['water']
        infra.handle(self.w, self.p, dict(action='structure_draw', target=node['id']), '', world)
        self.assertEqual(total, data['stores']['water'] + self.p['inventory']['water'])

    def test_failed_draw_does_not_transfer_supplies(self):
        node = self.node('water')
        self.approach(node)
        stock, inventory = copy.deepcopy(self.c['infrastructure']['stores']), self.p['inventory'].copy()
        with patch('world.secrets.randbelow', return_value=0):
            infra.handle(self.w, self.p, dict(action='structure_draw', target=node['id']), '', world)
        self.assertEqual(stock, self.c['infrastructure']['stores'])
        self.assertEqual(inventory, self.p['inventory'])

    def test_empty_public_stock_and_full_pack_reject_draw(self):
        node = self.node('water')
        self.approach(node)
        self.c['infrastructure']['stores']['water'] = 0
        with self.assertRaises(ValueError):
            self.act('structure_draw', node['id'])
        self.c['infrastructure']['stores']['water'] = 1
        self.p['inventory']['water'] = 99
        with self.assertRaises(ValueError):
            self.act('structure_draw', node['id'])

    def test_utility_cycle_accounts_for_production_consumption_and_conversion(self):
        data = self.c['infrastructure']
        before = {k: self.c[k] + data['stores'][k] for k in ['water', 'food', 'scrap']}
        self.w['tick'] = 6
        infra.cycle(self.w, world)
        metrics = data['metrics']
        after = {k: self.c[k] + data['stores'][k] for k in before}
        self.assertEqual(before['water'] - after['water'], metrics['water_consumed'] + metrics['cultivation_water_used'])
        self.assertEqual(before['food'] - after['food'], metrics['food_consumed'])
        self.assertEqual(before['scrap'], after['scrap'])
        self.assertEqual(data['stores']['power'], metrics['power_generated'] - metrics['power_spent'])

    def test_power_is_required_even_with_available_local_water(self):
        node = self.node('power')
        node['enabled'] = False
        self.w['tick'] = 6
        infra.cycle(self.w, world)
        self.assertEqual(self.c['infrastructure']['metrics']['water_produced'], 0)
        self.assertEqual(self.node('water')['status'], 'power deficit')

    def test_isolating_power_removes_live_relay_support_immediately(self):
        self.c['infrastructure']['nodes'].append(dict(id='relay-test',kind='relay',pos=[4,-1],condition=80,enabled=True,status='working'))
        self.c['infrastructure']['links'].append(dict(a=self.node('power')['id'],b='relay-test',condition=80))
        infra.refresh_support(self.c)
        self.assertEqual(self.c['network_bonus'],1)
        self.node('power')['enabled']=False
        infra.refresh_support(self.c)
        self.assertEqual(self.c['network_bonus'],0)

    def test_damaged_links_disconnect_consumers(self):
        for edge in self.c['infrastructure']['links']:
            edge['condition'] = 0
        connected = infra.network(self.c['infrastructure'])
        self.assertEqual(connected, {self.node('power')['id']})

    def test_cycles_are_idempotent_at_a_single_tick_and_stores_bounded(self):
        self.w['tick'] = 6
        infra.cycle(self.w, world)
        first = copy.deepcopy(self.c['infrastructure'])
        infra.cycle(self.w, world)
        self.assertEqual(first, self.c['infrastructure'])
        for tick in range(12, 301, 6):
            self.w['tick'] = tick
            infra.cycle(self.w, world)
        data = self.c['infrastructure']
        self.assertTrue(all(0 <= n <= data['cap'] for n in data['stores'].values()))
        self.assertLessEqual(len(data['ledger']), 30)

    def test_population_demand_reports_real_shortfalls(self):
        data = self.c['infrastructure']
        data['population'] = 40
        for node in data['nodes']:
            node['enabled'] = False
        data['stores'].update(water=1, food=0)
        self.w['tick'] = 6
        infra.cycle(self.w, world)
        self.assertEqual(data['metrics']['water_consumed'], 1)
        self.assertEqual(data['metrics']['unmet_water'], 4)
        self.assertEqual(data['metrics']['unmet_food'], 4)

    def test_maintenance_contract_requires_new_personal_work_and_pays_once(self):
        node = self.node('water')
        self.approach(node)
        node['condition'] = 60
        self.act('structure_contract', node['id'])
        node['condition'] = 90
        with self.assertRaises(ValueError):
            self.act('structure_fulfill', node['id'])
        node['condition'] = 60
        self.act('structure_repair', node['id'])
        old = self.p['inventory']['scrap']
        self.act('fulfill', '')
        self.assertEqual(self.p['inventory']['scrap'], old + 3)
        self.assertIsNone(self.p['contract'])
        self.assertEqual(self.p['contract_history'][-1]['kind'], 'infrastructure')
        with self.assertRaises(ValueError):
            self.act('structure_fulfill', node['id'])

    def test_old_repair_at_the_same_tick_cannot_close_new_contract(self):
        node = self.node('water')
        self.approach(node)
        node['condition'] = 30
        intent = dict(action='structure_repair', target=node['id'])
        infra.handle(self.w, self.p, intent, '', world)
        infra.handle(self.w, self.p, dict(action='structure_contract', target=node['id']), '', world)
        node['condition'] = 90
        with self.assertRaises(ValueError):
            infra.handle(self.w, self.p, dict(action='structure_fulfill', target=node['id']), '', world)

    def test_npc_repair_uses_its_own_pack_at_an_actual_apron(self):
        a = self.w['actors'][0]
        node = self.node('power')
        for other in self.c['infrastructure']['nodes']:
            other['condition'] = 90
        node['condition'] = 20
        free = next(pos for pos in hx.neighbors(node['pos']) if self.c['scene']['tiles'][hx.key(pos)]['passable'] and pos not in scene.occupied(self.w, self.c, a['id']))
        a['local']['pos'] = free
        a['engagement'].update(phase='work', task='repair', planned='repair', last_work=-20)
        own, player = a['inventory']['scrap'], self.p['inventory'].copy()
        self.w['tick'] = 4
        companions.cycle(self.w, world)
        self.assertEqual(a['inventory']['scrap'], own - 1)
        self.assertEqual(self.p['inventory'], player)
        self.assertEqual(node['condition'], 35)

    def test_shop_requires_physical_access_and_conserves_currency(self):
        node = self.node('exchange')
        with self.assertRaises(ValueError):
            self.act('buy', 'water')
        self.approach(node)
        b = world.institutions.business(self.w, self.p, world)
        total = b['reserve'] + self.p['inventory']['scrap']
        self.act('buy', 'water')
        self.assertEqual(b['reserve'] + self.p['inventory']['scrap'], total)


class TacticalTests(RoseTest):
    def test_combat_and_exploration_share_the_same_scene_tiles(self):
        same_tiles = self.c['scene']['tiles'].copy()
        tiles = {k:{f:v for f,v in tile.items() if f != 'material_state'} for k,tile in copy.deepcopy(same_tiles).items()}
        self.battle(pos=(2, 0))
        self.act('parley', '')
        self.assertFalse(self.c['scene']['encounter']['active'])
        self.assertTrue(all(tile is self.c['scene']['tiles'][k] for k,tile in same_tiles.items()))
        self.assertEqual(tiles, {k:{f:v for f,v in tile.items() if f != 'material_state'} for k,tile in self.c['scene']['tiles'].items()})

    def test_attack_costs_ap_and_defers_enemy_action_until_its_turn(self):
        enc = self.battle()
        ap, health = enc['ap'][self.p['id']], self.p['health']
        self.act('attack', '')
        self.assertEqual(enc['ap'][self.p['id']], ap - self.w['rules']['combat']['melee_ap'])
        self.assertEqual(self.p['health'], health)
        self.assertEqual(self.p['last_check']['skill'], 'transversal')

    def test_missed_attack_still_costs_ap(self):
        enc = self.battle()
        ap, health = enc['ap'][self.p['id']], self.c['threat']['health']
        with patch('world.secrets.randbelow', return_value=0):
            self.act('attack', '')
        self.assertLess(enc['ap'][self.p['id']], ap)
        self.assertEqual(self.c['threat']['health'], health)

    def test_insufficient_ap_cannot_change_target_or_resources(self):
        enc = self.battle()
        enc['ap'][self.p['id']] = 1
        hp, inventory = self.c['threat']['health'], self.p['inventory'].copy()
        with self.assertRaises(ValueError):
            self.act('attack', '')
        self.assertEqual(self.c['threat']['health'], hp)
        self.assertEqual(self.p['inventory'], inventory)

    def test_range_and_solid_line_of_sight_are_required(self):
        enc = self.battle(pos=(3, 0))
        with self.assertRaises(ValueError):
            self.act('attack', '')
        self.p['credentials'] = ['black.dot']
        self.p['loadout'] = ['crystallin']
        self.c['scene']['tiles']['1,0'].update(passable=False, opaque=True)
        ap, scrap = enc['ap'][self.p['id']], self.p['inventory']['scrap']
        with self.assertRaises(ValueError):
            self.act('shoot', '')
        self.assertEqual(enc['ap'][self.p['id']], ap)
        self.assertEqual(self.p['inventory']['scrap'], scrap)

    def test_registered_shot_spends_one_charge_and_records_cover(self):
        enc = self.battle(pos=(2, 0))
        self.p['credentials'] = ['black.dot']
        self.p['loadout'] = ['crystallin']
        self.c['scene']['tiles']['2,0']['cover'] = 2
        scrap = self.p['inventory']['scrap']
        self.act('shoot', '')
        self.assertEqual(self.p['inventory']['scrap'], scrap - 1)
        self.assertEqual(self.p['last_check']['skill'], 'ballistics')
        self.assertIn('target hex cover −2', self.p['last_check']['reasons'])

    def test_wrong_target_cannot_damage_npcs_or_other_players(self):
        self.battle()
        hp = self.c['threat']['health']
        with self.assertRaises(ValueError):
            self.act('attack', self.w['actors'][0]['id'])
        self.assertEqual(self.c['threat']['health'], hp)

    def test_active_combat_blocks_ordinary_work_and_sector_travel(self):
        self.battle()
        for text in ['north', 'forage', 'ask about history', 'buy water', 'repair structure water']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.act(text)

    def test_ecology_freezes_during_combat_but_personal_turn_cost_remains(self):
        enc = self.battle()
        tick, thirst = self.w['tick'], self.p['thirst']
        world.tick(self.w)
        self.assertEqual(self.w['tick'], tick)
        self.act('end turn')
        self.assertEqual(self.w['tick'], tick)
        self.assertEqual(self.p['thirst'], thirst + 4)
        self.assertGreater(enc['round'], 1)

    def test_enemy_moves_only_through_free_adjacent_hexes(self):
        enc = self.battle(pos=(6, 0))
        self.act('end turn')
        trail = self.c['threat'].get('trail', [])
        self.assertTrue(trail)
        self.assertTrue(all(hx.distance(a, b) == 1 for a, b in zip(trail, trail[1:])))
        self.assertTrue(all(self.c['scene']['tiles'][hx.key(pos)]['passable'] for pos in trail))
        self.assertNotEqual(self.c['threat']['local_pos'], self.p['local']['pos'])

    def test_companion_guard_requires_actual_adjacency(self):
        a = self.w['actors'][0]
        self.act('recruit', a['id'])
        self.act('npc_task', a['id'] + '|guard')
        enc = self.battle()
        a['local']['pos'] = [-1, 0]
        a['local_guard'] = 2
        enc.update(order=[self.p['id'], 'threat', a['id']], index=0, current=self.p['id'])
        health, mine = a['health'], self.p['health']
        with patch('world.secrets.randbelow', return_value=0):
            self.act('end turn')
        self.assertEqual(a['health'], health - 3)
        self.assertEqual(self.p['health'], mine - 4)

    def test_combat_care_uses_medkit_and_ap(self):
        enc = self.battle()
        self.p['health'] = 50
        medkit, ap = self.p['inventory']['medkit'], enc['ap'][self.p['id']]
        self.act('combat care')
        self.assertEqual(self.p['health'], 75)
        self.assertEqual(self.p['inventory']['medkit'], medkit - 1)
        self.assertEqual(enc['ap'][self.p['id']], ap - 3)

    def test_disable_rewards_only_once(self):
        self.battle(health=5)
        before = self.p['inventory']['scrap']
        self.act('attack', '')
        self.assertEqual(self.p['inventory']['scrap'], before + 2)
        self.assertTrue(self.c['threat']['cache_paid'])
        with self.assertRaises(ValueError):
            self.act('engage', '')

    def test_withdrawal_requires_an_outer_hex(self):
        self.battle()
        with self.assertRaises(ValueError):
            self.act('flee', '')

    def test_edge_withdrawal_is_real_overland_movement(self):
        self.act('goto', '-8,3')
        self.act('enter_location', '')
        self.p['local']['pos'] = [5, 0]
        self.battle(pos=(1, 0))
        before = self.p['pos'][:]
        self.act('flee', '')
        self.assertEqual(sum(abs(a-b) for a,b in zip(before,self.p['pos'])), 1)
        self.assertFalse(self.c['scene']['encounter']['active'])
        self.assertIsNone(world.snapshot(self.w,self.p)['atlas']['navigation']['target'])

    def test_proximity_interrupts_exploration_with_the_same_scene(self):
        self.p['local']['pos'] = [2, 0]
        self.c['threat'] = dict(name='test construct', id='threat', health=30, defense=12, attack=11,
                               damage=7, state='watchful', intent='guarding', lore='Generated fixture.',
                               resolved=False, local_pos=[4, 0])
        self.act('hex_move', '3,0')
        self.assertTrue(tactical.active(self.c))
        self.assertEqual(self.p['local']['pos'], [3, 0])


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / 'rose.db')
        server.init_db(self.db)
        server.ACTIVE.clear()
        self.dice = patch('world.secrets.randbelow', return_value=19)
        self.dice.start()
        self.addCleanup(self.dice.stop)
        self.h = server.request(dict(op='create', name='Host', build='NanoClad Scout', seed='save', profile='frontier'))

    def tearDown(self):
        server.DB.close()
        server.ACTIVE.clear()
        self.tmp.cleanup()

    def call(self, op, who=None, **kwargs):
        who = who or self.h
        revision = server.fetch(who['code'])['revision']
        return server.request(dict(**who, op=op, revision=revision, **kwargs))

    def test_rules_scene_and_network_survive_server_restart(self):
        self.call('start')
        self.call('act', intent=dict(action='hex_move', target='1,0'))
        before = self.call('state')
        server.DB.close()
        server.init_db(self.db)
        self.assertEqual(before, self.call('state'))

    def test_invalid_engine_rules_do_not_create_a_world(self):
        count = server.DB.execute('SELECT COUNT(*) FROM worlds').fetchone()[0]
        with self.assertRaises(ValueError):
            server.request(dict(op='create', name='Bad', build='NanoClad Scout', rules={'generation': {'scene_radius': 800}}))
        self.assertEqual(server.DB.execute('SELECT COUNT(*) FROM worlds').fetchone()[0], count)

    def test_failed_action_does_not_commit_partial_state(self):
        self.call('start')
        before = self.call('state')
        with self.assertRaises(ValueError):
            self.call('act', intent=dict(action='structure_repair', target='water'))
        self.assertEqual(before, self.call('state'))

    def test_blueprint_has_rules_and_tiles_without_tokens_or_character_bios(self):
        data = self.call('engine_export')
        text = json.dumps(data)
        self.assertEqual(data['format'], 'Rose-infrastructure-blueprint')
        self.assertEqual(data['profile'], 'frontier')
        self.assertTrue(data['sites'][0]['tiles'])
        self.assertNotIn(self.h['token'], text)
        self.assertNotIn('character', data)

    def test_saved_active_combat_freezes_server_pulses_and_resumes(self):
        self.call('start')
        w = server.fetch(self.h['code'])
        p = w['players'][0]
        world.snapshot(w, p)
        c = world.local(w, p)
        c['threat'] = dict(name='saved construct', id='threat', health=30, defense=12, attack=11,
                           damage=7, state='watchful', intent='guarding', lore='Generated fixture.',
                           resolved=False, local_pos=[1, 0])
        server.save(w)
        self.call('act', text='engage')
        before = self.call('state')
        server.pulse(server.ACTIVE[self.h['code']]['next'] + 1)
        self.assertEqual(before['tick'], self.call('state')['tick'])
        server.DB.close()
        server.init_db(self.db)
        self.assertEqual(before['scene']['combat'], self.call('state')['scene']['combat'])
        self.call('act', text='end turn')

    def test_host_can_advance_a_waiting_guest_turn_without_guest_need_cost(self):
        guest = self.call('join', name='Guest', build='NanoClad Scout')
        self.call('start')
        w = server.fetch(self.h['code'])
        p = w['players'][0]
        world.snapshot(w, p)
        c = world.local(w, p)
        c['threat'] = dict(name='multiplayer construct', id='threat', health=80, defense=12, attack=11,
                           damage=7, state='watchful', intent='guarding', lore='Generated fixture.',
                           resolved=False, local_pos=[2, 0])
        world.act(w, p, dict(action='engage', target=''))
        enc = c['scene']['encounter']
        enc['order'] = [guest['id'], p['id'], 'threat']
        enc.update(current=guest['id'], index=0)
        thirst = w['players'][1]['thirst']
        server.save(w)
        self.call('act', text='end turn')
        self.assertEqual(self.call('state', guest)['me']['thirst'], thirst)
        self.assertEqual(self.call('state')['scene']['combat']['current'], self.h['id'])

    def test_stem_save_is_rejected_without_changing_it(self):
        saved = server.fetch(self.h['code'])
        saved['game'] = 'Stem'
        server.save(saved)
        with self.assertRaises(ValueError):
            self.call('state')
        self.assertIn('Stem', server.DB.execute('SELECT state FROM worlds').fetchone()[0])


if __name__ == '__main__':
    unittest.main()
