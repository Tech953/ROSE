"""Individually persistent resonance objects, adapted from the supplied Aurora bundle.

Abstract simulation units. All objects in one materialized field interact pairwise.
Form changes preserve IDs and mass; fields and carried samples persist in SQLite.
"""
import copy
import hashlib
import json
import math
import re
import photonics
import research
import vrex
import machines

ACTS={'vrex_configure','vrex_stimulus','vrex_pump','vrex_stop','vrex_expand','vrex_perturb','vrex_diagnose','particle_survey','particle_audit','particle_excite','particle_tune','particle_quench','particle_sample','particle_deposit','void_prepare','void_enter','void_step','void_back','void_return'}
ELEMENTS=('cognitive','emotional','physical','temporal','ethereal')
COMPAT={
 'cognitive':dict(cognitive=1,emotional=.7,physical=.3,temporal=.8,ethereal=.9),
 'emotional':dict(cognitive=.7,emotional=1,physical=.5,temporal=.4,ethereal=.8),
 'physical':dict(cognitive=.3,emotional=.5,physical=1,temporal=.6,ethereal=.2),
 'temporal':dict(cognitive=.8,emotional=.4,physical=.6,temporal=1,ethereal=.7),
 'ethereal':dict(cognitive=.9,emotional=.8,physical=.2,temporal=.7,ethereal=1)}
MAX_OBJECTS=64
MAX_FIELDS=256
UNRESOLVED_REASON='The particle archive is full. Baseline exploration remains available; retained particles and return traces are preserved.'


def ensure(w,p=None):
    data=w.setdefault('substrate',dict(schema=1,fields={},carried={},generated_mass=0.,imported_mass=0.,imports=[],ledger=[]))
    if p is not None:p.setdefault('percept',dict(address=None,path=[],anchor=None,armor=0,immunix=0,strain=0))
    return data


def note(w,text):
    data=ensure(w);data['ledger'].append(dict(tick=w['tick'],text=text));data['ledger']=data['ledger'][-64:]


def materialize(w,address,engine):
    data=ensure(w)
    if address not in data['fields']:
        engine.require(len(data['fields'])<MAX_FIELDS,'This prototype has reached its 256-field particle archive budget. Recorded fields and return routes remain available.')
        g=engine.rng(w['seed'],'info-particle-v1',address);objects=[]
        for i in range(12):
            id='p-'+hashlib.sha256((w['seed']+'|'+address+'|'+str(i)).encode()).hexdigest()[:12]
            objects.append(dict(id=id,name=('EUNIX' if i%4==0 else 'interact')+' '+str(i+1),mass=round(g.uniform(.5,4),5),charge=round(g.uniform(-1,1),5),frequency=round(g.uniform(.5,2),5),phase=g.uniform(0,math.tau),element=ELEMENTS[i%5],polarity='matter' if i%7 else 'antimatter',matterType='normal' if i%6 else 'dark',position=dict(x=g.uniform(60,540),y=g.uniform(60,340)),velocity=dict(x=0.,y=0.),form='EUNIX' if i%4==0 else 'interact',lineage=dict(seed=w['seed'],address=address,index=i),history=[]))
        data['fields'][address]=dict(address=address,objects=objects,last_tick=w['tick'],metrics={},formations=[])
        data['generated_mass']+=sum(n['mass'] for n in objects);measure(data['fields'][address])
        note(w,address+' materializes 12 individually addressed particles; their generated mass is recorded.')
    photonics.ensure(data['fields'][address])
    return data['fields'][address]


def field(w,p,engine):
    data=ensure(w,p)
    address=p['percept']['address'] or 'base:'+engine.key(*p['pos'])
    if address.startswith('base:') and address not in data['fields'] and len(data['fields'])>=MAX_FIELDS:
        unresolved=dict(address=address,objects=[],formations=[],last_tick=w['tick'],unresolved_reason=UNRESOLVED_REASON)
        measure(unresolved);return unresolved
    return materialize(w,address,engine)


def amplification(a,b):
    return math.cos(a['phase']-b['phase'])*math.exp(-abs(a['frequency']-b['frequency']))


def influence(a,b):
    dx=b['position']['x']-a['position']['x'];dy=b['position']['y']-a['position']['y'];r=math.hypot(dx,dy)
    if r<20:return 0.,0.
    ma=a['mass']*(2 if a['matterType']=='dark' else 1);mb=b['mass']*(2 if b['matterType']=='dark' else 1)
    gravity=.5*ma*mb/(r*r);qa=a['charge']*(-1 if a['polarity']=='antimatter' else 1);qb=b['charge']*(-1 if b['polarity']=='antimatter' else 1)
    charge=0 if 'dark' in {a['matterType'],b['matterType']} else -.5*qa*qb
    polarity=2/r if a['polarity']!=b['polarity'] else 0
    magnitude=(gravity*amplification(a,b)*COMPAT[a['element']][b['element']]+charge+polarity)*.1
    return magnitude*dx/r,magnitude*dy/r


def measure(f):
    objects=f['objects'];pairs=0;ras=0.;formations=[]
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            score=(amplification(a,b)+1)/2*COMPAT[a['element']][b['element']];ras+=score;pairs+=1
            if score>=.6:formations.append(dict(memberIds=[a['id'],b['id']],cohesion=round(score,6)))
    energy=sum(.5*n['mass']*(n['velocity']['x']**2+n['velocity']['y']**2) for n in objects)
    coherent=100*math.hypot(sum(math.sin(n['phase']) for n in objects),sum(math.cos(n['phase']) for n in objects))/max(1,len(objects))
    f['metrics']=dict(count=len(objects),mass=sum(n['mass'] for n in objects),kinetic_energy=energy,ras=round(100*ras/max(1,pairs),5),phase_coherence=round(coherent,5),pair_interactions=pairs,eunix=sum(n.get('form')=='EUNIX' for n in objects),radiant=sum(n.get('form')=='radiant' for n in objects))
    f['formations']=formations


def step(w,f):
    if f['last_tick']==w['tick']:return
    objects=f['objects'];forces={n['id']:[0.,0.] for n in objects}
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            fx,fy=influence(a,b);forces[a['id']][0]+=fx;forces[a['id']][1]+=fy;forces[b['id']][0]-=fx;forces[b['id']][1]-=fy
            if a['polarity']!=b['polarity'] and a['matterType']==b['matterType']=='normal' and math.dist(list(a['position'].values()),list(b['position'].values()))<8:
                for n in (a,b):
                    if n.get('form')!='radiant':
                        n['form']='radiant';n['history']=(n.get('history',[])+[dict(tick=w['tick'],change='matter interaction becomes a radiant form; identity and mass persist')])[-16:]
                        note(w,n['id']+' changes to a radiant form without removal.')
    damping_loss=0.
    for n in objects:
        fx,fy=forces[n['id']]
        for axis,force in [('x',fx),('y',fy)]:
            v=n['velocity'][axis]+force/n['mass'];after=max(-4.,min(4.,v*.99));damping_loss+=max(0,.5*n['mass']*(v*v-after*after));n['velocity'][axis]=after
            n['position'][axis]+=after;edge=600 if axis=='x' else 400
            if n['position'][axis]<0 or n['position'][axis]>edge:n['position'][axis]=max(0.,min(float(edge),n['position'][axis]));n['velocity'][axis]*=-1
        n['phase']=(n['phase']+.04*n['frequency'])%math.tau
    f['last_tick']=w['tick'];f['dissipated_energy']=f.get('dissipated_energy',0.)+damping_loss;measure(f)


def advance(w):
    data=ensure(w)
    for f in data['fields'].values():
        if f['last_tick']==w['tick']:continue
        c=w['cells'].get(f['address'][5:]) if f['address'].startswith('base:') else None
        if c:
            for n in f['objects']:
                before=n.get('form','interact');damage=n.get('degradation',0)
                wet=c['moisture']>=35 and c.get('lifecycle',{}).get('soil_health',30)>=25
                if before in {'EUNIX','dormant'}:
                    damage=max(0,damage-2) if wet else min(100,damage+5)
                    n['degradation']=damage
                    if damage>=60:n['form']='dormant';n['charge']*=.99
                    elif wet and damage<30:n['form']='EUNIX'
                elif before=='interact' and n['element']=='physical' and wet and f['metrics'].get('phase_coherence',0)>=65:n['form']='EUNIX';n['degradation']=0
                n['complexity']=max(0,n.get('complexity',0)+(1 if wet and w['tick']%8==0 else -1 if not wet and w['tick']%8==0 else 0))
                if before!=n.get('form'):
                    n['history']=(n.get('history',[])+[dict(tick=w['tick'],change=before+' becomes '+n['form']+'; identity and mass persist')])[-16:];note(w,n['id']+' changes from '+before+' to '+n['form']+'.')
        step(w,f)
        photonics.step(w,f,c)
        machines.step(w,f,c)
    if data.get('carried_tick')!=w['tick']:
        owners={n['owner'] for n in data['carried'].values()}
        for owner in owners:step(w,dict(objects=[n['particle'] for n in data['carried'].values() if n['owner']==owner],last_tick=-1))
        data['carried_tick']=w['tick']


def coupling(w,c,engine):
    f=ensure(w)['fields'].get('base:'+engine.key(c['x'],c['y']))
    if not f:return dict(moisture=0,stress=0,growth=0)
    m=f['metrics'];light=photonics.coupling(f,c)
    return dict(moisture=int(m['eunix']>=3 and m['ras']>=55),stress=int(m['radiant']>=6)+light['stress'],growth=light['growth'])


def reconcile_sources(w):
    # Infrastructure wear and NPC repairs happen after the particle step. Apply
    # final source state without a second emission, cooling pass or paid input.
    for address,f in ensure(w)['fields'].items():
        if address.startswith('base:'):
            photonics.reconcile_source(f,w['cells'].get(address[5:]),w['tick'])
            vrex.reconcile(f,w['cells'].get(address[5:]))
            machines.reconcile(f,w['cells'].get(address[5:]))


def optical_node(c, identity, engine):
    node=photonics.source(c,identity)
    engine.require(node is not None and node['kind']=='workshop','Choose a registered workshop in this local field.')
    return node


def optical_record(w,c,p,node,op,ok,text):
    engine_record=dict(actor=p['id'],action=op,success=ok)
    import infrastructure
    infrastructure.record(w,c['infrastructure'],p['name']+': '+text,node)
    # Optical work is attributable, but is not a repair proof for a contract.
    c['infrastructure']['ledger'][-1].update(engine_record)
    node['ledger'][-1].update(engine_record)


def parse(text):
    value=text.strip().lower();exact={'inspect particles':'particle_survey','survey particles':'particle_survey','excite particles':'particle_excite','prepare void expedition':'void_prepare','enter void_null':'void_enter','return from void':'void_return','retreat void':'void_back'}
    if value in exact:return dict(action=exact[value],target='')
    if value=='quench resonance':return dict(action='particle_quench',target='')
    if value=='audit resonance':return dict(action='particle_audit',target='')
    for command,action in [('pump vrex','vrex_pump'),('stop vrex','vrex_stop'),('expand vrex','vrex_expand'),('perturb vrex','vrex_perturb'),('test vrex','vrex_diagnose')]:
        if value==command:return dict(action=action,target='')
    m=re.fullmatch(r'configure vrex (static|modulated|loaded|returned|gain)',value)
    if m:return dict(action='vrex_configure',target=m[1])
    m=re.fullmatch(r'stimulus vrex (0\.14|0\.28|0\.42) (1\.7|1\.8|1\.9)',value)
    if m:return dict(action='vrex_stimulus',target=m[1]+':'+m[2])
    m=re.fullmatch(r'tune spectrum (jade|amber|cyan|rose|violet) (steady|alternating|boundary)',value)
    if m:return dict(action='particle_tune',target=m[1]+':'+m[2])
    m=re.fullmatch(r'(sample|deposit) particle (p-[a-f0-9]{12})',value)
    if m:return dict(action='particle_'+m[1],target=m[2])
    m=re.fullmatch(r'advance void ([012])',value)
    if m:return dict(action='void_step',target=m[1])
    return None


def describe(w,p,engine):
    f=field(w,p,engine);s=p['percept'];m=f['metrics'];depth=len(s['path']);g=engine.rng(w['seed'],'apogean-description',f['address'])
    shapes=['a shell whose chambers repeat inside their own walls','a forked monolith opening onto smaller, equally immense spires','a lattice of water and polished metal with no visible terminal edge','a staircase that folds around a luminous central absence']
    return f"void_null / depth {depth}. {g.choice(shapes).capitalize()}. The contour is tangible: three branching interacts lead onward, and the recorded return trace remains accessible. {m['count']} individually registered particles sustain this local reading; RAS {m['ras']:.1f}, phase coherence {m['phase_coherence']:.1f}. Armor {s['armor']}, Immunix {s['immunix']}, perceptual strain {s['strain']}. The retained world anchor is {s['anchor']}."


def handle(w,p,intent,raw,engine):
    data=ensure(w,p);c=engine.local(w,p);s=p['percept'];op=intent['action'];context=dict(action=op,faction=engine.REGIONS[c['region']]['faction'])
    if op.startswith('vrex_'):
        engine.require(not s['address'],'Return through the recorded trace for baseline VREX systems.')
        f=field(w,p,engine);engine.require(not f.get('unresolved_reason'),f.get('unresolved_reason',''))
        target=intent.get('target','');node=None;values=target
        if '|' in target:identity,values=target.split('|',1);node=optical_node(c,identity,engine)
        elif op not in {'vrex_configure','vrex_stimulus'} and target:node=optical_node(c,target,engine)
        current=f.get('vrex',{})
        node=node or photonics.source(c,current.get('source_node')) or photonics.workshop(c,p['local']['pos'])
        if op=='vrex_diagnose':
            engine.require(current,'Configure or excite VREX before running its diagnostics.')
            engine.require(node is not None,'A registered local workshop is required for VREX diagnostics.')
            context['faction']=node['faction'];ok,roll=engine.check(w,p,'percept',11,'light',context)
            report=vrex.diagnostics(current);current['diagnostic_serial']+=1
            report.update(tick=w['tick'],field=f['address'],actor=p['id'],workshop=node['id'],engine_version=engine.VERSION,
                source_sha256=research.PROTOCOL['source']['sha256'],
                run_id='vrex-test-'+str(current['diagnostic_serial']),interpretation=ok,
                stimulus=copy.deepcopy(current['parameters']))
            current['diagnostics']=report
            text='VREX systems tests: convergence '+report['convergence']['status']+', topology '+report['topology']['status']+', passive load '+report['load']['status']+'. Collective subharmonic screening: '+report['order']['status']+'. Live energy and state were retained. '
            text+='The numerical readings are interpretable.' if ok else 'The readings are retained; interpretation remains uncertain.'
            if p['remote']:text='UNVERIFIED REMOTE PROJECTION. '+text
            optical_record(w,c,p,node,op,ok,text)
            return dict(text=text,mechanics=roll,time_spent=False)
        engine.require(not p['remote'] and not engine.tactical.active(c),'Return to physical exploration before VREX work.')
        if op=='vrex_configure':engine.require(values in vrex.PRESETS,'Choose a displayed VREX preset.')
        if op=='vrex_stimulus':engine.require(values in {a+':'+b for a in ['0.14','0.28','0.42'] for b in ['1.7','1.8','1.9']},'Choose displayed finite VREX force and frequency settings.')
        reason=vrex.source_reason(f,c,p,op,node);engine.require(not reason,reason)
        if op=='vrex_pump':engine.require(sum(bool(n.get('vrex',{}).get('running')) for n in data['fields'].values())<8 or current.get('running'),'Eight VREX drives are already active; stop one before starting another.')
        context['faction']=node['faction'];v=vrex.ensure(f,w['seed'])
        ok,roll=engine.check(w,p,'tech',10 if op=='vrex_stop' else 12 if op in {'vrex_configure','vrex_stimulus','vrex_expand'} else 11,'light',context)
        if op=='vrex_pump':
            c['infrastructure']['stores']['power']-=1;vrex.pump(v,ok,node)
            text='One public power was metered into VREX. '+('The finite drive is running.' if ok else 'Excitation became heat; the existing state is retained.')
        elif not ok:text='VREX adjustment did not hold; the measured state remains.'
        elif op=='vrex_configure':v.update(preset=values,source_node=node['id']);text='VREX preset '+values+' configured. Pump it to supply the drive.'
        elif op=='vrex_stimulus':
            force,frequency=map(float,values.split(':'));v['parameters'].update(force=force,drive_omega=frequency);v['source_node']=node['id']
            text='VREX stimulus set to force '+str(force)+' / angular frequency '+str(frequency)+'. Phase is continuous; all resulting drive work is metered.'
        elif op=='vrex_stop':vrex.stop(v);text='VREX stored mechanics and reservoir were dissipated into heat. The particle identities and measurements remain.'
        elif op=='vrex_expand':vrex.expand(v);text='VREX local generation extended to '+str(len(v['states']))+' unique states; retained states keep their identities.'
        else:count=vrex.perturb(v);text='VREX disturbed '+str(count)+' dialogue links. Local recovery will proceed without an evaluator reference.'
        vrex.event(v,w['tick'],op,p['id'],ok);optical_record(w,c,p,node,op,ok,text);note(w,p['name']+': '+text)
        return dict(text=text,mechanics=roll,time_spent=True)
    if op=='particle_audit':
        engine.require(not s['address'],'Return through the recorded trace to audit a baseline workshop.')
        f=field(w,p,engine);engine.require(not f.get('unresolved_reason'),f.get('unresolved_reason',''))
        identity=intent.get('target','')
        node=optical_node(c,identity,engine) if identity else photonics.source(c,photonics.ensure(f)['source_node'])
        if node is None:
            nodes=[n for n in c['infrastructure']['nodes'] if n['kind']=='workshop']
            node=min(nodes,key=lambda n:photonics.hexgrid.distance(p['local']['pos'],n['pos'])) if nodes else None
        engine.require(node is not None and node['kind']=='workshop','A registered local workshop is required for a systems measurement.')
        context['faction']=node['faction'];ok,roll=engine.check(w,p,'percept',11,'light',context)
        record=research.capture(w,f,p,node,ok);audit=record['energy_audit'];residual=audit['normalized_residual']
        text=f"Systems {record['id']} at {node['id']}: optical game ledger {audit['status']}; normalized residual "+(format(residual,'.3g') if residual is not None else 'unresolved')+'. '
        text+='VREX model ledger '+record['vrex_energy']['status']+'. Systems diagnostics: '+record['convergence']+'. Legacy detector: NOT REPRODUCED. '
        text+='The source, declared units and operator record are distinguishable.' if ok else 'The measured record is retained; interpretation remains uncertain.'
        if p['remote']:text='UNVERIFIED REMOTE PROJECTION. '+text
        optical_record(w,c,p,node,op,ok,text)
        return dict(text=text,mechanics=roll,time_spent=False)
    if op in {'particle_survey','look','inspect','listen','map'}:
        if op=='particle_survey' and intent.get('target'):
            engine.require(not s['address'],'Return through the recorded trace to inspect a baseline workshop.')
            node=optical_node(c,intent['target'],engine);context['faction']=node['faction']
            f=field(w,p,engine);ok,roll=engine.check(w,p,'percept',10,'light',context)
            if f.get('unresolved_reason'):
                return dict(text=node['name']+' ['+node['id']+']. '+f['unresolved_reason'],mechanics=roll,time_spent=False)
            ph=photonics.public(copy.deepcopy(f),c,p)
            text=f"{node['name']} [{node['id']}]: shared field resonance {ph['band']} / {ph['mode']}; assigned source {ph['source_node'] or 'none'}. "
            text+=f"Input {ph['input_energy']:.3f} = stored {ph['energy']:.3f} + emitted {ph['emitted_energy']:.3f} + heat {ph['heat_energy']:.3f}. "
            text+='The source and material response are distinguishable.' if ok else 'The registered ledger remains readable; source interpretation is uncertain.'
            if p['remote']:text='UNVERIFIED REMOTE PROJECTION. '+text
            return dict(text=text,mechanics=roll,time_spent=False)
        f=field(w,p,engine);ok,roll=engine.check(w,p,'percept',10,'nullsurvey' if s['address'] else 'archive',context)
        text=describe(w,p,engine) if s['address'] else f.get('unresolved_reason') or f"{f['address']}: {len(f['objects'])} persistent particles; RAS {f['metrics']['ras']:.1f}, mass {f['metrics']['mass']:.5f}. Their current forms and movements are registered."
        return dict(text=text+(' You resolve the measured interaction pattern.' if ok else 'Measured state remains accessible; deeper interpretation is uncertain.'),mechanics=roll,time_spent=False)
    engine.require(not p['remote'] and not engine.tactical.active(c),'Return to physical exploration before particulate work.')
    if op in {'void_return','void_back','return'}:
        engine.require(s['address'],'You are already in the baseline field.')
        ok,roll=engine.check(w,p,'percept',8,'nullsurvey',context)
        if op=='void_back' and s['path']:
            s['path'].pop();s['address']='void:'+engine.key(*s['anchor'])+':'+'.'.join(s['path']);s['strain']=max(0,s['strain']-3)
            materialize(w,s['address'],engine);text=describe(w,p,engine)
        else:s.update(address=None,path=[],anchor=None,strain=0);text='The recorded return trace brings you to your retained world anchor. Your carried particles and their identities remain.'
        return dict(text=text+(' The route reading holds.' if ok else 'You follow the retained trace despite an uncertain reading.'),mechanics=roll,time_spent=True)
    if op=='void_prepare':
        engine.require(not s['address'],'Prepare protection in the baseline field.')
        engine.require('black.dot' in p['credentials'],'Register the bounded field scope before requesting a Life-String expedition kit.')
        engine.require(c['shelter'] and any(n['kind']=='workshop' and n['condition']>=30 and n['enabled'] for n in c['infrastructure']['nodes']),'Prepare at a sheltered field with a maintained workshop.')
        engine.require(w['reputation'].get(context['faction'],0)+p['personal_reputation'].get(context['faction'],0)>=0,'Repair your local faction standing before requesting this scoped exchange.')
        engine.require(p['inventory']['scrap']>=3 and p['inventory']['water']>=1,'Preparation reserves three scrap and one water.')
        engine.require(s['armor']<100 or s['immunix']<12,'This expedition kit is already fully prepared.')
        p['inventory']['scrap']-=3;p['inventory']['water']-=1;ok,roll=engine.check(w,p,'tech',11,'needlurgy',context)
        if ok:s['armor']=min(100,s['armor']+40);s['immunix']=min(12,s['immunix']+2)
        text='Life-String protection gains 40 condition and two recorded Immunix doses.' if ok else 'The protective fitting needs another attempt; the reserved preparation materials were used.'
        note(w,p['name']+': '+text);return dict(text=text,mechanics=roll,time_spent=True)
    if op in {'void_enter','void_step'}:
        if op=='void_enter':engine.require(not s['address'],'You are already in void_null.')
        else:engine.require(s['address'] and intent.get('target') in {'0','1','2'},'Choose one of the three outward interacts.')
        engine.require('black.dot' in p['credentials'] and s['armor']>=5 and s['immunix']>=1,'An outward interact needs registered scope, five armor condition and one Immunix dose. Your return trace remains available without them.')
        path=[] if op=='void_enter' else s['path']+[intent['target']];anchor=p['pos'][:] if op=='void_enter' else s['anchor'][:]
        address='void:'+engine.key(*anchor)+':'+'.'.join(path)
        engine.require(address in data['fields'] or len(data['fields'])<MAX_FIELDS,'The particle archive budget is full; return traces remain available.')
        s['armor']-=5;s['immunix']-=1;ok,roll=engine.check(w,p,'percept',11+min(4,len(path)//3),'nullsurvey',dict(**context,modifier=-min(2,s['strain']//20),reason='perceptual strain'))
        s['strain']=min(100,s['strain']+(2 if ok else 8));s.update(address=address,path=path,anchor=anchor)
        engine.navigation.stop(p,reason='World travel stops at the void_null transition.');p['overworld']['mode']='local';materialize(w,address,engine)
        return dict(text=describe(w,p,engine),mechanics=roll,time_spent=True)
    f=field(w,p,engine);engine.require(not f.get('unresolved_reason'),f.get('unresolved_reason',''))
    if op in {'particle_tune','particle_quench','particle_excite'}:
        engine.require(not s['address'],'Return through the recorded trace for baseline optical work.')
        target=intent.get('target','');engine.require(isinstance(target,str),'Choose a displayed workshop action.')
        node=None
        if op=='particle_tune':
            if '|' in target:
                identity,target=target.split('|',1);node=optical_node(c,identity,engine)
            values=target.split(':');engine.require(len(values)==2 and values[0] in photonics.BANDS and values[1] in photonics.MODES,'Choose a displayed spectrum and response mode.')
        elif target:node=optical_node(c,target,engine)
        node=photonics.control_node(f,c,p,op,node)
        reason=photonics.control_reason(f,c,p,op,node);engine.require(not reason,reason)
        context['faction']=node['faction']
        if op=='particle_tune':
            ok,roll=engine.check(w,p,'tech',12,'light',context)
            if ok:
                ph=photonics.ensure(f);ph.update(band=values[0],mode=values[1],source_node=node['id']);photonics.measure(f,c)
            text=('The optical rig holds '+values[0]+' / '+values[1]+'. Pump it with stored public power to produce a finite response.' if ok else 'The tuning did not hold. The previous optical setting remains recorded.')
        elif op=='particle_quench':
            ok,roll=engine.check(w,p,'tech',10,'light',context)
            text=('The controller diverts '+format(photonics.quench(f),'.3f')+' stored optical units into heat.' if ok else 'The manual quench did not hold; the finite response continues to decay.')
        else:
            c['infrastructure']['stores']['power']-=1;ok,roll=engine.check(w,p,'tech',11,'light',context)
            photonics.pump(f,ok,node)
            if ok:
                for n in f['objects']:n['phase']=(n['phase']+.3)%math.tau;n['velocity']['x']+=.03
                f['external_drive_units']=f.get('external_drive_units',0)+1;measure(f)
            text='One public power was used. '+('Particle phases and velocities respond to the registered drive. The optical reservoir records its accepted input and heat loss.' if ok else 'The field drive did not hold; its optical input is recorded as heat.')
        optical_record(w,c,p,node,op,ok,text);note(w,p['name']+': '+text)
        return dict(text=text,mechanics=roll,time_spent=True)
    id=intent.get('target');sample=data['carried'].get(id)
    if op=='particle_sample':
        n=next((n for n in f['objects'] if n['id']==id),None);engine.require(n is not None,'Choose a particle currently present in this field.')
        engine.require('meta_fingers' in p['loadout'] and 'black.dot' in p['credentials'],'Sampling requires installed, registered Meta-Fingers.')
        engine.require(sum(n['owner']==p['id'] for n in data['carried'].values())<5,'The instrument carries at most five individual samples.')
        ok,roll=engine.check(w,p,'tech',12,'fractech',context)
        if ok:f['objects'].remove(n);data['carried'][id]=dict(owner=p['id'],particle=n,source=f['address']);note(w,id+' transfers into '+p['name']+'\'s instrument.');measure(f)
    elif op=='particle_deposit':
        engine.require(sample is not None and sample['owner']==p['id'],'Choose a particle carried by your own instrument.')
        engine.require(len(f['objects'])<MAX_OBJECTS,'This materialized field already holds 64 particles.')
        ok,roll=engine.check(w,p,'tech',10,'fractech',context)
        if ok:f['objects'].append(sample['particle']);del data['carried'][id];note(w,id+' transfers into '+f['address']+'.');measure(f)
    else:raise ValueError('Unsupported particulate action.')
    return dict(text=('The individual particle transfers; its ID, mass and lineage persist.' if ok else 'The transfer does not hold; the particle stays in its recorded location.'),mechanics=roll,time_spent=True)


def public(w,p,engine):
    # Internal physics histories stay on the authoritative host. Exclude them
    # before copying so ordinary polling does not duplicate diagnostic archives.
    retained=field(w,p,engine)
    view={k:v for k,v in retained.items() if k not in {'vrex','research','mechanism'}}
    if 'photonics' in view:
        view['photonics']={k:v for k,v in view['photonics'].items() if k not in {'research_runs','research_serial'}}
    f=copy.deepcopy(view);data=ensure(w,p);s=p['percept']
    f['photonics']=photonics.public(f,engine.local(w,p) if not s['address'] else None,p if not s['address'] else None)
    f.update(schema=1,percept=copy.deepcopy(s),samples=[dict(id=id,**copy.deepcopy(n)) for id,n in data['carried'].items() if n['owner']==p['id']],ledger=copy.deepcopy(data['ledger'][-12:]),description=describe(w,p,engine) if s['address'] else '',budgets=dict(fields=MAX_FIELDS,objects_per_field=MAX_OBJECTS),units='abstract simulator units')
    return f


def export(w,p,engine,target=''):
    f=field(w,p,engine);engine.require(not f.get('unresolved_reason'),f.get('unresolved_reason',''))
    if target:
        n=next((n for n in f['objects'] if n['id']==target),None);engine.require(n is not None,'Choose a particle present in this field.');selected=dict(objects=[copy.deepcopy(n)]);measure(selected)
    else:selected=dict(objects=copy.deepcopy(f['objects']),metrics=copy.deepcopy(f['metrics']))
    return dict(format='Rose-info-particles',schema=1,units='abstract',seed=w['seed'],address=f['address'],tick=w['tick'],state=dict(objects=selected['objects']),metrics=selected['metrics'])


def import_objects(w,p,raw,engine):
    engine.require(p['id']==w['host'] and w['paused'],'Only the host can import particle data while the clock is paused.')
    engine.require(not p['percept']['address'] and not engine.tactical.any_active(w),'Import into a baseline field after active encounters are resolved.')
    engine.require(type(raw) is dict and raw.get('format') in {'aurora-strata','Rose-info-particles'},'Use an Aurora STRATA or Rose particle export.')
    engine.require(type(raw.get('state')) is dict,'Use a particle export containing an object state.')
    incoming=raw['state'].get('objects');engine.require(type(incoming) is list and 0<len(incoming)<=MAX_OBJECTS,'Import 1–64 individual resonance objects.')
    f=field(w,p,engine);engine.require(not f.get('unresolved_reason'),f.get('unresolved_reason',''));engine.require(len(f['objects'])+len(incoming)<=MAX_OBJECTS,'Retained and imported objects must fit the 64-particle field budget.')
    validated=[];seen=set()
    for obj in incoming:
        engine.require(type(obj) is dict and isinstance(obj.get('id'),str) and 0<len(obj['id'])<=100 and obj['id'] not in seen,'Use unique bounded particle IDs.');seen.add(obj['id'])
        n={k:obj.get(k) for k in ['mass','charge','frequency','phase','element','polarity','matterType']}
        for k,lo,hi in [('mass',.1,100),('charge',-1,1),('frequency',.1,10),('phase',0,math.tau)]:engine.require(type(n[k]) in {int,float} and math.isfinite(n[k]) and lo<=n[k]<=hi,'Particle '+k+' is outside its finite range.')
        engine.require(all(type(n[k]) is str for k in ['element','polarity','matterType']) and n['element'] in ELEMENTS and n['polarity'] in {'matter','antimatter'} and n['matterType'] in {'normal','dark'},'Choose valid particle types.')
        for k,limit in [('position',100000),('velocity',4)]:
            value=obj.get(k);engine.require(type(value) is dict and all(type(value.get(a)) in {int,float} and math.isfinite(value[a]) and abs(value[a])<=limit for a in ['x','y']),'Use finite bounded particle '+k+'.');n[k]={a:float(value[a]) for a in ['x','y']}
        n['position']['x']%=600;n['position']['y']%=400;n['name']=str(obj.get('name','imported interact'))[:80];n['history']=[];n['form']='interact';n['lineage']=dict(source_id=obj['id'],source_format=raw['format']);validated.append(n)
    canonical=json.dumps(validated,sort_keys=True,separators=(',',':'));digest=hashlib.sha256(canonical.encode()).hexdigest();data=ensure(w)
    engine.require(digest not in data['imports'],'This particle batch is already imported; its retained identities cannot be duplicated.')
    ids={n['id'] for cell in data['fields'].values() for n in cell['objects']}|set(data['carried'])
    retained=[n for cell in data['fields'].values() for n in cell['objects']]+[n['particle'] for n in data['carried'].values()]
    source_ids={n.get('lineage',{}).get('source_id') for n in retained if n.get('lineage',{}).get('source_format')==raw['format']}
    engine.require(not any(n['lineage']['source_id'] in source_ids or n['lineage']['source_id'] in ids for n in validated),'A source particle identity is already retained; import cannot duplicate it.')
    for i,n in enumerate(validated):n['id']='p-'+hashlib.sha256((digest+'|'+str(i)).encode()).hexdigest()[:12]
    engine.require(not any(n['id'] in ids for n in validated),'This import collides with a retained particle identity.')
    f['objects']+=validated;data['imported_mass']+=sum(n['mass'] for n in validated);data['imports'].append(digest);measure(f);note(w,str(len(validated))+' Aurora-compatible objects join '+f['address']+' with preserved source IDs in lineage.')
    return dict(text='Imported '+str(len(validated))+' individually persistent particles. Existing objects, game rules and permissions remain authoritative.',mechanics='',intent=dict(action='particle_import',target=''),time_spent=False)
