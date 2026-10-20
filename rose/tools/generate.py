#!/usr/bin/env python3
"""Generate a reusable Rose infrastructure blueprint without running the host."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import engine
import world
import geography


def main():
    parser = argparse.ArgumentParser(description='Rose seeded infrastructure generator')
    parser.add_argument('--seed', default='rose-first-foundation')
    parser.add_argument('--profile', choices=list(engine.PROFILES), default='balanced')
    parser.add_argument('--rules', default=str(ROOT / 'rules.json'))
    parser.add_argument('--from-blueprint', help='Reuse the seed and rules only; saved site changes and characters are not imported.')
    parser.add_argument('--all-landmarks', action='store_true')
    parser.add_argument('--output', default='Rose-infrastructure-blueprint.json')
    args = parser.parse_args()
    try:
        engine.load(args.rules)
        overrides = None
        if args.from_blueprint:
            source = Path(args.from_blueprint)
            if source.stat().st_size > 16 * 1024 * 1024:
                raise ValueError('Blueprint configuration import is limited to 16 MiB.')
            data = json.loads(source.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or data.get('format') != 'Rose-infrastructure-blueprint' or data.get('schema') != 1:
                raise ValueError('Use a Rose schema 1 infrastructure blueprint.')
            args.seed, args.profile, overrides = data['seed'], data['profile'], engine.validate(data['rules'])
        if not isinstance(args.seed, str) or not 1 <= len(args.seed) <= 80:
            raise ValueError('Use a seed from 1 to 80 characters.')
        w = world.new_world(args.seed, rules=overrides, profile=args.profile)
        if args.all_landmarks:
            for landmark in geography.LANDMARKS.values():
                world.visit(w, *landmark['pos'])
        result = engine.blueprint(w)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    count = sum(len(c['infrastructure']['nodes']) for c in w['cells'].values())
    print(f'ROSE {engine.VERSION}: {len(w["cells"])} sites, {count} public structures. Saved {output}.')


if __name__ == '__main__':
    main()
