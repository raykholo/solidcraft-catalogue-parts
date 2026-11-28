"""Sweep every declared code through the host's package loader and parser."""
import json
import subprocess
from functools import lru_cache
from pathlib import Path

from runtime import registry, sc
from runtime.parametric import cli
from runtime.parametric.links import resolve

BLOCKED = {"what": "SolidCraft's own generator.parse on every code",
           "needs": "SolidCraft with #23175 (generator packages)"}


@lru_cache(maxsize=1)
def supports_parse():
    reply = subprocess.run([sc.CLI, 'commands'], capture_output=True, text=True, check=True)
    def contains(value):
        if isinstance(value, str):
            return value == 'generator.parse'
        if isinstance(value, list):
            return any(contains(x) for x in value)
        if isinstance(value, dict):
            return any(contains(k) or contains(v) for k, v in value.items())
        return False
    return contains(json.loads(reply.stdout))


def parse_row(package, line, refusals):
    row = {'code': line.code, 'valid': line.valid}
    try:
        if line.valid:
            own = resolve(package, line.code)
            row['expected'] = {k: own[k] for k in ('configuration', 'parameters')}
        else:
            row['expected'] = {'ok': False, 'message': refusals[line.code]}
    except Exception as error:
        row['expected'] = {'error': str(error)}
    # Still send every code if the reference resolver failed.
    try:
        replies, error = cli([{'command': 'generator.parse', 'params': {
            'generator': str(package.resolve()), 'code': line.code}}])
        reply = replies[0] if replies else {}
        if error:
            row['actual'] = {'error': error}
        elif line.valid and reply.get('ok') is True:
            row['actual'] = {'configuration': reply.get('configuration'), 'parameters': reply.get('parameters', {})}
        elif not line.valid and reply.get('ok') is False:
            row['actual'] = {'ok': False, 'message': reply.get('message')}
        else:
            row['actual'] = {'error': reply or 'missing reply'}
    except Exception as error:
        row['actual'] = {'error': str(error)}
    return row


def check_parse(generator_dir, outdir):
    generator_dir, outdir = Path(generator_dir).resolve(), Path(outdir)
    path = outdir / 'faithfulness.json'
    result = json.loads(path.read_text())
    if not supports_parse():
        if BLOCKED not in result['blocked']:
            result['blocked'].append(dict(BLOCKED))
    else:
        package, = (generator_dir / 'parametric').glob('*/generator.toml')
        refusals = {r['code'].lstrip('!'): r['python'] for r in result['rejects']}
        rows = [parse_row(package.parent, line, refusals) for line in registry.Generator(generator_dir).codes()]
        result.setdefault('parse', []).extend(rows)
    path.write_text(json.dumps(result, indent=1))


if __name__ == '__main__':
    import sys
    check_parse(sys.argv[1], sys.argv[2])
