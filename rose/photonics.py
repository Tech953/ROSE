"""Finite powered optical response, in game units.

The energy ledger belongs to this instrument, not to Aurora's heuristic particle
forces. Spectral bands and programmed echoes are authored game approximations;
they do not implement quantum field theory or establish a time-crystalline phase.
"""
import copy
import math
import hexgrid
import infrastructure

BANDS = {
    'jade': dict(center=1.0, color=[.24, .79, .53]),
    'amber': dict(center=.75, color=[.91, .61, .27]),
    'cyan': dict(center=1.4, color=[.22, .73, .96]),
    'rose': dict(center=1.65, color=[.94, .40, .62]),
    'violet': dict(center=1.9, color=[.58, .45, .94]),
}
MODES = ('steady', 'alternating', 'boundary')
CAPACITY = 4.0


def ensure(f):
    return f.setdefault('photonics', dict(schema=1, band='cyan', mode='steady',
        drive_period=4, energy=0., input_energy=0., emitted_energy=0., heat_energy=0.,
        exposure=0., temperature=0., controller_resets=0, signal=0., source_node=None,
        last_tick=f.get('last_tick', 0), response=0., linewidth=.08, stimulated=False,
        spectrum=[], trace=[]))


def source(c, id):
    if not c or not id:
        return None
    return next((n for n in c.get('infrastructure', {}).get('nodes', []) if n['id'] == id), None)


def maintained(n, c=None):
    return bool(n and n['kind'] == 'workshop' and n['enabled'] and n['condition'] >= 30
        and n.get('connected') is not False
        and (c is None or n['id'] in infrastructure.network(c['infrastructure']))
        and n.get('status') not in {'offline', 'disconnected', 'power deficit'})


def workshop(c, pos=None):
    if not c:
        return None
    nodes=[n for n in c['infrastructure']['nodes'] if maintained(n,c)]
    return min(nodes,key=lambda n:hexgrid.distance(pos,n['pos'])) if nodes and pos is not None else next(iter(nodes),None)


def control_node(f, c, p, action, node=None):
    if node is not None:
        return node
    assigned = source(c, f.get('photonics', {}).get('source_node'))
    return (assigned if action != 'particle_tune' and assigned else
            workshop(c, p.get('local', {}).get('pos')))


def control_reason(f, c, p, action, node=None):
    """Read-only prerequisites shared by the host, inspector and object menus."""
    node = control_node(f, c, p, action, node)
    if not maintained(node, c):
        return 'Optical work needs an enabled, connected workshop with condition 30 or higher and no power deficit.'
    pos = p.get('local', {}).get('pos')
    if pos is None or hexgrid.distance(pos, node['pos']) != 1:
        return 'Approach an adjacent hex of the maintained workshop.'
    ph = f.get('photonics', {})
    if ph.get('energy', 0) > 0 and ph.get('source_node') not in {None, node['id']}:
        return 'Quench the active reservoir at its assigned workshop before using another workshop.'
    if action == 'particle_quench' and ph.get('energy', 0) <= 0:
        return 'The optical reservoir is already empty.'
    if action == 'particle_excite' and c['infrastructure']['stores']['power'] < 1:
        return 'One unit of stored public power is required.'
    return ''


def spectral_response(f, carrier, width):
    objects = f['objects']
    if not objects:
        return 0.
    weights = [n['mass'] * (1 if n['element'] == 'physical' else .65) for n in objects]
    return sum(weight * width**2 / ((carrier - n['frequency'])**2 + width**2)
        for weight, n in zip(weights, objects)) / sum(weights)


def measure(f, c=None, include_spectrum=False):
    ph = ensure(f)
    objects = f['objects']
    damage = sum(n.get('degradation', 0) for n in objects) / max(1, len(objects))
    ph['linewidth'] = min(.4, .08 + (c or {}).get('moisture', 0) * .002 + damage * .0015)
    ph['response'] = spectral_response(f, BANDS[ph['band']]['center'], ph['linewidth'])
    ph['stimulated'] = bool(objects and ph['energy'] >= .25)
    if include_spectrum:
        ph['spectrum'] = [dict(frequency=.5 + i * .05,
            response=spectral_response(f, .5 + i * .05, ph['linewidth'])) for i in range(31)]
    return ph


def pump(f, success, node=None):
    ph = ensure(f)
    ph['input_energy'] += 1.
    accepted = min(.8, CAPACITY - ph['energy']) if success else 0.
    ph['energy'] += accepted
    ph['heat_energy'] += 1. - accepted
    ph['temperature'] += 1. - accepted
    if success:
        ph['source_node'] = node['id'] if node else None
    return ph


def quench(f):
    ph = ensure(f)
    released = ph['energy']
    ph['heat_energy'] += released
    ph['temperature'] += released
    ph['energy'] = 0.
    ph['signal'] = 0.
    ph['exposure'] = 0.
    ph['controller_resets'] += 1
    ph['stimulated'] = False
    return released


def reconcile_source(f, c=None, tick=None):
    """Shut down a failed source without losing its binding or charging input."""
    ph = ensure(f)
    if ph['source_node'] and not maintained(source(c, ph['source_node']), c):
        if ph['energy'] > 0:
            quench(f)
        ph['signal'] = ph['exposure'] = 0.
        if ph['trace'] and ph['trace'][-1]['tick'] == tick:
            ph['trace'][-1].update(signal=0., exposure=0., stored=ph['energy'])


def step(w, f, c=None):
    ph = ensure(f)
    if ph['last_tick'] == w['tick']:
        return
    ph['last_tick'] = w['tick']
    measure(f, c)
    reconcile_source(f, c, w['tick'])
    energy = ph['energy']
    damage = sum(n.get('degradation', 0) for n in f['objects']) / max(1, len(f['objects']))
    loss = energy * min(.25, .03 + damage * .001 + (c or {}).get('moisture', 0) * .0004)
    available = energy - loss
    coherent = f.get('metrics', {}).get('phase_coherence', 0) / 100
    rate = .18 if ph['stimulated'] else .035
    # Boundary motion redistributes a paid reservoir. It does not create particles.
    if ph['mode'] == 'boundary':
        rate *= .9 + .1 * math.sin(math.tau * w['tick'] / ph['drive_period'])
    emitted = available * rate * ph['response'] * (.2 + .8 * coherent)
    ph['energy'] = max(0., available - emitted)
    ph['emitted_energy'] += emitted
    ph['heat_energy'] += loss
    ph['temperature'] = max(0., (ph['temperature'] + loss) * (.88 if (c or {}).get('moisture', 0) >= 35 else .96))
    sign = -1 if ph['mode'] == 'alternating' and (w['tick'] // ph['drive_period']) % 2 else 1
    ph['exposure'] = emitted
    ph['signal'] = sign * emitted
    if ph['temperature'] >= 2.5 and ph['energy'] > 0:
        quench(f)
    ph['trace'] = (ph['trace'] + [dict(tick=w['tick'], signal=ph['signal'],
        exposure=ph['exposure'], stored=ph['energy'])])[-48:]
    measure(f, c)


def public(f, c=None, p=None):
    ph = copy.deepcopy(measure(f, c, include_spectrum=True))
    ph['color'] = BANDS[ph['band']]['color'][:]
    ph['carrier'] = BANDS[ph['band']]['center']
    ph['capacity'] = CAPACITY
    ph['balance_error'] = ph['input_energy'] - ph['energy'] - ph['emitted_energy'] - ph['heat_energy']
    ph['source_online'] = maintained(source(c, ph['source_node']), c)
    for action, key in [('particle_tune','tune_reason'), ('particle_excite','excite_reason'), ('particle_quench','quench_reason')]:
        ph[key] = control_reason(f, c, p, action) if c and p else 'Return to a baseline workshop for optical work.'
    return ph


def coupling(f, c):
    ph = ensure(f)
    online = maintained(source(c, ph['source_node']), c)
    return dict(growth=int(online and ph['band'] == 'jade' and ph['exposure'] >= .04
        and c['moisture'] >= 35 and c.get('lifecycle', {}).get('soil_health', 0) >= 25),
        stress=int(online and ph['band'] in {'rose', 'violet'} and ph['exposure'] >= .12))
