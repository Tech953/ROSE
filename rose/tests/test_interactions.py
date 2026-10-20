"""Observations, consent, physical yielding and menu prerequisites."""
import copy
from unittest.mock import patch
from test_engine import RoseTest
import hexgrid as hx
import interactions
import scene
import tactical
import world


class FieldInteractionTests(RoseTest):
    def test_look_records_one_check_without_ap_time_or_supply_cost(self):
        node = self.c['infrastructure']['nodes'][0]
        pack, tick, energy = self.p['inventory'].copy(), self.w['tick'], self.p['energy']
        checks = len(self.p['check_log'])
        result = self.act('field_look', 'structure:' + node['id'])
        self.assertIn(node['material'], result['text'])
        self.assertIn(world.REGIONS[self.c['region']]['scent'], result['text'])
        self.assertEqual(self.p['inventory'], pack)
        self.assertEqual((self.w['tick'], self.p['energy']), (tick, energy))
        self.assertEqual(len(self.p['check_log']), checks + 1)
        self.assertEqual(self.p['last_check']['action'], 'field_look')
        self.assertEqual(self.p['last_check']['faction'], node['faction'])

    def test_look_uses_character_designation_and_retains_setback_records(self):
        self.p['character']['appearance'] = 'A patched rose coat'
        with patch('world.secrets.randbelow', return_value=0):
            result = self.act('field_look', 'unit:' + self.p['id'])
        self.assertIn('A patched rose coat', result['text'])
        self.assertIn('uncertain', result['text'])
        self.assertFalse(self.p['last_check']['success'])

    def test_hex_look_keeps_collision_and_cover(self):
        rock = next(t for t in self.c['scene']['tiles'].values() if not t['passable'])
        before = copy.deepcopy(self.c['scene']['tiles'])
        result = self.act('field_look', 'hex:' + hx.key(rock['pos']))
        self.assertIn('solid', result['text'])
        self.assertEqual(self.c['scene']['tiles'], before)

    def test_look_during_combat_does_not_spend_or_advance_turn(self):
        self.c['threat'] = None
        # Obtain a seeded hostile field and keep its real encounter rules.
        self.w['rules']['generation']['hostility'] = 100
        self.p['pos'] = [-10, 2]
        world.visit(self.w, *self.p['pos'])
        self.c = world.local(self.w, self.p)
        self.act('engage', '')
        encounter = copy.deepcopy(self.c['scene']['encounter'])
        result = self.act('field_look', 'unit:threat')
        self.assertIn(self.c['threat']['name'], result['text'])
        self.assertEqual(self.c['scene']['encounter'], encounter)

    def test_remote_look_is_labelled_and_cannot_turn_into_work(self):
        self.act('remote', '')
        result = self.act('field_look', 'hex:0,0')
        self.assertIn('UNVERIFIED REMOTE PROJECTION', result['text'])
        with self.assertRaisesRegex(ValueError, 'remote apparatus'):
            self.act('companion_yield', self.w['actors'][0]['id'])

    def test_object_look_does_not_stop_a_world_journey(self):
        self.act('goto', '-8,3')
        before = copy.deepcopy(self.p['overworld'])
        self.act('field_look', 'hex:0,0')
        self.assertEqual(self.p['overworld'], before)

    def test_unknown_and_other_field_targets_are_rejected(self):
        for target in ['unit:unknown', 'structure:unknown', 'hex:99,99', 'hex:1.5,0', 'inventory:water']:
            with self.subTest(target=target), self.assertRaises(ValueError):
                self.act('field_look', target)

    def test_catalogue_is_read_only_and_reports_costs_and_training(self):
        units = world.snapshot(self.w, self.p)['scene']['units']
        before = copy.deepcopy(self.w)
        menu = interactions.public(self.w, self.c, self.p, units, world)
        self.assertEqual(self.w, before)
        node = self.c['infrastructure']['nodes'][0]
        repair = next(a for a in menu['structure:' + node['id']]['actions'] if a['intent']['action'] == 'structure_repair')
        self.assertEqual(repair['dc'], self.w['rules']['infrastructure']['repair_dc'])
        self.assertIn('1 scrap', repair['cost'])
        self.assertIn('adjacent', repair['reason'])
        self.assertIsInstance(repair['training'], int)

    def test_item_and_contract_menu_reasons_match_server_prerequisites(self):
        node = next(n for n in self.c['infrastructure']['nodes'] if n['kind'] == 'water')
        self.approach(node)
        self.p['inventory']['scrap'] = 0
        menu = world.snapshot(self.w, self.p)['scene']['interaction_options']['structure:' + node['id']]['actions']
        repair = next(a for a in menu if a['intent']['action'] == 'structure_repair')
        self.assertIn('scrap', repair['reason'])
        with self.assertRaisesRegex(ValueError, 'scrap'):
            self.act('structure_repair', node['id'])
        self.p['inventory']['scrap'] = 5
        node['condition'] = 60
        self.act('structure_contract', node['id'])
        menu = world.snapshot(self.w, self.p)['scene']['interaction_options']['structure:' + node['id']]['actions']
        fulfill = next(a for a in menu if a['intent']['action'] == 'structure_fulfill')
        self.assertIn('85', fulfill['reason'])

    def companion(self):
        ally = next(a for a in self.w['actors'] if [a['x'], a['y']] == self.p['pos'])
        ally['owner'] = self.p['id']
        self.p['companions'] = [ally['id']]
        scene.sync(self.w, self.c, world)
        self.p['local']['pos'] = [0, 0]
        ally['local']['pos'] = [1, 0]
        # Move any other living NPC clear of this small fixture.
        for other in self.w['actors']:
            if other is not ally and [other['x'], other['y']] == self.p['pos']:
                other['local']['pos'] = [-3, -1]
                self.c['scene']['tiles']['-3,-1']['passable'] = True
        return ally

    def test_companion_makes_one_physical_step_and_spends_own_energy(self):
        ally = self.companion()
        start, energy, tick = ally['local']['pos'][:], ally['energy'], self.w['tick']
        pack = self.p['inventory'].copy()
        self.act('companion_yield', ally['id'])
        self.assertEqual(hx.distance(start, ally['local']['pos']), 1)
        self.assertNotIn(ally['local']['pos'], scene.occupied(self.w, self.c, ally['id']))
        self.assertTrue(self.c['scene']['tiles'][hx.key(ally['local']['pos'])]['passable'])
        self.assertEqual(ally['energy'], energy - 1)
        self.assertEqual(self.p['inventory'], pack)
        self.assertEqual(self.w['tick'], tick)
        self.assertEqual(self.p['last_check']['skill'], 'community')
        self.assertEqual(self.p['last_check']['faction'], ally['faction'])

    def test_companion_yield_setback_never_moves_or_spends_energy(self):
        ally = self.companion()
        before, energy = ally['local']['pos'][:], ally['energy']
        with patch('world.secrets.randbelow', return_value=0):
            self.act('companion_yield', ally['id'])
        self.assertEqual(ally['local']['pos'], before)
        self.assertEqual(ally['energy'], energy)

    def test_yield_refuses_other_owners_exhaustion_unwillingness_and_distance(self):
        for field, value in [('owner', 'another-seat'), ('health', 34), ('energy', 14), ('attitude', 29)]:
            ally = self.companion()
            old = ally[field]
            ally[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.act('companion_yield', ally['id'])
            ally[field] = old
        ally = self.companion()
        ally['local']['pos'] = [4, -1]
        with self.assertRaisesRegex(ValueError, 'one hex'):
            self.act('companion_yield', ally['id'])

    def test_trapped_companion_is_not_teleported_through_solid_tiles(self):
        ally = self.companion()
        for pos in hx.neighbors(ally['local']['pos']):
            if pos != self.p['local']['pos']:
                self.c['scene']['tiles'][hx.key(pos)]['passable'] = False
        before = ally['local']['pos'][:]
        with self.assertRaisesRegex(ValueError, 'No free adjacent'):
            self.act('companion_yield', ally['id'])
        self.assertEqual(ally['local']['pos'], before)

    def test_resident_dialogue_targets_the_selected_person_and_records_voice(self):
        self.p['pos'] = world.geography.LANDMARKS['ed_net']['pos'][:]
        world.visit(self.w, *self.p['pos'])
        world.snapshot(self.w, self.p)
        self.c = world.local(self.w, self.p)
        resident = world.adventure.resident(self.w, self.p)
        self.p['character']['voice'] = 'quiet and exact'
        self.p['local']['pos'] = next(pos for pos in hx.neighbors(resident['local']['pos']) if self.c['scene']['tiles'].get(hx.key(pos), {}).get('passable'))
        self.act('field_dialogue', resident['id'] + '|place')
        self.assertIn('quiet and exact', self.p['last_result'])
        self.assertEqual(self.p['dialogue_log'][-1]['npc'], resident['name'])
        self.assertEqual(self.p['relationships'][resident['id']]['last_topic'], 'place')

    def test_parser_keeps_object_targets_bounded_and_explicit(self):
        self.assertEqual(world.parse('look at hex 1,-1')[0], dict(action='field_look', target='hex:1,-1'))
        self.assertEqual(world.parse('ask Sela to make room')[0], dict(action='companion_yield', target='Sela'))
        self.assertEqual(world.parse('look')[0]['action'], 'look')
