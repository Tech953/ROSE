"""Behavioral guarantees for wear, ownership, destruction and finite recovery."""
import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import characters
import geography
import hexgrid as hx
import infrastructure
import lifecycle
import materials
import server
import world


class MaterialTests(RoseTest):
    def object(self, material='wood', budget=5, condition=100):
        obj = dict(condition=condition)
        materials.ensure(obj, material, 0, budget)
        return obj

    def node(self, kind='water'):
        return next(n for n in self.c['infrastructure']['nodes'] if n['kind']==kind)

    def collapse(self, node):
        materials.damage(node,100,self.w['tick'])
        materials.collapse_node(self.w,self.c,node,world)

    def project(self, kind='shelter'):
        self.p['inventory']['scrap']=40
        site=next(s['pos'] for s in lifecycle.public(self.w,self.c,self.p,world)['candidates'] if not s['reason'])
        self.act('construction_plan',kind+'|'+hx.key(site))
        return self.c['lifecycle']['projects'][-1]

    def test_wet_wood_ages_faster_than_dry_and_same_tick_is_idempotent(self):
        dry=self.object();wet=self.object()
        for tick in range(1,101):
            materials.age(dry,tick,10,'dry wind');materials.age(wet,tick,80,'rain')
        self.assertGreater(dry['condition'],wet['condition'])
        before=copy.deepcopy(wet);materials.age(wet,100,80,'rain');materials.age(wet,99,80,'rain')
        self.assertEqual(wet,before)
        self.assertEqual(wet['material_state']['age'],100)

    def test_storm_fragility_and_protected_gear_differ(self):
        crystal=self.object('crystal');stone=self.object('stone');packed=self.object('crystal')
        for tick in range(1,101):
            materials.age(crystal,tick,30,'particulate storm')
            materials.age(stone,tick,30,'particulate storm')
            materials.age(packed,tick,30,'particulate storm',.25)
        self.assertLess(crystal['condition'],stone['condition'])
        self.assertGreater(packed['condition'],crystal['condition'])

    def test_all_profiles_close_a_finite_original_budget(self):
        for material in materials.PROFILES:
            with self.subTest(material=material):
                obj=self.object(material,7);self.assertTrue(materials.damage(obj,100,1))
                state=copy.deepcopy(obj['material_state']);self.assertFalse(materials.damage(obj,100,2))
                self.assertEqual(state,obj['material_state'])
                self.assertEqual(state['embodied_scrap'],state['salvage_remaining']+state['lost_scrap'])
                self.assertLess(state['salvage_remaining'],7)

    def test_invalid_damage_is_atomic_and_does_not_accept_boolean(self):
        for amount in [-1,101,True,2.5,'2']:
            obj=self.object();before=copy.deepcopy(obj)
            with self.assertRaises(ValueError):materials.damage(obj,amount,1)
            self.assertEqual(obj,before)

    def test_inspection_never_wears_items_or_advances_clock(self):
        before=copy.deepcopy(self.p['gear']);tick=self.w['tick'];pack=self.p['inventory'].copy()
        self.act('inspect weapon field_staff')
        self.act('inspect material structure '+self.node()['id'])
        self.assertEqual(self.p['gear'],before);self.assertEqual(self.w['tick'],tick);self.assertEqual(self.p['inventory'],pack)
        self.assertEqual(self.p['last_check']['skill'],'metallurgy')

    def test_parser_requires_a_registered_kind_and_whole_command(self):
        self.assertEqual(materials.parse('strike material hex -2,3'),dict(action='material_strike',target='hex:-2,3'))
        for text in ['strike material npc guest','repair weapon field_staff then grant admin','clear material structure water; free scrap','replace gear unknown space']:
            self.assertIsNone(materials.parse(text))

    def test_attack_miss_wears_weapon_without_hitting_or_aging_world(self):
        enc=self.battle();tick=self.w['tick'];health=self.c['threat']['health'];before=self.p['gear']['field_staff']['condition'];ap=enc['ap'][self.p['id']]
        with patch('world.secrets.randbelow',return_value=0):self.act('attack','')
        self.assertEqual(self.p['gear']['field_staff']['condition'],before-2)
        self.assertEqual(self.c['threat']['health'],health);self.assertEqual(self.w['tick'],tick)
        self.assertEqual(enc['ap'][self.p['id']],ap-self.w['rules']['combat']['melee_ap'])

    def test_insufficient_ap_precedes_wear_and_target_changes(self):
        enc=self.battle();enc['ap'][self.p['id']]=0;before=copy.deepcopy(self.p['gear']);health=self.c['threat']['health']
        with self.assertRaises(ValueError):self.act('attack','')
        self.assertEqual(self.p['gear'],before);self.assertEqual(self.c['threat']['health'],health)

    def test_last_use_breaks_staff_and_later_attacks_are_rejected(self):
        enc=self.battle();staff=self.p['gear']['field_staff'];staff['condition']=1
        self.act('attack','');self.assertTrue(staff['material_state']['destroyed']);ap=enc['ap'][self.p['id']]
        with self.assertRaises(ValueError):self.act('attack','')
        self.assertEqual(enc['ap'][self.p['id']],ap)
        self.assertTrue(world.snapshot(self.w,self.p)['scene']['action_availability']['attack']['reason'])

    def test_worn_weapon_reduces_successful_damage(self):
        self.battle();self.act('attack','');fresh=60-self.c['threat']['health']
        self.c['threat']['health']=60;self.c['scene']['encounter']['ap'][self.p['id']]=20
        self.p['gear']['field_staff']['condition']=20;self.act('attack','')
        self.assertLess(60-self.c['threat']['health'],fresh)

    def test_broken_ranged_gear_rejects_before_ap_and_ammo(self):
        self.p['loadout']=['crystallin'];self.p['credentials']=['black.dot'];materials.ensure_gear(self.p,self.w['tick'])
        self.p['gear']['crystallin']['condition']=19;enc=self.battle(pos=(2,0));ap=enc['ap'][self.p['id']];pack=self.p['inventory'].copy()
        with self.assertRaises(ValueError):self.act('shoot','')
        self.assertEqual(enc['ap'][self.p['id']],ap);self.assertEqual(self.p['inventory'],pack)

    def test_fractured_mods_no_longer_provide_check_bonuses(self):
        self.p['loadout']=['meta_fingers'];self.p['credentials']=['black.dot'];materials.ensure_gear(self.p,0)
        self.assertEqual(characters.bonus(self.p,'tech','fractech')['equipment'],1)
        self.p['gear']['meta_fingers']['condition']=29
        self.assertEqual(characters.bonus(self.p,'tech','fractech')['equipment'],0)

    def test_actual_uninstall_reinstall_cannot_reset_condition(self):
        self.p['pos']=geography.LANDMARKS['blackdot']['pos'][:];self.c=world.local(self.w,self.p)
        self.p['loadout']=['survey_lens'];self.p['credentials']=['black.dot'];self.p['inventory']['scrap']=20
        lens=materials.ensure_gear(self.p,self.w['tick'])['survey_lens'];lens['condition']=31;identity=lens['id']
        self.act('remove survey_lens');self.act('install survey_lens')
        self.assertIs(self.p['gear']['survey_lens'],lens);self.assertEqual(lens['id'],identity);self.assertEqual(lens['condition'],31)

    def test_repair_spends_one_and_restores_only_living_gear(self):
        item=self.p['gear']['field_staff'];item['condition']=40;pack=self.p['inventory']['scrap'];self.act('repair weapon field_staff')
        self.assertEqual(item['condition'],65);self.assertEqual(self.p['inventory']['scrap'],pack-1)
        materials.damage(item,100,self.w['tick']);pack=self.p['inventory'].copy()
        with self.assertRaises(ValueError):self.act('repair weapon field_staff')
        self.assertEqual(self.p['inventory'],pack)

    def test_failed_repair_spends_input_without_restoring_gear(self):
        item=self.p['gear']['field_staff'];item['condition']=40;pack=self.p['inventory']['scrap']
        with patch('world.secrets.randbelow',return_value=0):self.act('repair weapon field_staff')
        self.assertEqual(item['condition'],40);self.assertEqual(self.p['inventory']['scrap'],pack-1)

    def test_replacement_retires_old_shell_and_has_a_new_identity(self):
        old=self.p['gear']['field_staff'];materials.damage(old,100,0);pack=self.p['inventory']['scrap']
        self.act('replace weapon field_staff');fresh=self.p['gear']['field_staff']
        self.assertNotEqual(fresh['id'],old['id']);self.assertEqual(fresh['generation'],1);self.assertEqual(fresh['condition'],100)
        self.assertEqual(self.p['inventory']['scrap'],pack-2)
        retired=self.p['gear_history'][-1]['material_state']
        self.assertTrue(retired['retired']);self.assertEqual(retired['salvage_remaining'],0)
        self.assertEqual(retired['embodied_scrap'],retired['lost_scrap']+retired['recovered_scrap'])

    def test_regulated_replacement_needs_install_registration_and_workshop(self):
        self.p['loadout']=['leg_spikes'];materials.ensure_gear(self.p,self.w['tick'])
        materials.damage(self.p['gear']['leg_spikes'],100,0);self.p['inventory']['scrap']=20
        with self.assertRaises(ValueError):self.act('replace gear leg_spikes')
        self.p['credentials']=['black.dot']
        with self.assertRaises(ValueError):self.act('replace gear leg_spikes')
        self.approach(self.node('workshop'));self.act('replace gear leg_spikes')
        self.assertEqual(self.p['gear']['leg_spikes']['condition'],100)

    def test_broken_metal_shell_yields_one_scrap_once(self):
        self.p['loadout']=['leg_spikes'];item=materials.ensure_gear(self.p,0)['leg_spikes'];materials.damage(item,100,0)
        pack=self.p['inventory']['scrap'];self.act('reclaim gear leg_spikes')
        self.assertEqual(self.p['inventory']['scrap'],pack+1)
        with self.assertRaises(ValueError):self.act('reclaim gear leg_spikes')
        self.assertEqual(self.p['inventory']['scrap'],pack+1)

    def test_collapse_severs_connections_opens_sight_but_blocks_ground(self):
        node=self.node();tile=self.c['scene']['tiles'][hx.key(node['pos'])];self.assertTrue(tile['opaque'])
        self.collapse(node)
        self.assertFalse(tile['opaque']);self.assertFalse(tile['passable']);self.assertEqual(node['status'],'ruined');self.assertFalse(node['enabled'])
        self.assertTrue(all(e['condition']==0 for e in self.c['infrastructure']['links'] if node['id'] in [e['a'],e['b']]))
        neighbor=next(t for t in self.c['scene']['tiles'].values() if t['passable'] and hx.distance(t['pos'],node['pos'])==1)
        expected=min(2,sum(self.c['scene']['tiles'][hx.key(q)]['opaque'] for q in hx.neighbors(neighbor['pos']) if hx.key(q) in self.c['scene']['tiles']))
        self.assertEqual(neighbor['cover'],expected)

    def test_existing_actions_cannot_resurrect_ruins(self):
        node=self.node();self.approach(node);self.collapse(node)
        before=copy.deepcopy(node);pack=self.p['inventory'].copy()
        for op in ['structure_repair','structure_toggle','structure_draw','structure_contract']:
            with self.subTest(op=op),self.assertRaises(ValueError):self.act(op,node['id'])
        self.assertEqual(node,before);self.assertEqual(self.p['inventory'],pack)

    def test_clear_recovery_is_once_and_restores_walkable_footprint(self):
        node=self.node();self.approach(node);self.collapse(node);pending=node['material_state']['salvage_remaining'];pack=self.p['inventory']['scrap']
        self.act('clear material structure '+node['id'])
        self.assertEqual(self.p['inventory']['scrap'],pack+pending);self.assertNotIn(node,self.c['infrastructure']['nodes'])
        self.assertFalse(any(node['id'] in [e['a'],e['b']] for e in self.c['infrastructure']['links']))
        tile=self.c['scene']['tiles'][hx.key(node['pos'])];self.assertTrue(tile['passable']);self.assertEqual(tile['prefab'],'ground')
        pack=self.p['inventory']['scrap']
        with self.assertRaises(ValueError):self.act('clear material structure '+node['id'])
        self.assertEqual(self.p['inventory']['scrap'],pack)
        totals=self.c['material_record']['totals'];self.assertEqual(totals['embodied_cleared'],totals['recovered']+totals['lost'])

    def test_full_pack_rejects_clear_before_deleting_or_granting(self):
        node=self.node();self.approach(node);self.collapse(node);self.p['inventory']['scrap']=99;before=copy.deepcopy(node)
        with self.assertRaises(ValueError):self.act('material_clear','structure:'+node['id'])
        self.assertIn(node,self.c['infrastructure']['nodes']);self.assertEqual(node,before);self.assertEqual(self.p['inventory']['scrap'],99)

    def test_failed_recovery_preserves_debris_and_pending_material(self):
        node=self.node();self.approach(node);self.collapse(node);pending=node['material_state']['salvage_remaining'];pack=self.p['inventory']['scrap']
        with patch('world.secrets.randbelow',return_value=0):self.act('material_clear','structure:'+node['id'])
        self.assertIn(node,self.c['infrastructure']['nodes']);self.assertEqual(node['material_state']['salvage_remaining'],pending);self.assertEqual(self.p['inventory']['scrap'],pack)

    def test_destroyed_construction_cannot_refund_full_escrow_or_complete(self):
        project=self.project();escrow=project['escrow'];pack=self.p['inventory']['scrap']
        for _ in range(8):
            if project['stage']=='ruined':break
            self.act('material_strike','project:'+project['id'])
        self.assertEqual(project['stage'],'ruined')
        for op in ['construction_work','construction_cancel']:
            with self.assertRaises(ValueError):self.act(op,project['id'])
        self.act('material_clear','project:'+project['id']);self.assertEqual(project['stage'],'cleared')
        self.assertLess(self.p['inventory']['scrap']-pack,escrow)

    def test_completed_foundation_inherits_condition_clock_and_budget(self):
        project=self.project('water');project['condition']=72;state=copy.deepcopy(project['material_state'])
        lifecycle.complete(self.w,self.c,project,world);node=next(n for n in self.c['infrastructure']['nodes'] if n['id']==project['built_node'])
        self.assertEqual(node['condition'],72);self.assertEqual(node['material_state'],state)
        self.assertEqual(project['material_state']['transferred_to'],node['id']);self.assertEqual(node['owner'],self.p['id'])

    def test_collapsed_commissioned_shelter_removes_only_its_added_support(self):
        self.c['shelter']=1;project=self.project();lifecycle.complete(self.w,self.c,project,world)
        node=next(n for n in self.c['infrastructure']['nodes'] if n['id']==project['built_node']);self.assertEqual(self.c['shelter'],2)
        self.collapse(node);self.assertEqual(self.c['shelter'],1);materials.collapse_node(self.w,self.c,node,world);self.assertEqual(self.c['shelter'],1)

    def test_other_players_cannot_destroy_or_recover_private_commissions(self):
        project=self.project();guest=world.add_player(self.w,'Guest','Light Reader');world.snapshot(self.w,guest);guest['local']['pos']=self.p['local']['pos'][:]
        before=copy.deepcopy(project);gear=copy.deepcopy(guest['gear'])
        with self.assertRaises(ValueError):world.act(self.w,guest,dict(action='material_strike',target='project:'+project['id']))
        self.assertEqual(project,before);self.assertEqual(guest['gear'],gear)
        materials.damage(project,100,self.w['tick']);materials.collapse_project(self.w,self.c,project,world)
        with self.assertRaises(ValueError):world.act(self.w,guest,dict(action='material_clear',target='project:'+project['id']))
        self.assertTrue(materials.object_actions(self.w,self.c,guest,'project',project,world)[2]['reason'])

    def test_public_demolition_has_reputation_cost_even_on_miss(self):
        node=self.node();self.approach(node);faction=node['faction'];standing=self.p['personal_reputation'].get(faction,0);condition=node['condition']
        with patch('world.secrets.randbelow',return_value=0):self.act('material_strike','structure:'+node['id'])
        self.assertEqual(node['condition'],condition);self.assertEqual(self.p['personal_reputation'][faction],standing-1)
        self.assertEqual(self.p['last_check']['faction'],faction)

    def test_combat_strike_costs_ap_and_opens_cover_without_advancing_time(self):
        node=self.node();self.approach(node);node['condition']=1;enc=self.battle(pos=(0,0));ap=enc['ap'][self.p['id']];tick=self.w['tick'];gear=copy.deepcopy(self.p['gear'])
        world.tick(self.w);self.assertEqual(self.w['tick'],tick)
        self.act('material_strike','structure:'+node['id'])
        self.assertEqual(enc['ap'][self.p['id']],ap-self.w['rules']['combat']['melee_ap']);self.assertEqual(self.w['tick'],tick)
        self.assertTrue(enc['active']);self.assertFalse(self.c['scene']['tiles'][hx.key(node['pos'])]['opaque'])
        self.assertEqual(self.p['gear']['field_staff']['condition'],gear['field_staff']['condition']-2)
        with self.assertRaises(ValueError):self.act('material_clear','structure:'+node['id'])

    def test_remote_observation_can_inspect_but_not_perform_material_work(self):
        self.act('remote survey');self.act('inspect weapon field_staff');tick=self.w['tick'];pack=self.p['inventory'].copy()
        for op,target in [('gear_repair','field_staff'),('material_strike','structure:'+self.node()['id'])]:
            with self.assertRaises(ValueError):self.act(op,target)
        self.assertEqual(self.w['tick'],tick);self.assertEqual(self.p['inventory'],pack)

    def test_cold_migration_has_no_retroactive_weather_loss(self):
        self.w['tick']=900;self.p.pop('gear');nodes=self.c['infrastructure']['nodes'];before={n['id']:n['condition'] for n in nodes}
        for n in nodes:n.pop('material_state')
        for t in self.c['scene']['tiles'].values():t.pop('material_state',None)
        world.snapshot(self.w,self.p)
        self.assertEqual({n['id']:n['condition'] for n in nodes},before)
        self.assertTrue(all(n['material_state']['last_tick']==900 and n['material_state']['age']==0 for n in nodes))
        self.assertEqual(self.p['gear']['field_staff']['condition'],100)

    def test_legacy_zero_condition_migrates_as_ruins_without_free_revival(self):
        node=self.node();node['condition']=0;node.pop('material_state');self.w['tick']=900
        world.snapshot(self.w,self.p)
        self.assertTrue(node['material_state']['destroyed']);self.assertTrue(node['ruin_registered'])
        self.assertFalse(self.c['scene']['tiles'][hx.key(node['pos'])]['opaque']);self.assertEqual(node['material_state']['age'],0)
        self.approach(node)
        with self.assertRaises(ValueError):self.act('structure_repair',node['id'])

    def test_zero_condition_gear_normalization_closes_recovery_budget(self):
        self.p['loadout']=['leg_spikes'];item=materials.ensure_gear(self.p,self.w['tick'])['leg_spikes'];item['condition']=0
        materials.ensure_gear(self.p,self.w['tick'])
        self.assertTrue(item['material_state']['destroyed']);self.assertEqual(item['material_state']['salvage_remaining'],1)
        self.act('reclaim gear leg_spikes');self.assertTrue(item['material_state']['reclaimed'])

    def test_sqlite_roundtrip_retains_gear_ruins_pending_salvage_and_clocks(self):
        node=self.node();self.collapse(node);self.p['gear']['field_staff']['condition']=43
        with tempfile.TemporaryDirectory() as tmp:
            server.init_db(str(Path(tmp)/'materials.db'))
            try:
                server.save(self.w);loaded=server.fetch(self.w['code'])
                player=next(p for p in loaded['players'] if p['id']==self.p['id']);world.snapshot(loaded,player)
                self.assertEqual(player['gear'],self.p['gear'])
                restored=next(n for n in loaded['cells'][world.key(*self.p['pos'])]['infrastructure']['nodes'] if n['id']==node['id'])
                self.assertEqual(restored,node)
            finally:server.DB.close()

    def test_npc_maintenance_uses_its_own_scrap_and_never_repairs_ruins(self):
        actor=self.w['actors'][0];actor['inventory']['scrap']=3;item=materials.ensure_gear(actor,0)['field_staff'];item['condition']=20
        player_pack=self.p['inventory'].copy();infrastructure.autonomous_repair(self.w,actor,self.c,world)
        self.assertEqual(item['condition'],45);self.assertEqual(actor['inventory']['scrap'],2);self.assertEqual(self.p['inventory'],player_pack)
        node=self.node();self.collapse(node);before=copy.deepcopy(node);item['condition']=100
        infrastructure.autonomous_repair(self.w,actor,self.c,world);self.assertEqual(node,before)

    def test_destroyed_rock_can_be_cleared_once_into_open_ground(self):
        rock=next(t for t in self.c['scene']['tiles'].values() if t['prefab']=='rock');self.approach(rock)
        materials.damage(rock,100,self.w['tick']);rock['opaque']=False;lifecycle.cover(self.c['scene'])
        pack=self.p['inventory']['scrap'];selector='hex:'+hx.key(rock['pos']);self.act('material_clear',selector)
        self.assertEqual(self.p['inventory']['scrap'],pack+1);self.assertTrue(rock['passable']);self.assertEqual(rock['prefab'],'ground')
        with self.assertRaises(ValueError):self.act('material_clear',selector)

    def test_world_weather_collapses_brittle_rocks_and_recalculates_cover(self):
        rock=next(t for t in self.c['scene']['tiles'].values() if t['prefab']=='rock');rock['condition']=1;rock['material_state']['exposure']=.999
        self.w['tick']+=1;materials.advance(self.w,world)
        self.assertTrue(rock['material_state']['destroyed']);self.assertFalse(rock['opaque']);self.assertFalse(rock['passable'])
        self.assertTrue(any(r['source']=='hex:'+hx.key(rock['pos']) for r in self.c['material_record']['history']))
