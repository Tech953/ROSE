"""Restore every uploaded PNG filename, including aliases, into a new directory."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
def export(destination):
    d=json.loads((ROOT/'reference/visual-corpus/catalog.json').read_text(encoding='utf-8'))
    sources={r['sha256']:ROOT/r['path'] for r in d['references']}
    for r in d['original_aliases']:
        name=r['filename']
        if Path(name).name!=name or '/' in name or '\\' in name:raise ValueError('Invalid source filename.')
    for sha,path in sources.items():
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise ValueError('Source SHA256 check failed.')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=False)
    for r in d['original_aliases']:shutil.copyfile(sources[r['sha256']],destination/r['filename'])
    return len(d['original_aliases'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination',help='New directory for original PNG names')
    print(f'Restored {export(p.parse_args().destination)} original names.')
