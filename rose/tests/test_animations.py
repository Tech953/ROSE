"""Committed motion, combat timing, hidden solver poses and save boundaries."""
import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import test_physics
import animations
import hexgrid as hx
import materials
import machines
import physics
import scene
import server
import tactical
import world


class AnimationTests(RoseTest):
    def rows(self):
        return animations.public(self.c['scene'])['events']

    def test_one_adjacent_commit_records_direction_and_foot_path_without_clock_step(self):
        start=self.p['local']['pos'][:]
        target=next(q for q in hx.neighbors(start) if self.c['scene']['tiles'][hx.key(q)]['passable']
                    and q not in scene.occupied(self.w,self.c,self.p['id']))
        tick=self.w['tick'];self.act('hex_move',hx.key(target))
        row=next(e for e in reversed(self.rows()) if e['subject']==self.p['id'])
        self.assertEqual(row['kind'],'move');self.assertEqual(row['path'],[start,target])
        self.assertEqual(row['duration_ms'],360);self.assertEqual(row['facing'],hx.DIRS.index(tuple(target[i]-start[i] for i in range(2))))
        self.assertEqual(self.w['tick'],tick)

    def test_all_six_headings_match_hex_directions(self):
        for n,d in enumerate(hx.DIRS):
            self.assertEqual(animations.facing([0,0],d),n)
            self.assertEqual(animations.facing([2,-3],[2+5*d[0],-3+5*d[1]]),n)

    def test_successful_attack_contact_uses_committed_damage_while_ap_clock_is_held(self):
        enc=self.battle();tick=self.w['tick'];health=self.c['threat']['health'];serial=animations.ensure(self.c['scene'])['serial']
        self.act('attack','');row=next(e for e in self.rows() if e['id']>serial and e['kind']=='strike')
        self.assertEqual(row['damage'],health-self.c['threat']['health']);self.assertTrue(row['hit'])
        self.assertEqual(row['target'],'unit:threat');self.assertEqual(row['contact_ms'],435)
        self.assertEqual(row['facing'],animations.facing(row['source'],row['destination']))
        self.assertEqual(self.w['tick'],tick);self.assertTrue(enc['active'])

    def test_miss_retains_attack_but_has_no_hit_result(self):
        self.battle();health=self.c['threat']['health']
        with patch('world.secrets.randbelow',return_value=0):self.act('attack','')
        row=next(e for e in reversed(self.rows()) if e['kind']=='strike')
        self.assertFalse(row['hit']);self.assertEqual(row['damage'],0);self.assertEqual(row['reactions'],[])
        self.assertEqual(self.c['threat']['health'],health)

    def test_rejected_ap_weapon_and_range_actions_do_not_create_cues(self):
        enc=self.battle();enc['ap'][self.p['id']]=0;before=copy.deepcopy(animations.public(self.c['scene']))
        with self.assertRaises(ValueError):self.act('attack','')
        self.assertEqual(animations.public(self.c['scene']),before)
        enc['ap'][self.p['id']]=20;self.p['gear']['field_staff']['condition']=0
        with self.assertRaises(ValueError):self.act('attack','')
        self.assertEqual(animations.public(self.c['scene']),before)
        self.c['threat']['local_pos']=[5,0]
        with self.assertRaises(ValueError):self.act('attack','')
        self.assertEqual(animations.public(self.c['scene']),before)

    def test_ranged_cue_tracks_charge_and_contact_distance(self):
        self.p['loadout']=['crystallin'];self.p['credentials']=['black.dot'];materials.ensure_gear(self.p,self.w['tick'])
        self.battle(pos=(2,0));scrap=self.p['inventory']['scrap'];self.act('shoot','')
        row=next(e for e in reversed(self.rows()) if e['kind']=='strike')
        self.assertTrue(row['ranged']);self.assertEqual(row['contact_ms'],408)
        self.assertEqual(self.p['inventory']['scrap'],scrap-1)

    def test_enemy_chase_records_contiguous_path_before_strike(self):
        self.battle(pos=(3,0));s=self.c['scene'];enc=s['encounter'];enc['ap']['threat']=20
        before=animations.ensure(s)['serial'];tactical.enemy_turn(self.w,self.c,world)
        rows=[e for e in self.rows() if e['id']>before and e['subject']=='threat']
        self.assertEqual([e['kind'] for e in rows],['move','strike'])
        self.assertTrue(all(hx.distance(a,b)==1 for a,b in zip(rows[0]['path'],rows[0]['path'][1:])))
        self.assertEqual(rows[0]['path'][-1],rows[1]['source'])

    def test_shared_guard_has_one_attack_and_two_synchronized_reactions(self):
        self.battle();ally=self.w['actors'][0];ally.update(owner=self.p['id'],health=100,local_guard=2)
        ally['x'],ally['y']=self.p['pos'];ally['local']['pos']=[-1,0]
        self.c['scene']['encounter']['participants'].append(ally['id']);self.c['scene']['encounter']['ap']['threat']=20
        before=animations.ensure(self.c['scene'])['serial']
        with patch('world.check',return_value=(False,'impact fixture')):tactical.enemy_turn(self.w,self.c,world)
        rows=[e for e in self.rows() if e['id']>before and e['kind']=='strike']
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['target'],'unit:'+self.p['id'])
        self.assertEqual(rows[0]['damage'],4);self.assertEqual(rows[0]['reactions'],[dict(target='unit:'+ally['id'],destination=[-1,0],damage=3)])

    def test_demolition_orders_strike_collapse_and_once_only_clear(self):
        node=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='water');self.approach(node)
        node['condition']=1;before=animations.ensure(self.c['scene'])['serial'];self.act('material_strike','structure:'+node['id'])
        rows=[e for e in self.rows() if e['id']>before]
        strike=next(e for e in rows if e['kind']=='strike');collapse=next(e for e in rows if e['kind']=='collapse')
        self.assertLess(strike['id'],collapse['id']);self.assertEqual(collapse['subject'],strike['target'])
        self.assertEqual(collapse['before_condition'],1);serial=animations.ensure(self.c['scene'])['serial']
        materials.collapse_node(self.w,self.c,node,world);self.assertEqual(animations.ensure(self.c['scene'])['serial'],serial)
        self.act('material_clear','structure:'+node['id']);count=sum(e['kind']=='clear' for e in self.rows())
        with self.assertRaises(ValueError):self.act('material_clear','structure:'+node['id'])
        self.assertEqual(sum(e['kind']=='clear' for e in self.rows()),count)

    def test_full_pack_cannot_animate_or_consume_failed_recovery(self):
        node=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='water');self.approach(node)
        materials.damage(node,100,self.w['tick']);materials.collapse_node(self.w,self.c,node,world)
        self.p['inventory']['scrap']=99;before=copy.deepcopy(animations.public(self.c['scene']))
        with self.assertRaises(ValueError):self.act('material_clear','structure:'+node['id'])
        self.assertEqual(animations.public(self.c['scene']),before)

    def test_bounded_cue_history_is_detached_and_survives_sqlite(self):
        for _ in range(200):scene.pose(self.c['scene'],self.p,'work')
        data=animations.public(self.c['scene']);self.assertEqual(len(data['events']),96)
        self.assertEqual([e['id'] for e in data['events']],list(range(data['serial']-95,data['serial']+1)))
        data['events'][0]['path'][0][0]=100;self.assertNotEqual(data,animations.public(self.c['scene']))
        with tempfile.TemporaryDirectory() as d:
            server.init_db(str(Path(d)/'motion.sqlite'));server.save(self.w)
            try:self.assertEqual(server.fetch(self.w['code'])['cells'][hx.key(self.p['pos'])]['scene']['animation'],self.c['scene']['animation'])
            finally:server.DB.close()

    def test_existing_save_migrates_without_invented_actions_or_read_restart(self):
        self.c['scene'].pop('animation',None);tick=self.w['tick'];state=world.snapshot(self.w,self.p)
        self.assertEqual(state['scene']['animation'],dict(schema=1,serial=0,events=[]))
        before=copy.deepcopy(self.c['scene']['animation']);world.snapshot(self.w,self.p)
        self.assertEqual(self.c['scene']['animation'],before);self.assertEqual(self.w['tick'],tick)


class HardwareAnimationTests(RoseTest):
    def mount(self,kind='pump'):
        return test_physics.MachineTests.mount(self,kind)

    def test_public_frames_end_at_exact_solver_pose_for_all_three_applications(self):
        for kind in ['pump','press','damper']:
            with self.subTest(kind=kind):
                f,node=self.mount(kind);self.act('machine_operate',node['id']);r=f['mechanism'];m=node['machine']['motion']
                self.assertTrue(m['active']);self.assertEqual(m['duration_ms'],500);self.assertLessEqual(len(m['frames']),33)
                self.assertEqual(m['frames'][0]['at'],0.);self.assertEqual(m['frames'][-1]['at'],1.)
                self.assertEqual(m['frames'][-1]['offset'],machines.visible_frame(r)['offset'])
                self.assertTrue(all(a['at']<=b['at'] for a,b in zip(m['frames'],m['frames'][1:])))
                self.assertEqual(machines.combined_audit(f)['status'],'PASS');self.act('machine_stop',node['id'])

    def test_shutdown_publishes_parked_pose_once_and_no_motion_energy(self):
        f,node=self.mount();self.act('machine_operate',node['id']);self.act('machine_stop',node['id']);r=f['mechanism']
        m=copy.deepcopy(node['machine']['motion']);self.assertFalse(m['active']);self.assertEqual(m['duration_ms'],0)
        self.assertEqual(m['frames'][0]['offset'],[0.,0.]);self.assertEqual(physics.energy(r['solver']),0.)
        machines.reconcile(f,self.c);self.assertEqual(r['visual_motion'],m)

    def test_offline_and_fatigue_failure_park_without_another_job(self):
        f,node=self.mount();self.act('machine_operate',node['id']);r=f['mechanism'];node['enabled']=False
        machines.reconcile(f,self.c);self.assertFalse(node['machine']['motion']['active'])
        self.assertEqual(node['machine']['motion']['duration_ms'],0);self.assertEqual(physics.energy(r['solver']),0.)

    def test_no_input_has_no_invented_hardware_displacement(self):
        f,node=self.mount();f['vrex']['preset']='static';self.act('machine_operate',node['id'])
        for _ in range(4):
            self.act('wait');self.assertTrue(all(frame['offset']==[0.,0.] for frame in node['machine']['motion']['frames']))
        self.assertEqual(physics.energy(f['mechanism']['solver']),0.)

    def test_combat_hold_does_not_advance_hardware_and_reads_leave_ledgers_unchanged(self):
        f,node=self.mount();self.act('machine_operate',node['id']);self.battle(pos=(3,0))
        before=copy.deepcopy(f);motion=copy.deepcopy(node['machine']['motion']);world.tick(self.w)
        self.assertEqual(f,before);self.assertEqual(node['machine']['motion'],motion)
        for _ in range(3):world.snapshot(self.w,self.p)
        self.assertEqual(f,before)

    def test_game_snapshot_exposes_only_curated_hardware_poses(self):
        f,node=self.mount();self.act('machine_operate',node['id']);before=copy.deepcopy(f)
        state=world.snapshot(self.w,self.p);public=next(n['machine'] for n in state['scene']['infrastructure']['nodes'] if n['id']==node['id'])
        self.assertEqual(set(public['motion']),{'schema','serial','duration_ms','active','frames'})
        for frame in public['motion']['frames']:self.assertEqual(set(frame),{'at','offset','angle','contact','sleeping'})
        self.assertNotIn('mechanism',state['particles']);self.assertNotIn('vrex',state['particles'])
        self.assertNotIn('cross_correlation',json.dumps(state));self.assertNotIn('normalized_residual',json.dumps(state))
        public['motion']['frames'][0]['offset'][0]=999;self.assertEqual(f,before)

    def test_pre_animation_machine_save_restores_current_pose_without_a_solver_step(self):
        f,node=self.mount();self.act('machine_operate',node['id']);r=f['mechanism']
        for key in ['visual_frames','visual_serial','visual_motion']:r.pop(key,None)
        solver=copy.deepcopy(r['solver']);source=copy.deepcopy(f['vrex']);machines.reconcile(f,self.c)
        motion=node['machine']['motion'];self.assertEqual(motion['duration_ms'],0);self.assertEqual(len(motion['frames']),1)
        self.assertEqual(motion['frames'][0]['offset'],machines.visible_frame(r)['offset'])
        self.assertEqual(r['solver'],solver);self.assertEqual(f['vrex'],source)
