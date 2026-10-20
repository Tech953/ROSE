import copy
import math
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import particles
import photonics
import server
import world


class OpticalTests(RoseTest):
    def field(self):
        return particles.field(self.w,self.p,world)

    def rig(self):
        node=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='workshop')
        node.update(enabled=True,connected=True,status='working',condition=90)
        return node

    def balanced(self,ph):
        self.assertAlmostEqual(ph['input_energy'],ph['energy']+ph['emitted_energy']+ph['heat_energy'],places=10)
        self.assertTrue(0<=ph['energy']<=photonics.CAPACITY)

    def test_cold_readings_do_not_create_energy_or_advance_state(self):
        f=self.field();before=copy.deepcopy(f)
        s=world.snapshot(self.w,self.p)
        self.assertEqual(f,before)
        self.assertEqual(s['particles']['photonics']['input_energy'],0)
        self.assertEqual(len(s['particles']['photonics']['spectrum']),31)
        self.assertTrue(all(0<=n['response']<=1 for n in s['particles']['photonics']['spectrum']))

    def test_successful_excitation_spends_public_power_and_records_losses(self):
        self.approach(self.rig());f=self.field();self.c['infrastructure']['stores']['power']=5
        self.act('excite particles');ph=f['photonics']
        self.assertEqual(self.c['infrastructure']['stores']['power'],4)
        self.assertEqual(ph['input_energy'],1)
        self.assertGreater(ph['emitted_energy'],0)
        self.assertGreaterEqual(ph['heat_energy'],.2)
        self.balanced(ph)

    def test_failed_drive_records_consumed_input_as_heat(self):
        self.approach(self.rig());f=self.field();self.c['infrastructure']['stores']['power']=3
        with patch('world.secrets.randbelow',return_value=0):self.act('excite particles')
        self.assertEqual(f['photonics']['input_energy'],1)
        self.assertEqual(f['photonics']['heat_energy'],1)
        self.assertEqual(f['photonics']['energy'],0)
        self.assertEqual(self.c['infrastructure']['stores']['power'],2)
        self.balanced(f['photonics'])

    def test_empty_power_store_refuses_drive_without_optical_input(self):
        self.approach(self.rig());f=self.field();self.c['infrastructure']['stores']['power']=0;before=copy.deepcopy(f)
        with self.assertRaisesRegex(ValueError,'power'):self.act('excite particles')
        self.assertEqual(f,before)

    def test_spectral_response_tracks_individual_frequencies(self):
        f=self.field()
        for n in f['objects']:n['frequency']=1.4
        ph=photonics.measure(f,self.c);cyan=ph['response'];ph['band']='amber'
        self.assertLess(photonics.measure(f,self.c)['response'],cyan)
        self.assertAlmostEqual(cyan,1)
        for n in f['objects']:n['frequency']=.75
        self.assertAlmostEqual(photonics.measure(f,self.c)['response'],1)

    def test_moisture_and_degradation_broaden_authored_lines(self):
        f=self.field();self.c['moisture']=0
        low=photonics.measure(f,self.c)['linewidth'];self.c['moisture']=80
        wet=photonics.measure(f,self.c)['linewidth']
        for n in f['objects']:n['degradation']=80
        damaged=photonics.measure(f,self.c)['linewidth']
        self.assertLess(low,wet);self.assertLess(wet,damaged)

    def test_tuning_requires_physical_workshop_approach_and_records_light_check(self):
        node=self.rig();f=self.field()
        with self.assertRaisesRegex(ValueError,'adjacent'):self.act('tune spectrum jade alternating')
        self.approach(node);self.act('tune spectrum jade alternating')
        self.assertEqual(f['photonics']['band'],'jade');self.assertEqual(f['photonics']['mode'],'alternating')
        self.assertEqual(self.p['last_check']['skill'],'light')
        self.assertEqual(self.p['last_check']['faction'],world.REGIONS[self.c['region']]['faction'])
        self.assertEqual(f['photonics']['input_energy'],0)

    def test_failed_tuning_retains_previous_setting(self):
        node=self.rig();self.approach(node);f=self.field()
        with patch('world.secrets.randbelow',return_value=0):self.act('tune spectrum jade boundary')
        self.assertEqual(f['photonics']['band'],'cyan');self.assertEqual(f['photonics']['mode'],'steady')

    def test_tuning_rejects_invalid_modes_and_disabled_workshop(self):
        node=self.rig();self.approach(node);f=self.field();before=copy.deepcopy(f)
        for value in ['cyan:quantum-proof','cyan:steady:admin','nonsense',None]:
            with self.subTest(value=value),self.assertRaises(ValueError):world.act(self.w,self.p,dict(action='particle_tune',target=value))
        self.assertEqual(f,before);node['enabled']=False
        with self.assertRaisesRegex(ValueError,'workshop'):self.act('particle_tune','cyan:steady')

    def test_controller_quench_transfers_energy_to_heat_without_refunding_power(self):
        node=self.rig();self.approach(node);f=self.field();photonics.pump(f,True,node)
        self.c['infrastructure']['stores']['power']=2;self.act('quench resonance')
        self.assertEqual(f['photonics']['energy'],0);self.assertEqual(f['photonics']['heat_energy'],1)
        self.assertEqual(self.c['infrastructure']['stores']['power'],2);self.balanced(f['photonics'])

    def test_offline_or_broken_source_quenches_before_emission(self):
        for change in [dict(enabled=False),dict(condition=29),dict(connected=False),dict(status='power deficit')]:
            node=self.rig();f=self.field();photonics.pump(f,True,node);node.update(change)
            self.w['tick']+=1;photonics.step(self.w,f,self.c)
            self.assertEqual(f['photonics']['energy'],0);self.assertEqual(f['photonics']['exposure'],0)
            self.assertFalse(photonics.public(copy.deepcopy(f),self.c)['source_online']);self.balanced(f['photonics'])

    def test_capacity_and_thermal_quench_bound_repeated_drives(self):
        f=self.field();node=self.rig()
        for _ in range(12):photonics.pump(f,True,node);self.balanced(f['photonics'])
        self.assertEqual(f['photonics']['energy'],4)
        self.w['tick']+=1;photonics.step(self.w,f,self.c)
        self.assertEqual(f['photonics']['energy'],0)
        self.assertEqual(f['photonics']['controller_resets'],1);self.balanced(f['photonics'])

    def test_alternating_and_boundary_responses_decay_and_never_generate_mass(self):
        for mode in photonics.MODES:
            f=copy.deepcopy(self.field());ph=f['photonics'];ph['mode']=mode
            photonics.pump(f,True);mass=f['metrics']['mass'];values=[]
            for _ in range(60):
                self.w['tick']+=1;photonics.step(self.w,f,self.c);values.append(ph['signal']);self.balanced(ph)
            self.assertLess(ph['energy'],.05);self.assertEqual(f['metrics']['mass'],mass)
            self.assertLessEqual(len(ph['trace']),48)
            self.assertTrue(all(math.isfinite(n) for n in values))
            if mode=='alternating':self.assertLess(min(values),0);self.assertGreater(max(values),0)

    def test_duplicate_tick_cannot_repeat_emission_or_heat_loss(self):
        f=self.field();photonics.pump(f,True);self.w['tick']+=1;photonics.step(self.w,f,self.c)
        before=copy.deepcopy(f);photonics.step(self.w,f,self.c);self.assertEqual(f,before)

    def test_ecology_requires_powered_source_and_suitable_habitat(self):
        f=self.field();node=self.rig();ph=f['photonics'];ph.update(source_node=node['id'],band='jade',exposure=.08)
        self.c['moisture']=60;self.c['lifecycle']['soil_health']=60
        self.assertEqual(photonics.coupling(f,self.c)['growth'],1)
        self.c['moisture']=10;self.assertEqual(photonics.coupling(f,self.c)['growth'],0)
        ph.update(band='violet',exposure=.14);self.assertEqual(photonics.coupling(f,self.c)['stress'],1)
        node['enabled']=False;self.assertEqual(photonics.coupling(f,self.c),dict(growth=0,stress=0))

    def test_void_cannot_tune_or_quench_baseline_rig(self):
        self.p['credentials']=['black.dot'];self.p['percept'].update(armor=30,immunix=2)
        baseline=copy.deepcopy(self.field());self.act('enter void_null')
        retained=copy.deepcopy(self.w['substrate']['fields'][baseline['address']])
        for action,target in [('particle_tune','cyan:steady'),('particle_quench','')]:
            with self.subTest(action=action),self.assertRaises(ValueError):self.act(action,target)
        self.assertEqual(self.w['substrate']['fields'][baseline['address']],retained)

    def test_restart_retains_energy_settings_trace_and_source(self):
        f=self.field();node=self.rig();photonics.pump(f,True,node);f['photonics']['mode']='boundary'
        self.w['tick']+=1;particles.advance(self.w)
        with tempfile.TemporaryDirectory() as tmp:
            server.init_db(str(Path(tmp)/'optical.db'));server.save(self.w);loaded=server.fetch(self.w['code'])
        self.assertEqual(loaded['substrate']['fields'][f['address']]['photonics'],f['photonics'])

    def test_v09_field_migrates_cold_and_import_cannot_inject_rig_energy(self):
        f=self.field();del f['photonics'];self.field();self.assertEqual(f['photonics']['input_energy'],0)
        n=copy.deepcopy(f['objects'][0]);n['id']='forged-energy';self.w['paused']=True
        raw=dict(format='Rose-info-particles',state=dict(objects=[n],photonics=dict(energy=1000000)),photonics=dict(energy=1000000))
        particles.import_objects(self.w,self.p,raw,world)
        self.assertEqual(f['photonics']['energy'],0);self.assertEqual(f['photonics']['input_energy'],0)
