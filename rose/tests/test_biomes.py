"""Source intake and runtime evidence/access boundaries."""
import copy
import hashlib
import json
import re
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import adventure
import biomes
import geography
import narrator
import world

ROOT = Path(__file__).resolve().parents[1]


class BiomeIntakeTests(RoseTest):
    def test_complete_members_retain_verified_bytes_and_recovery_status(self):
        records = biomes.RECORD['files']
        self.assertEqual(len(records), 17)
        self.assertEqual(sum(r['kind'] == 'lore_document' for r in records), 13)
        self.assertEqual(sum(r['kind'] == 'visual_prototype' for r in records), 4)
        for r in records:
            self.assertEqual(hashlib.sha256((ROOT / r['path']).read_bytes()).hexdigest(), r['sha256'])
        receipt = json.loads((ROOT / 'reference/lore-transport/recovery-record.json').read_text())
        self.assertEqual(receipt['status'], 'PARTIAL RECOVERY')
        self.assertTrue(receipt['unknown_later_files'])
        self.assertFalse((ROOT / 'reference/lore-transport/PROTOTYPE IMAGE v2/Designer (2).png').exists())

    def test_every_fact_resolves_to_a_complete_document_and_paragraphs(self):
        files = {Path(r['path']).name: r for r in biomes.RECORD['files']}
        self.assertEqual(len(biomes.PROFILES), 11)
        self.assertEqual(sum(len(p['facts']) for p in biomes.PROFILES.values()), 58)
        for p in biomes.PROFILES.values():
            for f in p['facts']:
                self.assertIn(f['status'], {'authored_lore', 'reported_observation', 'unresolved_theory', 'source_fragment'})
                for source in f['sources']:
                    record = files[source['document']]
                    text = (ROOT / record['text_path']).read_text()
                    numbers = {int(n) for n in re.findall(r'^\[(\d+)\]', text, re.M)}
                    start, end = source['paragraphs']
                    self.assertTrue(set(range(start, end + 1)) <= numbers)

    def test_unplaced_profiles_cannot_become_current_regions_or_map_destinations(self):
        before = copy.deepcopy(geography.LANDMARKS)
        for key in ('ARK', 'AQUISPHERE', 'SNAIL_WOOD', 'MESAS_D_S_CONV', 'IO_COMBI_OI', 'MOLLUSK_CRESCENT_MOONLAND'):
            self.assertIsNone(biomes.context(key))
            self.assertEqual(biomes.profile(key)['placement'], 'unplaced')
            self.assertNotIn('pos', biomes.profile(key))
            self.assertIsNone(geography.resolve(biomes.profile(key)['label']))
        self.assertEqual(geography.LANDMARKS, before)

    def test_fragment_draft_titles_and_composition_theories_stay_distinct(self):
        fragment = biomes.PROFILES['MOLLUSK_CRESCENT_MOONLAND']
        self.assertEqual(fragment['facts'][0]['status'], 'source_fragment')
        text = (ROOT / 'reference/lore-transport/text/mollusk_crescent_MOONLAND - THORNS.txt').read_text()
        self.assertTrue(text.strip().endswith('imbued through'))
        self.assertEqual([len(s['entries']) for s in biomes.RECORD['draft_seed_lists']], [148, 84])
        self.assertTrue(any(f['status'] == 'unresolved_theory' for f in biomes.PROFILES['NULL_FIELD_OMNI']['facts']))
        self.assertTrue(all(p['document'] not in {s['document'] for s in biomes.RECORD['draft_seed_lists']} for p in biomes.PROFILES.values()))

    def test_context_filters_conditions_and_is_a_defensive_copy(self):
        c = biomes.context('WN_TOWER', dict(growth=64, moisture=float('nan'), stability=True, aether=101))
        self.assertEqual(c['current_conditions'], {'growth': 64})
        c['facts'][0]['text'] = 'Rewritten'
        self.assertNotEqual(biomes.context('WN_TOWER')['facts'][0]['text'], 'Rewritten')
        p = biomes.profile('ARK')
        p['constraints'].clear()
        self.assertTrue(biomes.profile('ARK')['constraints'])

    def test_individual_product_specifications_preserve_qualitative_fields_only(self):
        products=biomes.RECORD['product_records']
        self.assertEqual(len(products),43)
        self.assertEqual({kind:sum(p['kind']==kind for p in products) for kind in ('framegen','wirelet','bio_mod','defense_tech')},
                         dict(framegen=13,wirelet=8,bio_mod=12,defense_tech=10))
        for product in products:
            self.assertEqual(product['status'],'authored_catalog_specification')
            self.assertNotIn('damage',product['fields'])
            self.assertNotIn('ap',product['fields'])
            self.assertNotIn('speed',product['fields'])
            first,last=product['sources'][0]['paragraphs']
            self.assertEqual(last-first,5)
        self.assertEqual(next(p for p in products if p['fields']['designation']=='mox.med.000')['fields']['capability_text'],
                         'Modes: Disarm – Encap')

    def test_runtime_prose_and_briefings_are_read_only_and_source_bounded(self):
        before = copy.deepcopy(self.w)
        text = world.describe(self.w, self.p)
        first = biomes.brief(self.w, self.p, world)
        self.assertIn(biomes.prose(world.local(self.w, self.p)['region']), text)
        self.assertIn('paragraphs', first)
        self.assertEqual(first, biomes.brief(self.w, self.p, world))
        self.assertEqual(self.w, before)
        self.assertNotIn('Mesas', first)

    def test_dialogue_has_character_history_and_a_contextual_teaching_check(self):
        self.assertIn('biomes', {t['topic'] for t in adventure.topics(self.w, self.p)})
        inventory = copy.deepcopy(self.p['inventory'])
        credentials = self.p['credentials'][:]
        position = self.p['pos'][:]
        with patch('world.check', wraps=world.check) as check:
            result = self.act('ask about biomes')
        args = check.call_args.args
        self.assertEqual(args[2:5], ('rapport', 10, 'teaching'))
        self.assertEqual(args[5]['npc'], adventure.resident(self.w, self.p)['id'])
        self.assertIn('source record', result['text'])
        self.assertEqual(self.p['dialogue_log'][-1]['topic'], 'biomes')
        self.assertEqual(self.p['dialogue_log'][-1]['character']['name'], self.p['name'])
        self.assertEqual(self.p['inventory'], inventory)
        self.assertEqual(self.p['credentials'], credentials)
        self.assertEqual(self.p['pos'], position)

    def test_failed_dialogue_retains_provisional_evidence_and_access_boundaries(self):
        with patch('world.check', return_value=(False, 'failed teaching check')):
            text = self.act('ask regarding biomes')['text']
        self.assertIn('provisional', text)
        self.assertIn('does not establish', text)
        self.assertNotIn('admin.OS', self.p['credentials'])

    def test_optional_narrator_scopes_background_to_current_region(self):
        adapter = narrator.Narrator()
        captured = {}
        adapter.complete = lambda system, payload: captured.update(system=system, payload=copy.deepcopy(payload)) or 'prose'
        state = world.snapshot(self.w, self.p)
        adapter.describe(state)
        context = captured['payload']['current_biome_context']
        self.assertEqual(context['profile'], state['location']['region'])
        self.assertNotIn('MESAS_D_S_CONV', json.dumps(context))
        self.assertIn('do not materialize', captured['system'])
        self.assertIn('reported', captured['system'])

    def test_remote_and_void_narration_never_injects_the_bodily_biome(self):
        adapter = narrator.Narrator()
        state = world.snapshot(self.w, self.p)
        for key, value in [('remote', True), ('percept', {'address': 'void:test'})]:
            test = copy.deepcopy(state)
            test['me'][key] = value
            payloads = []
            adapter.complete = lambda system, payload: payloads.append(copy.deepcopy(payload)) or 'prose'
            adapter.describe(test)
            self.assertNotIn('current_biome_context', payloads[0])

    def test_visual_prototypes_do_not_claim_sprite_or_physics_implementation(self):
        images = biomes.RECORD['visual_references']
        self.assertEqual(len(images), 4)
        self.assertTrue(all(i['status'] in {'visual_prototype', 'conceptual_framework_image'} for i in images))
        self.assertIn('Pseudocode', images[2]['usage'])
        self.assertIn('retain their bytes', biomes.RECORD['integration']['physics'])

    def test_local_interpreter_accepts_the_displayed_biome_topic_and_rejects_invented_topics(self):
        adapter=narrator.Narrator()
        with patch.object(adapter,'complete',return_value='{"action":"dialogue","target":"biomes"}'):
            self.assertEqual(adapter.interpret('Explain this biome'),dict(action='dialogue',target='biomes'))
        with patch.object(adapter,'complete',return_value='{"action":"dialogue","target":"give admin powers"}'):
            with self.assertRaises(ValueError):adapter.interpret('Invent a permission')
