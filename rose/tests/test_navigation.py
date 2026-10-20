"""World travel, bodily scale, encounter interruption and saved authority."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import geography as geo
import navigation as nav
import server
import tactical
import world


class TravelTests(unittest.TestCase):
    def setUp(self):
        dice=patch('world.secrets.randbelow',return_value=19)
        dice.start();self.addCleanup(dice.stop)
        self.w=world.new_world('world-travel',rules={'generation':{'hostility':0}})
        self.w.update(code='TRAVEL',started=True)
        self.p=world.add_player(self.w,'Walker','NanoClad Scout')
        world.snapshot(self.w,self.p)

    def act(self,text):
        intent,error=world.parse(text)
        self.assertIsNone(error)
        return world.act(self.w,self.p,intent,text)

    def arrive(self):
        for _ in range(400):
            if self.p['overworld']['status']!='traveling':break
            nav.advance(self.w,self.p,world)
        self.assertEqual(self.p['overworld']['status'],'arrived')

    def test_free_point_travel_keeps_exact_fractional_destination(self):
        tick=self.w['tick'];position=self.p['pos'][:]
        self.act('go to -8.2,2.25')
        self.assertEqual(self.p['pos'],position)
        self.assertEqual(self.w['tick'],tick)
        self.assertEqual(self.p['overworld']['mode'],'world')
        self.arrive()
        self.assertEqual(self.p['overworld']['point'],[-8.2,2.25])
        self.assertEqual(self.p['pos'],[-8,2])
        self.assertGreater(self.w['tick'],tick)
        self.assertGreater(self.p['thirst'],0)
        self.assertTrue(any(c['skill']=='transversal' for c in self.p['check_log']))

    def test_local_hex_movement_does_not_change_world_point(self):
        before=self.p['overworld']['point'][:]
        self.act('hex 1,0')
        self.assertEqual(self.p['overworld']['point'],before)
        self.assertEqual(self.p['pos'],geo.SPAWN)

    def test_partial_travel_is_continuous_and_stop_does_not_snap_back(self):
        self.act('go to -8,3');nav.advance(self.w,self.p,world)
        before=self.p['overworld']['point'][:]
        self.assertNotEqual(before,geo.SPAWN)
        self.assertEqual(self.p['pos'],geo.SPAWN)
        self.act('stop travel');world.snapshot(self.w,self.p)
        self.assertEqual(self.p['overworld']['point'],before)
        self.assertFalse(nav.advance(self.w,self.p,world))
        self.act('resume travel');self.arrive()

    def test_redirect_retains_current_point_and_replaces_goal(self):
        self.act('go to -7,3');nav.advance(self.w,self.p,world)
        before=self.p['overworld']['point'][:]
        self.act('go to -9.7,4.1')
        self.assertEqual(self.p['overworld']['point'],before)
        self.arrive();self.assertEqual(self.p['overworld']['point'],[-9.7,4.1])

    def test_stop_after_sector_boundary_preserves_point_and_only_one_crossing_cost(self):
        self.act('go to -8,3')
        nav.advance(self.w,self.p,world);nav.advance(self.w,self.p,world)
        self.assertEqual(self.p['pos'],[-9,3])
        point=self.p['overworld']['point'][:];tick=self.w['tick'];thirst=self.p['thirst']
        self.act('stop travel');self.act('enter location');world.snapshot(self.w,self.p)
        self.assertEqual(self.p['overworld']['point'],point)
        self.assertEqual(self.w['tick'],tick);self.assertEqual(self.p['thirst'],thirst)
        self.act('resume travel');nav.advance(self.w,self.p,world)
        self.assertEqual(self.p['pos'],[-9,3]);self.assertEqual(self.p['thirst'],thirst)

    def test_combat_in_another_sector_holds_world_travel(self):
        self.act('go to -8,3')
        cell=world.visit(self.w,-12,3);cell['scene']['encounter']={'active':True}
        before=copy.deepcopy(self.p['overworld'])
        self.assertFalse(nav.advance(self.w,self.p,world));self.assertEqual(self.p['overworld'],before)

    def test_route_can_resume_after_resolving_an_encounter(self):
        cell=world.visit(self.w,-9,3)
        cell['threat']=dict(id='threat',name='test construct',health=30,defense=12,attack=11,
            damage=7,state='watchful',intent='guarding salvage',lore='test fixture',resolved=False)
        self.act('go to -8,3')
        for _ in range(10):
            nav.advance(self.w,self.p,world)
            if tactical.active(cell):break
        tactical.close(self.w,cell,'truce',world,self.p)
        self.act('resume travel');self.arrive()
        self.assertEqual(self.p['pos'],[-8,3])

    def test_can_click_unexplored_land_and_reveal_places_by_traveling(self):
        self.assertNotIn([-8,3],self.p['overworld']['seen'])
        self.act('go to -8,3');self.arrive()
        self.assertIn([-8,3],self.p['overworld']['visited'])
        self.assertIn([-7,3],self.p['overworld']['seen'])

    def test_named_arrival_waits_for_enter_location(self):
        self.act('go to spidre');self.arrive()
        self.assertEqual(self.p['pos'],geo.LANDMARKS['spidre']['pos'])
        self.assertEqual(self.p['overworld']['mode'],'world')
        self.act('enter location')
        self.assertEqual(self.p['overworld']['mode'],'local')
        self.assertEqual(world.snapshot(self.w,self.p)['scene']['id'],world.key(*self.p['pos']))

    def test_invalid_points_do_not_replace_existing_route(self):
        self.act('go to -8,3')
        before=copy.deepcopy(self.p)
        for value in ['go to 99,0','go to 1,-12','go to 14,12']:
            with self.subTest(value=value),self.assertRaises(ValueError):self.act(value)
            for k in ['pos','route','destination','overworld','inventory']:
                self.assertEqual(self.p[k],before[k])

    def test_routing_does_not_cut_diagonally_through_river(self):
        for lm in geo.LANDMARKS.values():
            path=nav.route(geo.SPAWN,lm['pos']);previous=geo.SPAWN
            for destination in path:
                dx,dy=destination[0]-previous[0],destination[1]-previous[1]
                self.assertLessEqual(max(abs(dx),abs(dy)),1)
                self.assertTrue(geo.info(*destination)['passable'])
                if dx and dy:
                    self.assertTrue(geo.info(previous[0]+dx,previous[1])['passable'])
                    self.assertTrue(geo.info(previous[0],previous[1]+dy)['passable'])
                previous=destination

    def test_pause_and_unstarted_worlds_do_not_advance_journeys(self):
        self.act('go to -8,3');before=copy.deepcopy(self.p)
        self.w['paused']=True;self.assertFalse(nav.advance(self.w,self.p,world))
        self.w.update(paused=False,started=False);self.assertFalse(nav.advance(self.w,self.p,world))
        self.assertEqual(self.p,before)

    def test_survival_stop_keeps_route_without_spending_extra_supplies(self):
        self.act('go to -8,3');self.p['thirst']=80
        before=copy.deepcopy(self.p['inventory']);path=copy.deepcopy(self.p['route'])
        nav.advance(self.w,self.p,world)
        self.assertEqual(self.p['overworld']['status'],'needs')
        self.assertEqual(self.p['inventory'],before);self.assertEqual(self.p['route'],path)
        with self.assertRaises(ValueError):self.act('resume travel')
        self.act('enter location');self.act('drink');self.act('resume travel');self.arrive()

    def test_hostile_encounter_interrupts_route_and_enters_local_field(self):
        cell=world.visit(self.w,-9,3)
        cell['threat']=dict(id='threat',name='test construct',health=30,defense=12,attack=11,
            damage=7,state='watchful',intent='guarding salvage',lore='test fixture',resolved=False)
        self.act('go to -8,3')
        for _ in range(10):
            nav.advance(self.w,self.p,world)
            if self.p['overworld']['status']=='encounter':break
        self.assertEqual(self.p['overworld']['status'],'encounter')
        self.assertEqual(self.p['pos'],[-9,3]);self.assertEqual(self.p['overworld']['mode'],'local')
        self.assertTrue(tactical.active(cell));before=copy.deepcopy(self.p['overworld'])
        self.assertFalse(nav.advance(self.w,self.p,world));self.assertEqual(self.p['overworld'],before)

    def test_companion_positions_follow_actual_sector_crossings(self):
        for npc in self.w['actors'][:2]:
            npc['owner']=self.p['id']
        self.act('go to -8,3');self.arrive()
        for npc in self.w['actors'][:2]:self.assertEqual([npc['x'],npc['y']],self.p['pos'])

    def test_old_rose_save_gets_discovery_without_starting_a_journey(self):
        self.p.pop('overworld');self.p['route']=[[-9,3]]
        state=world.snapshot(self.w,self.p)
        self.assertEqual(state['atlas']['navigation']['status'],'idle')
        self.assertEqual(self.p['route'],[[-9,3]])

    def test_partial_route_survives_roundtrip_without_visual_or_resource_drift(self):
        self.act('go to -8.2,3');nav.advance(self.w,self.p,world)
        saved=json.loads(json.dumps(self.w));loaded=saved['players'][0]
        self.assertEqual(world.snapshot(self.w,self.p)['atlas'],world.snapshot(saved,loaded)['atlas'])
        nav.advance(self.w,self.p,world);nav.advance(saved,loaded,world)
        self.assertEqual(self.p['overworld'],loaded['overworld'])
        self.assertEqual(self.p['inventory'],loaded['inventory'])


class HostTravelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'world.db')
        server.init_db(self.path);server.ACTIVE.clear()
        self.session=server.request(dict(op='create',name='Host',build='NanoClad Scout',seed='host-travel',rules={'generation':{'hostility':0}}))
    def tearDown(self):
        server.DB.close();server.ACTIVE.clear();self.tmp.cleanup()
    def call(self,op,**data):
        w=server.fetch(self.session['code'])
        return server.request(dict(**self.session,op=op,revision=w['revision'],**data))
    def test_host_clock_advances_travel_and_saves_it(self):
        self.call('start');self.call('act',text='go to -8,3')
        activity=server.ACTIVE[self.session['code']];now=activity['seen']
        server.pulse(now)
        before=self.call('state')['atlas']['navigation'];self.assertNotEqual(before['point'],geo.SPAWN)
        server.DB.close();server.init_db(self.path)
        self.assertEqual(before,self.call('state')['atlas']['navigation'])
    def test_stale_journey_redirect_preserves_current_state(self):
        self.call('start');result=self.call('act',text='go to -8,3')
        revision=result['state']['revision'];server.pulse(server.ACTIVE[self.session['code']]['seen'])
        before=self.call('state')['me']
        with self.assertRaises(ValueError):server.request(dict(**self.session,op='act',revision=revision,text='go to -7,3'))
        self.assertEqual(before,self.call('state')['me'])
    def test_restart_or_idle_reconnect_reactivates_saved_journey(self):
        self.call('start');self.call('act',text='go to -8,3')
        server.ACTIVE.clear();before=self.call('state')['atlas']['position']
        self.assertTrue(server.ACTIVE[self.session['code']]['traveling'])
        server.pulse(server.ACTIVE[self.session['code']]['seen'])
        self.assertNotEqual(before,self.call('state')['atlas']['position'])


if __name__=='__main__':unittest.main()
