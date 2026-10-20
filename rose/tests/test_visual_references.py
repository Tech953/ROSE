"""Source integrity, read-only generation scope and actual HTTP boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import biomes
import geography
import narrator
import server
import visual_references as visual
import world

ROOT=Path(__file__).resolve().parents[1]

class ReferenceIntegrityTests(unittest.TestCase):
    def test_every_alias_resolves_to_exact_original_payload_and_dimensions(self):
        d=visual.RECORD;records={r['sha256']:r for r in d['references']};aliases={r['filename']:r for r in d['original_aliases']}
        self.assertEqual(len(records),len(d['references']))
        self.assertEqual(len(aliases),d['coverage']['uploaded_files'])
        self.assertEqual(sum(len(r['aliases']) for r in records.values()),len(aliases))
        for sha,r in records.items():
            raw=(ROOT/r['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),sha);self.assertEqual(len(raw),r['bytes'])
            self.assertEqual(raw[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II',raw[16:24]),(r['width'],r['height']))
            for name in r['aliases']:
                self.assertEqual(aliases[name]['sha256'],sha)
                self.assertEqual(aliases[name]['pixel_sha256'],r['pixel_sha256'])
                self.assertEqual(aliases[name]['bytes'],len(raw))
        self.assertEqual(d['coverage']['unique_original_bytes'],sum(r['bytes'] for r in records.values()))

    def test_historical_recovery_and_similar_original_names_remain_distinct(self):
        receipt=json.loads((ROOT/'reference/lore-transport/recovery-record.json').read_text())
        self.assertEqual(receipt['status'],'PARTIAL RECOVERY');self.assertTrue(receipt['unknown_later_files'])
        aliases={a for r in visual.REFERENCES.values() for a in r['aliases']}
        for n in ('IMAGE TEST 51(1).png','TEST IMAGE 51(1).png','TEST image 13(1).png','PRODUCT TEST IAMGE(1).png','Designer (2)(1).png'):
            self.assertIn(n,aliases)
        a,b=[next(r['id'] for r in visual.REFERENCES.values() if n in r['aliases']) for n in ('IMAGE TEST 51(1).png','TEST IMAGE 51(1).png')]
        self.assertNotEqual(a,b)

    def test_unassigned_framework_and_scenarios_never_enter_profile_guidance(self):
        selected={i for p in visual.RECORD['profile_briefs'].values() for i in p['sources']}
        for r in visual.REFERENCES.values():
            if r['category'] in {'unassigned','framework','combat'}:self.assertNotIn(r['id'],selected)
            if r['category']=='unassigned':self.assertEqual(r['profiles'],[])
            for k in r['conflicts']:self.assertTrue(visual.RECORD['conflict_register'][k])

    def test_authoring_copies_cannot_place_regions_or_mutate_catalog(self):
        landmarks=copy.deepcopy(geography.LANDMARKS)
        for identity in ('ARK','AQUISPHERE','MESAS_D_S_CONV','NULL_FIELD_OMNI'):
            self.assertTrue(visual.brief(identity));self.assertIsNone(biomes.context(identity))
        value=visual.brief('WN_TOWER');value['materials'].clear();value['sources'][0]['filename']='changed'
        self.assertTrue(visual.brief('WN_TOWER')['materials'])
        self.assertNotEqual(visual.brief('WN_TOWER')['sources'][0]['filename'],'changed')
        self.assertIsNone(visual.brief('unknown'));self.assertEqual(geography.LANDMARKS,landmarks)

    def test_narrator_guidance_preserves_region_character_and_world(self):
        w=world.new_world('reference-scope');p=world.add_player(w,'Independent traveler','NanoClad Scout');w['code']='VISUALTEST'
        state=world.snapshot(w,p);before=copy.deepcopy(w);payloads=[];adapter=narrator.Narrator()
        adapter.complete=lambda system,payload:payloads.append(copy.deepcopy(payload)) or 'prose'
        adapter.describe(state);context=payloads[0]['current_biome_context'];guidance=context['visual_reference_context']
        self.assertEqual(context['profile'],state['location']['region']);self.assertTrue(guidance['sources'])
        self.assertIn('not current observations',guidance['status']);self.assertIn('remain authoritative',guidance['policy'])
        self.assertEqual(payloads[0]['observer']['name'],'Independent traveler')
        self.assertNotIn('Fractbound',json.dumps(context));self.assertNotIn('RENDER.STANCE',json.dumps(context))
        for s in guidance['sources']:self.assertIn(context['profile'],visual.REFERENCES[s['id']]['profiles'])
        self.assertEqual(w,before)

    def test_remote_and_percept_narration_omit_bodily_art_context(self):
        w=world.new_world('reference-remote');p=world.add_player(w,'Observer','NanoClad Scout');w['code']='REMOTETEST'
        state=world.snapshot(w,p);adapter=narrator.Narrator()
        for prop,value in [('remote',True),('percept',{'address':'void:test'})]:
            changed=copy.deepcopy(state);changed['me'][prop]=value;payloads=[]
            adapter.complete=lambda system,payload:payloads.append(copy.deepcopy(payload)) or 'prose'
            adapter.describe(changed);self.assertNotIn('current_biome_context',payloads[0])

    def test_registry_rejects_noncanonical_paths_before_serving(self):
        r=next(iter(visual.REFERENCES.values()));bad=copy.deepcopy(r);bad['path']='reference/visual-corpus/images/../../../server.py'
        with patch.object(visual,'REFERENCES',{r['id']:bad}):
            with self.assertRaises(ValueError):visual.asset_routes()

class ReferenceHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.http.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown();cls.http.server_close();cls.thread.join(timeout=2)

    def test_all_registered_sources_have_exact_hashes_types_and_headers(self):
        for route,(name,mime) in visual.ASSET_ROUTES.items():
            expected=hashlib.sha256((ROOT/'static'/name).read_bytes()).hexdigest()
            with urllib.request.urlopen(self.base+route) as response:
                sha=hashlib.sha256()
                while chunk:=response.read(1024*1024):sha.update(chunk)
                self.assertEqual(sha.hexdigest(),expected);self.assertEqual(response.headers['Content-Type'],mime)
                self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
                self.assertIn("frame-ancestors 'none'",response.headers['Content-Security-Policy'])
        for route,mime in [('/visual-references.html','text/html; charset=utf-8'),('/visual-reference-catalog.json','application/json'),('/visual-reference-review.txt','text/plain; charset=utf-8')]:
            with urllib.request.urlopen(self.base+route) as response:
                self.assertEqual(response.headers['Content-Type'],mime);self.assertTrue(response.read())

    def test_altered_unknown_and_encoded_paths_cannot_escape_allowlist(self):
        route=next(iter(visual.ASSET_ROUTES))
        for altered in (route+'?source=1',route.replace('.png','.PNG'),'/visual-reference/unknown.png','/visual-reference/../../server.py','/visual-reference/%2e%2e/server.py','/visual-reference/%2fserver.py'):
            with self.assertRaises(urllib.error.HTTPError) as raised:urllib.request.urlopen(self.base+altered)
            self.assertEqual(raised.exception.code,404)

if __name__=='__main__':unittest.main()
