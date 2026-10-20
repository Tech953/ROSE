"""The new proposal informs provenance without promoting unrun physics gates."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import lore
import particles
import photonics
import research
import server
import world


class ResearchProtocolTests(RoseTest):
    def node(self):
        return next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='workshop')

    def field(self):
        return particles.field(self.w,self.p,world)

    def test_proposal_source_is_exact_and_all_pages_are_registered(self):
        source=research.PROTOCOL['source'];path=Path(world.__file__).parent/source['path']
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),source['sha256'])
        self.assertEqual(source['pages'],12);self.assertEqual(path.stat().st_size,674752)
        self.assertEqual({page for section in research.PROTOCOL['page_map'] for page in section['pages']},set(range(1,13)))
        self.assertEqual(research.PROTOCOL['legacy_record']['rose_status'],'NOT REPRODUCED')
        self.assertTrue(all(id in lore.BY_ID for id in ['vrex-evidence-gates','vrex-dialogue-topology','vrex-tether-load','vrex-provenance']))

    def test_cold_audit_retains_provenance_without_time_ap_energy_or_inventory_cost(self):
        f=self.field();node=self.node();before=copy.deepcopy(f);tick=self.w['tick'];pack=self.p['inventory'].copy();energy=self.p['energy']
        self.act('particle_audit',node['id']);record=f['photonics']['research_runs'][-1]
        after=copy.deepcopy(f);after['photonics'].pop('research_runs');after['photonics'].pop('research_serial')
        self.assertEqual(after,before);self.assertEqual(self.w['tick'],tick);self.assertEqual(self.p['inventory'],pack);self.assertEqual(self.p['energy'],energy)
        self.assertEqual(record['energy_audit']['status'],'EMPTY');self.assertEqual(record['seed'],self.w['seed']);self.assertEqual(record['field'],f['address'])
        self.assertEqual(record['engine_version'],world.VERSION);self.assertEqual(record['actor'],self.p['id']);self.assertEqual(record['workshop'],node['id'])
        self.assertEqual(self.p['last_check']['skill'],'light');self.assertEqual(self.p['last_check']['faction'],node['faction'])
        self.assertEqual({g['status'] for g in record['gates']},{'NOT RUN'})

    def test_balanced_paid_optical_output_never_passes_a_proposal_gate(self):
        node=self.node();self.approach(node);self.c['infrastructure']['stores']['power']=5
        self.act('particle_excite',node['id']);self.act('audit resonance');record=self.field()['photonics']['research_runs'][-1]
        self.assertEqual(record['energy_audit']['status'],'PASS');self.assertLess(record['energy_audit']['normalized_residual'],research.TOLERANCE)
        self.assertGreater(record['energy_audit']['values']['emitted_energy'],0)
        self.assertEqual(record['convergence'],'NOT RUN');self.assertEqual(record['legacy_detector'],'NOT REPRODUCED')
        self.assertEqual([g['status'] for g in record['gates']],['NOT RUN']*5)

    def test_failed_skill_interpretation_does_not_change_measurements_or_evidence(self):
        f=self.field();before=research.energy_audit(f)
        with patch('world.secrets.randbelow',return_value=0):result=self.act('particle_audit',self.node()['id'])
        record=f['photonics']['research_runs'][-1];self.assertFalse(record['interpretation'])
        self.assertEqual(record['energy_audit'],before);self.assertIn('interpretation remains uncertain',result['text'])
        self.assertTrue(all(g['status']=='NOT RUN' for g in record['gates']))

    def test_nonclosing_and_nonfinite_ledgers_fail_without_repairing_them(self):
        f=self.field()
        for value in [1,float('nan'),float('inf'),True,-1,5]:
            probe=copy.deepcopy(f);probe['photonics']['energy']=value;before=copy.deepcopy(probe)
            result=research.energy_audit(probe);self.assertEqual(result['status'],'FAIL')
            if value==value:self.assertEqual(probe,before)
            json.dumps(result,allow_nan=False)

    def test_reading_and_export_are_read_only_and_journal_is_bounded(self):
        f=self.field();node=self.node();tick=self.w['tick']
        with self.assertRaisesRegex(ValueError,'Record a workshop'):research.export(f)
        for _ in range(research.HISTORY_LIMIT+4):self.act('particle_audit',node['id'])
        self.assertEqual(len(f['photonics']['research_runs']),research.HISTORY_LIMIT);self.assertEqual(f['photonics']['research_serial'],research.HISTORY_LIMIT+4)
        before=copy.deepcopy(f);research.public(f);raw=research.export(f);raw['record']['gates'][0]['status']='PASS'
        self.assertEqual(f,before);self.assertEqual(self.w['tick'],tick)
        with tempfile.TemporaryDirectory() as tmp:
            server.init_db(str(Path(tmp)/'audit.db'));server.save(self.w);saved=server.fetch(self.w['code'])
            exported=server.request(dict(op='research_export',code=self.w['code'],token=self.p['token']))
            self.assertEqual(exported['format'],'Rose-research-audit');self.assertEqual(server.fetch(self.w['code']),saved)
            self.assertNotIn(self.p['token'],json.dumps(exported))

    def test_audit_preserves_travel_combat_turn_and_labels_remote_observation(self):
        self.act('goto','-8,3');route=copy.deepcopy(self.p['overworld']);self.act('audit resonance');self.assertEqual(self.p['overworld'],route)
        self.act('stop_travel','');self.act('remote','');result=self.act('audit resonance');self.assertIn('UNVERIFIED REMOTE PROJECTION',result['text'])
        self.act('return','');self.battle();turn=copy.deepcopy(self.c['scene']['encounter']);self.act('audit resonance');self.assertEqual(self.c['scene']['encounter'],turn)

    def test_void_paused_and_foreign_targets_cannot_record_baseline_audits(self):
        node=self.node();self.w['paused']=True
        with self.assertRaisesRegex(ValueError,'paused'):self.act('audit resonance')
        self.w['paused']=False
        for identity in ['unknown',next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='water')['id']]:
            with self.assertRaises(ValueError):self.act('particle_audit',identity)
        self.p['credentials']=['black.dot'];self.p['percept'].update(armor=30,immunix=2);self.act('enter void_null')
        with self.assertRaisesRegex(ValueError,'baseline workshop'):self.act('particle_audit',node['id'])

    def test_particle_import_cannot_inject_audits_or_gate_passes(self):
        f=self.field();self.w['paused']=True;n=copy.deepcopy(f['objects'][0]);n['id']='forged-protocol'
        forged=dict(format='Rose-info-particles',state=dict(objects=[n],photonics=dict(research_runs=[dict(proposal_gates=[dict(id='A',status='PASS')])])),research=dict(gates=[dict(id='C',status='PASS')]))
        particles.import_objects(self.w,self.p,forged,world)
        self.assertEqual(research.public(f)['runs'],[]);self.assertTrue(all(g['status']=='NOT RUN' for g in research.public(f)['gates']))

    def test_old_reservoirs_load_without_a_journal_or_fabricated_results(self):
        f=self.field();old=copy.deepcopy(f)
        with tempfile.TemporaryDirectory() as tmp:
            server.init_db(str(Path(tmp)/'old.db'));server.save(self.w);loaded=server.fetch(self.w['code']);p=server.identify(loaded,self.p['token'])
            state=world.snapshot(loaded,p)
            self.assertNotIn('research',state['particles']);self.assertNotIn('vrex',state['particles']);self.assertEqual(research.public(old)['legacy_record']['rose_status'],'NOT REPRODUCED')
            self.assertEqual(loaded['substrate']['fields'][f['address']],old)
