import json
import os
import pathlib
import queue
import subprocess
import threading
import sys

binary = sys.argv[1]
env = os.environ.copy()
env.pop('DOCKER_MCP_CODEX_TOKEN', None)
p = subprocess.Popen([binary, 'app-server', '--stdio'], stdin=subprocess.PIPE,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, env=env)
messages = queue.Queue()
def reader():
    for line in p.stdout:
        try:
            messages.put(json.loads(line))
        except ValueError:
            pass
threading.Thread(target=reader, daemon=True).start()
counter = 0
def request(method, params):
    global counter
    counter += 1
    p.stdin.write(json.dumps({'id': counter, 'method': method, 'params': params}) + '\n')
    p.stdin.flush()
    while True:
        message = messages.get(timeout=300)
        if message.get('id') == counter:
            if 'error' in message:
                raise RuntimeError(json.dumps(message['error']))
            return message['result']
        if 'id' in message and 'method' in message:
            raise RuntimeError('Unexpected client request: ' + message['method'])
try:
    initialized = request('initialize', {'clientInfo': {'name': 'docker_mcp_validation', 'version': '1'},
                                        'capabilities': {'experimentalApi': True}})
    p.stdin.write('{"method":"initialized"}\n')
    p.stdin.flush()
    data=request('skills/list',{'cwds':[str(pathlib.Path.cwd())],'forceReload':True})
    found=[s for entry in data.get('data',[]) for s in entry.get('skills',[]) if s.get('name')=='serena']
    print(json.dumps({'serena_skills':found}),flush=True)
    assert any(s.get('path')=='/Users/fngux2/AI/skills/shared/serena/SKILL.md' or s.get('path')=='/Users/fngux2/.agents/skills/serena/SKILL.md' for s in found),data

finally:
    p.terminate()
    p.wait(timeout=10)
