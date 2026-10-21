#!/usr/bin/env python3
"""Remove this plugin's config additions, preserving unrelated concurrent edits."""
import json
import os
from pathlib import Path
import sys

backup = Path(sys.argv[1]) / 'openclaw.json'
config = Path.home() / '.openclaw/openclaw.json'
before = config.read_bytes()
current = json.loads(before)
old = json.loads(backup.read_bytes())
plugin = 'omlx-thinking'
location = str(Path(__file__).resolve().parent)
plugins = current['plugins']
entry = plugins.get('entries', {}).get(plugin)
if entry not in (None, {'enabled': True}):
    raise SystemExit('STOP: plugin settings changed since installation; inspect first')
if plugin in old.get('plugins', {}).get('entries', {}):
    raise SystemExit('STOP: backup already contains plugin; inspect first')
plugins.get('entries', {}).pop(plugin, None)
paths = plugins.get('load', {}).get('paths', [])
paths[:] = [p for p in paths if p != location]
if plugin not in old.get('plugins', {}).get('allow', []) and isinstance(plugins.get('allow'), list):
    plugins['allow'][:] = [p for p in plugins['allow'] if p != plugin]
temporary = config.with_name('openclaw.json.omlx-thinking-rollback.tmp')
if '--dry-run' in sys.argv[2:]:
    assert current['agents'] == old['agents'], 'Agent settings differ from backup'
    assert current['models'] == old['models'], 'Model settings differ from backup'
    print('PASS: rollback removes only plugin additions; agents and models preserved')
    raise SystemExit(0)
if config.read_bytes() != before:
    raise SystemExit('STOP: concurrent config change')
temporary.write_text(json.dumps(current, ensure_ascii=False, indent=2) + '\n')
os.chmod(temporary, 0o600)
os.replace(temporary, config)
print('Plugin config removed; Gateway config watcher applies the removal. Plugin source retained.')
