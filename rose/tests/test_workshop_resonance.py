"""Physical workshop scope, outage recovery and shared authority regressions."""
import copy
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import hexgrid as hx
import infrastructure
import interactions
import particles
import photonics
import scene
import server
import world


class WorkshopResonanceTests(RoseTest):
    def rig(self, approach=True):
        node=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='workshop')
        if approach:self.approach(node)
        self.c['infrastructure']['stores']['power']=5
        return node

    def field(self):
        return particles.field(self.w,self.p,world)

    def menu(self,node):
        return world.snapshot(self.w,self.p)['scene']['interaction_options']['structure:'+node['id']]['actions']

    def option(self,node,action):
        return next(a for a in self.menu(node) if a['intent']['action']==action)

    def balanced(self):
        ph=self.field()['photonics']
        self.assertAlmostEqual(ph['input_energy'],ph['energy']+ph['emitted_energy']+ph['heat_energy'],places=10)

    def other_rig(self):
        node=copy.deepcopy(next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='workshop'))
        node.update(id='built-project-987654321',pos=[3,0],status='working',ledger=[],repaired_by=[])
        self.c['scene']['tiles'][hx.key(node['pos'])]['passable']=False
        self.c['infrastructure']['nodes'].append(node)
        root=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='power')
        self.c['infrastructure']['links'].append(dict(a=root['id'],b=node['id'],condition=100,path=hx.line(root['pos'],node['pos'])))
        return node

    def test_workshop_catalogue_is_read_only_target_bound_and_priced(self):
        node=self.rig(False);units=world.snapshot(self.w,self.p)['scene']['units'];before=copy.deepcopy(self.w)
        menu=interactions.public(self.w,self.c,self.p,units,world)['structure:'+node['id']]['actions']
        self.assertEqual(self.w,before)
        optical=[a for a in menu if a['intent']['action'].startswith('particle_')]
        self.assertEqual(len(optical),4)
        for a in optical:
            self.assertEqual(a['skill'],world.characters.SKILLS['light']['label'])
            self.assertTrue(a['intent']['target'].startswith(node['id']))
            self.assertIn('survival cycle',a['cost'])
        tune=next(a for a in optical if a['intent']['action']=='particle_tune')
        self.assertEqual(tune['settings']['bands'],list(photonics.BANDS))
        self.assertEqual(tune['settings']['modes'],list(photonics.MODES))
        self.assertIn('adjacent',tune['reason'])
        self.assertTrue(all(a['reason'] for a in optical if a['intent']['action'] not in {'particle_survey','particle_audit'}))

    def test_bound_reading_records_light_context_without_advancing_field(self):
        node=self.rig(False);f=copy.deepcopy(self.field());tick=self.w['tick'];pack=self.p['inventory'].copy()
        self.act('goto','-8,3');journey=copy.deepcopy(self.p['overworld'])
        result=self.act('particle_survey',node['id'])
        self.assertIn(node['id'],result['text']);self.assertIn('shared field resonance',result['text'])
        self.assertEqual(self.p['last_check']['skill'],'light');self.assertEqual(self.p['last_check']['faction'],node['faction'])
        self.assertEqual(self.field(),f);self.assertEqual(self.w['tick'],tick);self.assertEqual(self.p['inventory'],pack)
        self.assertEqual(self.p['overworld'],journey)

    def test_reading_works_in_remote_and_combat_but_not_across_void(self):
        node=self.rig(False);self.act('remote','')
        self.assertIn('UNVERIFIED REMOTE PROJECTION',self.act('particle_survey',node['id'])['text'])
        self.act('return','');self.battle();enc=copy.deepcopy(self.c['scene']['encounter'])
        self.act('particle_survey',node['id']);self.assertEqual(self.c['scene']['encounter'],enc)
        self.c['scene']['encounter']['active']=False;self.p['credentials']=['black.dot'];self.p['percept'].update(armor=30,immunix=2)
        self.act('enter void_null')
        with self.assertRaisesRegex(ValueError,'baseline workshop'):self.act('particle_survey',node['id'])

    def test_every_physical_entry_point_requires_an_adjacent_workshop(self):
        node=self.rig(False);photonics.pump(self.field(),True,node)
        for action,target in [('particle_excite',''),('particle_excite',node['id']),('particle_quench',''),('particle_quench',node['id']),('particle_tune','jade:steady'),('particle_tune',node['id']+'|jade:steady')]:
            with self.subTest(action=action,target=target):
                before=copy.deepcopy(self.field());power=self.c['infrastructure']['stores']['power'];tick=self.w['tick'];checks=len(self.p['check_log'])
                with self.assertRaisesRegex(ValueError,'adjacent'):self.act(action,target)
                self.assertEqual(self.field(),before);self.assertEqual(self.c['infrastructure']['stores']['power'],power)
                self.assertEqual(self.w['tick'],tick);self.assertEqual(len(self.p['check_log']),checks)

    def test_selected_workshop_is_not_replaced_by_another_maintained_one(self):
        node=self.rig();other=self.other_rig();node['enabled']=False
        for action,target in [('particle_tune',node['id']+'|jade:steady'),('particle_excite',node['id']),('particle_quench',node['id'])]:
            with self.subTest(action=action),self.assertRaisesRegex(ValueError,'enabled, connected'):self.act(action,target)
        self.assertTrue(photonics.maintained(other,self.c));self.assertEqual(self.field()['photonics']['input_energy'],0)

    def test_active_source_cannot_be_hijacked_from_a_second_workshop(self):
        node=self.rig();self.act('particle_excite',node['id']);other=self.other_rig();self.approach(other)
        for action,target in [('particle_tune',other['id']+'|violet:boundary'),('particle_excite',other['id']),('particle_quench',other['id'])]:
            with self.subTest(action=action),self.assertRaisesRegex(ValueError,'assigned workshop'):self.act(action,target)
            self.assertIn('assigned workshop',self.option(other,action)['reason'])
        self.assertEqual(self.field()['photonics']['source_node'],node['id']);self.balanced()

    def test_empty_reservoir_can_bind_a_different_physically_approached_workshop(self):
        node=self.rig();self.act('particle_excite',node['id']);self.act('particle_quench',node['id'])
        other=self.other_rig();self.approach(other);self.act('particle_tune',other['id']+'|amber:steady')
        ph=self.field()['photonics'];self.assertEqual(ph['source_node'],other['id']);self.assertEqual(ph['energy'],0)
        self.c['infrastructure']['stores']['power']=5;self.act('particle_excite',other['id'])
        self.assertGreater(ph['energy'],0);self.assertEqual(ph['input_energy'],2);self.balanced()

    def test_full_archive_menu_refuses_work_but_reports_unresolved_observations(self):
        node=self.rig();data=particles.ensure(self.w);f=self.field();del data['fields'][f['address']]
        for i in range(particles.MAX_FIELDS):data['fields']['void:budget:'+str(i)]=dict(address='void:budget:'+str(i),objects=[],metrics={})
        before=copy.deepcopy(data);units=scene.public(self.w,self.p,world)['units']
        menu=interactions.public(self.w,self.c,self.p,units,world)['structure:'+node['id']]['actions']
        self.assertEqual(data,before)
        for option in menu:
            if option['intent']['action'] in {'particle_tune','particle_excite','particle_quench'}:
                self.assertIn('archive',option['reason'])
                with self.assertRaisesRegex(ValueError,'archive'):self.act(**option['intent'])
        result=self.act('particle_survey',node['id']);self.assertIn('archive',result['text']);self.assertNotIn('Input 0.000',result['text'])
        self.assertEqual(data,before)

    def test_bound_tuning_uses_selected_faction_and_failed_attempt_is_attributed(self):
        node=self.rig();node['faction']='Test Guild'
        self.act('particle_tune',node['id']+'|jade:alternating')
        self.assertEqual(self.p['last_check']['faction'],'Test Guild');ph=self.field()['photonics']
        self.assertEqual((ph['band'],ph['mode'],ph['source_node']),('jade','alternating',node['id']))
        with patch('world.secrets.randbelow',return_value=0):self.act('particle_excite',node['id'])
        self.assertEqual(ph['input_energy'],1);self.assertEqual(ph['heat_energy'],1)
        item=node['ledger'][-1];self.assertEqual(item['actor'],self.p['id']);self.assertFalse(item['success'])
        self.assertNotIn('work_serial',item);self.assertEqual(item['action'],'particle_excite');self.balanced()

    def test_optical_work_cannot_prove_a_maintenance_contract(self):
        node=self.rig();node['condition']=60;node['repaired_by']=[self.p['id']]
        self.act('structure_contract',node['id']);node['condition']=90;node['work_serial']+=1
        self.act('particle_tune',node['id']+'|cyan:steady')
        self.assertIn('your own successful repair',self.option(node,'structure_fulfill')['reason'])
        with self.assertRaisesRegex(ValueError,'repair'):self.act('structure_fulfill',node['id'])

    def test_broken_network_link_blocks_and_quenches_before_a_utility_cycle(self):
        node=self.rig();self.act('particle_excite',node['id']);ph=self.field()['photonics'];emitted=ph['emitted_energy']
        for edge in self.c['infrastructure']['links']:edge['condition']=0
        node['status']='working';node.pop('connected',None)
        self.assertFalse(photonics.maintained(node,self.c));self.assertIn('connected',self.option(node,'particle_excite')['reason'])
        self.act('wait','');self.assertEqual(ph['energy'],0);self.assertEqual(ph['emitted_energy'],emitted)
        self.assertEqual(ph['source_node'],node['id']);self.assertEqual(ph['exposure'],0);self.balanced()

    def test_wear_outage_is_reconciled_in_the_same_utility_cycle(self):
        node=self.rig();node['condition']=30;self.w['tick']=self.w['rules']['infrastructure']['cycle_ticks']-1
        ph=photonics.pump(self.field(),True,node);world.tick(self.w)
        self.assertLess(node['condition'],30);self.assertEqual(ph['energy'],0);self.assertEqual(ph['exposure'],0)
        self.assertEqual(ph['trace'][-1]['signal'],0);self.assertEqual(ph['trace'][-1]['stored'],0)
        self.assertEqual(ph['source_node'],node['id']);self.balanced()

    def test_repair_retains_settings_but_requires_new_paid_input(self):
        node=self.rig();self.act('particle_tune',node['id']+'|jade:boundary');self.act('particle_excite',node['id'])
        ph=self.field()['photonics'];node['condition']=29;self.w['tick']=self.w['rules']['infrastructure']['cycle_ticks']-1
        self.act('wait','');self.assertEqual(ph['energy'],0);self.assertEqual(node['status'],'offline')
        self.act('structure_repair',node['id']);self.assertGreaterEqual(node['condition'],30)
        self.assertEqual((ph['band'],ph['mode'],ph['source_node']),('jade','boundary',node['id']))
        self.assertEqual(ph['energy'],0);self.assertEqual(ph['input_energy'],1)
        with self.assertRaisesRegex(ValueError,'power deficit'):self.act('particle_excite',node['id'])
        for _ in range(self.w['rules']['infrastructure']['cycle_ticks']):
            if photonics.maintained(node,self.c):break
            self.act('wait','')
        self.assertTrue(photonics.maintained(node,self.c));self.assertEqual(ph['input_energy'],1)
        self.c['infrastructure']['stores']['power']=5;self.act('particle_excite',node['id'])
        self.assertEqual(ph['input_energy'],2);self.assertGreater(ph['energy'],0);self.balanced()

    def test_invalid_bound_targets_never_fall_back_to_a_workshop(self):
        node=self.rig();wrong=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='water')
        for action,target in [('particle_survey','unknown'),('particle_excite',wrong['id']),('particle_tune','unknown|cyan:steady'),('particle_tune',node['id']+'|cyan:steady|admin')]:
            with self.subTest(action=action,target=target),self.assertRaises(ValueError):self.act(action,target)
        self.assertEqual(self.field()['photonics']['input_energy'],0)

    def test_paused_void_remote_and_combat_menu_guards_match_physical_server(self):
        node=self.rig();photonics.pump(self.field(),True,node)
        for field,value,fragment in [('paused',True,'paused'),('remote',True,'remote'),('void','void:test','trace')]:
            subject=self.w if field=='paused' else self.p if field=='remote' else self.p['percept'];name='address' if field=='void' else field
            old=subject[name];subject[name]=value
            try:
                units=scene.public(self.w,self.p,world)['units']
                menu=interactions.public(self.w,self.c,self.p,units,world)['structure:'+node['id']]['actions']
                self.assertTrue(all(fragment in a['reason'] for a in menu if a['intent']['action'] in {'particle_tune','particle_excite','particle_quench'}))
                with self.assertRaises(ValueError):self.act('particle_excite',node['id'])
            finally:subject[name]=old
        self.battle();self.assertIn('encounter',self.option(node,'particle_excite')['reason'])
        with self.assertRaises(ValueError):self.act('particle_excite',node['id'])

    def test_shared_http_revision_refuses_stale_drive_without_spending(self):
        node=self.rig();guest=world.add_player(self.w,'Guest','Light Reader');world.snapshot(self.w,guest)
        routes=[hx.path(self.c['scene']['tiles'],guest['local']['pos'],pos,scene.occupied(self.w,self.c,guest['id'])) for pos in hx.neighbors(node['pos'])]
        route=min((r for r in routes if r),key=len)
        for pos in route[1:]:world.act(self.w,guest,dict(action='hex_move',target=hx.key(pos)))
        self.c['infrastructure']['stores']['power']=5
        with tempfile.TemporaryDirectory() as tmp:
            server.init_db(str(Path(tmp)/'shared.db'));server.save(self.w)
            old_revision=self.w['revision']
            def request(p,revision,action,target):
                return server.request(dict(op='act',code=self.w['code'],token=p['token'],revision=revision,intent=dict(action=action,target=target)))
            first=request(self.p,old_revision,'particle_excite',node['id']);before=copy.deepcopy(server.fetch(self.w['code']))
            with self.assertRaisesRegex(ValueError,'world changed'):request(guest,old_revision,'particle_excite',node['id'])
            self.assertEqual(server.fetch(self.w['code']),before)
            second=request(guest,first['state']['revision'],'particle_excite',node['id'])
            self.assertEqual(second['state']['particles']['photonics']['input_energy'],2)
            self.assertEqual(second['state']['particles']['photonics']['source_node'],node['id'])
            self.assertEqual(second['state']['me']['last_check']['skill'],'light')
            ledger=second['state']['scene']['infrastructure']['nodes']
            events=next(n for n in ledger if n['id']==node['id'])['ledger']
            self.assertEqual([n['actor'] for n in events if n.get('action')=='particle_excite'][-2:],[self.p['id'],guest['id']])

    def test_long_constructed_workshop_target_passes_only_scoped_request_limit(self):
        self.rig();node=self.other_rig();self.approach(node);target=node['id']+'|violet:alternating'
        self.assertGreater(len(target),30)
        with tempfile.TemporaryDirectory() as tmp:
            server.init_db(str(Path(tmp)/'long-id.db'));server.save(self.w)
            request=dict(op='act',code=self.w['code'],token=self.p['token'],revision=self.w['revision'])
            with self.assertRaisesRegex(ValueError,'Invalid proposed action'):
                server.request(dict(**request,intent=dict(action='structure_inspect',target='x'*31)))
            result=server.request(dict(**request,intent=dict(action='particle_tune',target=target)))
            self.assertEqual(result['state']['particles']['photonics']['source_node'],node['id'])
            self.assertEqual(result['state']['particles']['photonics']['mode'],'alternating')
