"""Independent mechanics solutions and game integration, rather than UI telemetry."""
import copy
import json
import math
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import hexgrid as hx
import lifecycle
import machines
import particles
import physics
import server
import vrex
import world


class SolverTests(unittest.TestCase):
    def test_inertial_translation_and_rotation_are_exact(self):
        s=physics.new();b=physics.body(s,'free',velocity=[1.,2.],omega=.3,damping=0.)
        physics.advance(s,.5)
        self.assertAlmostEqual(b['position'][0],.5);self.assertAlmostEqual(b['position'][1],1.)
        self.assertAlmostEqual(b['angle'],.15);self.assertEqual(physics.audit(s)['status'],'PASS')

    def test_gravity_velocity_and_position_converge_to_the_analytic_solution(self):
        errors=[]
        for dt in [1/32,1/64,1/128]:
            s=physics.new(gravity=[0.,-1.]);b=physics.body(s,'fall',damping=0.)
            physics.advance(s,.5,dt)
            self.assertAlmostEqual(b['velocity'][1],-.5)
            errors.append(abs(b['position'][1]+.125));self.assertEqual(physics.audit(s)['status'],'PASS')
        self.assertGreater(errors[0]/errors[-1],3.9)

    def test_applied_torque_uses_shape_inertia_and_accounts_for_external_work(self):
        s=physics.new();b=physics.body(s,'box',half=[.2,.3],mass=2.,damping=0.)
        b['torque']=.1;physics.advance(s,.25)
        self.assertAlmostEqual(b['omega'],.1*b['inverse_inertia']*.25)
        self.assertEqual(physics.audit(s)['status'],'PASS')

    def test_spring_period_and_energy_match_independent_harmonic_solution(self):
        s=physics.new();b=physics.body(s,'spring',position=[.2,0.],damping=0.)
        physics.spring(s,'spring',stiffness=1.,damping=0.)
        remaining=math.tau
        while remaining>1e-10:
            h=min(.5,remaining);physics.advance(s,h);remaining-=h
        self.assertAlmostEqual(b['position'][0],.2,places=5)
        self.assertLess(abs(b['velocity'][0]),1e-4);self.assertEqual(physics.audit(s)['status'],'PASS')

    def test_spring_endpoint_forces_conserve_total_momentum(self):
        s=physics.new();a=physics.body(s,'a',position=[-1.,0.],mass=2.,damping=0.)
        b=physics.body(s,'b',position=[1.,0.],mass=3.,damping=0.)
        physics.spring(s,'a','b',rest=1.,stiffness=2.,damping=.3)
        physics.advance(s,.25)
        self.assertAlmostEqual(2*a['velocity'][0]+3*b['velocity'][0],0.,places=12)

    def test_equal_mass_elastic_collision_exchanges_velocities_without_energy_gain(self):
        s=physics.new();a=physics.body(s,'a',position=[-.1,0.],velocity=[1.,0.],radius=.1,damping=0.,restitution=1.,friction=0.)
        b=physics.body(s,'b',position=[.1,0.],radius=.1,damping=0.,restitution=1.,friction=0.)
        physics.resolve(s,physics.contact(a,b))
        self.assertAlmostEqual(a['velocity'][0],0.);self.assertAlmostEqual(b['velocity'][0],1.)
        self.assertEqual(physics.audit(s)['status'],'PASS');self.assertAlmostEqual(s['ledger']['heat'],0.)

    def test_friction_and_off_center_impulse_generate_rotation_and_dissipate_energy(self):
        s=physics.new();a=physics.body(s,'a',position=[0.,.3],velocity=[2.,1.],radius=.2,damping=0.,friction=.8)
        b=physics.body(s,'b',position=[.6,0.],half=[.5,.5],damping=0.,friction=.8)
        before=physics.energy(s);physics.resolve(s,physics.contact(a,b))
        self.assertNotEqual(b['omega'],0.);self.assertLess(physics.energy(s),before)
        self.assertGreater(s['ledger']['heat'],0.);self.assertEqual(physics.audit(s)['status'],'PASS')

    def test_circle_inside_box_and_rotated_boxes_have_consistent_normals(self):
        s=physics.new();a=physics.body(s,'circle',position=[.4,0.],radius=.1)
        b=physics.body(s,'box',mass=0.,half=[.5,.5],angle=.1)
        c=physics.contact(a,b);reverse=physics.contact(b,a)
        self.assertAlmostEqual(c['normal'][0],-reverse['normal'][0]);self.assertGreater(c['depth'],0)
        d=physics.body(s,'other',position=[.8,0.],half=[.5,.5],angle=-.2)
        self.assertIsNotNone(physics.contact(b,d));d['position']=[3.,0.]
        self.assertIsNone(physics.contact(b,d))

    def test_sweep_candidates_match_brute_force_overlap_set(self):
        s=physics.new();g=random.Random(2)
        for i in range(25):physics.body(s,str(i),position=[g.uniform(-2,2),g.uniform(-2,2)])
        hits={(a['id'],b['id']) for a,b in physics.broadphase(s) if physics.contact(a,b)}
        brute={tuple(sorted([a['id'],b['id']])) for i,a in enumerate(s['bodies']) for b in s['bodies'][i+1:] if physics.contact(a,b)}
        self.assertEqual({tuple(sorted(pair)) for pair in hits},brute)

    def test_adaptive_substeps_prevent_thin_wall_tunneling_within_budget(self):
        s=physics.new();b=physics.body(s,'moving',velocity=[12.,0.],radius=.04,damping=0.,restitution=0.)
        physics.body(s,'wall',position=[.2,0.],mass=0.,half=[.01,1.],restitution=0.)
        physics.advance(s,.03)
        self.assertLessEqual(b['position'][0],.151);self.assertLessEqual(b['velocity'][0],1e-8)
        self.assertGreater(s['stats']['contacts'],0)

    def test_extreme_motion_is_rejected_before_mutation(self):
        s=physics.new();physics.body(s,'fast',velocity=[100.,0.],radius=.01)
        before=copy.deepcopy(s)
        with self.assertRaises(ValueError):physics.advance(s,.5)
        self.assertEqual(s,before)

    def test_work_receipt_and_axis_dissipation_close_the_ledger(self):
        s=physics.new();b=physics.body(s,'receiver',axis=[1.,0.],useful=.5)
        physics.supply(s,'receiver',.3);self.assertAlmostEqual(physics.energy(s),.3)
        physics.advance(s,.5);self.assertEqual(physics.audit(s)['status'],'PASS')
        self.assertGreater(s['ledger']['work'],0.);self.assertEqual(b['position'][1],0.)

    def test_quiet_spring_island_sleeps_and_input_wakes_connected_members(self):
        s=physics.new();a=physics.body(s,'a');b=physics.body(s,'b',position=[1.,0.])
        physics.spring(s,'a','b',rest=1.)
        physics.advance(s,.5);physics.advance(s,.5)
        self.assertFalse(a['awake']);self.assertFalse(b['awake'])
        physics.supply(s,'a',.1);physics.advance(s,.02)
        self.assertTrue(a['awake']);self.assertTrue(b['awake'])

    def test_cross_correlation_finds_known_delay_and_refuses_constant_signals(self):
        g=random.Random(12);signal=[g.uniform(-1,1) for _ in range(80)]
        rows=[dict(time=i*.03125,x=x,y=signal[i-3] if i>=3 else 0.) for i,x in enumerate(signal)]
        result=physics.correlation(rows,'x','y',max_lag=6)
        self.assertEqual(result['peak']['lag_samples'],3);self.assertAlmostEqual(result['peak']['coefficient'],1.)
        self.assertAlmostEqual(result['peak']['lag_time'],3/32)
        self.assertEqual(physics.correlation([dict(time=i,x=0.,y=1.) for i in range(40)],'x','y')['status'],'INSUFFICIENT VARIATION')

    def test_registry_rejects_nonfinite_values_and_enforces_identity_and_budget(self):
        s=physics.new()
        for value in [float('nan'),float('inf'),True,-1.]:
            with self.assertRaises(ValueError):physics.body(s,'invalid',mass=value)
        for i in range(physics.MAX_BODIES):physics.body(s,str(i))
        with self.assertRaises(ValueError):physics.body(s,'extra')

    def test_nonuniform_sampling_does_not_invent_a_lag_time(self):
        samples=[dict(time=i if i<20 else i+4,x=math.sin(i),y=math.cos(i)) for i in range(40)]
        self.assertEqual(physics.correlation(samples,'x','y')['status'],'NONUNIFORM SAMPLING')

    def test_angled_elastic_collision_keeps_rail_and_reverses_velocity(self):
        s=physics.new();a=physics.body(s,'rail',axis=[1.,0.],velocity=[1.,0.],damping=0.,restitution=1.,friction=0.)
        b=physics.body(s,'stop',position=[.15,.1],mass=0.,restitution=1.,friction=0.)
        physics.resolve(s,physics.contact(a,b))
        self.assertAlmostEqual(a['velocity'][0],-1.);self.assertEqual(a['velocity'][1],0.)
        self.assertEqual(a['position'][1],0.);self.assertEqual(a['omega'],0.)
        self.assertEqual(physics.audit(s)['status'],'PASS')

    def test_perpendicular_rail_input_is_rejected_without_receipt_or_motion(self):
        s=physics.new();physics.body(s,'rail',axis=[1.,0.]);before=copy.deepcopy(s)
        with self.assertRaises(ValueError):physics.supply(s,'rail',.1,[0.,1.])
        self.assertEqual(s,before)
        physics.supply(s,'rail',.1,[1.,1.]);self.assertAlmostEqual(physics.energy(s),.1)
        self.assertEqual(physics.find(s,'rail')['velocity'][1],0.)

    def test_rail_constraint_reaction_does_no_work_or_heat(self):
        s=physics.new(gravity=[0.,-1.]);a=physics.body(s,'rail',axis=[1.,0.],damping=0.)
        a['force']=[0.,2.];physics.advance(s,.5)
        self.assertEqual(a['position'],[0.,0.]);self.assertEqual(a['velocity'],[0.,0.])
        self.assertEqual(s['ledger']['external_work'],0.);self.assertEqual(s['ledger']['heat'],0.)
        self.assertEqual(physics.audit(s)['status'],'PASS')

    def test_perpendicular_contact_has_no_allowed_rail_correction(self):
        s=physics.new();a=physics.body(s,'rail',axis=[1.,0.]);b=physics.body(s,'wall',mass=0.,position=[0.,.15])
        physics.resolve(s,physics.contact(a,b));self.assertEqual(a['position'],[0.,0.])

    def test_rail_dashpot_uses_projected_effective_mass(self):
        s=physics.new();a=physics.body(s,'rail',position=[1.,1.],velocity=[1.,0.],axis=[1.,0.],damping=0.)
        physics.spring(s,'rail',stiffness=0.,damping=2.)
        physics._damp(s,.25)
        self.assertAlmostEqual(a['velocity'][0],math.exp(-.25))
        self.assertEqual(a['velocity'][1],0.);self.assertEqual(physics.audit(s)['status'],'PASS')

    def test_zero_rail_and_underflow_mass_are_rejected_before_registration(self):
        s=physics.new()
        for args in [dict(axis=[0.,0.]),dict(mass=1e-300)]:
            with self.assertRaises(ValueError):physics.body(s,'invalid',**args)
        self.assertEqual(s['bodies'],[]);self.assertEqual(s['ledger']['initial'],0.)

    def test_energy_balance_alone_cannot_pass_invalid_ledger_or_rail_geometry(self):
        s=physics.new();physics.body(s,'rail',axis=[1.,0.])
        cases=[]
        bad=copy.deepcopy(s);bad['ledger'].update(input=-1.,heat=-1.);cases.append(bad)
        bad=copy.deepcopy(s);bad['bodies'][0]['position'][1]=.01;cases.append(bad)
        bad=copy.deepcopy(s);bad['ledger']['input']=True;cases.append(bad)
        bad=copy.deepcopy(s);del bad['ledger']['input'];cases.append(bad)
        for bad in cases:
            before=copy.deepcopy(bad);self.assertEqual(physics.audit(bad)['status'],'FAIL');self.assertEqual(bad,before)

    def test_shutdown_preserves_static_geometry_and_registered_assembly_angle(self):
        s=physics.new();a=physics.body(s,'moving',angle=.4,omega=.3,damping=0.)
        b=physics.body(s,'wall',position=[2.,0.],half=[.1,.5],mass=0.,angle=1.2)
        wall=copy.deepcopy(b);physics.advance(s,.25);physics.dissipate(s)
        self.assertEqual(b,wall);self.assertEqual(a['angle'],.4);self.assertEqual(a['omega'],0.)
        self.assertEqual(physics.audit(s)['status'],'PASS')

    def test_shutdown_refuses_external_loading_before_mutation(self):
        for args in [dict(gravity=[0.,-1.]),dict(gravity=[0.,0.])]:
            s=physics.new(**args);a=physics.body(s,'body')
            if not args['gravity'][1]:a['force']=[1.,0.]
            before=copy.deepcopy(s)
            with self.assertRaises(ValueError):physics.dissipate(s)
            self.assertEqual(s,before)


class MachineTests(RoseTest):
    def mount(self,kind='pump'):
        node=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='workshop')
        self.approach(node);node.update(enabled=True,condition=90,status='working')
        self.c['infrastructure']['stores']['power']=40;self.p['inventory']['scrap']=10
        self.act('machine_fit',node['id']+'|'+kind)
        return particles.field(self.w,self.p,world),node

    def accumulate_owned_work(self,f,node):
        self.act('machine_operate',node['id'])
        for _ in range(40):vrex.advance(f['vrex'],observer=lambda _,h:machines.transfer(f,h))

    def test_fitting_is_paid_physical_and_records_skill_faction_context(self):
        f,node=self.mount();self.assertEqual(self.p['inventory']['scrap'],8)
        self.assertEqual(self.p['last_check']['skill'],'metallurgy');self.assertEqual(self.p['last_check']['faction'],node['faction'])
        self.assertEqual(f['vrex']['ledger']['input'],0.);self.assertEqual(physics.energy(f['mechanism']['solver']),0.)
        menu=world.snapshot(self.w,self.p)['scene']['interaction_options']['structure:'+node['id']]['actions']
        self.assertTrue(any(n['intent']['action']=='machine_operate' for n in menu))
        self.assertFalse(any(n['intent']['action'].startswith('vrex_') for n in menu))

    def test_paid_operation_transfers_load_once_and_runs_during_ordinary_wait(self):
        f,node=self.mount();power=self.c['infrastructure']['stores']['power'];self.act('machine_operate',node['id'])
        self.assertEqual(f['vrex']['ledger']['input'],1.);self.assertLessEqual(self.c['infrastructure']['stores']['power'],power-1)
        r=f['mechanism'];self.assertGreater(r['solver']['ledger']['input'],0.);self.assertGreater(physics.energy(r['solver']),0.)
        before=r['solver']['time'];self.act('wait');self.assertGreater(r['solver']['time'],before)
        self.assertEqual(machines.combined_audit(f)['status'],'PASS')
        saved=copy.deepcopy(f);particles.advance(self.w);machines.finish(self.w,world);self.assertEqual(f,saved)
        self.assertNotIn('mechanism',world.snapshot(self.w,self.p)['particles'])

    def test_adapter_leaves_upstream_coordinates_and_work_channels_unchanged(self):
        f,node=self.mount();v=vrex.bench(f['vrex']);vrex.pump(v,True,node);v2=copy.deepcopy(v)
        downstream=copy.deepcopy(f);downstream['vrex']=v2;downstream['mechanism']['engaged']=True
        vrex.advance(v);vrex.advance(v2,observer=lambda _,h:machines.transfer(downstream,h))
        self.assertEqual(v,v2);self.assertAlmostEqual(downstream['mechanism']['solver']['ledger']['input'],v['ledger']['load'])
        self.assertEqual(machines.combined_audit(downstream)['status'],'PASS')

    def test_no_input_and_unloaded_nulls_do_no_jobs_or_create_motion(self):
        f,node=self.mount();r=f['mechanism']
        for _ in range(6):self.act('wait')
        self.assertEqual(r['jobs'],0);self.assertEqual(r['solver']['ledger']['input'],0.)
        f['vrex']['preset']='static';self.act('machine_operate',node['id'])
        self.assertEqual(r['solver']['ledger']['input'],0.);self.assertEqual(physics.energy(r['solver']),0.)

    def test_pump_transfers_actual_source_water_without_mass_creation(self):
        f,node=self.mount();r=f['mechanism'];self.accumulate_owned_work(f,node)
        self.c['water']=10;data=self.c['infrastructure'];data['stores']['water']=1
        for n in data['nodes']:
            if n['kind']=='water':n.update(enabled=True,condition=90,status='working')
        before=self.c['water']+data['stores']['water'];r['effect_tick']=None
        machines.finish(self.w,world)
        self.assertEqual(r['water_transferred'],1);self.assertEqual(self.c['water']+data['stores']['water'],before)
        again=copy.deepcopy(r);machines.finish(self.w,world);self.assertEqual(r,again)

    def test_pump_waits_when_source_water_is_empty(self):
        f,node=self.mount();r=f['mechanism'];self.accumulate_owned_work(f,node);self.c['water']=0;r['effect_tick']=None
        machines.finish(self.w,world);self.assertEqual(r['water_transferred'],0)
        self.assertIn('waiting',r['status'])

    def test_unowned_downstream_energy_cannot_create_world_output(self):
        f,node=self.mount();r=f['mechanism'];r['engaged']=True
        physics.supply(r['solver'],'carriage',.02);physics.advance(r['solver'],.5)
        before=self.c['water']+self.c['infrastructure']['stores']['water'];r['effect_tick']=None
        machines.finish(self.w,world)
        self.assertFalse(r['engaged']);self.assertEqual(r['jobs'],0)
        self.assertEqual(self.c['water']+self.c['infrastructure']['stores']['water'],before)
        self.assertEqual(machines.combined_audit(f)['status'],'FAIL')

    def test_same_cycle_fatigue_failure_stops_before_any_device_job(self):
        f,node=self.mount();r=f['mechanism'];self.accumulate_owned_work(f,node)
        node['condition']=30;r['fatigue']=.04;r['progress']=machines.APPLICATIONS['pump']['job_work']
        r['effect_tick']=None;before=r['jobs'];machines.finish(self.w,world)
        self.assertEqual(node['condition'],29);self.assertEqual(r['jobs'],before)
        self.assertFalse(r['engaged']);self.assertFalse(f['vrex']['running'])
        self.assertEqual(machines.combined_audit(f)['status'],'PASS')

    def test_physical_access_and_pause_guards_preserve_power_and_motion(self):
        f,node=self.mount();power=self.c['infrastructure']['stores']['power'];before=copy.deepcopy(f)
        for field in ['remote','paused']:
            subject=self.p if field=='remote' else self.w;subject[field]=True
            with self.assertRaises(ValueError):self.act('machine_operate',node['id'])
            subject[field]=False
        self.assertEqual(self.c['infrastructure']['stores']['power'],power);self.assertEqual(f,before)

    def test_press_contributes_only_to_owned_reserved_nearby_projects(self):
        f,node=self.mount('press');r=f['mechanism']
        positions=[t['pos'] for t in self.c['scene']['tiles'].values() if hx.distance(t['pos'],node['pos'])<=3
                   and not lifecycle.site_reason(self.w,self.c,self.p,t['pos'],world)]
        self.assertTrue(positions)
        self.p['inventory'].update(scrap=20,seed=10,food=20,water=20)
        self.act('construction_plan','shelter|'+hx.key(positions[0]))
        project=lifecycle.ensure(self.w,self.c)['projects'][-1]
        self.accumulate_owned_work(f,node)
        r['effect_tick']=None;before=project['work_done'];machines.finish(self.w,world)
        self.assertEqual(project['work_done'],before+1);self.assertEqual(r['construction_steps'],1)
        self.assertTrue(any(id.startswith('machine:') for id in project['contributors']))

    def test_disconnect_dissipates_motion_and_repairs_cannot_restart_paid_drive(self):
        f,node=self.mount();self.act('machine_operate',node['id']);r=f['mechanism']
        node['enabled']=False;particles.reconcile_sources(self.w)
        self.assertFalse(r['engaged']);self.assertEqual(physics.energy(r['solver']),0.)
        self.assertFalse(f['vrex']['running']);self.assertEqual(machines.combined_audit(f)['status'],'PASS')
        node.update(enabled=True,condition=90,status='working');self.act('wait')
        self.assertFalse(r['engaged']);self.assertEqual(f['vrex']['ledger']['input'],1.)

    def test_failed_fit_and_drive_spend_declared_cost_without_new_hardware_or_energy(self):
        f,node=self.mount();old=copy.deepcopy(f['mechanism']);scrap=self.p['inventory']['scrap']
        with patch('world.secrets.randbelow',return_value=0):
            self.act('machine_fit',node['id']+'|press');self.act('machine_operate',node['id'])
        self.assertEqual(self.p['inventory']['scrap'],scrap-2);self.assertEqual(f['mechanism']['application'],old['application'])
        self.assertEqual(f['vrex']['ledger']['input'],1.);self.assertEqual(f['vrex']['ledger']['heat'],1.)
        self.assertEqual(physics.energy(f['mechanism']['solver']),0.)

    def test_early_refit_rejected_without_cost_and_stop_retains_closed_accounting(self):
        f,node=self.mount();self.act('machine_operate',node['id']);before=copy.deepcopy(f);scrap=self.p['inventory']['scrap']
        with self.assertRaises(ValueError):self.act('machine_fit',node['id']+'|damper')
        self.assertEqual(f,before);self.assertEqual(self.p['inventory']['scrap'],scrap)
        # Existing 0.13.0 workshop saves predate the authored-angle field.
        for b in f['mechanism']['solver']['bodies']:b.pop('origin_angle',None)
        self.act('machine_stop',node['id']);self.assertEqual(physics.energy(f['mechanism']['solver']),0.)
        self.assertEqual(machines.combined_audit(f)['status'],'PASS')
        self.act('machine_fit',node['id']+'|damper');self.assertEqual(len(f['mechanism']['history']),1)

    def test_save_replay_and_read_only_development_export_retain_records(self):
        f,node=self.mount();self.act('machine_operate',node['id'])
        saved=json.loads(json.dumps(self.w));original=copy.deepcopy(self.w)
        world.tick(saved);world.tick(original);self.assertEqual(saved,original)
        with tempfile.TemporaryDirectory() as d:
            server.init_db(str(Path(d)/'physics.sqlite'));server.save(self.w)
            before=copy.deepcopy(server.fetch(self.w['code']))
            result=server.request(dict(op='physics_export',code=self.w['code'],token=self.p['token']))
            self.assertEqual(server.fetch(self.w['code']),before);self.assertEqual(result['energy']['status'],'PASS')
            self.assertNotIn(self.p['token'],json.dumps(result));server.DB.close()

    def test_physics_controls_are_isolated_metered_and_do_not_mutate_source(self):
        f,node=self.mount();before=copy.deepcopy(self.w)
        with tempfile.TemporaryDirectory() as d:
            server.init_db(str(Path(d)/'controls.sqlite'));server.save(self.w)
            stored=copy.deepcopy(server.fetch(self.w['code']))
            result=server.request(dict(op='physics_diagnose',code=self.w['code'],token=self.p['token']))
            self.assertEqual(server.fetch(self.w['code']),stored);server.DB.close()
        self.assertEqual(self.w,before);self.assertEqual(result['status'],'PASS')
        self.assertEqual(len(result['cases']),9)
        for row in result['cases']:
            self.assertEqual(row['energy']['status'],'PASS')
            self.assertEqual(row['input'],0. if row['control']=='no-input' else 4.)
            if row['control']!='loaded':self.assertEqual(row['work'],0.)

    def test_measurements_are_hidden_but_observable_hardware_remains_in_look(self):
        f,node=self.mount();self.act('machine_operate',node['id']);s=world.snapshot(self.w,self.p)
        self.assertNotIn('mechanism',s['particles']);self.assertNotIn('vrex',s['particles'])
        self.assertNotIn('cross_correlation',json.dumps(s));self.assertNotIn('normalized_residual',json.dumps(s))
        out=self.act('field_look','structure:'+node['id']);self.assertIn('transfer pump',out['text'])
        self.assertEqual(set(node['machine']),{'kind','label','status','motion'})
        self.assertEqual(set(node['machine']['motion']),{'schema','serial','duration_ms','active','frames'})
        for frame in node['machine']['motion']['frames']:
            self.assertEqual(set(frame),{'at','offset','angle','contact','sleeping'})

    def test_fit_and_operation_never_count_as_maintenance_repair_proof(self):
        f,node=self.mount();node['condition']=60;self.act('structure_contract',node['id'])
        serial=node['work_serial'];self.act('machine_operate',node['id'])
        self.assertEqual(node['work_serial'],serial)
        self.assertFalse(any(e.get('actor')==self.p['id'] and e.get('work_serial',0)>serial for e in node['ledger']))

    def test_parser_preserves_negation_and_comprehension_boundaries(self):
        self.assertEqual(world.parse('fit pump')[0],dict(action='machine_fit',target='|pump'))
        self.assertIsNone(world.parse('do not fit pump')[0]);self.assertIsNone(world.parse('fit pump and operate machine')[0])
        with self.assertRaises(ValueError):world.parse(None)
