"""Stable visual designation; independent of simulation RNG and earned equipment."""
import hashlib
import json
from pathlib import Path

CATALOG = json.loads((Path(__file__).parent / 'static/visual-catalog.json').read_text())


def fingerprint(seed, identity):
    return hashlib.sha256((str(seed) + '|rose-visual-v1|' + str(identity)).encode()).digest()


def ensure_actor(w, actor):
    character = actor.get('character', {})
    chosen = character.get('presentation', 'automatic')
    model = chosen if chosen in CATALOG['profiles'] else CATALOG['role_defaults'].get(character.get('role'), 'traveler')
    if chosen == 'automatic' and character.get('form') == 'Metal-kin': model = 'metal_kin'
    # Only an explicit character edit changes the family. Origin is not current location.
    digest = fingerprint(w['seed'], actor['id'])
    old = actor.get('visual', {})
    actor['visual'] = dict(schema=1, model=model, tone=digest[0] % len(CATALOG['tones']),
                           signature=digest.hex()[:12], origin=character.get('origin', old.get('origin', 'WN_TOWER')))
    return actor['visual']


def ensure_node(w, cell, node):
    identity = f"{cell['x']},{cell['y']}:{node['id']}"
    digest = fingerprint(w['seed'], identity)
    node.setdefault('visual', dict(schema=1, model=node['kind'] + '_' + cell['region'],
                                  tone=digest[0] % len(CATALOG['tones']), signature=digest.hex()[:12]))
    return node['visual']


def designation(visual):
    model=visual['model']
    label=CATALOG['profiles'].get(model, {}).get('label', model.replace('_', ' '))
    for region,style in [('WN_TOWER','Root-grown framing'),('CITY_CLOUD_S','Salvaged city metal'),('ENACT_HILLS','Hills masonry'),('AETHERGALE','Crystal and wind fabric')]:
        if model.endswith('_'+region): label=style
    return label + ' / ' + CATALOG['tones'][visual['tone']]
