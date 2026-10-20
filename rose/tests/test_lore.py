import copy
from test_engine import RoseTest
import adventure
import lore
import world


class LoreContinuityTests(RoseTest):
    def test_supplied_commentary_has_sources_status_and_aliases(self):
        self.assertGreaterEqual(len(lore.RECORD['records']),30)
        for id in ['series','scale','substrate','void','immunix','absolutix','endcaps','eunix','great-web','economy','research']:
            self.assertTrue(lore.BY_ID[id]['status']);self.assertTrue(lore.BY_ID[id]['text'])
        self.assertIn('UNIX',lore.RECORD['aliases']['EUNIX'])

    def test_map_wide_briefing_records_character_and_does_not_grant_scope(self):
        before=self.p['credentials'][:];topics={n['topic'] for n in adventure.topics(self.w,self.p)}
        self.assertTrue(set(lore.TOPICS)<=topics)
        for topic in lore.TOPICS:
            self.act('ask about '+topic);entry=self.p['dialogue_log'][-1];self.assertEqual(entry['topic'],topic);self.assertEqual(entry['character']['name'],self.p['name']);self.assertIn('briefing',entry['response'])
        self.assertEqual(self.p['credentials'],before);self.assertNotIn('admin.OS',self.p['credentials'])
