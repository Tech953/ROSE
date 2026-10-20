"""Source provenance, authoring/runtime boundaries and public host routes."""
import copy
import hashlib
import json
import threading
import urllib.request
from pathlib import Path
import unittest

from test_engine import RoseTest
import art_direction
import biomes
import engine
import geography
import narrator
import server
import world

ROOT=Path(__file__).resolve().parents[1]

class ArtDirectionTests(RoseTest):
    def test_exact_source_coverage_and_provenance(self):
        r=art_direction.export()
        visual=json.loads((ROOT/'reference/visual-corpus/catalog.json').read_text())
        lore=json.loads((ROOT/'reference/lore-record-v012.json').read_text())
        self.assertEqual(r['coverage'],dict(unique_images=80,uploaded_names=93,lore_records=44,biome_profiles=11,biome_facts=58,unit_recipes=110,product_briefs=43))
        self.assertEqual({i['image_id'] for i in r['image_contributions']},{i['id'] for i in visual['references']})
        self.assertEqual(len(r['image_contributions']),80)
        self.assertEqual({i['record_id']:i['source_text'] for i in r['lore_crosswalk']},{i['id']:i['text'] for i in lore['records']})
        expected={f"{p['id']}:{i}":f for p in biomes.RECORD['profiles'] for i,f in enumerate(p['facts'],1)}
        for f in r['biome_crosswalk']:
            src=expected[f['id']]
            self.assertEqual((f['source_text'],f['evidence_status'],f['sources']),(src['text'],src['status'],src['sources']))
        for source in r['sources']:self.assertEqual(source['sha256'],hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest())

    def test_unassigned_and_scenario_sources_stay_out_of_named_region_briefs(self):
        r=art_direction.RECORD
        source=json.loads((ROOT/'reference/visual-corpus/catalog.json').read_text())
        excluded={i['id'] for i in source['references'] if i['category'] in {'unassigned','framework','combat'}}
        for p in r['profiles'].values():self.assertFalse(excluded.intersection(p['image_sources']))
        for c in r['image_contributions']:
            if c['image_id'] in excluded:self.assertFalse(c['ordinary_region_source'])
        for pid in ('SNAIL_WOOD','IO_COMBI_OI','MOLLUSK_CRESCENT_MOONLAND'):
            self.assertEqual(r['profiles'][pid]['image_sources'],[])
            self.assertIsNone(biomes.context(pid))

    def test_engineering_fragments_and_independent_identities_keep_their_scope(self):
        r=art_direction.RECORD
        for x in r['lore_crosswalk']:
            if x['record_id'].startswith('vrex-') or x['record_id'] in {'aurora','research','engram-json-capacity'}:
                self.assertEqual(x['rules'],['offscreen']);self.assertEqual(x['image_sources'],[])
        for f in r['biome_crosswalk']:
            if f['evidence_status'] in {'source_fragment','unresolved_theory'}:self.assertEqual(f['rules'],['unresolved'])
            if 'kho.dev' in f['source_text'].lower():self.assertEqual(f['rules'],['independent_identity'])
        self.assertEqual(r['conflicts'],json.loads((ROOT/'reference/visual-corpus/catalog.json').read_text())['conflict_register'])

    def test_individual_recipes_preserve_qualitative_specifications(self):
        r=art_direction.RECORD
        self.assertEqual(len({x['id'] for x in r['unit_recipes']}),110)
        for x in r['unit_recipes']:
            self.assertEqual(x['placement'],biomes.PROFILES[x['profile']]['placement'])
            self.assertIn('Not a new modeled asset',x['production'])
        for p in biomes.RECORD['product_records']:
            brief=art_direction.product_brief(p['id'])
            self.assertEqual(brief['source_specification'],p['fields'])
            self.assertEqual(brief['text_sources'],p['sources'])
            self.assertFalse({'damage','ap','speed','price'}.intersection(brief['source_specification']))

    def test_authoring_access_is_defensive_and_never_changes_the_map_or_world(self):
        before=copy.deepcopy(self.w);landmarks=copy.deepcopy(geography.LANDMARKS)
        c=art_direction.context('WN_TOWER');c['materials'].clear()
        self.assertTrue(art_direction.context('WN_TOWER')['materials'])
        recipe=art_direction.asset_brief('ARK','actor');recipe['materials'].clear()
        self.assertTrue(art_direction.asset_brief('ARK','actor')['materials'])
        data=art_direction.export();data['profiles'].clear();self.assertEqual(len(art_direction.RECORD['profiles']),11)
        self.assertIsNone(art_direction.context('unknown'))
        with self.assertRaises(ValueError):art_direction.asset_brief('WN_TOWER','teleport')
        with self.assertRaises(ValueError):art_direction.product_brief('unknown')
        self.assertEqual(self.w,before);self.assertEqual(geography.LANDMARKS,landmarks)

    def test_narrator_is_current_region_only_and_keeps_registered_identity(self):
        adapter=narrator.Narrator();payloads=[]
        adapter.complete=lambda system,payload:payloads.append(copy.deepcopy(payload)) or 'prose'
        state=world.snapshot(self.w,self.p);before=copy.deepcopy(state);adapter.describe(state)
        c=payloads[-1]['current_biome_context']['text_visual_interpretation']
        self.assertEqual(c['principles'],art_direction.NARRATIVE_RULES)
        self.assertEqual(payloads[-1]['observer']['name'],self.p['name'])
        for term in ('RK4','VREX','Node 7B','Fractbound','MMTX_CORE','0.52','foot anchors','hex grid'):self.assertNotIn(term,json.dumps(c))
        for key,value in [('remote',True),('percept',{'address':'void:test'})]:
            test=copy.deepcopy(state);test['me'][key]=value;adapter.describe(test)
            self.assertNotIn('current_biome_context',payloads[-1])
        self.assertEqual(state,before)

    def test_blueprint_has_public_direction_without_character_or_session_data(self):
        before=copy.deepcopy(self.w);bp=engine.blueprint(self.w)
        self.assertEqual(bp['art_direction']['version'],'0.18.0')
        self.assertEqual(bp['art_direction']['unit_recipe_count'],110)
        self.assertEqual(bp['art_direction']['source_register'],'/art-direction-register.json')
        self.assertNotIn(self.p['name'],json.dumps(bp));self.assertNotIn('token',json.dumps(bp))
        bp['art_direction']['principles'].clear();self.assertTrue(art_direction.RECORD['global_rules'])
        self.assertEqual(self.w,before)

    def test_host_serves_only_registered_source_routes_with_exact_bytes(self):
        host=server.ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        thread=threading.Thread(target=host.serve_forever,daemon=True);thread.start()
        try:
            routes={'/art-direction.js':'static/art-direction.js','/art-direction-runtime.json':'static/art-direction-runtime.json',
              '/art-direction-register.json':'reference/art-direction/direction-v018.json','/art-direction.html':'static/art-direction.html',
              '/art-direction-guide.txt':'docs/ART-DIRECTION-AND-TEXT-INTERPRETATION.md'}
            for route,path in routes.items():
                with urllib.request.urlopen(f'http://127.0.0.1:{host.server_port}'+route) as response:
                    self.assertEqual(response.read(),(ROOT/path).read_bytes());self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
        finally:host.shutdown();host.server_close();thread.join()
