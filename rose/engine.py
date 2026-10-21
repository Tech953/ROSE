"""Rose's versioned, validated generation and simulation variables."""
import copy
import json
from pathlib import Path
import art_direction
import generation

VERSION = '0.19.0'
LIMITS = {
    'generation': {'scene_radius': (5, 9), 'obstacle_density': (0, 28),
                   'infrastructure_density': (0, 100), 'population': (2, 40),
                   'starting_condition': (35, 90), 'hostility': (0, 100)},
    'infrastructure': {'cycle_ticks': (4, 24), 'wear': (1, 5),
                       'power_output': (2, 12), 'storage_cap': (10, 60), 'repair_dc': (8, 18)},
    'combat': {'base_ap': (6, 12), 'move_ap': (1, 2), 'melee_ap': (2, 5),
               'ranged_ap': (3, 6), 'guard_ap': (1, 4), 'parley_ap': (2, 5),
               'enemy_ap': (4, 10), 'trigger_distance': (1, 3)},
}
DEFAULTS = {
    'schema': 1,
    'generation': {'scene_radius': 6, 'obstacle_density': 12, 'infrastructure_density': 55,
                   'population': 8, 'starting_condition': 65, 'hostility': 20},
    'infrastructure': {'cycle_ticks': 6, 'wear': 1, 'power_output': 5,
                       'storage_cap': 30, 'repair_dc': 12},
    'combat': {'base_ap': 8, 'move_ap': 1, 'melee_ap': 3, 'ranged_ap': 4,
               'guard_ap': 2, 'parley_ap': 3, 'enemy_ap': 6, 'trigger_distance': 2},
}
PROFILES = {
    'balanced': {},
    'frontier': {'generation': {'infrastructure_density': 25, 'population': 4,
                              'starting_condition': 45, 'hostility': 35}},
    'settlement': {'generation': {'infrastructure_density': 90, 'population': 20,
                                'starting_condition': 75, 'hostility': 10}},
}
HOST_RULES = copy.deepcopy(DEFAULTS)


def validate(raw=None, base=None):
    """Partial overrides are allowed; unknown fields and booleans are rejected."""
    value = copy.deepcopy(DEFAULTS if base is None else base)
    if raw is None:
        return value
    if type(raw) is not dict or set(raw) - {'schema', *LIMITS}:
        raise ValueError('Use Rose schema 1 with generation, infrastructure and combat variables.')
    if type(raw.get('schema', 1)) is not int or raw.get('schema', 1) != 1:
        raise ValueError('Unsupported engine rules schema.')
    for group, fields in LIMITS.items():
        supplied = raw.get(group, {})
        if type(supplied) is not dict or set(supplied) - set(fields):
            raise ValueError('Unknown variables in ' + group + '.')
        for name, number in supplied.items():
            lo, hi = fields[name]
            if type(number) is not int or not lo <= number <= hi:
                raise ValueError(f'{group}.{name} must be an integer from {lo} to {hi}.')
            value[group][name] = number
    if max(value['combat'][x] for x in ['melee_ap', 'ranged_ap', 'guard_ap', 'parley_ap']) > value['combat']['base_ap']:
        raise ValueError('Base AP must support every single combat action.')
    return value


def load(path):
    global HOST_RULES
    HOST_RULES = validate(json.loads(Path(path).read_text(encoding='utf-8')))
    return copy.deepcopy(HOST_RULES)


def for_world(overrides=None, profile='balanced'):
    if profile not in PROFILES:
        raise ValueError('Choose balanced, frontier or settlement infrastructure.')
    return validate(overrides, validate(PROFILES[profile], HOST_RULES))


def catalog():
    return {'version': VERSION, 'rules': copy.deepcopy(HOST_RULES), 'limits': copy.deepcopy(LIMITS),
            'profiles': list(PROFILES), 'capabilities': ['continuous world travel', 'axial local hex scenes', 'AP combat',
            'seeded infrastructure', 'resource networks', 'persistent NPCs', 'contextual checks', 'shared state-grounded content grammar',
            'regional spectrum lighting', 'soil and planted succession', 'staged physical construction',
            'persistent info-particle identity', 'Aurora-compatible particle exchange', 'prepared void_null expeditions',
            'finite optical energy ledger', 'material spectral response', 'powered workshop projection',
            'background physics measurements', 'systems evidence gates', 'planar rigid-body emulation',
            'contact and spring dynamics', 'metered workshop mechanisms',
            'persistent material aging', 'weapon durability', 'physical destruction and finite salvage',
            'committed motion cues', 'solver-driven hardware animation'],
            'profile_rules': {k: validate(v, HOST_RULES) for k, v in PROFILES.items()},
            'art': 'Individual rendered field bodies, regional buildings with condition frames, original raster/vector archives and optional CRT presentation.'}


def blueprint(w):
    """Export generation data and public works, excluding sessions and character records."""
    return copy.deepcopy(dict(format='Rose-infrastructure-blueprint',schema=1,game='Rose',
        version=w['version'],seed=w['seed'],rules=w['rules'],profile=w['generation_profile'],layout=w['layout'],
        content_generation=dict(version=generation.VERSION,schema=generation.SCHEMA),
        art_direction=dict(version=art_direction.RECORD['version'],source_register='/art-direction-register.json',
            principles=art_direction.RECORD['global_rules'],unit_recipe_count=len(art_direction.RECORD['unit_recipes'])),
        sites=[dict(pos=[c['x'],c['y']],title=c['title'],region=c['region'],presentation=c.get('presentation',{}),
                    infrastructure=c['infrastructure'],tiles=c['scene']['tiles'],palette=c['scene']['palette'],
                    lifecycle={k:v for k,v in c.get('lifecycle',{}).items() if k not in {'plantings','projects'}})
               for c in w['cells'].values()]))
