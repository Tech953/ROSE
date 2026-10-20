"""Visual identity and save migration cannot affect survival mechanics."""
import copy
import json
import unittest
from pathlib import Path

import characters
import visuals
import world

ROOT = Path(__file__).resolve().parents[1]


class VisualIdentityTests(unittest.TestCase):
    def test_old_character_templates_gain_automatic_presentation(self):
        old=characters.default('NanoClad Scout');old.pop('presentation')
        self.assertEqual(characters.validate(old)['presentation'],'automatic')

    def test_invalid_profiles_and_managed_visual_fields_are_rejected(self):
        for bad in ['unknown', {}, None]:
            ch=characters.default();ch['presentation']=bad
            with self.assertRaises(ValueError):characters.validate(ch)
        ch=characters.default();ch['visual']={'model':'artisan'}
        with self.assertRaises(ValueError):characters.validate(ch)

    def test_presentation_is_independent_of_pronouns_and_stats(self):
        ch=characters.default();ch.update(presentation='artisan',pronouns='they/them')
        actor=dict(id='player-a',character=characters.validate(ch),health=76,inventory={'water':3})
        prior=copy.deepcopy(actor);v=visuals.ensure_actor({'seed':'rose'},actor)
        self.assertEqual(v['model'],'artisan')
        for key in prior:self.assertEqual(actor[key],prior[key])

    def test_embodiment_auto_and_explicit_model_override(self):
        ch=characters.default('Metal-kin Artisan');a=dict(id='repairer',character=ch)
        self.assertEqual(visuals.ensure_actor({'seed':'rose'},a)['model'],'metal_kin')
        ch['presentation']='artisan'
        self.assertEqual(visuals.ensure_actor({'seed':'rose'},a)['model'],'artisan')

    def test_identity_survives_travel_recruitment_and_json_round_trip(self):
        w={'seed':'rose'};a=dict(id='npc-a',x=0,y=0,character=characters.default('Seam Mediator'))
        original=copy.deepcopy(visuals.ensure_actor(w,a))
        a.update(x=19,y=-10,owner='player-a');a=json.loads(json.dumps(a))
        self.assertEqual(visuals.ensure_actor(w,a),original)

    def test_node_identity_survives_condition_and_cycle_changes(self):
        w={'seed':'rose'};cell={'x':3,'y':4,'region':'ENACT_HILLS'};n=dict(id='shelter-2',kind='shelter',condition=70)
        old=copy.deepcopy(visuals.ensure_node(w,cell,n));n['condition']=29
        self.assertEqual(visuals.ensure_node(w,cell,n),old)
        self.assertEqual(old['model'],'shelter_ENACT_HILLS')

    def test_sector_qualified_structure_ids_and_people_have_distinct_signatures(self):
        w={'seed':'rose'};a=dict(id='npc-a',character=characters.default());b=dict(id='npc-b',character=characters.default())
        self.assertNotEqual(visuals.ensure_actor(w,a)['signature'],visuals.ensure_actor(w,b)['signature'])
        signatures=[]
        for x in range(5):
            signatures.append(visuals.ensure_node(w,{'x':x,'y':0,'region':'WN_TOWER'},dict(id='water-1',kind='water'))['signature'])
        self.assertEqual(len(set(signatures)),5)

    def test_every_actor_profile_and_regional_building_is_registered(self):
        m=json.loads((ROOT/'static/art-manifest-rendered.json').read_text())
        for profile in visuals.CATALOG['profiles']:
            for suffix in ['', '_tone1', '_tone2']:self.assertIn(profile+suffix,m['assets'])
        for region in visuals.CATALOG['regions']:
            for kind in visuals.CATALOG['structures']:
                asset=m['assets'][kind+'_'+region]
                self.assertIn('idle',asset['clips']);self.assertIn('worn',asset['clips'])

    def test_first_host_snapshot_has_consistent_visuals_without_changing_geometry_or_needs(self):
        w=world.new_world('unit-identity-audit');w['code']='ARTAUDIT'
        p=world.add_player(w,'Auditor','Fractech Archivist')
        c=w['cells'][','.join(map(str,p['pos']))];geometry=copy.deepcopy(c['scene']['tiles'])
        stats=(p['health'],p['energy'],p['inventory'].copy(),w['tick'])
        s=world.snapshot(w,p);u=next(u for u in s['scene']['units'] if u['mine'])
        self.assertEqual(s['me']['visual'],u['visual']);self.assertEqual(s['me']['visual'],p['visual'])
        self.assertEqual((p['health'],p['energy'],p['inventory'],w['tick']),stats)
        self.assertEqual(c['scene']['tiles'],geometry)


if __name__=='__main__':unittest.main()
