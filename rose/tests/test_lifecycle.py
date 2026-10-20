import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import hexgrid as hx
import infrastructure
import lifecycle
import scene
import server
import world
import companions


class EnvironmentTests(RoseTest):
    def advance(self,climate='rain',growth=None):
        self.w['tick']+=1;lifecycle.advance(self.w,self.c,climate,self.c['growth'] if growth is None else growth,world)

    def site(self):
        return next(n['pos'] for n in lifecycle.public(self.w,self.c,self.p,world)['candidates'] if not n['reason'])

    def plan(self,kind='shelter'):
        self.p['inventory']['scrap']=40;pos=self.site();self.act('construction_plan',kind+'|'+hx.key(pos));return self.c['lifecycle']['projects'][-1]

    def test_seedling_establishment_is_delayed_and_only_rewards_once(self):
        self.c.update(moisture=70,stability=80,growth=20);self.c['lifecycle']['soil_health']=60
        lifecycle.register_planting(self.w,self.c,self.p,world);plant=self.c['lifecycle']['plantings'][0]
        self.assertEqual(plant['stage'],'germinating');self.assertEqual(plant['pos'],self.p['local']['pos'])
        for _ in range(4):self.advance()
        self.assertEqual(plant['stage'],'seedling');self.assertEqual(self.c['growth'],20)
        for _ in range(8):self.advance()
        self.assertEqual(plant['stage'],'established');self.assertEqual(self.c['growth'],28)
        for _ in range(20):self.advance()
        self.assertEqual(self.c['growth'],28)

    def test_drought_wilts_and_decays_with_material_return(self):
        lifecycle.register_planting(self.w,self.c,self.p,world);plant=self.c['lifecycle']['plantings'][0];plant.update(age=12,matured=True,stage='established')
        self.c.update(moisture=0,growth=30);litter=self.c['lifecycle']['litter']
        for _ in range(4):self.advance('dry wind')
        self.assertEqual(plant['stage'],'wilted')
        for _ in range(5):self.advance('dry wind')
        self.assertEqual(plant['stage'],'decayed');self.assertEqual(self.c['lifecycle']['litter'],litter+4);self.assertEqual(self.c['growth'],26)
        for _ in range(12):self.advance('dry wind')
        self.assertEqual(self.c['lifecycle']['litter'],litter+4)

    def test_moist_detritus_returns_to_soil_while_dry_litter_persists(self):
        self.c['lifecycle'].update(litter=10,soil_health=40);self.c['moisture']=70;self.w['tick']=3;self.advance();self.assertEqual(self.c['lifecycle']['litter'],8);self.assertEqual(self.c['lifecycle']['soil_health'],41)
        self.c['moisture']=5;self.w['tick']=7;self.advance('dry wind');self.assertEqual(self.c['lifecycle']['litter'],8)

    def test_storm_erosion_and_nutrient_limits_are_authoritative(self):
        self.c.update(growth=10,moisture=70);self.c['lifecycle'].update(erosion=0,soil_health=12);self.c['growth']=14;self.advance('particulate storm',10)
        self.assertEqual(self.c['growth'],10);self.assertEqual(self.c['lifecycle']['erosion'],2);self.assertEqual(self.c['lifecycle']['soil_health'],11)

    def test_reading_and_same_tick_do_not_advance_ecology(self):
        self.advance();before=copy.deepcopy(self.c['lifecycle']);tick=self.w['tick'];inventory=self.p['inventory'].copy()
        lifecycle.advance(self.w,self.c,'particulate storm',self.c['growth'],world);self.act('inspect environment')
        self.assertEqual(self.c['lifecycle'],before);self.assertEqual(self.w['tick'],tick);self.assertEqual(self.p['inventory'],inventory)
        self.assertEqual(self.p['last_check']['skill'],'druid')

    def test_failed_care_uses_water_without_creating_soil(self):
        self.c['lifecycle'].update(litter=12,soil_health=30);self.c['moisture']=40;water=self.p['inventory']['water']
        with patch('world.secrets.randbelow',return_value=0):self.act('compost litter')
        self.assertEqual(self.p['inventory']['water'],water-1);self.assertEqual(self.c['lifecycle']['soil_health'],30);self.assertEqual(self.c['lifecycle']['litter'],12)

    def test_construction_reserves_material_and_rejects_occupied_tiles(self):
        p=self.plan();self.assertEqual(self.p['inventory']['scrap'],35);self.assertFalse(self.c['scene']['tiles'][hx.key(p['pos'])]['passable'])
        inv=self.p['inventory'].copy()
        with self.assertRaises(ValueError):self.act('construction_plan','shelter|'+hx.key(p['pos']))
        self.assertEqual(self.p['inventory'],inv)

    def test_failed_foundation_does_not_reserve_or_create_project(self):
        self.p['inventory']['scrap']=30;pos=self.site();before=self.p['inventory'].copy()
        with patch('world.secrets.randbelow',return_value=0):self.act('construction_plan','shelter|'+hx.key(pos))
        self.assertEqual(self.p['inventory'],before);self.assertEqual(self.c['lifecycle']['projects'],[]);self.assertTrue(self.c['scene']['tiles'][hx.key(pos)]['passable'])

    def test_completed_building_is_physical_and_connected(self):
        p=self.plan('water');nodes=len(self.c['infrastructure']['nodes'])
        for _ in range(p['work_required']):self.act('construction_work',p['id'])
        self.assertEqual(p['stage'],'complete');self.assertEqual(p['spent'],p['escrow']);self.assertEqual(len(self.c['infrastructure']['nodes']),nodes+1)
        node=next(n for n in self.c['infrastructure']['nodes'] if n['id']==p['built_node'])
        self.assertEqual(node['pos'],p['pos']);self.assertTrue(self.c['scene']['tiles'][hx.key(p['pos'])]['opaque']);self.assertTrue(any(p['built_node'] in [n['a'],n['b']] for n in self.c['infrastructure']['links']))
        with self.assertRaises(ValueError):self.act('construction_cancel',p['id'])

    def test_cancel_refunds_only_unspent_material_once_and_restores_tile(self):
        p=self.plan();original=copy.deepcopy(p['tile_before']);self.act('construction_work',p['id']);refund=p['escrow']-p['spent'];before=self.p['inventory']['scrap'];self.act('construction_cancel',p['id'])
        self.assertEqual(self.p['inventory']['scrap'],before+refund);self.assertEqual(self.c['scene']['tiles'][hx.key(p['pos'])],original)
        with self.assertRaises(ValueError):self.act('construction_cancel',p['id'])
        self.assertEqual(self.p['inventory']['scrap'],before+refund)

    def test_cooperation_keeps_commissioning_and_refund_authority(self):
        p=self.plan();guest=world.add_player(self.w,'Guest','Light Reader');world.snapshot(self.w,guest)
        routes=[hx.path(self.c['scene']['tiles'],guest['local']['pos'],q,scene.occupied(self.w,self.c,guest['id'])) for q in hx.neighbors(p['pos'])];route=min((r for r in routes if r),key=len);guest['local']['pos']=route[-1]
        before=guest['inventory'].copy();world.act(self.w,guest,dict(action='construction_work',target=p['id']))
        self.assertEqual(guest['inventory'],before);self.assertIn(guest['id'],p['contributors'])
        with self.assertRaises(ValueError):world.act(self.w,guest,dict(action='construction_cancel',target=p['id']))

    def test_no_material_refund_from_weather_regression(self):
        p=self.plan();lifecycle.work(self.w,self.c,p,self.p,world);spent=p['spent']
        for tick in [6,12,18]:self.w['tick']=tick;lifecycle.advance(self.w,self.c,'particulate storm',self.c['growth'],world)
        self.assertEqual(p['work_done'],0);self.assertEqual(p['spent'],spent)

    def test_connectivity_check_preserves_the_central_exit(self):
        pos=self.site();self.p['local']['pos']=[2,0];self.c['scene']['tiles'][hx.key(pos)]['passable']=True
        self.w['actors']=[];self.w['residents']={}
        # An isolated test corridor makes this adjacent site the only way home.
        for tile in self.c['scene']['tiles'].values():tile['passable']=tile['pos'] in [[0,0],[1,0],[2,0]]
        self.assertIn('cut',lifecycle.site_reason(self.w,self.c,self.p,[1,0],world))

    def test_companion_build_uses_blueprint_check_and_escrow_without_personal_scrap(self):
        p=self.plan('garden');a=self.w['actors'][0];a['owner']=self.p['id'];self.p['companions']=[a['id']];a['inventory']['scrap']=0;a['energy']=90;a['attitude']=80
        a['local']['pos']=next(q for q in hx.neighbors(p['pos']) if self.c['scene']['tiles'].get(hx.key(q),{}).get('passable') and q!=self.p['local']['pos']);a['engagement'].update(task='repair',planned='repair',phase='work',last_work=-100)
        self.w['tick']=4;companions.cycle(self.w,world)
        self.assertEqual(p['work_done'],1);self.assertEqual(a['last_check']['skill'],'druid');self.assertEqual(a['last_check']['dc'],11);self.assertEqual(a['inventory']['scrap'],0)

    def test_legacy_migration_and_restart_retain_growth_projects_and_accounting(self):
        self.c.pop('lifecycle');world.snapshot(self.w,self.p);p=self.plan();lifecycle.register_planting(self.w,self.c,self.p,world)
        with tempfile.TemporaryDirectory() as tmp:
            server.init_db(str(Path(tmp)/'environment.db'));server.save(self.w);loaded=server.fetch(self.w['code'])
            self.assertEqual(loaded['cells'][world.key(*self.p['pos'])]['lifecycle'],self.c['lifecycle']);self.assertEqual(loaded['cells'][world.key(*self.p['pos'])]['scene']['tiles'][hx.key(p['pos'])]['passable'],False)

    def test_long_succession_stays_bounded_and_keeps_history_limits(self):
        lifecycle.register_planting(self.w,self.c,self.p,world)
        for i in range(500):
            self.c['moisture']=70 if i%24<12 else 0;self.advance('particulate storm' if i%3==0 else 'rain')
        for key in ['soil_health','litter','erosion']:self.assertTrue(0<=self.c['lifecycle'][key]<=100)
        self.assertLessEqual(len(self.c['lifecycle']['ledger']),32)
