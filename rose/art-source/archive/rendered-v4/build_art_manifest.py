"""Developer-only UV/foot-anchor registration; does not modify generated artwork."""
import copy
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'static' / 'art'


def register(filename, columns, rows, sheet=0):
    image = Image.open(ART / filename)
    frames, anchors = [], []
    for row in range(rows):
        for col in range(columns):
            left, top = round(col*image.width/columns), round(row*image.height/rows)
            right, bottom = round((col+1)*image.width/columns), round((row+1)*image.height/rows)
            alpha = image.getchannel('A').crop((left,top,right,bottom))
            bounds = alpha.point(lambda a: 255 if a >= 64 else 0).getbbox()
            if not bounds:
                raise ValueError(f'Empty sprite cell: {filename} {row},{col}')
            frames.append([left,top,right-left,bottom-top,sheet])
            anchors.append([(right-left)/2,bounds[3]-1])
    return frames, anchors


def build():
    value = json.loads((ROOT/'static'/'art-manifest-vector.json').read_text())
    value['license'] = 'Original Rose code and generated artwork; no Fallout assets are included.'
    value['styles'] = ['raster','vector']
    value['art_direction'] = 'CRT terminal, orthographic isometric prefabs, weathered druid / nano / neon materials.'
    prefab_frames, prefab_anchors = register('rose-prefabs-crt-v1.png',3,3)
    sizes = [(66,90),(74,68),(82,54),(92,72),(88,75),(92,75),(64,86),(54,44),(62,50)]
    for index,kind in enumerate(['power','water','garden','shelter','workshop','exchange','relay','rock','threat']):
        frame = prefab_frames[index]
        image = Image.open(ART/'rose-prefabs-crt-v1.png')
        bounds = image.getchannel('A').crop((frame[0],frame[1],frame[0]+frame[2],frame[1]+frame[3])).point(lambda a:255 if a>=64 else 0).getbbox()
        scale = min(sizes[index][0]/(bounds[2]-bounds[0]),sizes[index][1]/(bounds[3]-bounds[1]))
        value['assets'][kind] = dict(kind='sprite',image='/art/rose-prefabs-crt-v1.png',
            frames=[frame],anchors=[prefab_anchors[index]],scale=round(scale,5),clips={p:[0] for p in value['animations']})
    walk_frames, walk_anchors = register('rose-traveler-walk-v1.png',4,6)
    action_frames, action_anchors = register('rose-traveler-actions-v1.png',6,6,1)
    clips = {}
    for direction in range(6):
        base = len(walk_frames)+direction*6
        clips[f'walk_{direction}'] = list(range(direction*4,direction*4+4))
        for pose,indices in {'idle':[base],'attack':[base,base+1,base],
                             'guard':[base+2],'work':[base+3],'talk':[base,base+4],
                             'hit':[base+2],'down':[base+5]}.items():
            clips[f'{pose}_{direction}'] = indices
    traveler = dict(kind='sprite',images=['/art/rose-traveler-walk-v1.png','/art/rose-traveler-actions-v1.png'],
        frames=walk_frames+action_frames,anchors=walk_anchors+action_anchors,
        scales=[.255]*len(walk_frames)+[.32]*len(action_frames),clips=clips,
        note='Shared provisional traveler body. Biography, equipment stats and dialogue remain individually registered; visual body/loadout variants are future assets.')
    for kind in ['player','companion','npc']:
        value['assets'][kind] = copy.deepcopy(traveler)
    ground=Image.open(ART/'rose-ground-materials-v1.png')
    for index,region in enumerate(['WN_TOWER','CITY_CLOUD_S','ENACT_HILLS','AETHERGALE']):
        x,y=(index%2)*ground.width//2,(index//2)*ground.height//2
        value['assets']['ground_'+region]=dict(kind='texture',image='/art/rose-ground-materials-v1.png',frames=[[x,y,ground.width//2,ground.height//2]])
    value['animations']['walk']['frames'] = 4
    value['animations']['attack']['frame_ms'] = 220
    value['replacement']['note'] = 'Single-sheet example. Installed traveler entries demonstrate multi-sheet frames [x,y,w,h,sheet], per-frame anchors and scales.'
    (ROOT/'static'/'art-manifest.json').write_text(json.dumps(value,indent=2)+'\n')
    print('Registered 9 environment prefabs, 4 ground materials, 24 walk frames and 36 action poses in six directions.')


if __name__ == '__main__':
    build()
