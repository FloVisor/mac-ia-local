#!/usr/bin/env python3
"""Conservative Codex PreToolUse selector. No output means native execution."""
import json
import os
import re
import subprocess
import sys

RTK = '/opt/homebrew/bin/rtk'
# Deliberately no quoting, expansion, shell operators, wrappers or redirects.
SIMPLE = re.compile(r'[A-Za-z0-9_./,:=@%+~ -]+\Z')
SENSITIVE = re.compile(r'(?i)(llm.router|standup|trace|session|\.json|\.log|\.ndjson)')


def eligible(command):
    if not isinstance(command, str) or not SIMPLE.fullmatch(command):
        return False
    parts = command.split()
    if not parts:
        return False
    if parts[:2] == ['git', 'status']:
        return all(x in ('-s', '--short', '-b', '--branch') for x in parts[2:])
    if parts[:2] == ['git', 'log']:
        return all(re.fullmatch(r'-[1-9][0-9]*', x) or x in ('--oneline', '--all', '--graph', '--decorate') for x in parts[2:])
    if parts[0] == 'ls':
        return all((re.fullmatch(r'-[alh]+', x) if x.startswith('-') else not SENSITIVE.search(x)) for x in parts[1:])
    return False


def main():
    try:
        if os.getenv('RTK_DISABLED') == '1':
            return
        payload = json.load(sys.stdin)
        if payload.get('hook_event_name') != 'PreToolUse' or payload.get('tool_name') not in ('Bash', 'bash'):
            return
        command = payload.get('tool_input', {}).get('command')
        if not eligible(command):
            return
        result = subprocess.run([RTK, 'hook', 'codex'], input=json.dumps(payload), text=True,
                                capture_output=True, timeout=3)
        if result.returncode or not result.stdout.strip():
            return
        response = json.loads(result.stdout)
        specific = response.get('hookSpecificOutput', {})
        updated = specific.get('updatedInput', {})
        # Accept only the expected prefixing, preserving every other argument.
        if updated.get('command') != 'rtk ' + command:
            return
        original = dict(payload['tool_input'])
        original['command'] = updated['command']
        specific['updatedInput'] = original
        print(json.dumps(response))
    except (ValueError, TypeError, AttributeError, OSError, subprocess.TimeoutExpired):
        return  # Hook trouble must preserve native execution.


if __name__ == '__main__':
    main()
