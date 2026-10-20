"""Read-only source-linked art direction. This module owns no game state."""
import copy
import json
from pathlib import Path

RECORD=json.loads((Path(__file__).parent/'reference/art-direction/direction-v018.json').read_text(encoding='utf-8'))
NARRATIVE_RULES=[RECORD['global_rules'][i] for i in (0,1,4,5,6,8)]
POLICY=('Describe established objects only. These are authoring materials, light and scale directions, not current observations. '
        'Do not introduce events, people, equipment, routes, access, resources or completed actions. '
        'Current identity, weather, material condition, power, checks and permissions remain authoritative.')

def context(profile_id):
    p=RECORD['profiles'].get(profile_id)
    if not p:return None
    return copy.deepcopy(dict(status='art-direction adaptation; not current observations',materials=p['materials'],
        lighting=p['lighting'],scale=p['scale'],principles=NARRATIVE_RULES,policy=POLICY))

def asset_brief(profile_id,subject):
    for recipe in RECORD['unit_recipes']:
        if recipe['profile']==profile_id and recipe['subject']==subject:return copy.deepcopy(recipe)
    raise ValueError('Unknown profile or asset subject.')

def product_brief(identity):
    for p in RECORD['product_briefs']:
        if p['id']==identity:return copy.deepcopy(p)
    raise ValueError('Unknown product brief.')

def export():
    return copy.deepcopy(RECORD)
