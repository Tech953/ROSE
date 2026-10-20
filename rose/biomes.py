"""Read-only source-grounded biome context; reference lore never executes game actions."""
import copy
import hashlib
import json
import math
from pathlib import Path
import visual_references
import art_direction

RECORD = json.loads((Path(__file__).parent / 'reference/lore-transport/catalog.json').read_text(encoding='utf-8'))
PROFILES = {p['id']: p for p in RECORD['profiles']}
ACTIVE = {p['engine_region']: p['id'] for p in RECORD['profiles'] if p['engine_region']}
POLICY = ('Regional facts are background reference, not current observations or completed actions. '
          'Locations without an established position stay unplaced. Reading a reference cannot grant '
          'resources, a companion, a contract, clearance, immortality or passage through RED>GATE>. '
          'Reports, fragments, prototypes and engine adaptations retain their evidence status.')


def profile(identity):
    """A defensive copy for authoring tools, including explicitly unplaced profiles."""
    return copy.deepcopy(PROFILES[identity])


def context(region, conditions=None):
    """Current-region context only, with existing bounded ecological state as observations."""
    if region not in ACTIVE:
        return None
    p = PROFILES[ACTIVE[region]]
    values = {}
    for name in ('growth', 'moisture', 'stability', 'aether'):
        value = (conditions or {}).get(name)
        if type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100:
            values[name] = value
    return dict(profile=p['id'], label=p['label'], placement=p['placement'],
                evidence_policy=POLICY, facts=copy.deepcopy(p['facts']),
                material_motifs=p['material_motifs'][:],
                art_direction=copy.deepcopy(p['lighting']), constraints=p['constraints'][:],
                current_conditions=values, sensory_detail=p['local_observation'],
                sensory_status='Rose sensory adaptation; does not add a physical event',
                visual_reference_context=visual_references.brief(p['id']),
                text_visual_interpretation=art_direction.context(p['id']),
                source_archive_status=RECORD['intake_status'])


def brief(w, p, engine):
    """Seeded variation inside the current region; no state mutation or unplaced geography."""
    cell = engine.local(w, p)
    data = context(cell['region'])
    if not data:
        return 'There is no source-backed briefing registered for this region.'
    turn = len(p.get('dialogue_log', []))
    digest = hashlib.sha256(f"{w['seed']}|{p['id']}|{data['profile']}|{turn}".encode()).digest()
    facts = data['facts']
    selected = facts[int.from_bytes(digest[:8], 'big') % len(facts)]
    source = selected['sources'][0]
    first, last = source['paragraphs']
    span = str(first) if first == last else f'{first}–{last}'
    return (f"The {data['label']} source record says: {selected['text']} "
            f"[{selected['status']}; {source['document']}, paragraphs {span}]. "
            'That is regional background. It does not establish a new object, a present person, '
            'a route or an access right here.')


def prose(region):
    """Sensory variation uses motifs only; dynamic effects remain owned by existing systems."""
    identity = ACTIVE.get(region)
    return PROFILES[identity]['local_observation'] if identity else ''
