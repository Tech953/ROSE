"""Bounded planar rigid-body emulation; canonical records contain no UI state.

The pipeline follows the supplied Millington and Coumans guides. Game units are
explicit, contact geometry is approximate, and integration error is reported.
"""
import copy
import math

MODEL = 'rose-planar-1'
DT = 1 / 256
MAX_BODIES = 32
MAX_SPRINGS = 32
MAX_STEPS = 256
ITERATIONS = 10
TOLERANCE = .01


def add(a, b): return [a[0]+b[0], a[1]+b[1]]
def sub(a, b): return [a[0]-b[0], a[1]-b[1]]
def scale(a, s): return [a[0]*s, a[1]*s]
def dot(a, b): return a[0]*b[0]+a[1]*b[1]
def cross(a, b): return a[0]*b[1]-a[1]*b[0]
def length(a): return math.hypot(*a)
def unit(a): return scale(a, 1/length(a)) if length(a)>1e-12 else [1., 0.]
def rotate(a, angle):
    c, s = math.cos(angle), math.sin(angle)
    return [c*a[0]-s*a[1], s*a[0]+c*a[1]]


def finite(value, low=-1e6, high=1e6):
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError('Physics values must be finite and within the local emulation bounds.')
    return float(value)


def vector(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError('A planar vector requires two finite coordinates.')
    return [finite(x) for x in value]


def new(gravity=(0., 0.)):
    return dict(schema=1, model=MODEL, time=0., gravity=vector(gravity), bodies=[], springs=[],
                ledger=dict(initial=0., input=0., external_work=0., heat=0., work=0.),
                stats=dict(steps=0, candidates=0, contacts=0, sleeping=0), last_contacts=[])


def body(s, identity, position=(0., 0.), mass=1., radius=.1, half=None,
         velocity=(0., 0.), angle=0., omega=0., restitution=.1, friction=.4,
         damping=.1, useful=0., axis=None):
    if not isinstance(identity,str) or not 0<len(identity)<=80:raise ValueError('A body needs a bounded string identity.')
    if len(s['bodies']) >= MAX_BODIES or any(b['id']==identity for b in s['bodies']):
        raise ValueError('Physics body identities must be unique within the 32-body budget.')
    mass=finite(mass, 0., 1e4); radius=finite(radius, .01, 100.)
    if 0 < mass < 1e-4:raise ValueError('Dynamic mass must be at least 0.0001 local units.')
    rail=vector(axis) if axis is not None else None
    if rail is not None and length(rail)<1e-12:raise ValueError('A rail requires a nonzero direction.')
    half=vector(half) if half is not None else None
    if half and not all(.01 <= x <= 100 for x in half): raise ValueError('Invalid box half extents.')
    inertia=mass*(sum(x*x for x in half)/3 if half else radius*radius/2)
    b=dict(id=str(identity), position=vector(position), origin=vector(position), velocity=vector(velocity),
           angle=finite(angle), origin_angle=finite(angle), omega=finite(omega, -100., 100.), mass=mass,
           inverse_mass=1/mass if mass else 0., inverse_inertia=1/inertia if inertia and axis is None else 0.,
           radius=radius, half=half, restitution=finite(restitution, 0., 1.), friction=finite(friction, 0., 2.),
           damping=finite(damping, 0., 20.), useful=finite(useful, 0., 1.),
           axis=unit(rail) if rail is not None else None, force=[0., 0.], torque=0., awake=True, quiet=0)
    if not mass: b.update(velocity=[0., 0.], omega=0., awake=False)
    if axis is not None:b.update(omega=0.,velocity=scale(b['axis'],dot(b['axis'],b['velocity'])))
    s['bodies'].append(b); s['ledger']['initial']+=kinetic(b)
    return b


def find(s, identity):
    return next(b for b in s['bodies'] if b['id']==identity)


def spring(s, a, b=None, anchor=(0., 0.), rest=0., stiffness=1., damping=.1,
           local_a=(0., 0.), local_b=(0., 0.)):
    if len(s['springs'])>=MAX_SPRINGS: raise ValueError('The local spring budget is 32.')
    find(s,a)
    if b is not None: find(s,b)
    if a==b: raise ValueError('A spring needs distinct endpoints.')
    j=dict(a=a,b=b,anchor=vector(anchor),rest=finite(rest,0.,100.),
           stiffness=finite(stiffness,0.,64.),damping=finite(damping,0.,20.),
           local_a=vector(local_a),local_b=vector(local_b))
    s['springs'].append(j);s['ledger']['initial']+=potential(s,j)
    return j


def endpoint(s,j,end):
    b=find(s,j[end]) if j[end] is not None else None
    return add(b['position'],rotate(j['local_'+end],b['angle'])) if b else j['anchor'][:]


def kinetic(b):
    return .5*b['mass']*dot(b['velocity'],b['velocity']) + (.5*b['omega']**2/b['inverse_inertia'] if b['inverse_inertia'] else 0.)


def potential(s,j):
    return .5*j['stiffness']*(length(sub(endpoint(s,j,'b'),endpoint(s,j,'a')))-j['rest'])**2


def energy(s): return sum(kinetic(b) for b in s['bodies'])+sum(potential(s,j) for j in s['springs'])


def audit(s):
    try:
        ledger=s['ledger'];stored=energy(s)
        values=[stored,*ledger.values(),s['time'],*(v for b in s['bodies'] for v in b['position']+b['velocity']+[b['angle'],b['omega']])]
        valid=all(type(x) in (int,float) and math.isfinite(x) for x in values)
        valid=valid and s['time']>=0 and all(ledger[k]>=-1e-12 for k in ['initial','input','heat','work'])
        for b in s['bodies']:
            if b['axis']:
                valid=valid and abs(cross(b['axis'],sub(b['position'],b['origin'])))<=1e-7
                valid=valid and abs(cross(b['axis'],b['velocity']))<=1e-7 and abs(b['omega'])<=1e-7
        residual=ledger['initial']+ledger['input']+ledger['external_work']-stored-ledger['heat']-ledger['work']
        normalized=abs(residual)/(sum(abs(v) for v in ledger.values())+abs(stored)+1e-12)
    except (KeyError,TypeError,ValueError,IndexError,StopIteration,OverflowError,ZeroDivisionError):
        valid=False
    if not valid:return dict(status='FAIL',reason='Invalid finite state, ledger bounds or rail geometry.',residual=None,normalized_residual=None)
    return dict(status='PASS' if normalized<=TOLERANCE else 'FAIL',residual=residual,
                normalized_residual=normalized,tolerance=TOLERANCE,stored=stored,
                input=ledger['input'],initial=ledger['initial'],external_work=ledger['external_work'],
                heat=ledger['heat'],work=ledger['work'],units='local mechanical game units')


def impulse(b,j,point=None):
    if not b['inverse_mass'] or length(j)<1e-16: return
    b['velocity']=add(b['velocity'],mobility(b,j))
    if point is not None:b['omega']+=cross(sub(point,b['position']),j)*b['inverse_inertia']
    b.update(awake=True,quiet=0)


def supply(s,identity,amount,direction=(1.,0.)):
    """Convert an owned positive work packet into exactly that kinetic increment."""
    amount=finite(amount,0.,1e4);b=find(s,identity)
    if not b['mass']:raise ValueError('Paid work requires a dynamic receiver.')
    d=vector(direction)
    if b['axis']:d=scale(b['axis'],dot(b['axis'],d))
    if length(d)<1e-12:raise ValueError('Work direction must have a nonzero component along the allowed motion.')
    d=unit(d);v=dot(b['velocity'],d)
    sign=-1. if v<0 else 1.
    jump=sign*math.sqrt(v*v+2*amount/b['mass'])-v
    impulse(b,scale(d,jump*b['mass']));s['ledger']['input']+=amount


def aabb(b):
    if b['half']:
        c, sn=abs(math.cos(b['angle'])),abs(math.sin(b['angle']))
        rx=c*b['half'][0]+sn*b['half'][1];ry=sn*b['half'][0]+c*b['half'][1]
    else:rx=ry=b['radius']
    x,y=b['position'];return [x-rx,y-ry,x+rx,y+ry]


def broadphase(s):
    ordered=sorted([(aabb(b),b) for b in s['bodies']],key=lambda pair:(pair[0][0],pair[1]['id']))
    pairs=[]
    for i,(aa,a) in enumerate(ordered):
        for bb,b in ordered[i+1:]:
            if bb[0]>aa[2]:break
            if (a['mass'] or b['mass']) and bb[1]<=aa[3] and bb[3]>=aa[1]:pairs.append((a,b))
    return pairs


def axes(b):return [rotate([1.,0.],b['angle']),rotate([0.,1.],b['angle'])]


def support(b,n):
    if not b['half']:return add(b['position'],scale(n,b['radius']))
    result=b['position'][:]
    for axis,extent in zip(axes(b),b['half']):
        value=dot(axis,n)
        if abs(value)>1e-10:result=add(result,scale(axis,extent if value>0 else -extent))
    return result


def contact(a,b):
    """Normal points A to B. Circle/box shapes share one contact convention."""
    delta=sub(b['position'],a['position'])
    if not a['half'] and not b['half']:
        distance=length(delta);depth=a['radius']+b['radius']-distance
        if depth < -1e-8:return None
        n=unit(delta);point=scale(add(support(a,n),support(b,scale(n,-1))),.5)
    elif not a['half'] and b['half']:
        local=rotate(sub(a['position'],b['position']),-b['angle']);hx,hy=b['half']
        closest=[max(-hx,min(hx,local[0])),max(-hy,min(hy,local[1]))]
        d=sub(closest,local);distance=length(d)
        if distance>1e-12:
            depth=a['radius']-distance;n=rotate(scale(d,1/distance),b['angle'])
        else:
            edge=0 if hx-abs(local[0])<hy-abs(local[1]) else 1
            outward=[0.,0.];outward[edge]=1. if local[edge]>=0 else -1.
            depth=a['radius']+b['half'][edge]-abs(local[edge]);n=rotate(scale(outward,-1),b['angle'])
            closest[edge]=outward[edge]*b['half'][edge]
        if depth < -1e-8:return None
        point=add(b['position'],rotate(closest,b['angle']))
    elif a['half'] and not b['half']:
        c=contact(b,a)
        if c is None:return None
        return dict(a=a['id'],b=b['id'],normal=scale(c['normal'],-1),point=c['point'],depth=c['depth'])
    else:
        depth=float('inf');n=None
        for axis in axes(a)+axes(b):
            ra=sum(abs(dot(axis,u))*h for u,h in zip(axes(a),a['half']))
            rb=sum(abs(dot(axis,u))*h for u,h in zip(axes(b),b['half']))
            overlap=ra+rb-abs(dot(delta,axis))
            if overlap < -1e-8:return None
            if overlap<depth:depth=overlap;n=axis if dot(delta,axis)>=0 else scale(axis,-1)
        point=scale(add(support(a,n),support(b,scale(n,-1))),.5)
    return dict(a=a['id'],b=b['id'],normal=n,point=point,depth=max(0.,depth))


def point_velocity(b,p):
    r=sub(p,b['position']);return add(b['velocity'],[-b['omega']*r[1],b['omega']*r[0]])


def mobility(b,vector):
    """Inverse-mass response respects the rail at every solver stage."""
    allowed=scale(b['axis'],dot(b['axis'],vector)) if b['axis'] else vector
    return scale(allowed,b['inverse_mass'])


def response(b,point,n):
    return dot(n,mobility(b,n))+cross(sub(point,b['position']),n)**2*b['inverse_inertia']


def effective(a,b,point,n):
    return sum(response(x,point,n) for x in (a,b))


def resolve(s,c):
    a,b=find(s,c['a']),find(s,c['b']);n,point=c['normal'],c['point']
    before=kinetic(a)+kinetic(b);rel=sub(point_velocity(b,point),point_velocity(a,point))
    speed=dot(rel,n);den=effective(a,b,point,n);j=0.
    if speed < -1e-10 and den:
        bounce=min(a['restitution'],b['restitution']) if speed<-.1 else 0.
        j=-(1+bounce)*speed/den
        impulse(a,scale(n,-j),point);impulse(b,scale(n,j),point)
        tangent=[-n[1],n[0]];rel=sub(point_velocity(b,point),point_velocity(a,point))
        tangent_den=effective(a,b,point,tangent)
        jt=-dot(rel,tangent)/tangent_den if tangent_den>1e-12 else 0.
        limit=math.sqrt(a['friction']*b['friction'])*j;jt=max(-limit,min(limit,jt))
        impulse(a,scale(tangent,-jt),point);impulse(b,scale(tangent,jt),point)
    s['ledger']['heat']+=max(0.,before-kinetic(a)-kinetic(b))
    total=dot(n,mobility(a,n))+dot(n,mobility(b,n))
    if total and c['depth']>1e-7:
        correction=scale(n,(c['depth']-1e-7)*.8/total)
        a['position']=sub(a['position'],mobility(a,correction))
        b['position']=add(b['position'],mobility(b,correction))
    return j


def _forces(s):
    result={b['id']:[add(scale(s['gravity'],b['mass']),b['force']),b['torque']] for b in s['bodies']}
    for j in s['springs']:
        pa,pb=endpoint(s,j,'a'),endpoint(s,j,'b');d=sub(pb,pa)
        f=scale(unit(d),j['stiffness']*(length(d)-j['rest']))
        for end,point,sign in [('a',pa,1),('b',pb,-1)]:
            if j[end] is None:continue
            b=find(s,j[end]);result[b['id']][0]=add(result[b['id']][0],scale(f,sign))
            result[b['id']][1]+=cross(sub(point,b['position']),scale(f,sign))
    return result


def _damp(s,h):
    for b in s['bodies']:
        before=kinetic(b);factor=math.exp(-b['damping']*h)
        b['velocity']=scale(b['velocity'],factor);b['omega']*=factor
        lost=max(0.,before-kinetic(b));s['ledger']['work']+=lost*b['useful'];s['ledger']['heat']+=lost*(1-b['useful'])
        if b['axis']:
            before=kinetic(b);b['velocity']=scale(b['axis'],dot(b['axis'],b['velocity']));b['omega']=0.
            s['ledger']['heat']+=max(0.,before-kinetic(b))
    for j in s['springs']:
        if not j['damping']:continue
        a=find(s,j['a']);b=find(s,j['b']) if j['b'] is not None else None
        pa,pb=endpoint(s,j,'a'),endpoint(s,j,'b');n=unit(sub(pb,pa))
        relative=dot(sub(point_velocity(b,pb) if b else [0.,0.],point_velocity(a,pa)),n)
        den=response(a,pa,n)
        if b:den+=response(b,pb,n)
        if not den:continue
        before=kinetic(a)+(kinetic(b) if b else 0.)
        force=relative*(1-math.exp(-j['damping']*den*h))/den
        impulse(a,scale(n,force),pa)
        if b:impulse(b,scale(n,-force),pb)
        s['ledger']['heat']+=max(0.,before-kinetic(a)-(kinetic(b) if b else 0.))


def _step(s,h):
    forces=_forces(s)
    for b in s['bodies']:
        if not b['mass']:continue
        f,torque=forces[b['id']]
        if not b['awake'] and length(f)+abs(torque)<1e-10:continue
        old=b['velocity'][:];old_omega=b['omega']
        b['velocity']=add(old,scale(mobility(b,f),h));b['omega']+=torque*b['inverse_inertia']*h
        external=add(scale(s['gravity'],b['mass']),b['force'])
        s['ledger']['external_work']+=dot(external,scale(add(old,b['velocity']),.5))*h+b['torque']*(old_omega+b['omega'])*.5*h
    _damp(s,h)
    for b in s['bodies']:
        if b['mass']:
            b['position']=add(b['position'],scale(b['velocity'],h));b['angle']=(b['angle']+b['omega']*h+math.pi)%math.tau-math.pi
            if b['axis']:b['position']=add(b['origin'],scale(b['axis'],dot(sub(b['position'],b['origin']),b['axis'])))
    contacts=[]
    for iteration in range(ITERATIONS):
        pairs=broadphase(s)
        if iteration==0:s['stats']['candidates']+=len(pairs)
        current=[c for a,b in pairs if (c:=contact(a,b)) is not None]
        if iteration==0:contacts=current
        if not current:break
        for c in current:resolve(s,c)
    s['last_contacts']=contacts[:128];s['stats']['contacts']+=len(contacts)
    # Sleep only a quiet connected set; any applied impulse wakes its receiver.
    groups=[{b['id']} for b in s['bodies'] if b['mass']]
    for j in s['springs']:
        linked=[g for g in groups if j['a'] in g or j['b'] in g]
        if len(linked)>1:
            union=set.union(*linked);groups=[g for g in groups if g not in linked]+[union]
    for group in groups:
        bs=[find(s,id) for id in sorted(group)]
        quiet=all(kinetic(b)<1e-10 and length(forces[b['id']][0])+abs(forces[b['id']][1])<1e-8 for b in bs)
        for b in bs:
            b['quiet']=b['quiet']+h if quiet else 0.;b['awake']=b['quiet']<.35
    s['stats']['sleeping']=sum(b['mass']>0 and not b['awake'] for b in s['bodies'])
    s['time']+=h;s['stats']['steps']+=1


def advance(s,duration=.5,dt=DT):
    duration=finite(duration,0.,.5);dt=finite(dt,1e-5,.05)
    forces=_forces(s);steps=max(1,math.ceil(duration/dt))
    # Bound displacement relative to collision thickness before mutating state.
    for b in s['bodies']:
        if not b['mass']:continue
        extent=min(b['half']) if b['half'] else b['radius']
        speed=length(b['velocity'])+abs(b['omega'])*length(b['half'] or [b['radius'],0.])
        speed+=(length(forces[b['id']][0])*b['inverse_mass']+abs(forces[b['id']][1])*b['inverse_inertia'])*duration
        steps=max(steps,math.ceil(speed*duration/(.35*extent)))
    if steps>MAX_STEPS:raise ValueError('Motion exceeds the bounded physics substep budget; no step was applied.')
    if not duration:return
    for _ in range(steps):_step(s,duration/steps)


def dissipate(s):
    if length(s['gravity'])>1e-12 or any(b['mass'] and (length(b['force'])>1e-12 or abs(b['torque'])>1e-12) for b in s['bodies']):
        raise ValueError('Assembly shutdown requires zero gravity and external force/torque.')
    rest=copy.deepcopy(s)
    for b in rest['bodies']:
        if b['mass']:b.update(position=b['origin'][:],angle=b.get('origin_angle',0.))
    if any(potential(rest,j)>1e-10 for j in rest['springs']):
        raise ValueError('Shutdown requires zero-potential assembly origins.')
    s['ledger']['heat']+=energy(s)
    for b in s['bodies']:
        if b['mass']:b.update(position=b['origin'][:],velocity=[0.,0.],omega=0.,angle=b.get('origin_angle',0.),awake=False,quiet=.35)
    # Production rigs are assembled with zero extension. Generic loaded springs
    # retain their rest geometry; this shutdown helper is restricted to that case.


def correlation(samples,xkey,ykey,max_lag=16,min_overlap=12):
    """Pearson cross-correlation: positive lag means Y follows X, not causality."""
    if len(samples)>2:
        spacing=samples[1]['time']-samples[0]['time']
        if spacing<=0 or any(abs(b['time']-a['time']-spacing)>1e-8 for a,b in zip(samples,samples[1:])):
            return dict(status='NONUNIFORM SAMPLING',pairs=[],peak=None)
    rows=[]
    for lag in range(-max_lag,max_lag+1):
        pairs=list(zip(samples[:len(samples)-lag],samples[lag:])) if lag>=0 else list(zip(samples[-lag:],samples[:len(samples)+lag]))
        if len(pairs)<min_overlap:continue
        xx=[a[xkey] for a,b in pairs];yy=[b[ykey] for a,b in pairs]
        mx=sum(xx)/len(xx);my=sum(yy)/len(yy)
        vx=sum((x-mx)**2 for x in xx);vy=sum((y-my)**2 for y in yy)
        if min(vx,vy)<1e-18:continue
        coefficient=sum((x-mx)*(y-my) for x,y in zip(xx,yy))/math.sqrt(vx*vy)
        rows.append(dict(lag_samples=lag,coefficient=max(-1.,min(1.,coefficient)),overlap=len(pairs)))
    if not rows:return dict(status='INSUFFICIENT VARIATION',pairs=[],peak=None)
    peak=max(rows,key=lambda r:(abs(r['coefficient']),r['overlap'],-abs(r['lag_samples'])))
    spacing=(samples[-1]['time']-samples[0]['time'])/(len(samples)-1)
    return dict(status='MEASURED',pairs=rows,peak=dict(**peak,lag_time=peak['lag_samples']*spacing),
                units='local model time',interpretation='Positive lag: response follows reference. Association is not causal proof.')
