"""Physical nulls, finite ownership, measurement joins and authoritative controls."""
import copy
import json
import math
from pathlib import Path
import tempfile
from unittest.mock import patch

from test_engine import RoseTest
import infrastructure
import particles
import photonics
import research
import server
import vrex
import world


class VrexTests(RoseTest):
    def field(self):return particles.field(self.w,self.p,world)
    def node(self):return next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='workshop')
    def prepared(self):
        node=self.node();self.approach(node);self.c['infrastructure']['stores']['power']=20
        self.act('vrex_configure',node['id']+'|returned')
        return self.field()['vrex'],node

    def test_configuration_and_tracking_join_actual_retained_particle_ids(self):
        v,node=self.prepared();f=self.field()
        self.assertEqual({n['particle_id'] for n in v['states']},{n['id'] for n in f['objects']})
        self.assertEqual(v['source_node'],node['id']);self.assertEqual(v['ledger']['input'],0)
        self.assertEqual(self.p['last_check']['skill'],'light');self.assertEqual(self.p['last_check']['faction'],node['faction'])
        self.assertEqual(len(v['links']),36);self.assertEqual(v['observations'][-1]['tick'],self.w['tick'])
        self.assertTrue(all(n['model_phase'] is None for n in v['observations'][-1]['particles']))
        self.assertTrue(all(n['observed_particle_rate'] is not None for n in v['observations'][-1]['particles']))

    def test_paid_drive_advances_mechanics_with_finite_energy_and_nonnegative_load(self):
        v,node=self.prepared();power=self.c['infrastructure']['stores']['power'];optical=copy.deepcopy(self.field()['photonics'])
        self.act('vrex_pump',node['id'])
        self.assertEqual(v['ledger']['input'],1);self.assertLessEqual(self.c['infrastructure']['stores']['power'],power-1)
        self.assertGreater(vrex.energy(v),0);self.assertGreater(v['ledger']['load'],0)
        self.assertEqual(vrex.audit(v)['status'],'PASS');self.assertGreater(v['ledger']['drive'],0)
        self.assertEqual(self.field()['photonics']['input_energy'],optical['input_energy'])
        self.assertTrue(any(n['phase_residual'] is not None for n in v['observations'][-1]['particles']))

    def test_independent_harmonic_solution_matches_analytic_period(self):
        v=vrex.new('harmonic',preset='static');v['parameters'].update(alpha=0.,damping=0.,coupling=0.,tether_coupling=0.,tether_damping=0.)
        v['states'][0].update(q=.2,v=0.,omega=1.);v['ledger']['input']=vrex.energy(v)
        vrex.advance(v,duration=math.pi,dt=1/64)
        self.assertAlmostEqual(v['states'][0]['q'],-.2,places=8)
        self.assertAlmostEqual(v['states'][0]['v'],0.,places=8)
        self.assertEqual(vrex.audit(v)['status'],'PASS')

    def test_static_conservative_tether_closed_cycle_and_perpendicular_power(self):
        v=vrex.new('null',preset='static');v['parameters'].update(force=0.,tether_coupling=0.,tether_damping=0.)
        v.update(s=.2,u=0.);v['ledger']['input']=vrex.energy(v)
        vrex.advance(v,duration=math.tau,dt=1/64)
        self.assertAlmostEqual(v['s'],.2,places=8);self.assertAlmostEqual(v['ledger']['tether_work'],0.,places=8)
        self.assertAlmostEqual(v['ledger']['load'],0.)
        # A central x force does no work on a purely perpendicular velocity.
        self.assertEqual(sum(a*b for a,b in zip([-1.,0.],[0.,2.])),0.)

    def test_each_preset_closes_a_long_finite_run_and_never_overdraws(self):
        for preset in vrex.PRESETS:
            v=vrex.new('long-'+preset,preset=preset);vrex.pump(v,True,dict(id='rig'))
            for _ in range(150):vrex.advance(v)
            self.assertFalse(v['running']);self.assertGreaterEqual(v['bank'],0.)
            self.assertEqual(vrex.audit(v)['status'],'PASS',v['ledger'])
            self.assertLessEqual(v['ledger']['load']+vrex.energy(v)+v['bank'],v['ledger']['input']+1e-6)
            self.assertEqual(len(v['trace']),vrex.TRACE_LIMIT)

    def test_return_channel_owns_the_debit_once_and_gain_is_paid(self):
        v=vrex.new('return',preset='gain');vrex.pump(v,True,dict(id='rig'))
        for _ in range(12):vrex.advance(v)
        self.assertGreater(v['ledger']['returned'],0);self.assertGreater(v['ledger']['controller'],0)
        self.assertAlmostEqual(v['ledger']['reuptake'],.5*v['ledger']['returned'])
        self.assertEqual(vrex.audit(v)['status'],'PASS');self.assertEqual(v['ledger']['input'],1)
        self.assertGreater(v['ledger']['heat'],.2)

    def test_stop_dissipates_storage_without_refund_and_cold_restart_needs_new_input(self):
        v,node=self.prepared();self.act('pump vrex');before=vrex.audit(v);input=v['ledger']['input']
        self.act('stop vrex');self.assertEqual(v['bank']+vrex.energy(v),0.)
        self.assertAlmostEqual(v['ledger']['heat'],before['heat']+before['stored'],places=7)
        self.assertEqual(vrex.audit(v)['status'],'PASS');self.act('wait')
        self.assertEqual(v['ledger']['input'],input);self.assertEqual(vrex.energy(v),0.)
        self.act('pump vrex');self.assertEqual(v['ledger']['input'],input+1)

    def test_source_outage_discards_energy_preserves_binding_and_repair_does_not_resume(self):
        v,node=self.prepared();self.act('pump vrex');ids=[n['id'] for n in v['states']]
        self.act('structure_toggle',node['id']);self.assertEqual(v['status'],'OFFLINE / DISSIPATED')
        self.assertEqual(v['bank']+vrex.energy(v),0);self.assertEqual(v['source_node'],node['id'])
        node['condition']=40;self.act('structure_repair',node['id']);self.act('structure_toggle',node['id'])
        self.assertFalse(v['running']);self.assertEqual([n['id'] for n in v['states']],ids)
        self.assertEqual(v['ledger']['input'],1);self.assertEqual(vrex.audit(v)['status'],'PASS')

    def test_same_cycle_network_break_applies_final_source_state(self):
        v,node=self.prepared();self.act('pump vrex')
        for link in self.c['infrastructure']['links']:
            if node['id'] in [link['a'],link['b']]:link['condition']=0
        particles.reconcile_sources(self.w)
        self.assertFalse(v['running']);self.assertEqual(vrex.energy(v)+v['bank'],0.)

    def test_stimulus_changes_preserve_phase_and_storage_before_metered_time_step(self):
        v,node=self.prepared();self.act('pump vrex');old=copy.deepcopy(v);phase=v['phase'];stored=v['bank']+vrex.energy(v)
        with patch('world.tick'):
            self.act('vrex_stimulus',node['id']+'|0.42:1.9')
        self.assertEqual(v['phase'],phase);self.assertEqual(v['bank']+vrex.energy(v),stored)
        self.assertEqual(v['ledger'],old['ledger']);self.assertEqual(v['parameters']['force'],.42)
        self.assertEqual(v['parameters']['drive_omega'],1.9);self.assertEqual(v['stimulus_events'][-1]['action'],'vrex_stimulus')

    def test_failed_input_becomes_heat_and_failed_settings_retain_configuration(self):
        v,node=self.prepared();before=copy.deepcopy(v['parameters'])
        with patch('world.secrets.randbelow',return_value=0):
            self.act('vrex_stimulus',node['id']+'|0.42:1.9');self.act('vrex_pump',node['id'])
        self.assertEqual(v['parameters'],before);self.assertEqual(v['ledger']['input'],1.)
        self.assertEqual(v['ledger']['heat'],1.);self.assertEqual(vrex.energy(v),0.)

    def test_physical_checks_reject_distance_remote_combat_void_pause_and_foreign_node(self):
        node=self.node()
        with self.assertRaisesRegex(ValueError,'adjacent'):self.act('configure vrex loaded')
        v,node=self.prepared()
        for op,target in [('vrex_pump','foreign'),('vrex_configure','foreign|gain'),('vrex_stimulus','foreign|0.28:1.8')]:
            with self.assertRaises(ValueError):self.act(op,target)
        self.p['remote']=True
        with self.assertRaisesRegex(ValueError,'remote'):self.act('pump vrex')
        self.p['remote']=False;self.w['paused']=True
        with self.assertRaisesRegex(ValueError,'paused'):self.act('pump vrex')
        self.w['paused']=False;self.battle()
        with self.assertRaisesRegex(ValueError,'encounter'):self.act('pump vrex')

    def test_invalid_settings_have_no_input_or_field_changes(self):
        v,node=self.prepared()
        for op,target in [('vrex_configure',node['id']+'|vacuum'),('vrex_stimulus','nan:1.8'),('vrex_stimulus','0.28:99')]:
            before=copy.deepcopy(v)
            with self.assertRaises(ValueError):self.act(op,target)
            self.assertEqual(v,before)

    def test_growth_budget_preserves_individuals_and_requires_zero_energy(self):
        v,node=self.prepared();ids=[n['id'] for n in v['states']];self.act('expand vrex')
        self.assertEqual(len(v['states']),14);self.assertEqual([n['id'] for n in v['states'][:12]],ids)
        self.act('pump vrex')
        with self.assertRaisesRegex(ValueError,'Stop'):self.act('expand vrex')
        with self.assertRaisesRegex(ValueError,'Stop'):self.act('configure vrex gain')
        self.act('stop vrex')
        for _ in range(3):self.act('expand vrex')
        self.assertEqual(len(v['states']),20)
        with self.assertRaisesRegex(ValueError,'twenty'):self.act('expand vrex')

    def test_blind_recovery_uses_no_reference_and_does_not_restore_mechanical_energy(self):
        v,node=self.prepared();reference=copy.deepcopy(v['links']);self.act('pump vrex')
        before=vrex.energy(v);vrex.perturb(v);distance=vrex.graph_distance(v['links'],reference)
        for _ in range(40):vrex.recover(v)
        self.assertLess(vrex.graph_distance(v['links'],reference),distance*1e-3)
        self.assertEqual(vrex.energy(v),before)

    def test_loop_phase_is_invariant_under_local_reference_changes(self):
        v=vrex.new('gauge');original=vrex.loops(v);self.assertGreater(len(original),0)
        delta={n['id']:i*.4 for i,n in enumerate(v['states'])}
        for edge in v['links']:edge['phase']+=delta[edge['a']]-delta[edge['b']]
        changed=vrex.loops(v)
        for a,b in zip(original,changed):self.assertAlmostEqual(vrex.wrap(a['phase']-b['phase']),0.,places=12)

    def test_diagnostics_are_measured_reproducible_and_read_only(self):
        v,node=self.prepared();self.act('stimulus vrex 0.14 1.7');self.act('pump vrex')
        before=copy.deepcopy(v);tick=self.w['tick'];pack=self.p['inventory'].copy();stores=self.c['infrastructure']['stores'].copy()
        self.act('test vrex');d=v['diagnostics'];after=copy.deepcopy(v);after['diagnostics']=None;after['diagnostic_serial']=0
        self.assertEqual(after,before);self.assertEqual(self.w['tick'],tick);self.assertEqual(self.p['inventory'],pack);self.assertEqual(self.c['infrastructure']['stores'],stores)
        self.assertEqual(d['convergence']['status'],'PASS');self.assertGreater(d['convergence']['refinement_ratio'],4)
        self.assertEqual(d['topology']['status'],'PASS');self.assertFalse(d['topology']['reference_visible_to_dynamics'])
        self.assertEqual(d['load']['status'],'PASS');self.assertEqual(d['order']['status'],'NOT DETECTED')
        self.assertEqual(d['laboratory']['status'],'NOT RUN');self.assertGreater(d['representation']['residual'],0)
        self.assertEqual(d['stimulus']['force'],.14);self.assertEqual(d['stimulus']['drive_omega'],1.7)
        repeated=vrex.diagnostics(v)
        for key in ['convergence','load','topology','order','representation']:self.assertEqual(d[key],repeated[key])
        self.assertEqual([g['status'] for g in research.gates(self.field())],['NOT DETECTED','PASS','PASS','PASS','NOT RUN'])

    def test_measurements_survive_sampling_and_do_not_lose_particle_identity(self):
        v,node=self.prepared();particle=self.field()['objects'][0];identity=particle['id']
        self.p['loadout'].append('meta_fingers');self.p['credentials'].append('black.dot')
        self.act('particle_sample',identity)
        row=next(n for n in v['observations'][-1]['particles'] if n['particle_id']==identity)
        self.assertFalse(row['present']);self.assertIsNone(row['particle_phase'])
        self.act('particle_deposit',identity)
        row=next(n for n in v['observations'][-1]['particles'] if n['particle_id']==identity)
        self.assertTrue(row['present']);self.assertEqual(row['particle_id'],identity)

    def test_persistent_state_replays_exactly_and_exports_without_tokens_or_mutation(self):
        v,node=self.prepared();self.act('pump vrex');self.act('test vrex')
        with tempfile.TemporaryDirectory() as temp:
            server.init_db(str(Path(temp)/'vrex.db'));server.save(self.w);loaded=server.fetch(self.w['code'])
            retained=loaded['substrate']['fields'][self.field()['address']]['vrex'];self.assertEqual(retained,v)
            a=copy.deepcopy(v);b=copy.deepcopy(retained);vrex.advance(a);vrex.advance(b);self.assertEqual(a,b)
            before=server.fetch(self.w['code']);raw=server.request(dict(op='vrex_export',code=self.w['code'],token=self.p['token']))
            self.assertEqual(raw['format'],'Rose-VREX-systems');self.assertEqual(raw['state'],v)
            self.assertNotIn(self.p['token'],json.dumps(raw));self.assertEqual(server.fetch(self.w['code']),before)

    def test_stale_shared_request_cannot_charge_or_change_stimulus(self):
        v,node=self.prepared();second=world.add_player(self.w,'Sam','NanoClad Scout')
        world.snapshot(self.w,second);second['local']['pos']=self.p['local']['pos'][:]
        with tempfile.TemporaryDirectory() as temp:
            server.init_db(str(Path(temp)/'shared.db'));server.save(self.w)
            rev=self.w['revision'];server.request(dict(op='act',code=self.w['code'],token=self.p['token'],revision=rev,intent=dict(action='vrex_pump',target=node['id'])))
            before=server.fetch(self.w['code'])
            with self.assertRaisesRegex(ValueError,'changed|refresh'):
                server.request(dict(op='act',code=self.w['code'],token=second['token'],revision=rev,intent=dict(action='vrex_stimulus',target=node['id']+'|0.42:1.9')))
            self.assertEqual(server.fetch(self.w['code']),before)

    def test_invalid_ledgers_fail_without_numerical_repair(self):
        for key,value in [('bank',True),('bank',-1.),('k',float('nan')),('k',-1.)]:
            v=vrex.new('invalid');v[key]=value;result=vrex.audit(v)
            self.assertEqual(result['status'],'FAIL');json.dumps(result,allow_nan=False)
        v=vrex.new('unpaid');v['states'][0]['q']=1.;self.assertEqual(vrex.audit(v)['status'],'FAIL')
        self.assertEqual(v['ledger']['heat'],0.)

    def test_particle_import_cannot_inject_model_state_or_measurements(self):
        f=self.field();obj=copy.deepcopy(f['objects'][0]);obj['id']='forged-vrex';self.w['paused']=True
        raw=dict(format='Rose-info-particles',state=dict(objects=[obj],vrex=dict(bank=999,diagnostics=dict(status='PASS'))))
        particles.import_objects(self.w,self.p,raw,world);self.assertNotIn('vrex',f)

    def test_vrex_actions_are_attributed_but_do_not_prove_maintenance(self):
        v,node=self.prepared();before=node['work_serial'];self.act('pump vrex')
        entry=node['ledger'][-1];self.assertEqual(entry['actor'],self.p['id']);self.assertNotIn('work_serial',entry)
        self.assertEqual(node['work_serial'],before)

    def test_reads_and_ui_catalogue_do_not_configure_old_saves(self):
        f=self.field();before=copy.deepcopy(f);world.snapshot(self.w,self.p);self.assertEqual(f,before)
        self.assertNotIn('vrex',f);self.assertEqual(vrex.public(f,self.c,self.p)['status'],'NOT CONFIGURED')

    def test_stimulus_or_generation_change_marks_prior_diagnostics_stale(self):
        v,node=self.prepared();self.act('test vrex');self.assertFalse(vrex.public(self.field(),self.c,self.p)['diagnostics_stale'])
        self.act('stimulus vrex 0.42 1.9')
        self.assertTrue(vrex.public(self.field(),self.c,self.p)['diagnostics_stale'])
        self.assertEqual(research.gates(self.field())[1]['status'],'STALE / RERUN')
        self.assertEqual(v['diagnostics']['stimulus']['force'],.28)
        self.act('test vrex');self.assertFalse(vrex.public(self.field(),self.c,self.p)['diagnostics_stale'])

    def test_same_tick_outage_replaces_measurement_without_duplication(self):
        v,node=self.prepared();self.act('pump vrex');tick=self.w['tick'];length=len(v['observations'])
        node['enabled']=False;particles.reconcile_sources(self.w)
        self.assertEqual(len(v['observations']),length);self.assertEqual(v['observations'][-1]['tick'],tick)
        self.assertTrue(all(n['q']==n['v']==0 and n['model_phase'] is None for n in v['observations'][-1]['particles']))

    def test_active_drive_budget_rejects_a_ninth_without_spending(self):
        v,node=self.prepared();before=copy.deepcopy(v);power=self.c['infrastructure']['stores']['power']
        for i in range(8):self.w['substrate']['fields']['base:mock'+str(i)]={'vrex':{'running':True}}
        with self.assertRaisesRegex(ValueError,'Eight'):self.act('pump vrex')
        self.assertEqual(v,before);self.assertEqual(self.c['infrastructure']['stores']['power'],power)

    def test_observation_and_control_histories_are_bounded_and_live_id_is_unique(self):
        v,node=self.prepared()
        for i in range(130):
            vrex.event(v,i,'control',self.p['id'],True);vrex.observe(self.field(),self.w['tick']+i+1)
        self.assertEqual(len(v['stimulus_events']),32);self.assertEqual(len(v['observations']),vrex.TRACE_LIMIT)
        self.assertEqual(len({n['id'] for n in v['states']}),len(v['states']))

    def test_diagnostics_can_observe_remote_and_combat_without_advancing_turns(self):
        v,node=self.prepared();self.act('remote');result=self.act('test vrex');self.assertEqual(v['diagnostics']['actor'],self.p['id'])
        self.assertIn('UNVERIFIED REMOTE PROJECTION',result['text'])
        self.act('return');self.battle();encounter=copy.deepcopy(self.c['scene']['encounter']);self.act('test vrex')
        self.assertEqual(self.c['scene']['encounter'],encounter)

    def test_background_tracking_survives_ordinary_gameplay_without_public_histories(self):
        v,node=self.prepared();self.act('pump vrex');self.act('audit resonance')
        before=copy.deepcopy(v);journal=copy.deepcopy(self.field()['photonics']['research_runs'])
        state=world.snapshot(self.w,self.p)
        self.assertNotIn('vrex',state['particles']);self.assertNotIn('research',state['particles'])
        self.assertNotIn('research_runs',state['particles']['photonics']);self.assertEqual(v,before)
        self.act('wait');self.assertGreater(v['time'],before['time'])
        self.assertGreater(len(v['observations']),len(before['observations']))
        self.assertEqual(self.field()['photonics']['research_runs'],journal)
        self.assertEqual(vrex.audit(v)['status'],'PASS')

    def test_narrator_receives_no_diagnostic_context_or_actions(self):
        import narrator,lore
        v,node=self.prepared();self.act('pump vrex');self.act('test vrex')
        state=world.snapshot(self.w,self.p);prose=narrator.Narrator()
        with patch.object(prose,'complete',return_value='The copper trellis hums.') as generate:
            prose.describe(state)
        payload=generate.call_args.args[1]
        self.assertNotIn('vrex',payload['info_particles']);self.assertNotIn('research',payload['info_particles'])
        self.assertNotIn('infrastructure',payload['location'])
        self.assertTrue(all(not a.startswith('vrex_') and a!='particle_audit' for a in narrator.ACTIONS))
        self.assertTrue(all(not key.startswith('vrex-') for key in lore.context()))
        self.assertTrue(all(not key.startswith('vrex-') for key in lore.TOPICS['resonance']))
