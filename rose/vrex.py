"""VREX systems update: finite, source-bound dynamics in dimensionless game units.

RK4 integrates both coordinates and work channels; the energy residual is measured,
never repaired. Topology recovery sees local state only. Diagnostics run on isolated
copies and cannot provision energy, alter the live field, or establish laboratory facts.
"""
import copy
import hashlib
import json
import math
import random

import photonics

MODEL = 'vrex-1'
CAPACITY = 4.
MAX_STATES = 20
TRACE_LIMIT = 96
DT = 1 / 32
TICK_DURATION = .5
TOLERANCE = 1e-6
PRESETS = {
    'static': dict(modulation=0., load=0., reuptake=0., gain=0.),
    'modulated': dict(modulation=.24, load=0., reuptake=0., gain=0.),
    'loaded': dict(modulation=.24, load=.18, reuptake=0., gain=0.),
    'returned': dict(modulation=.24, load=.18, reuptake=.5, gain=0.),
    'gain': dict(modulation=.24, load=.18, reuptake=.5, gain=.08),
}
PARAMETERS = dict(omega=1., drive_omega=1.8, alpha=.15, damping=.04,
                  force=.28, coupling=.12, tether_coupling=.6, tether_damping=.03)
CHANNELS = ('drive', 'modulation', 'controller', 'return', 'load', 'dissipation', 'tether_work')


def wrap(value):
    return (value + math.pi) % math.tau - math.pi


def generator(seed):
    return random.Random(int.from_bytes(hashlib.sha256(str(seed).encode()).digest()[:16], 'big'))


def local_links(states):
    """Nearest-three rule uses no reference graph, evaluator or saved edges."""
    result = []
    for a in states:
        others = sorted((b for b in states if b['id'] != a['id']),
                        key=lambda b: (math.dist(a['X'], b['X']), b['id']))[:3]
        for b in others:
            dx, dy = b['X'][0] - a['X'][0], b['X'][1] - a['X'][1]
            result.append(dict(a=a['id'], b=b['id'], gain=math.exp(-math.hypot(dx, dy)),
                               phase=.35 * math.atan2(dy, dx)))
    return result


def new(seed, count=12, preset='loaded'):
    if type(count) is not int or not 12 <= count <= MAX_STATES or preset not in PRESETS:
        raise ValueError('Choose 12–20 states and a displayed VREX preset.')
    g = generator(seed)
    states = [dict(id='q-' + hashlib.sha256((str(seed) + ':' + str(i)).encode()).hexdigest()[:12],
                   X=[g.uniform(-1, 1), g.uniform(-1, 1)], q=0., v=0.,
                   omega=PARAMETERS['omega'] * g.uniform(.97, 1.03)) for i in range(count)]
    return dict(schema=1, model=MODEL, seed=str(seed), preset=preset, parameters=PARAMETERS.copy(),
                states=states, links=local_links(states), bank=0., s=0., u=0., k=1., phase=0.,
                time=0., last_tick=None, running=False, status='IDLE', source_node=None,
                ledger=dict(input=0., heat=0., load=0., drive=0., modulation=0., controller=0.,
                            returned=0., reuptake=0., dissipation=0., tether_work=0.),
                trace=[], observations=[], stimulus_events=[], topology_events=0, diagnostics=None, diagnostic_serial=0)


def ensure(f, seed):
    if 'vrex' not in f:
        v=new(str(seed)+'|'+f['address'])
        for state, particle in zip(v['states'],f['objects']):
            state['particle_id']=particle['id']
            state['X']=[particle['position']['x']/300-1,particle['position']['y']/200-1]
        v['links']=local_links(v['states']); f['vrex']=v
        observe(f,f.get('last_tick',0))
    return f['vrex']


def observe(f,tick,replace=False):
    """Join real field and VREX measurements by retained source identity."""
    v=f.get('vrex')
    if not v:return
    if v['observations'] and v['observations'][-1]['tick']==tick:
        if not replace:return
        v['observations'].pop()
    objects={p['id']:p for p in f['objects']}; previous=v['observations'][-1] if v['observations'] else None
    prior={row['id']:row for row in previous['particles']} if previous else {}; rows=[]
    cycles=tick-previous['tick'] if previous else 0
    for state in v['states']:
        particle=objects.get(state.get('particle_id')); old=prior.get(state['id']); phase=None
        if abs(state['q'])+abs(state['v'])>1e-12:phase=math.atan2(-state['v'],state['omega']*state['q'])
        row=dict(id=state['id'],particle_id=state.get('particle_id'),present=particle is not None,
            q=state['q'],v=state['v'],model_phase=phase,kinetic=.5*state['v']**2,
            oscillator_energy=.5*state['v']**2+.5*state['omega']**2*state['q']**2+.25*v['parameters']['alpha']*state['q']**4,
            amplitude=math.hypot(state['q'],state['v']/state['omega']),
            particle_phase=particle['phase'] if particle else None,
            particle_position=copy.deepcopy(particle['position']) if particle else None,
            particle_kinetic=.5*particle['mass']*sum(a*a for a in particle['velocity'].values()) if particle else None,
            particle_frequency=particle['frequency'] if particle else None,
            phase_residual=wrap(phase-particle['phase']) if particle and phase is not None else None,
            observed_particle_rate=None,observed_model_rate=None)
        if cycles and old:
            if particle and old['particle_phase'] is not None:row['observed_particle_rate']=wrap(particle['phase']-old['particle_phase'])/cycles
            if phase is not None and old['model_phase'] is not None:row['observed_model_rate']=wrap(phase-old['model_phase'])/(cycles*TICK_DURATION)
        rows.append(row)
    v['observations']=(v['observations']+[dict(tick=tick,time=v['time'],particles=rows,
        units=dict(particle_rate='radians per world cycle',model_rate='radians per VREX time unit',
            particle_kinetic='heuristic particle game units',oscillator_energy='VREX game units'),
        sampling='Wrapped phase differences; angular changes above pi between samples alias.')])[-TRACE_LIMIT:]


def event(v,tick,action,actor,success):
    v['stimulus_events']=(v['stimulus_events']+[dict(tick=tick,action=action,actor=actor,success=bool(success),
        force=v['parameters']['force'],drive_omega=v['parameters']['drive_omega'],preset=v['preset'],
        input=v['ledger']['input'],source_node=v['source_node'])])[-32:]


def energy(v):
    p = v['parameters']; mean = sum(n['q'] for n in v['states']) / len(v['states'])
    return (sum(.5 * n['v']**2 + .5 * n['omega']**2 * n['q']**2 + .25 * p['alpha'] * n['q']**4
                for n in v['states']) + .5 * v['u']**2 + .5 * v['k'] * v['s']**2
            + .5 * p['tether_coupling'] * (mean - v['s'])**2)


def audit(v):
    """Read-only balance of the owned reservoir, mechanics, load and losses."""
    if v is None:
        return dict(status='EMPTY', residual=0., normalized_residual=0., stored=0., input=0., load=0., heat=0., units='VREX game units')
    try:
        values = [v['bank'], energy(v), *v['ledger'].values(), v['k'],v['s'],v['u'],v['phase'],v['time'],
                  *(x for n in v['states'] for x in [n['q'],n['v'],n['omega']])]
        valid = all(type(x) in (float, int) and math.isfinite(x) for x in values)
        valid = valid and 0 <= v['bank'] <= CAPACITY + 1e-9 and v['k'] > 0
        valid = valid and all(v['ledger'][key] >= -1e-12 for key in v['ledger'] if key != 'tether_work')
        stored = v['bank'] + energy(v)
        residual = v['ledger']['input'] - stored - v['ledger']['load'] - v['ledger']['heat']
        norm = abs(residual) / (v['ledger']['input'] + stored + v['ledger']['load'] + v['ledger']['heat'] + 1e-12)
        valid = valid and math.isfinite(norm)
    except (KeyError, TypeError, OverflowError, ZeroDivisionError):
        valid = False
    if not valid:
        return dict(status='FAIL', residual=None, normalized_residual=None, units='VREX game units', reason='Invalid finite state or ledger bounds.')
    return dict(status='FAIL' if norm > TOLERANCE else 'PASS' if v['ledger']['input'] else 'EMPTY',
                residual=residual, normalized_residual=norm, tolerance=TOLERANCE,
                stored=stored, input=v['ledger']['input'], load=v['ledger']['load'], heat=v['ledger']['heat'],
                units='VREX game units')


def phases(v):
    return [math.atan2(-n['v'], n['omega'] * n['q']) for n in v['states'] if abs(n['q']) + abs(n['v']) > 1e-12]


def coherence(v):
    pp = phases(v)
    return math.hypot(sum(math.cos(p) for p in pp), sum(math.sin(p) for p in pp)) / len(pp) if pp else 0.


def loops(v):
    edges = {(n['a'], n['b']): n for n in v['links']}; ids = sorted(n['id'] for n in v['states']); result = []
    for i, a in enumerate(ids):
        for b in ids[i+1:]:
            for c in ids:
                if c <= a or c == b or not all(pair in edges for pair in [(a,b),(b,c),(c,a)]):
                    continue
                orbit = [edges[a,b], edges[b,c], edges[c,a]]
                result.append(dict(members=[a,b,c], gain=math.prod(e['gain'] for e in orbit),
                                   phase=wrap(sum(e['phase'] for e in orbit))))
    return result[:80]


def recover(v, amount=.2):
    """Blind local relaxation; identity and X are retained, reference is absent."""
    known = {(e['a'], e['b']): e for e in v['links']}; result = []
    for target in local_links(v['states']):
        edge = known.get((target['a'], target['b']))
        if edge is None:
            edge = dict(a=target['a'], b=target['b'], gain=0., phase=0.)
        edge['gain'] += amount * (target['gain'] - edge['gain'])
        edge['phase'] = wrap(edge['phase'] + amount * wrap(target['phase'] - edge['phase']))
        result.append(edge)
    v['links'] = result


def perturb(v):
    g = generator(v['seed'] + '|perturb|' + str(v['topology_events']))
    selected = g.sample(range(len(v['links'])), max(1, math.ceil(.4 * len(v['links']))))
    v['links'] = [dict(e, phase=wrap(e['phase'] + g.uniform(.6, 2.5)), gain=e['gain']*.2)
                  if i in selected else e for i, e in enumerate(v['links']) if i not in selected[::2]]
    v['topology_events'] += 1
    return len(selected)


def expand(v):
    if len(v['states']) >= MAX_STATES:
        raise ValueError('The VREX local graph has reached its twenty-state budget.')
    # New zero-energy states may change the mean coupling coordinate only at rest.
    if v['running'] or v['bank'] + energy(v) > 1e-12:
        raise ValueError('Stop and dissipate VREX before extending its local graph.')
    count = min(MAX_STATES, len(v['states']) + 2)
    fresh = new(v['seed'], count, v['preset'])
    v['states'].extend(fresh['states'][len(v['states']):])
    v['links'] = local_links(v['states']); v['topology_events'] += 1


def _vector(v):
    return [x for n in v['states'] for x in [n['q'], n['v']]] + [v['s'], v['u'], v['k'], v['phase']] + [0.] * len(CHANNELS)


def _derivative(y, v, powered, coupling=True):
    n = len(v['states']); p = v['parameters']; cfg = PRESETS[v['preset']]
    q = y[:2*n:2]; vel = y[1:2*n:2]; s, u, k, phase = y[2*n:2*n+4]; mean = sum(q)/n
    force = p['force'] * math.cos(phase) if powered else 0.
    controller = [cfg['gain'] * math.tanh(a) if powered else 0. for a in vel]
    acceleration = [-(node['omega']**2)*q[i] - p['alpha']*q[i]**3 - p['damping']*vel[i]
                    + force + controller[i] - p['tether_coupling']*(mean-s)/n
                    for i, node in enumerate(v['states'])]
    diffusion = 0.; lookup = {node['id']: i for i, node in enumerate(v['states'])}
    if coupling:
        for edge in v['links']:
            a, b = lookup[edge['a']], lookup[edge['b']]
            friction = p['coupling'] * edge['gain'] / 6
            dv = vel[a] - vel[b]; acceleration[a] -= friction*dv; acceleration[b] += friction*dv
            diffusion += friction*dv*dv
    kd = cfg['modulation'] * p['drive_omega'] * math.cos(phase) if powered else 0.
    pd = force * sum(vel); pm = .5 * kd * s*s; pc = sum(a*b for a,b in zip(controller,vel))
    loss = p['damping']*sum(a*a for a in vel) + p['tether_damping']*u*u + diffusion
    result = [x for pair in zip(vel, acceleration) for x in pair]
    result += [u, -k*s - (cfg['load']+p['tether_damping'])*u + p['tether_coupling']*(mean-s), kd,
               p['drive_omega'] if powered else 0.]
    result += [max(0., pd), max(0., pm), max(0., pc), max(0., -pd)+max(0., -pm), cfg['load']*u*u,
               loss, -k*s*u]
    return result


def integrate(v, dt, powered=True, coupling=True):
    """Fourth-order step; work terms are integrated through the same stages."""
    y = _vector(v)
    def add(a, b, scale): return [x + scale*z for x,z in zip(a,b)]
    k1 = _derivative(y,v,powered,coupling); k2 = _derivative(add(y,k1,dt/2),v,powered,coupling)
    k3 = _derivative(add(y,k2,dt/2),v,powered,coupling); k4 = _derivative(add(y,k3,dt),v,powered,coupling)
    yy = [a + dt*(b+2*c+2*d+e)/6 for a,b,c,d,e in zip(y,k1,k2,k3,k4)]
    return yy


def _apply(v, y):
    n = len(v['states'])
    for i, node in enumerate(v['states']): node.update(q=y[2*i], v=y[2*i+1])
    v['s'], v['u'], v['k'], v['phase'] = y[2*n:2*n+4]
    work = dict(zip(CHANNELS, y[2*n+4:])); cfg = PRESETS[v['preset']]; ledger = v['ledger']
    returned = cfg['reuptake'] * work['return']
    v['bank'] += returned - work['drive'] - work['modulation'] - work['controller']
    # Overflow belongs to heat exactly once; it cannot be paid input again.
    overflow = max(0., v['bank']-CAPACITY); v['bank'] -= overflow
    ledger['heat'] += work['dissipation'] + work['return'] - returned + overflow
    ledger['load'] += work['load']; ledger['returned'] += work['return']; ledger['reuptake'] += returned
    for name in ['drive','modulation','controller','dissipation','tether_work']: ledger[name] += work[name]


def advance(v, duration=TICK_DURATION, dt=DT, observer=None):
    elapsed = 0.
    while elapsed < duration - 1e-12:
        h = min(dt, duration-elapsed); powered = v['running'] and v['bank'] > 1e-12
        trial = integrate(v, h, powered)
        work = dict(zip(CHANNELS,trial[2*len(v['states'])+4:]))
        # Do not borrow from a future return within this step. Empty-bank coasting
        # freezes modulation and drive phase, with no potential-energy jump.
        if powered and sum(work[x] for x in ['drive','modulation','controller']) > v['bank']:
            v['running'] = False; powered = False; v['status'] = 'COASTING / INPUT EXHAUSTED'
            trial = integrate(v, h, False)
        _apply(v, trial); elapsed += h; v['time'] += h
        if observer is not None: observer(v,h)
    recover(v)
    v['trace'] = (v['trace'] + [dict(time=v['time'], mean=sum(n['q'] for n in v['states'])/len(v['states']),
        displacement=v['s'], coherence=coherence(v), bank=v['bank'], load=v['ledger']['load'],
        phase=v['phase'], stored=v['bank']+energy(v))])[-TRACE_LIMIT:]


def pump(v, success, node):
    v['ledger']['input'] += 1.
    accepted = min(.8, max(0., CAPACITY-v['bank'])) if success else 0.
    v['bank'] += accepted; v['ledger']['heat'] += 1.-accepted
    if success: v.update(source_node=node['id'], running=True, status='RUNNING')


def stop(v, reason='STOPPED'):
    v['ledger']['heat'] += v['bank'] + energy(v); v['bank'] = v['s'] = v['u'] = v['phase'] = 0.
    v['k'] = 1.; v['running'] = False; v['status'] = reason
    for n in v['states']: n['q'] = n['v'] = 0.
    if v['trace']: v['trace'][-1].update(displacement=0., mean=0., coherence=0., bank=0., stored=0.)


def source_reason(f, c, p, action, node=None):
    v = f.get('vrex'); node = node or photonics.source(c,(v or {}).get('source_node')) or photonics.workshop(c,p.get('local',{}).get('pos'))
    if not photonics.maintained(node,c): return 'VREX needs an enabled, connected workshop with condition at least 30 and no power deficit.'
    if photonics.hexgrid.distance(p['local']['pos'],node['pos']) != 1: return 'Approach an adjacent hex of the VREX workshop.'
    if v and v['bank']+energy(v) > 1e-12 and v['source_node'] not in {None,node['id']}: return 'Stop VREX at its assigned workshop before rebinding it.'
    if action == 'vrex_pump' and c['infrastructure']['stores']['power'] < 1: return 'VREX excitation requires one stored public power.'
    if action in {'vrex_configure','vrex_expand'} and v and (v['running'] or v['bank']+energy(v) > 1e-12): return 'Stop and dissipate VREX before changing its preset or state count.'
    if action == 'vrex_expand' and v and len(v['states']) >= MAX_STATES: return 'The VREX local graph has reached its twenty-state budget.'
    if action in {'vrex_stop','vrex_perturb'} and not v: return 'Configure or excite VREX at a workshop first.'
    if action == 'vrex_stop' and v and not v['running'] and v['bank']+energy(v) <= 1e-12: return 'VREX is already dissipated.'
    return ''


def reconcile(f, c):
    v = f.get('vrex')
    if v and v['source_node'] and not photonics.maintained(photonics.source(c,v['source_node']),c):
        if v['running'] or v['bank']+energy(v) > 1e-12:
            stop(v,'OFFLINE / DISSIPATED');observe(f,f.get('last_tick',0),replace=True)


def step(w, f, c, observer=None):
    v = f.get('vrex')
    if not v or v['last_tick'] == w['tick']: return
    v['last_tick'] = w['tick']; reconcile(f,c)
    if v['running'] or energy(v) > 1e-12: advance(v,observer=observer)
    elif v['links']: recover(v)
    observe(f,w['tick'])


def graph_distance(a,b):
    aa = {(e['a'],e['b']): e for e in a}; bb = {(e['a'],e['b']): e for e in b}; keys = set(aa)|set(bb)
    return sum(1. if key not in aa or key not in bb else abs(aa[key]['gain']-bb[key]['gain'])
               + abs(wrap(aa[key]['phase']-bb[key]['phase']))/math.pi for key in keys)/max(1,len(keys))


def configuration_hash(v):
    if not v:return None
    raw=dict(model=v['model'],seed=v['seed'],preset=v['preset'],parameters=v['parameters'],
        states=[{k:n[k] for k in ['id','X','omega']} for n in v['states']])
    return hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _unlimited(v, duration, dt, coupling=True):
    """Diagnostic bench has an explicitly metered external drive, no game supply."""
    remaining = duration
    while remaining > 1e-10:
        h = min(dt,remaining); y = integrate(v,h,True,coupling)
        work = dict(zip(CHANNELS,y[2*len(v['states'])+4:]))
        need = sum(work[x] for x in ['drive','modulation','controller'])
        v['ledger']['input'] += need; v['bank'] += need
        _apply(v,y); v['time'] += h; remaining -= h


def bench(template, preset=None, count=None, seed=None):
    count=count or len(template['states']);seed=seed or template['seed']
    v=new(seed,count,preset or template['preset']);v['parameters']=copy.deepcopy(template['parameters'])
    if seed==template['seed']:
        for fresh,saved in zip(v['states'],template['states']):
            fresh.update(X=saved['X'][:],omega=saved['omega'],id=saved['id'])
        v['links']=local_links(v['states'])
    return v


def _response(template, count=None, detune=1., coupling=True, offset=0., periods=24, seed=None):
    v = bench(template,count=count,seed=seed); count=len(v['states']);v['parameters']['drive_omega'] *= detune
    # Paid seed energy; perturbation is explicitly introduced as an initial state.
    for i,n in enumerate(v['states']): n['q'] = .015*math.sin(i+.7+offset); n['v'] = .015*math.cos(i+offset)
    v['ledger']['input'] = energy(v); period = math.tau/v['parameters']['drive_omega']; samples = []; coherent = []
    for j in range(periods):
        _unlimited(v,period,1/16,coupling)
        samples.append(sum(n['q'] for n in v['states'])/count); coherent.append(coherence(v))
    tail = samples[periods//2:]; variance = sum(a*a for a in tail)/len(tail)
    recurrence = lambda m: sum((tail[i]-tail[i-m])**2 for i in range(m,len(tail)))/max(1,len(tail)-m)/(variance+1e-12)
    # DFT of the stroboscopic sequence: bin 0 is drive-periodic, .5 period-doubled.
    spectrum = [dict(ratio=j/len(tail), power=abs(sum(a*complex(math.cos(-math.tau*j*i/len(tail)),
                   math.sin(-math.tau*j*i/len(tail))) for i,a in enumerate(tail)))**2/len(tail)**2)
                for j in range(len(tail)//2+1)]
    total = sum(point['power'] for point in spectrum)+1e-12
    streak=longest=0
    for i in range(2,len(tail)):
        streak=streak+1 if abs(tail[i]-tail[i-2]) < .1*math.sqrt(variance+1e-12) else 0
        longest=max(longest,streak)
    participation=sum(abs(n['q'])+abs(n['v'])>1e-4 for n in v['states'])/count
    return dict(states=count, periods=periods, detune=detune, coupling=coupling,initial_offset=offset,
                participation=participation,seed=v['seed'],
                mean_coherence=sum(coherent[-len(tail):])/len(tail), recurrence_1=recurrence(1), recurrence_2=recurrence(2),
                subharmonic_fraction=spectrum[-1]['power']/total, spectrum=spectrum,
                lifetime_periods=longest,
                energy=audit(v))


def diagnostics(v):
    """Measured tests, including negative controls. Does not change live dynamics."""
    seed = v['seed']; graph = bench(v); reference = copy.deepcopy(graph['links'])
    perturb(graph); before = graph_distance(graph['links'],reference)
    for _ in range(40): recover(graph)
    after = graph_distance(graph['links'],reference)
    rg = generator(seed+'|control')
    randomized = [dict(e,gain=rg.random(),phase=rg.uniform(-math.pi,math.pi)) for e in reference]
    control_distance = graph_distance(randomized,reference)
    # The reference changes only for evaluation; recover's API has no target input.
    loop_before = loops(graph); gauged = copy.deepcopy(graph); shifts={n['id']:rg.uniform(-3,3) for n in graph['states']}
    for e in gauged['links']: e['phase'] += shifts[e['a']]-shifts[e['b']]
    invariance = max((abs(wrap(a['phase']-b['phase'])) for a,b in zip(loop_before,loops(gauged))),default=0.)
    null = sum(-((1.02+i*.02)+(1.+i*.02))*.5*.02 for i in range(50))
    null += sum(-((1.98-i*.02)+(2.-i*.02))*.5*(-.02) for i in range(50))
    convergence=[]; solutions=[]
    for dt in [1/8,1/16,1/32]:
        probe=bench(v); _unlimited(probe,12.,dt)
        solutions.append([n['q'] for n in probe['states']]+[probe['s'],probe['u']])
        convergence.append(dict(dt=dt, audit=audit(probe), load=probe['ledger']['load'],
                                modulation=probe['ledger']['modulation'], controller=probe['ledger']['controller']))
    diff=lambda a,b:math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
    coarse=diff(solutions[0],solutions[1]); fine=diff(solutions[1],solutions[2]); ratio=coarse/(fine+1e-15)
    conv_status='PASS' if fine < 1e-4 and ratio > 4 and convergence[-1]['audit']['status']=='PASS' else 'FAIL'
    load_probe=bench(v,'returned'); _unlimited(load_probe,12.,1/32)
    gain_probe=bench(v,'gain'); _unlimited(gain_probe,12.,1/32)
    order=[_response(v),_response(v,detune=.97),_response(v,detune=1.03),
           _response(v,coupling=False),_response(v,offset=1.1),_response(v,seed=seed+'|seed-control'),_response(v,count=20)]
    candidate=lambda r:r['subharmonic_fraction']>.2 and r['recurrence_2']<.1 and r['recurrence_1']>.2
    order_status='CANDIDATE' if all(candidate(r) for r in order if r['coupling']) else 'NOT DETECTED'
    # Compare RK4 forward motion with a second-order temporal prediction.
    # This offset changes the reference, never a force or a time direction.
    offset=1/32; initial=_vector(load_probe); derivative=_derivative(initial,load_probe,True)
    future=integrate(load_probe,offset,True)
    forward=future[:2*len(load_probe['states']):2]
    reference=[n['q']+offset*n['v']+.5*offset**2*derivative[2*i+1] for i,n in enumerate(load_probe['states'])]
    repr_res=math.sqrt(sum((a-b)**2 for a,b in zip(forward,reference)))/(math.sqrt(sum(a*a for a in forward))+1e-12)
    return dict(schema=1,model=MODEL,seed=seed,preset=v['preset'],units='VREX game units',configuration_hash=configuration_hash(v),
        classification='SOFTWARE MODEL DIAGNOSTICS',convergence=dict(status=conv_status,steps=convergence,
            coarse_difference=coarse,fine_difference=fine,refinement_ratio=ratio),
        topology=dict(status='PASS' if after<before and after<control_distance and invariance<1e-10 else 'FAIL',
            perturbation_fraction=.4,reference_visible_to_dynamics=False,before=before,after=after,
            recovery_score=1-after/(before+1e-12),random_control_distance=control_distance,
            gauge_error=invariance,loop_count=len(loop_before)),
        load=dict(status='PASS' if abs(null)<1e-10 and load_probe['ledger']['load']>0 and audit(load_probe)['status']=='PASS' else 'FAIL',
            static_cycle_work=null,passive_work=load_probe['ledger']['load'],returned=load_probe['ledger']['returned'],
            reuptake=load_probe['ledger']['reuptake'],energy=audit(load_probe),
            gain_controller_work=gain_probe['ledger']['controller'],gain_energy=audit(gain_probe)),
        order=dict(status=order_status,runs=order,interpretation='Finite driven Duffing network screening; a candidate is not a verified many-body DTC.'),
        representation=dict(status='MEASURED',residual=repr_res,offset=offset,
            scope='RK4 forward positions versus second-order temporal prediction; no temporal force'),
        sustained=dict(status='PASS' if all(r['energy']['status']=='PASS' for r in order) else 'FAIL',
            periods=24,scope='Metered diagnostic input over 24 drive periods; finite game bank still exhausts.'),
        laboratory=dict(status='NOT RUN',reason='No physical apparatus or calibration is attached.'))


def public(f,c,p):
    v=f.get('vrex'); result=copy.deepcopy(v) if v else dict(schema=1,model=MODEL,status='NOT CONFIGURED',
        preset='loaded',states=[],links=[],trace=[],diagnostics=None,source_node=None,bank=0.,ledger={})
    result.update(audit=audit(v),capacity=CAPACITY,max_states=MAX_STATES,presets=list(PRESETS),
                  coherence=coherence(v) if v else 0.,loops=loops(v) if v else [],units='VREX game units')
    result['diagnostics_stale']=bool(v and v['diagnostics'] and v['diagnostics'].get('configuration_hash')!=configuration_hash(v))
    baseline='Return through the recorded trace for baseline VREX systems.' if p.get('percept',{}).get('address') else f.get('unresolved_reason','')
    result['reasons']={action:baseline or source_reason(f,c,p,action) for action in
        ['vrex_configure','vrex_stimulus','vrex_pump','vrex_stop','vrex_expand','vrex_perturb']}
    result['reasons']['vrex_diagnose']=baseline or ('Configure or excite VREX before running its diagnostics.' if not v else '')
    return result
