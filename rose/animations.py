"""Bounded presentation cues from committed actions, not a second simulation."""
import copy
import math

import hexgrid as hx

LIMIT = 96
STEP_MS = 360
DURATIONS = dict(idle=1280, walk=STEP_MS, attack=870, guard=640, work=720, talk=960, hit=540, down=1000)


def ensure(s):
    return s.setdefault('animation', dict(schema=1, serial=0, events=[]))


def emit(s, kind, subject, duration_ms, **payload):
    if type(duration_ms) is not int or not 0 <= duration_ms <= 36000:
        raise ValueError('Animation duration must be a bounded integer.')
    data = ensure(s); data['serial'] += 1
    row = dict(id=data['serial'], kind=kind, subject=str(subject), duration_ms=duration_ms, **copy.deepcopy(payload))
    data['events'] = (data['events'] + [row])[-LIMIT:]
    return row


def facing(source, target):
    if source == target: return 0
    delta=[target[i]-source[i] for i in range(2)]
    # Convert axial directions into the ground plane before finding a heading.
    xy=[math.sqrt(3)*(delta[0]+delta[1]/2),1.5*delta[1]]
    directions=[[math.sqrt(3)*(q+r/2),1.5*r] for q,r in hx.DIRS]
    return max(range(6),key=lambda n:sum(xy[i]*directions[n][i] for i in range(2)))


def pose(s, subject, animation, trail=None):
    path=copy.deepcopy(trail or [subject['local']['pos']])
    duration=DURATIONS.get(animation,720)*(max(1,len(path)-1) if animation=='walk' else 1)
    duration=min(36000,duration)
    return emit(s,'move' if animation=='walk' and len(path)>1 else 'pose',subject['id'],duration,
                pose=animation,path=path,facing=subject['local'].get('facing',0))


def strike(s, actor, source, target, destination, damage, ranged=False, material='metal', reactions=None):
    if type(damage) is not int or damage < 0:
        raise ValueError('Animation impact must follow a committed damage result.')
    reactions=copy.deepcopy(reactions or [])
    if len(reactions)>2 or any(type(row['damage']) is not int or row['damage']<0 for row in reactions):
        raise ValueError('A strike supports at most two additional committed reactions.')
    cue=emit(s,'strike',actor,DURATIONS['attack'],pose='attack',source=list(source),
             target=target,destination=list(destination),damage=damage,hit=damage>0,
             ranged=bool(ranged),facing=facing(source,destination),material=material,reactions=reactions,
             contact_ms=435 if not ranged else 360+min(200,hx.distance(source,destination)*24))
    return cue


def collapse(s, selector, obj):
    state=obj['material_state']
    return emit(s,'collapse',selector,1200,pos=obj['pos'][:],material=state['material'],
                visual=copy.deepcopy(obj.get('visual',{})),object_kind=obj.get('kind','rock'),
                before_condition=state.get('last_intact_condition',1))


def clear(s, selector, obj):
    return emit(s,'clear',selector,560,pos=obj['pos'][:],material=obj['material_state']['material'])


def public(s):
    return copy.deepcopy(ensure(s))
