"""Audit regressions: recovery, availability and isolation of clock faults."""
import copy
from pathlib import Path
import sys
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import navigation
import server
import tactical
import world
from test_engine import RoseTest


class RecoveryAndControlTests(RoseTest):
    def test_open_map_during_travel_preserves_journey_and_costs(self):
        self.act('goto', '-8,3')
        navigation.advance(self.w, self.p, world)
        before = copy.deepcopy(self.p['overworld'])
        inventory, tick = copy.deepcopy(self.p['inventory']), self.w['tick']
        self.act('world_map', '')
        self.assertEqual(self.p['overworld'], before)
        self.assertEqual(self.p['inventory'], inventory)
        self.assertEqual(self.w['tick'], tick)

    def test_relocation_clears_the_obsolete_destination(self):
        self.act('goto', '-8,3')
        self.p.update(pos=[-14,3], route=[], destination=None)
        state = world.snapshot(self.w, self.p)
        self.assertIsNone(state['atlas']['navigation']['target'])
        self.assertEqual(state['atlas']['navigation']['point'], [-14,3])
        with self.assertRaises(ValueError): self.act('resume_travel', '')

    def test_recovery_at_spawn_cancels_a_route_even_without_relocation(self):
        self.act('goto', '-8,3')
        self.p.update(health=1, thirst=100)
        self.act('wait', '')
        state = world.snapshot(self.w, self.p)
        self.assertEqual(state['atlas']['navigation']['status'], 'recovery')
        self.assertIsNone(state['atlas']['navigation']['target'])
        self.assertEqual(self.p['route'], [])
        with self.assertRaises(ValueError): self.act('resume_travel', '')

    def test_resume_replans_an_older_inconsistent_route(self):
        self.act('goto', '12,3')
        self.act('stop_travel', '')
        self.p['route'] = [[12,3]]  # Older/inconsistent saves must not head through water.
        expected = navigation.route(self.p['pos'], [12,3])
        before = self.p['inventory'].copy()
        self.act('resume_travel', '')
        self.assertEqual(self.p['route'], expected)
        self.assertEqual(self.p['inventory'], before)

    def test_control_prerequisites_do_not_spend_or_roll(self):
        before = copy.deepcopy(self.w)
        tactical.availability(self.w, self.c, self.p, world)
        self.assertEqual(self.w, before)
        for field, value, fragment in [('started',False,'begin'),('paused',True,'paused')]:
            with self.subTest(field=field):
                old=self.w[field];self.w[field]=value
                controls=tactical.availability(self.w,self.c,self.p,world)
                self.assertTrue(all(not c['allowed'] and fragment in c['reason'] for c in controls.values()))
                self.w[field]=old
        self.p['remote']=True
        self.assertFalse(tactical.availability(self.w,self.c,self.p,world)['hex_move']['allowed'])

    def test_ap_turn_and_host_override_are_reflected_in_controls(self):
        enc=self.battle()
        enc['ap'][self.p['id']]=1
        controls=tactical.availability(self.w,self.c,self.p,world)
        self.assertFalse(controls['attack']['allowed'])
        self.assertIn('AP',controls['attack']['reason'])
        self.assertTrue(controls['end_turn']['allowed'])
        guest=world.add_player(self.w,'Guest','Light Reader');world.snapshot(self.w,guest)
        enc['current']=guest['id']
        host=tactical.availability(self.w,self.c,self.p,world)
        self.assertFalse(host['hex_move']['allowed'])
        self.assertTrue(host['end_turn']['allowed'])
        enc['current']=self.p['id']
        self.assertFalse(tactical.availability(self.w,self.c,guest,world)['end_turn']['allowed'])

    def test_range_equipment_and_care_requirements_are_reflected(self):
        self.battle(pos=(2,0))
        controls=tactical.availability(self.w,self.c,self.p,world)
        self.assertIn('Approach',controls['attack']['reason'])
        self.assertIn('registered',controls['shoot']['reason'])
        self.assertIn('No care',controls['combat_care']['reason'])
        self.p['health']=50;self.p['inventory']['medkit']=0
        self.assertIn('medkit',tactical.availability(self.w,self.c,self.p,world)['combat_care']['reason'])


class ClockIsolationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();server.init_db(str(Path(self.tmp.name)/'audit.db'));server.ACTIVE.clear()
        self.sessions=[]
        for name in ['Faulted','Healthy']:
            s=server.request(dict(op='create',name=name,build='NanoClad Scout',seed=name,rules={'generation':{'hostility':0}}))
            self.sessions.append(s)
            w=server.fetch(s['code'])
            server.request(dict(**s,op='start',revision=w['revision']))
            w=server.fetch(s['code'])
            server.request(dict(**s,op='act',text='go to -8,3',revision=w['revision']))
    def tearDown(self):
        server.DB.close();server.ACTIVE.clear();self.tmp.cleanup()

    def test_one_faulted_room_cannot_kill_other_journeys_or_commit_partial_work(self):
        broken,healthy=self.sessions
        before=server.fetch(broken['code'])
        original=navigation.advance
        def fail_one(w,p,engine):
            if w['code']==broken['code']:
                p['inventory']['scrap']=0
                raise ValueError('Injected travel fault')
            return original(w,p,engine)
        now=max(a['seen'] for a in server.ACTIVE.values())
        with patch('navigation.advance',side_effect=fail_one),self.assertLogs(level='ERROR'):
            server.pulse(now)
        self.assertEqual(server.fetch(broken['code']),before)
        self.assertNotEqual(server.fetch(healthy['code'])['players'][0]['overworld']['point'],before['spawn'])
        self.assertTrue(server.request(dict(**broken,op='state'))['clock_error'])
        frozen=server.fetch(broken['code']);server.pulse(now+1)
        self.assertEqual(server.fetch(broken['code']),frozen)
        w=server.fetch(broken['code'])
        answer=server.request(dict(**broken,op='pause',revision=w['revision']))
        self.assertEqual(answer['state']['clock_error'],'')

    def test_ecology_fault_is_isolated_too(self):
        broken,healthy=self.sessions
        for s in self.sessions:
            w=server.fetch(s['code']);server.request(dict(**s,op='act',text='stop travel',revision=w['revision']))
        now=max(a['next'] for a in server.ACTIVE.values());original=world.tick
        def fail_one(w,*args):
            if w['code']==broken['code']:raise RuntimeError('Injected ecology fault')
            return original(w,*args)
        with patch('world.tick',side_effect=fail_one),self.assertLogs(level='ERROR'):server.pulse(now)
        self.assertEqual(server.fetch(broken['code'])['tick'],0)
        self.assertEqual(server.fetch(healthy['code'])['tick'],1)

    def test_rejected_sqlite_write_rolls_back_and_leaves_the_saved_world_intact(self):
        session=self.sessions[0];before=server.fetch(session['code'])
        server.DB.execute('PRAGMA query_only=ON')
        try:
            with self.assertRaises(sqlite3.OperationalError):
                server.request(dict(**session,op='act',text='look',revision=before['revision']))
            self.assertFalse(server.DB.in_transaction)
            self.assertEqual(server.fetch(session['code']),before)
        finally:server.DB.execute('PRAGMA query_only=OFF')
        self.assertEqual(server.request(dict(**session,op='state'))['revision'],before['revision'])


if __name__=='__main__':unittest.main()
