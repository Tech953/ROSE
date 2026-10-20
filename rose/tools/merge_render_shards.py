"""Merge complete model shards only when their saved-source identities agree."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def merge(sources,destination):
    expected=json.loads((ROOT/'art-source/render-catalog.json').read_text())
    catalog=None;models={};files=[]
    for source in sources:
        part=json.loads((source/'catalog-partial.json').read_text())
        if catalog is None:catalog={**part,'models':{}}
        if any(part[k]!=catalog[k] for k in ['settings','render','projection','animations','visual_catalog']):
            raise ValueError('Render shards have different source/settings identities')
        for key,record in part['models'].items():
            if key in models or record!=expected['models'].get(key):raise ValueError('Duplicate or unexpected model: '+key)
            models[key]=record
            for filename in record['frames']:
                path=(source/filename).resolve()
                if not path.is_relative_to(source.resolve()) or not path.is_file():raise ValueError('Missing or unsafe frame: '+filename)
                files.append((path,filename))
    if set(models)!=set(expected['models']):raise ValueError('Shards do not cover the complete source catalog')
    sha=hashlib.sha256((ROOT/'art-source/Rose-prefabs.blend').read_bytes()).hexdigest()
    if catalog['render']['blend_sha256']!=sha:raise ValueError('Saved source changed after rendering')
    destination.mkdir(parents=True,exist_ok=True)
    for path,filename in files:
        target=destination/filename;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    catalog['models']={key:models[key] for key in expected['models']}
    (destination/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    (destination/'render-identity.json').write_text(json.dumps(catalog['render'],indent=2)+'\n')
    print('Merged',len(files),'verified frame paths from',len(models),'models.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',nargs='+',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();merge(a.input,a.output)
