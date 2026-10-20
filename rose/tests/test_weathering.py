"""Observed weather, finite surface care, ownership and migration boundaries."""
import copy
import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from test_engine import RoseTest
import hexgrid as hx
import materials
import scene
import server
import weathering
import world
import narrator


class WeatheringTests(RoseTest):
    def canopy(self):
        self.p['pos']=[-2,5]
        self.c=world.local(self.w,self.p)
        scene.sync(self.w,self.c,world)
        node=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='shelter')
        self.assertTrue(weathering.canopy(node))
        return node

    def step(self,climate='particulate storm'):
        self.w['tick']+=1
        weathering.advance(self.w,self.c,world,climate)

    def test_rain_wets_and_washes_while_dry_air_drains_surface_water(self):
        node=self.canopy();s=weathering.surface(node);s['dust']=40
        for _ in range(4):self.step('rain')
        self.assertEqual(s['wetness'],64);self.assertEqual(s['dust'],8)
        self.step('still air');self.assertEqual(s['wetness'],61)

    def test_dust_and_wind_strain_are_bounded_and_do_not_repair_material(self):
        node=self.canopy();s=weathering.surface(node);condition=node['condition']
        for _ in range(350):self.step()
        self.assertEqual(s['dust'],100);self.assertEqual(s['lashings'],0)
        self.assertEqual(node['condition'],condition)
        self.assertTrue(all(0<=s[k]<=100 for k in ['wetness','dust','lashings']))

    def test_shared_climate_has_shared_wind_without_moving_geometry(self):
        self.canopy();other=world.visit(self.w,-1,5)
        geometry={k:{f:v for f,v in t.items() if f!='material_state'} for k,t in copy.deepcopy(self.c['scene']['tiles']).items()}
        self.step('contrail squall');weathering.advance(self.w,other,world,'contrail squall')
        for key in ['strength','direction','climate']:
            self.assertEqual(self.c['surface_weather'][key],other['surface_weather'][key])
        self.assertEqual(geometry,{k:{f:v for f,v in t.items() if f!='material_state'} for k,t in self.c['scene']['tiles'].items()})

    def test_same_tick_old_tick_and_read_operations_never_accumulate_weather(self):
        node=self.canopy();self.step();before=copy.deepcopy(self.c)
        weathering.advance(self.w,self.c,world,'rain')
        weathering.public(self.w,self.c,self.p);weathering.public_object(node);weathering.prose(self.c)
        self.assertEqual(self.c,before)
        self.w['tick']-=1;weathering.advance(self.w,self.c,world,'rain');self.assertEqual(self.c,before)

    def test_held_clocks_and_paused_worlds_do_not_advance_weather(self):
        self.canopy();before=copy.deepcopy(self.c);self.w['tick']+=1
        self.w['paused']=True;weathering.advance(self.w,self.c,world,'rain');self.assertEqual(self.c,before)
        self.w['paused']=False
        with patch.object(world.tactical,'any_active',return_value=True):
            weathering.advance(self.w,self.c,world,'rain')
        self.assertEqual(self.c,before)

    def test_cold_save_migration_starts_now_and_never_applies_a_clock_gap(self):
        node=self.canopy()
        for obj in weathering.objects(self.c):obj['material_state'].pop('surface',None)
        self.c.pop('surface_weather');self.w['tick']=900
        condition=node['condition'];weathering.ensure(self.w,self.c,world)
        weathering.advance(self.w,self.c,world,'rain')
        self.assertEqual(node['condition'],condition);self.assertEqual(weathering.surface(node)['wetness'],0)
        self.assertEqual(weathering.surface(node)['last_tick'],900)
        self.w['tick']=1900;weathering.advance(self.w,self.c,world,'rain')
        self.assertEqual(weathering.surface(node)['wetness'],16)

    def test_newly_seen_objects_do_not_inherit_old_surface_history(self):
        self.canopy();self.step('rain')
        new=dict(id='fresh',kind='shelter',pos=[0,0],condition=80)
        materials.ensure(new,'fabric',self.w['tick'])
        weathering.ensure_object(self.w,self.c,new)
        self.assertEqual(weathering.surface(new)['wetness'],0)
        self.assertEqual(weathering.surface(new)['dust'],0)

    def test_paid_bracing_records_appropriate_check_without_repair_or_salvage(self):
        node=self.canopy();self.approach(node)
        before=self.p['inventory']['scrap'];condition=node['condition'];budget=node['material_state']['embodied_scrap']
        with patch('world.weather',return_value='still air'):
            result=self.act('brace canopy '+node['id'])
        self.assertTrue(result['time_spent']);self.assertEqual(self.p['inventory']['scrap'],before-1)
        self.assertTrue(weathering.braced(node));self.assertEqual(weathering.surface(node)['brace_inputs'],1)
        self.assertEqual(self.p['last_check']['skill'],'seamllurgy')
        self.assertEqual(node['condition'],condition);self.assertEqual(node['material_state']['embodied_scrap'],budget)

    def test_failed_brace_spends_one_input_and_does_not_tighten(self):
        node=self.canopy();self.approach(node);s=weathering.surface(node);s['lashings']=35
        before=self.p['inventory']['scrap']
        with patch('world.weather',return_value='still air'),patch('world.secrets.randbelow',return_value=0):
            self.act('canopy_brace','structure:'+node['id'])
        self.assertEqual(self.p['inventory']['scrap'],before-1);self.assertEqual(s['lashings'],35)
        self.assertEqual(s['brace_inputs'],1)

    def test_cleaning_spends_real_water_and_never_repairs_condition(self):
        node=self.canopy();self.approach(node);s=weathering.surface(node);s['dust']=80
        before=self.p['inventory']['water'];condition=node['condition']
        with patch('world.weather',return_value='still air'):
            self.act('clean surface structure '+node['id'])
        self.assertEqual(self.p['inventory']['water'],before-1);self.assertEqual(s['dust'],30)
        self.assertEqual(s['wetness'],32);self.assertEqual(node['condition'],condition)
        self.assertEqual(self.p['last_check']['skill'],'resource')

    def test_failed_cleaning_wets_surface_without_removing_dust(self):
        node=self.canopy();self.approach(node);s=weathering.surface(node);s['dust']=80
        before=self.p['inventory']['water']
        with patch('world.weather',return_value='still air'),patch('world.secrets.randbelow',return_value=0):
            self.act('surface_clean','structure:'+node['id'])
        self.assertEqual(self.p['inventory']['water'],before-1);self.assertEqual(s['dust'],80)
        self.assertEqual(s['wetness'],32)

    def test_invalid_target_distance_stock_and_ownership_reject_before_spending(self):
        node=self.canopy();self.approach(node);s=weathering.surface(node);s['dust']=40
        guest=world.add_player(self.w,'Other owner','Surveyor');node['owner']=guest['id']
        pack=copy.deepcopy(self.p['inventory']);tick=self.w['tick']
        with self.assertRaises(ValueError):self.act('surface_clean','structure:'+node['id'])
        node.pop('owner');self.p['inventory']['scrap']=0
        with self.assertRaises(ValueError):self.act('canopy_brace','structure:'+node['id'])
        self.p['inventory']=pack.copy();self.p['local']['pos']=[0,0]
        if hx.distance([0,0],node['pos'])==1:self.p['local']['pos']=[3,0]
        with self.assertRaises(ValueError):self.act('surface_clean','structure:'+node['id'])
        with self.assertRaises(ValueError):self.act('canopy_brace','structure:not-here')
        self.assertEqual(self.p['inventory'],pack);self.assertEqual(self.w['tick'],tick)

    def test_nonfabric_structures_and_ruins_cannot_be_braced_or_reanimated(self):
        node=next(n for n in self.c['infrastructure']['nodes'] if n['kind']=='water');self.approach(node)
        with self.assertRaises(ValueError):self.act('canopy_brace','structure:'+node['id'])
        node=self.canopy();self.approach(node);materials.damage(node,100,self.w['tick'])
        materials.collapse_node(self.w,self.c,node,world)
        before=copy.deepcopy(node['material_state'])
        with self.assertRaises(ValueError):self.act('canopy_brace','structure:'+node['id'])
        self.step('rain');self.assertEqual(weathering.surface(node)['wetness'],before['surface']['wetness'])
        self.assertEqual(node['condition'],0)

    def test_bracing_reduces_existing_weather_wear_and_relaxes_with_storms(self):
        node=self.canopy();other=copy.deepcopy(node)
        weathering.surface(node)['lashings']=95;weathering.surface(other)['lashings']=55
        for tick in range(self.w['tick']+1,self.w['tick']+101):
            materials.age(node,tick,30,'particulate storm',weathering.protection(node))
            materials.age(other,tick,30,'particulate storm',weathering.protection(other))
        self.assertGreater(node['condition'],other['condition'])
        for _ in range(40):self.step()
        self.assertFalse(weathering.braced(node))

    def test_remote_and_void_views_do_not_export_a_live_weather_driver(self):
        self.canopy();self.assertIsNotNone(weathering.public(self.w,self.c,self.p))
        self.p['remote']=True;self.assertIsNone(weathering.public(self.w,self.c,self.p))
        self.p['remote']=False;self.p['percept']={'address':'void:test'}
        self.assertIsNone(weathering.public(self.w,self.c,self.p))

    def test_optional_interpreter_does_not_offer_actions_without_registered_field_targets(self):
        self.assertFalse(weathering.ACTS & set(narrator.ACTIONS))
        adapter=narrator.Narrator()
        with patch.object(adapter,'complete',return_value='{"action":"canopy_brace","target":"structure:invented"}'):
            with self.assertRaises(ValueError):adapter.interpret('Brace an invented canopy')

    def test_sqlite_reload_preserves_surface_identity_treatment_and_input_receipts(self):
        node=self.canopy();weathering.surface(node).update(wetness=44,dust=33,lashings=91,brace_inputs=2,clean_inputs=3)
        expected=copy.deepcopy(weathering.surface(node));old=server.DB
        with tempfile.TemporaryDirectory() as directory:
            try:
                server.init_db(str(Path(directory)/'weather.db'));server.save(self.w)
                restored=server.fetch(self.w['code']);cell=restored['cells'][world.key(*self.p['pos'])]
                weathering.ensure(restored,cell,world)
                actual=next(n for n in cell['infrastructure']['nodes'] if n['id']==node['id'])
                self.assertEqual(weathering.surface(actual),expected)
            finally:
                if server.DB is not old:server.DB.close()
                server.DB=old
