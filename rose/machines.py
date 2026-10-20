"""Practical local mechanisms driven by owned VREX-TETHER load work.

Measurements live on the host. Public nodes expose only installed hardware and
its observable condition. A downstream receipt never becomes upstream input.
"""
import copy
import hashlib
import json
import math

import hexgrid as hx
import infrastructure
import lifecycle
import photonics
import physics
import vrex

ACTS={'machine_fit','machine_operate','machine_stop'}
MAX_RIGS=16
TRACE_LIMIT=128
VISUAL_LIMIT=33
APPLICATIONS={
    'pump':dict(label='transfer pump',stiffness=1.8,damping=1.4,useful=.65,job_work=.002),
    'press':dict(label='construction press',stiffness=4.,damping=.9,useful=.65,job_work=.003),
    'damper':dict(label='vibration damper',stiffness=1.,damping=4.,useful=0.,job_work=None),
}


def new(kind,node,actor,load_cursor=0.):
    cfg=APPLICATIONS[kind];s=physics.new()
    physics.body(s,'carriage',radius=.08,damping=cfg['damping'],useful=cfg['useful'],axis=[1.,0.])
    for side in [-1,1]:
        physics.body(s,'stop-'+str(side),position=[side*.55,0.],mass=0.,half=[.05,.25],restitution=.05)
    physics.spring(s,'carriage',anchor=[0.,0.],stiffness=cfg['stiffness'],damping=.04)
    return dict(schema=1,model='vrex-tether-mechanism-1',application=kind,node=node,
                operator=actor,engaged=False,status='idle',solver=s,load_cursor=load_cursor,
                trace=[],world_trace=[],correlations={},segments=[],configuration_hash=None,
                last_tick=None,effect_tick=None,progress=0.,work_cursor=0.,heat_cursor=0.,
                fatigue=0.,jobs=0,water_transferred=0,construction_steps=0,wear_events=0,
                receipts=0,history=[],visual_serial=0,visual_frames=[],visual_motion=None)


def visible_frame(r):
    """Only local hardware pixel poses leave the off-screen solver archive."""
    try:
        b=physics.find(r['solver'],'carriage')
        if not all(math.isfinite(x) for x in b['position']+[b['angle']]):return None
        return dict(offset=[round(x*24,4) for x in b['position']],angle=round(b['angle'],5),
                    contact=bool(r['solver']['last_contacts']),sleeping=not b['awake'])
    except (KeyError,TypeError,ValueError):return None


def publish_motion(r,parked=False):
    frames=r.get('visual_frames',[])
    if parked or not frames:
        frame=visible_frame(r)
        frames=[dict(at=0.,**frame)] if frame else []
    else:
        start,end=frames[0]['time'],frames[-1]['time'];span=max(1e-12,end-start)
        frames=[dict(at=round((f['time']-start)/span,6),**{k:v for k,v in f.items() if k!='time'}) for f in frames]
    r['visual_serial']=r.get('visual_serial',0)+1
    span=0. if parked or not r.get('visual_frames') else r['visual_frames'][-1]['time']-r['visual_frames'][0]['time']
    r['visual_motion']=dict(schema=1,serial=r['visual_serial'],duration_ms=max(0,min(4000,round(span*1000))),
                            active=bool(r['engaged'] and not parked),frames=frames[-VISUAL_LIMIT:])


def hardware(r):
    if not r.get('visual_motion'):publish_motion(r)
    return dict(kind=r['application'],label=APPLICATIONS[r['application']]['label'],status=r['status'],
                motion=copy.deepcopy(r.get('visual_motion')))


def config(f):
    rig=f['mechanism']
    raw=dict(vrex=vrex.configuration_hash(f['vrex']),application=rig['application'],model=rig['model'])
    return hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest()


def sample(f):
    r=f['mechanism'];v=f['vrex'];key=config(f)
    if r['configuration_hash']!=key:
        if r['configuration_hash']:
            r['segments']=(r['segments']+[dict(configuration_hash=r['configuration_hash'],
                correlations=copy.deepcopy(r['correlations']))])[-8:]
        r.update(configuration_hash=key,trace=[],world_trace=[],correlations={})
    b=physics.find(r['solver'],'carriage')
    row=dict(time=r['solver']['time'],mean=sum(n['q'] for n in v['states'])/len(v['states']),
             tether=v['s'],tether_velocity=v['u'],position=b['position'][0],velocity=b['velocity'][0])
    r['trace']=(r['trace']+[row])[-TRACE_LIMIT:]
    frame=visible_frame(r)
    if frame:
        r['visual_frames']=(r.get('visual_frames',[])+[dict(time=r['solver']['time'],**frame)])[-VISUAL_LIMIT:]


def transfer(f,h):
    """Called after each committed RK4 step; one monotonic source-load cursor."""
    r=f['mechanism'];v=f['vrex'];load=v['ledger']['load']
    delta=load-r['load_cursor']
    if delta < -1e-10:raise ValueError('The source load ledger moved backwards; no work can be issued.')
    r['load_cursor']=load
    if r['engaged'] and delta>0:
        physics.supply(r['solver'],'carriage',delta,[1. if v['u']>=0 else -1.,0.]);r['receipts']+=1
    physics.advance(r['solver'],h);sample(f)


def step(w,f,c):
    r=f.get('mechanism')
    if not r:
        vrex.step(w,f,c);return
    if r['last_tick']==w['tick']:return
    r['last_tick']=w['tick'];reconcile(f,c)
    initial=visible_frame(r)
    r['visual_frames']=[dict(time=r['solver']['time'],**initial)] if initial else []
    before=r['solver']['time']
    vrex.step(w,f,c,observer=lambda v,h:transfer(f,h))
    # A downstream mechanism may coast after the upstream drive has exhausted.
    if r['solver']['time']==before:
        for _ in range(16):transfer(f,vrex.DT)
    publish_motion(r,not r['engaged'])
    r['correlations']=dict(network_tether=physics.correlation(r['trace'],'mean','tether'),
        tether_mechanism=physics.correlation(r['trace'],'tether','position'))
    mapped={n.get('particle_id') for n in f['vrex']['states'] if n.get('particle_id')}
    present=[n for n in f['objects'] if n['id'] in mapped]
    if present:
        r['world_trace']=(r['world_trace']+[dict(time=float(w['tick']),
            particle_signal=sum(math.cos(n['phase']) for n in present)/len(present),
            network_signal=sum(n['q'] for n in f['vrex']['states'])/len(f['vrex']['states']),
            source_ids=sorted(n['id'] for n in present))])[-96:]
        # Identity loss changes the sampled population; never correlate across it.
        rows=r['world_trace'];tail=next((i for i in range(len(rows)-2,-1,-1) if rows[i]['source_ids']!=rows[-1]['source_ids']),-1)
        correlation=physics.correlation(rows[tail+1:],'particle_signal','network_signal',max_lag=8)
        correlation['units']='world cycles';r['correlations']['particle_network']=correlation


def shutdown(f,reason='disengaged'):
    r=f.get('mechanism')
    if not r:return
    before=(r['engaged'],r['status'],visible_frame(r))
    physics.dissipate(r['solver']);r.update(engaged=False,status=reason,progress=0.)
    r['work_cursor']=r['solver']['ledger']['work'];r['load_cursor']=f['vrex']['ledger']['load']
    if before!=(r['engaged'],r['status'],visible_frame(r)) or not r.get('visual_motion'):
        publish_motion(r,True)


def reconcile(f,c):
    r=f.get('mechanism')
    if not r:return
    node=photonics.source(c,r['node']) if c else None
    if not photonics.maintained(node,c) or f['vrex']['source_node']!=r['node']:
        shutdown(f,'offline')
    if node:node['machine']=hardware(r)


def finish(w,engine):
    """Commit world effects only after weather, NPC work and final utility wear."""
    for address,f in w.get('substrate',{}).get('fields',{}).items():
        r=f.get('mechanism')
        if not r or r['effect_tick']==w['tick']:continue
        r['effect_tick']=w['tick'];c=w['cells'].get(address[5:]) if address.startswith('base:') else None
        reconcile(f,c)
        if not c:continue
        node=photonics.source(c,r['node']);s=r['solver'];ledger=s['ledger']
        work=max(0.,ledger['work']-r['work_cursor']);heat=max(0.,ledger['heat']-r['heat_cursor'])
        r['work_cursor']=ledger['work'];r['heat_cursor']=ledger['heat']
        if not r['engaged'] or not photonics.maintained(node,c):continue
        if combined_audit(f)['status']!='PASS':
            shutdown(f,'stopped for unstable operation');vrex.stop(f['vrex'],'MECHANISM / AUDIT STOP');continue
        cfg=APPLICATIONS[r['application']];r['status']='operating' if f['vrex']['running'] else 'coasting'
        r['fatigue']+=heat*(.05 if r['application']=='damper' else 1.)
        if r['fatigue']>=.04:
            import materials
            r['fatigue']-=.04;materials.ensure_node(w,c,node)
            if materials.damage(node,1,w['tick'],'mechanical fatigue'):materials.collapse_node(w,c,node,engine)
            r['wear_events']+=1
            infrastructure.record(w,c['infrastructure'],'The fitted '+cfg['label']+' shows mechanical wear.',node)
        if node['condition']<30:
            vrex.reconcile(f,c);shutdown(f,'offline')
            node['machine']=hardware(r);continue
        if cfg['job_work']:
            r['progress']=min(cfg['job_work'],r['progress']+work)
            if r['progress']>=cfg['job_work']:
                completed=False
                if r['application']=='pump':
                    connected=infrastructure.network(c['infrastructure'])
                    receivers=[n for n in c['infrastructure']['nodes'] if n['kind']=='water' and n['enabled']
                        and n['condition']>=30 and n['id'] in connected
                        and n['status'] not in {'offline','disconnected','power deficit'}]
                    data=c['infrastructure']
                    if receivers and c['water']>0 and data['stores']['water']<data['cap']:
                        c['water']-=1;data['stores']['water']+=1;r['water_transferred']+=1;completed=True
                        infrastructure.record(w,data,'The fitted pump transfers one actual source water into the public cistern.',node)
                    else:r['status']='waiting for source water or cistern space'
                elif r['application']=='press':
                    jobs=[p for p in lifecycle.ensure(w,c)['projects'] if p['stage'] in lifecycle.LIVE
                          and p['owner']==r['operator'] and hx.distance(p['pos'],node['pos'])<=3]
                    if jobs:
                        subject=dict(id='machine:'+address+':'+r['node'],name='The fitted construction press',local=dict(pos=node['pos'][:],serial=0))
                        lifecycle.work(w,c,jobs[0],subject,engine);r['construction_steps']+=1;completed=True
                    else:r['status']='waiting for an owned nearby construction project'
                if completed:r['progress']=0.;r['jobs']+=1
        if node['condition']<30:
            vrex.reconcile(f,c);shutdown(f,'offline')
        node['machine']=hardware(r)


def reason(w,c,p,f,node,op,kind=None):
    if hx.distance(p['local']['pos'],node['pos'])!=1:return 'Approach an adjacent hex of the workshop.'
    if op=='machine_stop':
        return '' if f.get('mechanism',{}).get('node')==node['id'] else 'Fit a mechanism at this workshop first.'
    if not photonics.maintained(node,c):return 'Restore, enable and connect this workshop first.'
    v=f.get('vrex');r=f.get('mechanism')
    if op=='machine_fit':
        if v and (v['running'] or v['bank']+vrex.energy(v)>1e-12):return 'Disengage and dissipate the source drive before refitting hardware.'
        if r and physics.energy(r['solver'])>1e-12:return 'Disengage the existing mechanism before refitting it.'
        if p['inventory']['scrap']<2:return 'Fitting a mechanism consumes two personal scrap.'
        if not r and sum('mechanism' in x for x in w.get('substrate',{}).get('fields',{}).values())>=MAX_RIGS:return 'The host has reached its sixteen-mechanism budget.'
    elif not r or r['node']!=node['id']:return 'Fit a pump, press or damper at this workshop first.'
    elif v['source_node']!=node['id']:return 'The fitted mechanism needs its assigned workshop drive.'
    elif c['infrastructure']['stores']['power']<1:return 'Operation consumes one actual stored public power.'
    elif not v['running'] and sum(x.get('vrex',{}).get('running',False) for x in w.get('substrate',{}).get('fields',{}).values())>=8:return 'Eight local source drives are already active.'
    return ''


def parse(text):
    import re
    s=text.strip().lower()
    m=re.fullmatch(r'fit (?:a |the )?(pump|press|damper)(?: at (.+))?',s)
    if m:return dict(action='machine_fit',target=(m.group(2) or '')+'|'+m.group(1))
    m=re.fullmatch(r'(operate|disengage) (?:the )?machine(?: at (.+))?',s)
    if m:return dict(action='machine_operate' if m.group(1)=='operate' else 'machine_stop',target=m.group(2) or '')


def handle(w,p,intent,raw,engine):
    c=engine.local(w,p);op=intent['action'];target=intent.get('target','');identity,_,kind=target.partition('|')
    if op=='machine_fit':engine.require(kind in APPLICATIONS,'Choose pump, press or damper hardware.')
    nodes=[n for n in c['infrastructure']['nodes'] if n['kind']=='workshop']
    node=next((n for n in nodes if identity in (n['id'],n['name'])),None) if identity else min(nodes,key=lambda n:hx.distance(p['local']['pos'],n['pos']),default=None)
    engine.require(node is not None,'Choose a physical workshop in this field.')
    fields=w.get('substrate',{}).get('fields',{});address='base:'+engine.key(*p['pos']);existing=fields.get(address,{})
    engine.require(address in fields or len(fields)<engine.particles.MAX_FIELDS,engine.particles.UNRESOLVED_REASON)
    engine.require(not reason(w,c,p,existing,node,op,kind),reason(w,c,p,existing,node,op,kind))
    f=engine.particles.field(w,p,engine);v=f.get('vrex')
    skill='metallurgy' if op=='machine_fit' else 'fractech'
    if op=='machine_fit':p['inventory']['scrap']-=2
    if op=='machine_operate':c['infrastructure']['stores']['power']-=1
    ok,roll=engine.check(w,p,'tech',12 if op=='machine_fit' else 11,skill,dict(faction=node['faction'],action=op))
    if op=='machine_fit':
        if ok:
            v=vrex.ensure(f,w['seed']);v['source_node']=node['id']
            if not vrex.PRESETS[v['preset']]['load']:v['preset']='loaded'
            old=f.get('mechanism');history=(old.get('history',[])+[dict(application=old['application'],jobs=old['jobs'],energy=physics.audit(old['solver']))])[-8:] if old else []
            f['mechanism']=new(kind,node['id'],p['id'],v['ledger']['load']);f['mechanism']['history']=history
            node['machine']=dict(kind=kind,label=APPLICATIONS[kind]['label'],status='idle')
            out='You fit a '+APPLICATIONS[kind]['label']+' to the workshop. Its source drive is disengaged.'
        else:out='The fitting fails to seat. Two scrap are spent; existing hardware remains unchanged.'
    elif op=='machine_operate':
        vrex.pump(v,ok,node)
        if ok:
            f['mechanism'].update(engaged=True,operator=p['id'],status='operating')
            out='You start the fitted '+APPLICATIONS[f['mechanism']['application']]['label']+' with one stored public power.'
        else:out='The operating check fails. The supplied power is lost as heat; no new drive starts.'
    else:
        if ok:vrex.stop(v,'MECHANISM / DISENGAGED');shutdown(f);out='You disengage the mechanism. Remaining motion and stored drive dissipate; no power is refunded.'
        else:out='The disengagement check fails; the mechanism retains its operating state.'
    if ok:
        infrastructure.record(w,c['infrastructure'],p['name']+' '+op.replace('_',' ')+' at '+node['id']+'.',node)
        import scene
        scene.pose(c['scene'],p,'work')
    return dict(text=out,mechanics=roll,time_spent=True)


def combined_audit(f):
    v=f['vrex'];r=f['mechanism'];s=r['solver'];p=physics.audit(s);a=vrex.audit(v)
    if p.get('residual') is None or a.get('residual') is None:
        return dict(status='FAIL',residual=None,normalized_residual=None,tolerance=physics.TOLERANCE,
            source=a,mechanism=p,reason='Invalid source or downstream record; world effects are blocked.')
    remaining=v['ledger']['load']-s['ledger']['input']
    residual=(v['ledger']['input']+s['ledger']['initial']+s['ledger']['external_work']
        -v['bank']-vrex.energy(v)-physics.energy(s)-v['ledger']['heat']-s['ledger']['heat']-s['ledger']['work']-remaining)
    denominator=sum(abs(x) for x in [v['ledger']['input'],s['ledger']['initial'],s['ledger']['external_work'],v['bank'],vrex.energy(v),physics.energy(s),v['ledger']['heat'],s['ledger']['heat'],s['ledger']['work'],remaining])+1e-12
    norm=abs(residual)/denominator
    return dict(status='PASS' if remaining>=-1e-10 and a['status']!='FAIL' and p['status']=='PASS' and norm<=physics.TOLERANCE else 'FAIL',
        residual=residual,normalized_residual=norm,tolerance=physics.TOLERANCE,
        transfer=s['ledger']['input'],unapplied_load=remaining,source=a,mechanism=p,
        units='shared dimensionless work units',ownership='VREX load debit equals downstream input credit; it is eliminated once from the combined ledger.')


def export(w,f,version):
    if 'mechanism' not in f:raise ValueError('Fit a local mechanism before exporting its development record.')
    return dict(format='Rose-physics-emulation',schema=1,engine_version=version,tick=w['tick'],field=f['address'],
                state=copy.deepcopy(f['mechanism']),energy=combined_audit(f),configuration_hash=vrex.configuration_hash(f['vrex']),
                references='reference/physics/source-register-v013.json')


def diagnostics(template):
    """Isolated, explicitly supplied application tests; no game inventory or clock."""
    result=[]
    for kind in APPLICATIONS:
        for control in ['loaded','unloaded','no-input']:
            v=vrex.bench(template,preset='static' if control=='unloaded' else 'loaded')
            f=dict(address='diagnostic',objects=[],vrex=v,mechanism=new(kind,'bench','development'))
            r=f['mechanism'];r['engaged']=True
            for cycle in range(80):
                if control!='no-input' and cycle in (0,20,40,60):vrex.pump(v,True,dict(id='bench'))
                vrex.advance(v,observer=lambda _,h:transfer(f,h))
            correlation=physics.correlation(r['trace'],'tether','position')
            result.append(dict(application=kind,control=control,input=v['ledger']['input'],
                load=v['ledger']['load'],work=r['solver']['ledger']['work'],heat=r['solver']['ledger']['heat'],
                energy=combined_audit(f),correlation=dict(status=correlation['status'],peak=correlation['peak']),
                duration=r['solver']['time'],receipts=r['receipts']))
    return dict(schema=1,classification='ISOLATED SOFTWARE MECHANICS TEST',source_configuration=vrex.configuration_hash(template),
        status='PASS' if all(r['energy']['status']=='PASS' and
            (r['control']=='loaded' or r['load']==r['work']==0.) for r in result) else 'FAIL',
        cases=result,world_unchanged=True,units='dimensionless game units',
        scope='Four explicitly supplied diagnostic inputs per driven case; no game stock, device output, laboratory result or calibration is created.')
