"""Write package manifests with declared text fields shared by their templates."""
import json
import re
import tomllib


def write_manifest(path, text, text_parameters):
    """Merge text declarations, preserving existing defaults and other metadata."""
    manifest = tomllib.loads(text)
    declarations = []
    for name, definition in text_parameters.items():
        previous = manifest.get('parameters', {}).get(name, {})
        value = previous | definition
        line = name + ' = { ' + ', '.join(k + ' = ' + json.dumps(v) for k, v in value.items()) + ' }'
        pattern = rf'(?m)^{re.escape(name)}\s*=\s*\{{[^\n]*\}}[^\n]*$'
        if previous:
            text, count = re.subn(pattern, lambda _: line, text, count=1)
            if not count:
                raise ValueError(f'cannot replace parameter {name}')
        else:
            declarations.append(line)
    if declarations:
        if '[parameters]' not in text:
            text = text.replace('[[template]]', '[parameters]\n\n[[template]]', 1)
        text = text.replace('[parameters]', '[parameters]\n' + '\n'.join(declarations), 1)
    path.write_text(text)
