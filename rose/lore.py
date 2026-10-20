"""Authored commentary is data; NPC briefings do not create rights or possessions."""
import json
from pathlib import Path
import biomes

RECORD=json.loads((Path(__file__).parent/'reference/lore-record-v012.json').read_text(encoding='utf-8'))
BY_ID={n['id']:n for n in RECORD['records']}
TOPICS={'void':['void','life-string','immunix'],'particles':['substrate','continuity','eunix'],
        'resonance':['driven-light','temporal-response','spectral-materials','energy-controller','faceted-projection'],
        'administration':['enact','signatories','institutions'],'greatweb':['fractech','great-web','aqua-sphere'],
        'biomes':['source-biome']}


def brief(w,p,topic,engine):
    if topic=='biomes':return biomes.brief(w,p,engine)
    values=TOPICS[topic];g=engine.rng(w['seed'],'lore-briefing',p['id'],topic,len(p.get('dialogue_log',[])))
    text=BY_ID[g.choice(values)]['text']
    if topic=='particles':
        f=engine.particles.field(w,p,engine);text+=f" Your current instrument record holds {len(f['objects'])} individual particles at {f['address']}."
    elif topic=='resonance':
        f=engine.particles.field(w,p,engine);ph=engine.particles.photonics.ensure(f)
        text+=f" The retained rig setting is {ph['band']} / {ph['mode']}, with {ph['energy']:.3f} stored optical units. Adjacent maintained workshops permit physical work; public power pays for excitation."
    elif topic=='void':text+=' Prepare deliberately and keep a return trace. A current dose and protective fitting matter more than a claim of rank.'
    return text


def context():return {key:BY_ID[key]['text'] for key in ['substrate','void','apogean','institutions','enact','great-web','eunix','driven-light','temporal-response']}
