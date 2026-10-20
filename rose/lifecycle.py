"""Persistent soil/plant succession and finite, physical construction projects.

Rates are bounded game-scale approximations. Existing moisture, grazing,
weather and resource stocks remain the environmental inputs and authority.
"""
import copy
import re

import hexgrid as hx
import infrastructure
import scene
import visuals
import materials

ACTS={'environment_survey','soil_tend','soil_compost','construction_plan','construction_work','construction_cancel'}
BLUEPRINTS={
    'garden':dict(scrap=4,work=4,skill='druid',dc=11),
    'shelter':dict(scrap=5,work=5,skill='metallurgy',dc=11),
    'water':dict(scrap=6,work=6,skill='resource',dc=12),
    'power':dict(scrap=7,work=6,skill='fractech',dc=12),
    'workshop':dict(scrap=7,work=6,skill='metallurgy',dc=12),
    'relay':dict(scrap=6,work=5,skill='fractech',dc=12),
}
LIVE={'foundation','frame','finishing'}


def ensure(w,c):
    if 'lifecycle' not in c:
        c['lifecycle']=dict(schema=1,soil_health=min(85,45+c['growth']//4),litter=8+c['growth']//6,
                            erosion=max(0,40-c['growth']//2),last_tick=-1,plant_serial=0,
                            project_serial=0,plantings=[],projects=[],ledger=[])
    return c['lifecycle']


def record(w,data,text):
    data['ledger'].append(dict(tick=w['tick'],text=text));data['ledger']=data['ledger'][-32:]


def register_planting(w,c,p,engine):
    data=ensure(w,c)
    engine.require(sum(n['stage']!='decayed' for n in data['plantings'])<12,'Twelve living planted patches already need care here.')
    data['plant_serial']+=1
    species=engine.REGIONS[c['region']]['plants'][(data['plant_serial']-1)%len(engine.REGIONS[c['region']]['plants'])]
    item=dict(id='plant-'+str(data['plant_serial']),species=species,owner=p['id'],age=0,stress=0,
              stage='germinating',matured=False,planted_at=w['tick'],pos=p['local']['pos'][:])
    data['plantings']=[n for n in data['plantings'] if n['stage']!='decayed'][-11:]+[item]
    record(w,data,p['name']+' establishes '+species+'; germination and establishment still require suitable moisture and soil.')


def advance(w,c,climate,previous_growth,engine):
    data=ensure(w,c)
    if data['last_tick']==w['tick']:return
    data['last_tick']=w['tick']
    storm=climate in {'particulate storm','contrail squall'}
    if data['soil_health']<15:c['growth']=min(previous_growth,c['growth'])
    elif data['soil_health']<35:c['growth']=min(previous_growth+1,c['growth'])
    lost=max(0,previous_growth-c['growth'])
    data['litter']=engine.clamp(data['litter']+lost)
    if c['growth']>previous_growth and w['tick']%6==0:data['soil_health']=engine.clamp(data['soil_health']-1)
    if w['tick']%4==0 and c['moisture']>=35 and data['litter']>=2:
        data['litter']-=2;data['soil_health']=engine.clamp(data['soil_health']+1)
    if storm and c['growth']<35:
        data['erosion']=engine.clamp(data['erosion']+2);data['soil_health']=engine.clamp(data['soil_health']-1)
    elif w['tick']%6==0 and c['growth']>=50 and c['moisture']>=30:
        data['erosion']=engine.clamp(data['erosion']-1)
    for plant in data['plantings']:
        if plant['stage']=='decayed':continue
        before=plant['stage']
        good=c['moisture']>=30 and data['soil_health']>=25 and c['stability']>=30
        plant['stress']=max(0,plant['stress']-1) if good else min(12,plant['stress']+1)
        if good:plant['age']+=1
        if plant['stress']>=9:
            plant['stage']='decayed';data['litter']=engine.clamp(data['litter']+4)
            if plant['matured']:c['growth']=engine.clamp(c['growth']-4)
        elif plant['stress']>=4:plant['stage']='wilted'
        elif plant['age']>=12:
            plant['stage']='established'
            if not plant['matured']:
                plant['matured']=True;c['growth']=engine.clamp(c['growth']+8);c['moisture']=engine.clamp(c['moisture']-2)
        elif plant['age']>=4:plant['stage']='seedling'
        else:plant['stage']='germinating'
        if before!=plant['stage']:record(w,data,plant['species']+' changes from '+before+' to '+plant['stage']+'.')
    for project in data['projects']:
        if project['stage'] not in LIVE:continue
        if storm and w['tick']%6==0:
            project['exposure']+=1
            if project['exposure']%3==0 and project['work_done']:
                project['work_done']-=1;project['stage']=stage(project)
                c['scene']['tiles'][hx.key(project['pos'])]['opaque']=project['stage']!='foundation'
                record(w,data,project['id']+' loses one work step to prolonged storm exposure; used materials are not refunded.')


def stage(project):
    fraction=project['work_done']/project['work_required']
    return 'foundation' if fraction<.34 else 'frame' if fraction<.75 else 'finishing'


def cover(s):
    for tile in s['tiles'].values():
        if tile['passable']:tile['cover']=min(2,sum(s['tiles'][hx.key(p)]['opaque'] for p in hx.neighbors(tile['pos']) if hx.key(p) in s['tiles']))


def site_reason(w,c,p,pos,engine):
    s=c['scene'];tile=s['tiles'].get(hx.key(pos))
    if not tile or not tile['passable']:return 'Choose an empty walkable hex.'
    if pos==[0,0]:return 'Keep the central approach open.'
    if hx.distance(p['local']['pos'],pos)!=1:return 'Stand one hex beside the construction site.'
    if pos in scene.occupied(w,c):return 'A living unit occupies this site.'
    if len(c['infrastructure']['nodes'])>=28:return 'This field already holds 28 completed structures.'
    if sum(n['stage'] in LIVE | {'ruined'} for n in ensure(w,c)['projects'])>=6:return 'Complete, cancel or clear an existing project before opening a seventh site.'
    trial=copy.deepcopy(s['tiles']);trial[hx.key(pos)]['passable']=False
    players,npcs=scene.locals_here(w,c)
    for unit in [*players,*npcs]:
        if unit.get('health',100)>0 and unit.get('local',{}).get('sector')==s['id'] and hx.path(trial,unit['local']['pos'],[0,0]) is None:
            return 'This foundation would cut a living unit off from the central approach.'
    for node in c['infrastructure']['nodes']:
        if not any(trial.get(hx.key(q),{}).get('passable') and hx.path(trial,[0,0],q) is not None for q in hx.neighbors(node['pos'])):
            return 'This foundation would seal an existing structure apron.'
    return ''


def complete(w,c,project,engine):
    data=c['infrastructure'];kind=project['kind'];data_life=ensure(w,c)
    node=dict(id='built-'+project['id'],kind=kind,name='commissioned '+infrastructure.TYPES[kind]['label'],
              pos=project['pos'][:],condition=project.get('condition',100),enabled=True,material=project['material'],
              faction=project['faction'],capacity=2,status='awaiting cycle',repaired_by=[],work_serial=1,ledger=[],
              owner=project['owner'],embodied_scrap=project['escrow'],shelter_contribution=0)
    visuals.ensure_node(w,c,node)
    materials.ensure_node(w,c,node)
    if project.get('material_state'):
        node['material_state']=copy.deepcopy(project['material_state'])
        project['material_state']['transferred_to']=node['id']
    viable=[n for n in data['nodes'] if not n.get('ruin_registered')]
    parent=min(viable,key=lambda n:hx.distance(n['pos'],node['pos'])) if viable else None
    data['nodes'].append(node)
    if parent:data['links'].append(dict(a=parent['id'],b=node['id'],condition=100,path=hx.line(parent['pos'],node['pos'])))
    c['scene']['tiles'][hx.key(node['pos'])].update(prefab=kind,opaque=True,passable=False,elevation=0)
    cover(c['scene']);infrastructure.refresh_support(c)
    project.update(stage='complete',built_node=node['id'],spent=project['escrow'],completed_at=w['tick'])
    if kind=='shelter':
        node['shelter_contribution']=min(3,c['shelter']+1)-c['shelter'];c['shelter']+=node['shelter_contribution']
    record(w,data_life,project['id']+' is complete; '+node['id']+' joins the actual public works network.')


def work(w,c,project,subject,engine):
    project['work_done']+=1
    project['spent']=max(project['spent'],min(project['escrow'],(project['escrow']*project['work_done']+project['work_required']-1)//project['work_required']))
    project['contributors'][subject['id']]=project['contributors'].get(subject['id'],0)+1
    if project['work_done']>=project['work_required']:complete(w,c,project,engine)
    else:
        project['stage']=stage(project)
        c['scene']['tiles'][hx.key(project['pos'])]['opaque']=project['stage']!='foundation'
    scene.pose(c['scene'],subject,'work')
    record(w,ensure(w,c),subject['name']+' contributes one actual work step to '+project['id']+' ('+str(project['work_done'])+'/'+str(project['work_required'])+').')


def autonomous_build(w,subject,c,engine):
    scene.sync(w,c,engine)
    projects=[p for p in ensure(w,c)['projects'] if p['stage'] in LIVE and p['owner']==subject.get('owner')]
    if not projects:return None
    project=projects[0]
    if hx.distance(subject['local']['pos'],project['pos'])>1:
        routes=[hx.path(c['scene']['tiles'],subject['local']['pos'],q,scene.occupied(w,c,subject['id'])) for q in hx.neighbors(project['pos'])]
        routes=[r for r in routes if r]
        if not routes:return 'No physical construction approach is available.'
        route=min(routes,key=len)
        if len(route)>1:scene.pose(c['scene'],subject,'walk',route[1])
        return 'Moved one actual hex toward '+project['id']+' for a later work cycle.'
    work(w,c,project,subject,engine)
    return 'Contributed to '+project['id']+' using its reserved materials.'


def parse(text):
    value=text.strip().lower()
    exact={'inspect environment':'environment_survey','survey environment':'environment_survey','tend soil':'soil_tend','compost litter':'soil_compost'}
    if value in exact:return dict(action=exact[value],target='')
    match=re.fullmatch(r'plan (garden|shelter|water|power|workshop|relay)\s+(-?\d{1,2},-?\d{1,2})',value)
    if match:return dict(action='construction_plan',target=match[1]+'|'+match[2])
    match=re.fullmatch(r'(work|cancel) project\s+([\w-]{1,50})',value)
    if match:return dict(action='construction_'+('work' if match[1]=='work' else 'cancel'),target=match[2])
    return None


def handle(w,p,intent,raw,engine):
    c=engine.local(w,p);data=ensure(w,c);op=intent['action'];context=dict(action=op,faction=engine.REGIONS[c['region']]['faction'])
    if op=='environment_survey':
        ok,roll=engine.check(w,p,'percept',10,'druid',context)
        text=f"Moisture {c['moisture']}, growth {c['growth']}, soil health {data['soil_health']}, detritus {data['litter']}, erosion {data['erosion']}. "
        text+='The stand responds to weather, grazing, soil and elapsed cycles. '+('You distinguish the conditions for establishment and decay.' if ok else 'The measured record remains readable; the next succession is uncertain.')
        selected=next((n for n in data['projects'] if n['id']==intent.get('target')),None)
        if selected:text+=f" {selected['id']}: {selected['kind']}, {selected['stage']}, work {selected['work_done']}/{selected['work_required']}; {selected['escrow']-selected['spent']} unspent scrap remain reserved."
        return dict(text=text,mechanics=roll,time_spent=False)
    engine.require(not p['remote'] and not engine.tactical.active(c),'Return to physical exploration before environmental work.')
    if op in {'soil_tend','soil_compost'}:
        engine.require(p['inventory']['water']>=1,'Soil care requires one water from your pack.')
        if op=='soil_compost':engine.require(data['litter']>=4 and data['soil_health']<95,'Composting needs four detritus and soil health below 95.')
        else:engine.require(c['moisture']<95 or data['soil_health']<95,'The soil already has enough moisture and care.')
        p['inventory']['water']-=1;ok,roll=engine.check(w,p,'tech',10,'druid',context)
        if ok:
            if op=='soil_compost':data['litter']-=4;data['soil_health']=engine.clamp(data['soil_health']+6)
            else:c['moisture']=engine.clamp(c['moisture']+8);data['soil_health']=engine.clamp(data['soil_health']+2)
            text='Soil care holds; '+('four detritus are worked into the soil.' if op=='soil_compost' else 'one water moistens and protects the planted ground.')
        else:text='The soil preparation does not hold; one water was used, and no detritus was converted.'
        record(w,data,p['name']+': '+text);scene.pose(c['scene'],p,'work')
        return dict(text=text,mechanics=roll,time_spent=True)
    if op=='construction_plan':
        kind,_,coordinates=intent.get('target','').partition('|')
        engine.require(kind in BLUEPRINTS,'Choose a supported construction blueprint.')
        pos=hx.parse(coordinates);reason=site_reason(w,c,p,pos,engine);engine.require(not reason,reason)
        bp=BLUEPRINTS[kind];engine.require(p['inventory']['scrap']>=bp['scrap'],f"Reserve {bp['scrap']} scrap for this complete project.")
        ok,roll=engine.check(w,p,'tech',bp['dc'],bp['skill'],context)
        if not ok:return dict(text='The construction survey finds no dependable foundation. No materials were reserved.',mechanics=roll,time_spent=True)
        p['inventory']['scrap']-=bp['scrap'];data['project_serial']+=1
        material=engine.REGIONS[c['region']]['material']
        project=dict(id='project-'+str(data['project_serial']),kind=kind,pos=pos,owner=p['id'],stage='foundation',
                     work_done=0,work_required=bp['work'],escrow=bp['scrap'],spent=0,exposure=0,
                     contributors={},started_at=w['tick'],material=material,faction=context['faction'],
                     tile_before=copy.deepcopy(c['scene']['tiles'][hx.key(pos)]),visual=dict(model=kind+'_'+c['region'],tone=0))
        materials.ensure(project,materials.profile_for(c,kind),w['tick'],bp['scrap'])
        data['projects']=[n for n in data['projects'] if n['stage'] in LIVE | {'ruined'}]+[n for n in data['projects'] if n['stage'] not in LIVE | {'ruined'}][-10:]+[project]
        c['scene']['tiles'][hx.key(pos)].update(passable=False,opaque=False,prefab='construction',elevation=0);cover(c['scene'])
        scene.pose(c['scene'],p,'work');record(w,data,p['name']+' reserves '+str(bp['scrap'])+' scrap for '+project['id']+'.')
        return dict(text=f"{project['id']} begins at hex {pos}; {bp['scrap']} scrap are reserved and {bp['work']} successful physical work steps remain.",mechanics=roll,time_spent=True)
    project=next((n for n in data['projects'] if n['id']==intent.get('target') and n['stage'] in LIVE),None)
    engine.require(project is not None,'Choose an active construction project in this field.')
    engine.require(hx.distance(p['local']['pos'],project['pos'])==1,'Approach one hex beside this project.')
    bp=BLUEPRINTS[project['kind']]
    if op=='construction_cancel':
        engine.require(project['owner']==p['id'],'Only the commissioning player can cancel this project.')
        refund=project['escrow']-project['spent'];engine.require(p['inventory']['scrap']+refund<=99,'Make room in your pack for the unspent materials.')
        ok,roll=engine.check(w,p,'tech',9,bp['skill'],context)
        if not ok:return dict(text='The safe dismantling attempt needs further work. The project and escrow remain intact.',mechanics=roll,time_spent=True)
        p['inventory']['scrap']+=refund;project['stage']='cancelled';project['refunded']=refund
        c['scene']['tiles'][hx.key(project['pos'])]=copy.deepcopy(project['tile_before']);cover(c['scene'])
        record(w,data,project['id']+' is dismantled; '+str(refund)+' unspent scrap return to the commissioning pack.')
        return dict(text=f"{project['id']} is cancelled. {refund} unspent scrap return; used materials remain consumed.",mechanics=roll,time_spent=True)
    ok,roll=engine.check(w,p,'tech',bp['dc'],bp['skill'],context)
    if ok:work(w,c,project,p,engine)
    text=f"{project['id']}: {project['stage']}, work {project['work_done']}/{project['work_required']}. "+('The fitted work holds.' if ok else 'The fit needs another attempt; reserved materials remain accounted for.')
    return dict(text=text,mechanics=roll,time_spent=True)


def public(w,c,p,engine):
    data=copy.deepcopy(ensure(w,c))
    for project in data['projects']:project.pop('tile_before',None)
    blocked='Begin the expedition first.' if not w['started'] else 'The host has paused the clock.' if w['paused'] else 'Return through the recorded void trace before baseline work.' if p.get('percept',{}).get('address') else 'Return from remote observation.' if p['remote'] else 'Resolve the encounter first.' if engine.tactical.active(c) else ''
    for project in data['projects']:
        if project['stage']=='ruined':
            project['actions']=materials.object_actions(w,c,p,'project',project,engine);continue
        if project['stage'] not in LIVE:continue
        bp=BLUEPRINTS[project['kind']]
        adjacent=hx.distance(p['local']['pos'],project['pos'])==1
        reason=blocked or ('' if adjacent else 'Approach one hex beside this project.')
        project['actions']=[dict(label='LOOK / PROJECT',group='look',intent=dict(action='environment_survey',target=project['id']),skill='druid',training=p['character']['skills'].get('druid',0),stat='percept',dc=10,cost='Observation only.',reason='Begin the expedition first.' if not w['started'] else 'The host has paused the clock.' if w['paused'] else '',default=True),dict(label='WORK ONE STEP',group='skill',intent=dict(action='construction_work',target=project['id']),skill=bp['skill'],training=p['character']['skills'].get(bp['skill'],0),stat='tech',dc=bp['dc'],cost='Uses reserved materials; one survival action.',reason=reason),
                            dict(label='DISMANTLE PROJECT',group='use',intent=dict(action='construction_cancel',target=project['id']),skill=bp['skill'],training=p['character']['skills'].get(bp['skill'],0),stat='tech',dc=9,cost=str(project['escrow']-project['spent'])+' unspent scrap recoverable.',reason=reason or ('Only the commissioning player can cancel this project.' if p['id']!=project['owner'] else 'Make room for unspent materials.' if p['inventory']['scrap']+project['escrow']-project['spent']>99 else ''))]+materials.object_actions(w,c,p,'project',project,engine)
    data.update(moisture=c['moisture'],growth=c['growth'],season=engine.season(w['tick']),blueprints=copy.deepcopy(BLUEPRINTS),
                candidates=[dict(pos=q,reason=site_reason(w,c,p,q,engine)) for q in hx.neighbors(p['local']['pos']) if hx.key(q) in c['scene']['tiles']])
    data['work_reason']=blocked
    return data
