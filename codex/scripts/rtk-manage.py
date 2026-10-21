#!/usr/bin/env python3
"""Install/remove only the RTK-owned Codex hook; preserve unrelated entries."""
import json
import os
from pathlib import Path
import sys

HOME = Path.home() / '.codex'
TARGET = HOME / 'hooks' / 'rtk-selective.py'
CONFIG = HOME / 'hooks.json'
COMMAND = '/usr/bin/python3 ' + str(TARGET)
ENTRY = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': COMMAND, 'timeout': 5}]}


def main():
    action = sys.argv[1]
    if action not in ('install', 'uninstall'):
        raise SystemExit('use install or uninstall')
    # Read shared config immediately before targeted merge, then compare before replace.
    before = CONFIG.read_bytes() if CONFIG.exists() else None
    data = json.loads(before) if before is not None else {}
    hooks = data.setdefault('hooks', {})
    entries = hooks.setdefault('PreToolUse', [])
    for entry in entries[:]:
        items = entry.get('hooks', [])
        entry['hooks'] = [h for h in items if h.get('command') != COMMAND]
        if not entry['hooks']:
            entries.remove(entry)
    if action == 'install':
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_bytes(Path(__file__).with_name('rtk-selective-hook.py').read_bytes())
        entries.append(ENTRY)
    if not entries:
        hooks.pop('PreToolUse', None)
    if not hooks:
        data.pop('hooks', None)
    if (CONFIG.read_bytes() if CONFIG.exists() else None) != before:
        raise SystemExit('Concurrent hooks.json change: no config write performed')
    if data:
        tmp = CONFIG.with_name('hooks.json.rtk-tmp')
        with tmp.open('x') as f:
            json.dump(data, f, indent=2)
            f.write('\n')
        os.replace(tmp, CONFIG)
    elif CONFIG.exists():
        CONFIG.unlink()
    if action == 'uninstall' and TARGET.exists():
        TARGET.unlink()
    print(action + ': RTK hook only; unrelated configuration preserved')


if __name__ == '__main__':
    main()
