"""Faithfulness checks for choices outside an ordering code."""
import json
import subprocess
import tempfile
import tomllib
from functools import lru_cache
from pathlib import Path

from runtime import registry, sc
from runtime.parametric import cli, measure

BLOCKED = {"what": "options outside the code (caps) through generator.parse/insert",
           "needs": "SolidCraft with #23175 (fields.options)"}


@lru_cache(maxsize=1)
def supports_options():
    """Probe the command catalogue's advertised fields.options contract, not a version."""
    reply = subprocess.run([sc.CLI, "commands"], capture_output=True, text=True, check=True)
    def contains(value):
        if isinstance(value, list):
            return any(contains(x) for x in value)
        if isinstance(value, dict):
            if "generator.parse" in value.values() and "fields.options" in json.dumps(value):
                return True
            return any(contains(x) for x in value.values())
        return False
    return contains(json.loads(reply.stdout))


def caps_reference(generator, code, work):
    """Keep the dimensioned build plus exactly the Python build's cap cylinders.

    Caps are gated by appearance in Python. Exclude its other appearance geometry,
    as the existing MG rebuild comparisons do, without duplicating dimensions.
    """
    _, commands = generator.build(code, appearance=False, screws=False, caps=True)
    _, decorated = generator.build(code, appearance=True, screws=False, caps=True)
    commands += [c for c in decorated if c['command'] == 'solid.cylinder'
                 and c['params'].get('body_name', '').startswith('Rail cap ')]
    path, _ = sc.run_script(commands, str(work), 'python-caps')
    return measure(path, work, 'python-caps.measure', threads=False, include_threads=False)


def option_rows(generator, package, fixture, work):
    rows = []
    code, options = fixture['code'], fixture['options']
    expected = fixture.get('refusal')
    for command in ('generator.parse', 'generator.insert'):
        label = f"options: {command} {code} {json.dumps(options, sort_keys=True)}"
        host = work / (command + '.sc')
        replies, error = cli([{'command': command, 'params': {
            'generator': str(package.resolve()), 'code': code, 'options': options}}], save=host)
        reply = replies[0] if replies else {}
        if expected:
            message = str(error or reply.get('message') or '')
            refused = bool(error or reply.get('ok') is False)
            rows.append({'label': label, 'direct': {'refused': True},
                         'changed': {'refused': refused and expected in message, 'message': message}})
            continue
        reference = caps_reference(generator, code, work)
        if error or reply.get('ok') is False:
            changed = {'error': error or reply}
        elif command == 'generator.parse':
            if reply.get('parameters', {}).get('caps') != '1' or reply.get('fields', {}).get('options') != options:
                changed = {'error': 'parse did not retain caps options and override'}
            else:
                manifest = tomllib.loads((package / 'generator.toml').read_text())
                _, error = cli([{'command': 'component.insert_design', 'params': {
                    'path': str((package / manifest['model']).resolve()),
                    'configuration': reply['configuration'], 'parameters': reply['parameters']}}], save=host)
                changed = {'error': error} if error else measure(host, work, command, threads=False, include_threads=False)
        else:
            changed = measure(host, work, command, threads=False, include_threads=False)
        rows.append({'label': label, 'direct': reference, 'changed': changed})
    return rows


def check_options(generator_dir, outdir):
    generator_dir, outdir = Path(generator_dir), Path(outdir)
    fixtures = json.loads((generator_dir / 'parametric/options_checks.json').read_text())
    path = outdir / 'faithfulness.json'
    result = json.loads(path.read_text())
    if not supports_options():
        if BLOCKED not in result['blocked']:
            result['blocked'].append(dict(BLOCKED))
    else:
        generator = registry.Generator(generator_dir.resolve())
        package = generator_dir / 'parametric' / fixtures['package']
        for fixture in fixtures['checks']:
            with tempfile.TemporaryDirectory() as temporary:
                try:
                    rows = option_rows(generator, package, fixture, Path(temporary))
                except Exception as error:
                    rows = [{'label': f"options: {fixture['code']}", 'direct': {'ran': True},
                             'changed': {'error': str(error)}}]   # a crash is a difference, never a match
                result['rebuild'].extend(rows)
    path.write_text(json.dumps(result, indent=1))


if __name__ == '__main__':
    import sys
    check_options(sys.argv[1], sys.argv[2])
