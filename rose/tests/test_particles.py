import copy
import math
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import particles
import server
import world


class ParticleTests(RoseTest):
    def field(self):return particles.field(self.w,self.p,world)

    def prepared(self):
        self.p['credentials']=['black.dot'];self.p['percept'].update(armor=80,immunix=8)

    def imported(self):
        return dict(format='aurora-strata',version='1.0.0',state=dict(objects=[dict(id='source-a',name='Aurora object',mass=2.,charge=.5,frequency=1.5,phase=.1,element='physical',polarity='matter',matterType='normal',position=dict(x=120.,y=130.),velocity=dict(x=.1,y=0.))]))

    def test_field_seed_identity_is_reproducible_and_individual(self):
        f=self.field();other=world.new_world(self.w['seed']);other['code']='REPRO';p=world.add_player(other,'Other','Light Reader');world.snapshot(other,p)
        self.assertEqual(f,particles.field(other,p,world));self.assertEqual(len({n['id'] for n in f['objects']}),12);self.assertEqual(f['metrics']['pair_interactions'],66)

    def test_pair_force_is_equal_opposite_with_repelling_equal_charges(self):
        a,b=copy.deepcopy(self.field()['objects'][:2]);a.update(charge=1,matterType='normal',polarity='matter');b.update(charge=1,matterType='normal',polarity='matter');a['position']=dict(x=100.,y=100.);b['position']=dict(x=200.,y=100.)
        fx,fy=particles.influence(a,b);gx,gy=particles.influence(b,a);self.assertLess(fx,0);self.assertAlmostEqual(fx,-gx);self.assertAlmostEqual(fy,-gy)

    def test_same_tick_and_snapshot_do_not_move_particles(self):
        before=copy.deepcopy(self.field());particles.advance(self.w);world.snapshot(self.w,self.p);self.assertEqual(self.field(),before)

    def test_long_evolution_preserves_mass_ids_and_finite_bounds(self):
        f=self.field();ids={n['id'] for n in f['objects']};mass=sum(n['mass'] for n in f['objects'])
        for _ in range(600):self.w['tick']+=1;particles.advance(self.w)
        self.assertEqual({n['id'] for n in f['objects']},ids);self.assertEqual(sum(n['mass'] for n in f['objects']),mass)
        for n in f['objects']:
            self.assertTrue(0<=n['position']['x']<=600 and 0<=n['position']['y']<=400 and 0<=n['phase']<math.tau);self.assertTrue(all(math.isfinite(v) and abs(v)<=4 for v in n['velocity'].values()))

    def test_collision_changes_form_without_annihilating_identity(self):
        f=self.field();a,b=f['objects'][:2];a.update(polarity='matter',matterType='normal');b.update(polarity='antimatter',matterType='normal');a['position']=dict(x=100.,y=100.);b['position']=dict(x=101.,y=100.);before=particles.ensure(self.w)['generated_mass']
        self.w['tick']+=1;particles.advance(self.w);self.assertEqual(a['form'],'radiant');self.assertEqual(b['form'],'radiant');self.assertEqual(len(f['objects']),12);self.assertEqual(particles.ensure(self.w)['generated_mass'],before)

    def test_formations_reference_retained_particles_without_replacement(self):
        f=self.field()
        for n in f['objects']:n.update(element='physical',frequency=1.,phase=0.)
        particles.measure(f);self.assertEqual(len(f['formations']),66);self.assertEqual(len(f['objects']),12);self.assertEqual(f['metrics']['ras'],100)

    def test_particle_measurements_couple_to_habitat(self):
        f=self.field()
        for n in f['objects']:n.update(element='physical',frequency=1.,phase=0.)
        particles.measure(f);self.assertEqual(particles.coupling(self.w,self.c,world)['moisture'],1)
        for n in f['objects']:n['form']='radiant'
        particles.measure(f);self.assertEqual(particles.coupling(self.w,self.c,world)['stress'],1)

    def test_driving_uses_actual_power_even_on_setback(self):
        self.approach(next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='workshop'))
        f=self.field();self.c['infrastructure']['stores']['power']=5;before=copy.deepcopy(f['objects'])
        with patch('world.secrets.randbelow',return_value=0):self.act('excite particles')
        self.assertEqual(self.c['infrastructure']['stores']['power'],4);self.assertNotIn('external_drive_units',f);self.assertEqual(len(f['objects']),len(before))

    def test_import_preserves_source_identity_and_cannot_duplicate_an_evolved_batch(self):
        self.w['paused']=True;raw=self.imported();f=self.field();mass=f['metrics']['mass'];particles.import_objects(self.w,self.p,raw,world);self.assertEqual(f['metrics']['mass'],mass+2);n=f['objects'][-1];self.assertEqual(n['lineage']['source_id'],'source-a')
        raw['state']['objects'][0]['phase']=.5;before=copy.deepcopy(self.w)
        with self.assertRaisesRegex(ValueError,'identity'):particles.import_objects(self.w,self.p,raw,world)
        self.assertEqual(self.w,before)

    def test_import_rejects_partial_invalid_batches_and_nonfinite_or_boolean_data(self):
        self.w['paused']=True
        for key,value in [('mass',float('nan')),('charge',True),('frequency',float('inf')),('element',[]),('phase',-1)]:
            raw=self.imported();bad=copy.deepcopy(raw['state']['objects'][0]);bad['id']='source-b';bad[key]=value;raw['state']['objects'].append(bad);before=copy.deepcopy(self.w)
            with self.subTest(key=key),self.assertRaises(ValueError):particles.import_objects(self.w,self.p,raw,world)
            self.assertEqual(self.w,before)

    def test_import_requires_host_pause_and_cannot_grant_permissions(self):
        raw=self.imported();raw.update(rules={'admin':True},credentials=['admin.OS'])
        with self.assertRaises(ValueError):particles.import_objects(self.w,self.p,raw,world)
        guest=world.add_player(self.w,'Guest','Light Reader');world.snapshot(self.w,guest);self.w['paused']=True
        with self.assertRaises(ValueError):particles.import_objects(self.w,guest,raw,world)
        before=self.p['credentials'][:];particles.import_objects(self.w,self.p,raw,world);self.assertEqual(self.p['credentials'],before)

    def test_void_entry_and_branching_keep_anchor_and_return_trace(self):
        self.prepared();anchor=self.p['pos'][:];self.act('enter void_null');root=self.p['percept']['address'];self.act('advance void 2');child=self.p['percept']['address']
        self.assertNotEqual(root,child);self.assertEqual(self.p['pos'],anchor);self.assertEqual(self.p['percept']['path'],['2']);self.act('retreat void');self.assertEqual(self.p['percept']['address'],root)
        ids={n['id'] for n in self.w['substrate']['fields'][child]['objects']};self.act('advance void 2');self.assertEqual({n['id'] for n in self.field()['objects']},ids)

    def test_exhaustion_prevents_outward_step_but_never_traps_return(self):
        self.prepared();self.act('enter void_null');self.p['percept'].update(immunix=0,armor=0);before=copy.deepcopy(self.p['percept'])
        with self.assertRaises(ValueError):self.act('advance void 1')
        self.assertEqual(self.p['percept'],before)
        with patch('world.secrets.randbelow',return_value=0):self.act('return from void')
        self.assertIsNone(self.p['percept']['address'])

    def test_void_rejects_baseline_actions_and_preserves_admin_restrictions(self):
        self.prepared();self.act('enter void_null');inventory=self.p['inventory'].copy();tick=self.w['tick']
        for action,target in [('goto','red_gate'),('construction_plan','garden|1,0'),('attack',''),('register','')]:
            with self.subTest(action=action),self.assertRaises(ValueError):self.act(action,target)
        self.assertEqual(self.p['inventory'],inventory);self.assertEqual(self.w['tick'],tick);self.assertNotIn('admin.OS',self.p['credentials'])

    def test_sampling_deposit_and_carried_evolution_preserve_one_identity(self):
        self.p['credentials']=['black.dot'];self.p['loadout']=['meta_fingers'];f=self.field();n=f['objects'][0];id=n['id'];mass=n['mass'];self.act('particle_sample',id)
        self.assertNotIn(id,{o['id'] for o in f['objects']});sample=self.w['substrate']['carried'][id]['particle'];phase=sample['phase'];self.w['tick']+=1;particles.advance(self.w);self.assertNotEqual(sample['phase'],phase)
        self.act('particle_deposit',id);self.assertNotIn(id,self.w['substrate']['carried']);self.assertEqual(sum(o['id']==id for o in f['objects']),1);self.assertEqual(next(o['mass'] for o in f['objects'] if o['id']==id),mass)

    def test_snapshot_export_and_sqlite_restart_retain_particle_and_void_state(self):
        self.prepared();self.act('enter void_null');export=particles.export(self.w,self.p,world);self.assertNotIn('token',str(export));before=copy.deepcopy(self.w['substrate'])
        with tempfile.TemporaryDirectory() as tmp:
            server.init_db(str(Path(tmp)/'particles.db'));server.save(self.w);loaded=server.fetch(self.w['code']);p=next(p for p in loaded['players'] if p['id']==self.p['id']);world.snapshot(loaded,p)
            self.assertEqual(loaded['substrate'],before);self.assertEqual(p['percept'],self.p['percept'])

    def test_generation_and_import_mass_equal_all_retained_locations(self):
        self.prepared();self.act('enter void_null');self.act('advance void 0');self.act('return from void');self.w['paused']=True;particles.import_objects(self.w,self.p,self.imported(),world)
        data=self.w['substrate'];retained=sum(n['mass'] for f in data['fields'].values() for n in f['objects'])+sum(n['particle']['mass'] for n in data['carried'].values())
        self.assertAlmostEqual(retained,data['generated_mass']+data['imported_mass']);ids=[n['id'] for f in data['fields'].values() for n in f['objects']]+list(data['carried']);self.assertEqual(len(ids),len(set(ids)))

    def test_archive_budget_refusal_preserves_return_and_does_not_spend(self):
        self.prepared();self.act('enter void_null');before=self.p['percept'].copy()
        with patch('particles.MAX_FIELDS',len(self.w['substrate']['fields'])):
            with self.assertRaises(ValueError):self.act('advance void 1')
            self.assertEqual(self.p['percept'],before);self.act('return from void');self.assertIsNone(self.p['percept']['address'])

    def test_particle_degradation_and_reactivation_keep_identity_and_mass(self):
        f=self.field();n=next(n for n in f['objects'] if n['form']=='EUNIX');id=n['id'];mass=n['mass'];self.c['moisture']=0
        for _ in range(12):self.w['tick']+=1;particles.advance(self.w)
        self.assertEqual(n['form'],'dormant');self.assertEqual(n['id'],id);self.assertEqual(n['mass'],mass)
        self.c['moisture']=70;self.c['lifecycle']['soil_health']=50
        for _ in range(20):self.w['tick']+=1;particles.advance(self.w)
        self.assertEqual(n['form'],'EUNIX');self.assertEqual(n['mass'],mass);self.assertGreaterEqual(n['complexity'],1)

    def test_single_particle_export_is_isolated_and_does_not_extract_or_advance(self):
        f=self.field();before=copy.deepcopy(self.w);id=f['objects'][0]['id'];export=particles.export(self.w,self.p,world,id)
        self.assertEqual(len(export['state']['objects']),1);self.assertEqual(export['state']['objects'][0]['id'],id);self.assertEqual(self.w,before)

    def test_particle_archive_budget_does_not_block_new_baseline_exploration(self):
        retained=copy.deepcopy(self.w['substrate']['fields']);self.p['pos']=[-9,3]
        with patch('particles.MAX_FIELDS',len(retained)):
            state=world.snapshot(self.w,self.p)
            self.assertEqual(state['particles']['objects'],[]);self.assertIn('unresolved_reason',state['particles'])
            self.assertEqual(self.w['substrate']['fields'],retained)
            with self.assertRaisesRegex(ValueError,'archive'):self.act('excite particles')
            self.act('inspect environment');self.assertEqual(self.p['pos'],[-9,3])
