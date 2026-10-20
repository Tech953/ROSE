"""Read-only art guidance and fixed routes for reviewed original image sources."""
import copy
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RECORD=json.loads((ROOT/'reference/visual-corpus/catalog.json').read_text(encoding='utf-8'))
REFERENCES={r['id']:r for r in RECORD['references']}
POLICY=('Visual guidance applies only to established objects. It is background reference, not current observation. '
        'Do not add places, people, weather, resources, credentials, routes, topology or completed actions. '
        'Current saved weather, lighting, material condition and character identity remain authoritative. '
        'Source concepts and measurements stay off screen. Unassigned images and battle scenarios are excluded.')


def brief(profile_id):
    """Authoring access does not map unplaced profiles into live regions."""
    value=RECORD['profile_briefs'].get(profile_id)
    if value is None:return None
    result=copy.deepcopy(value)
    result.update(status='visual reference guidance; not current observations',policy=POLICY)
    result['sources']=[dict(id=i,filename=REFERENCES[i]['filename'],status=REFERENCES[i]['status']) for i in value['sources']]
    return result


def asset_routes():
    """No request path is joined to the filesystem; register known IDs only."""
    routes={}
    for identity,record in REFERENCES.items():
        expected=f'reference/visual-corpus/images/{identity}.png'
        if not re.fullmatch(r'vr-[0-9a-f]{16}',identity) or record['path']!=expected or record['url']!=f'/visual-reference/{identity}.png':
            raise ValueError('Invalid visual reference identity or path.')
        routes[record['url']]=('../'+expected,'image/png')
    return routes


ASSET_ROUTES=asset_routes()
