"""Restore only audited OpenClaw model fields, preserving concurrent changes.

Reads private local preimages; applies through the supported OpenClaw CLI.
The plugin and remote metadata have separate rollback procedures in the report.
"""
import json
import pathlib
import subprocess
import tempfile

root = pathlib.Path.home() / '.openclaw'
backup = root / 'backups-model-audit-20261021'
current = json.loads((root / 'openclaw.json').read_text())
changes = json.loads((backup / 'changes.json').read_text())
patch = {'models': {'providers': {}}}
for change in changes:
    provider = change['provider']
    models = patch['models']['providers'].setdefault(provider, {
        'models': current['models']['providers'][provider]['models']})['models']
    entry = next(m for m in models if m['id'] == change['id'])
    if [entry['contextWindow'], entry['maxTokens']] != change['after']:
        raise SystemExit('STOP: concurrent change on ' + provider + '/' + change['id'])
    entry['contextWindow'], entry['maxTokens'] = change['before']
with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as handle:
    json.dump(patch, handle)
    handle.flush()
    subprocess.run(['openclaw', 'config', 'patch', '--file', handle.name,
                    '--dry-run', '--json'], check=True)
    subprocess.run(['openclaw', 'config', 'patch', '--file', handle.name], check=True)
