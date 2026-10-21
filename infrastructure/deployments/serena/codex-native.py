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
    thread = request('thread/start', {'ephemeral': True, 'cwd': str(pathlib.Path.home()),
                                      'approvalPolicy': 'never'})
    tid = thread['thread']['id']
    inventory = request('mcpServerStatus/list', {'threadId': tid, 'serverName': 'docker-mcp-gateway'})
    selected = [s for s in inventory.get('data', []) if s['name'] == 'docker-mcp-gateway']
    print(json.dumps({'binary': binary, 'inventory': selected}, ensure_ascii=False), flush=True)
    assert len(selected)==1 and {'get_current_time','convert_time','resolve-library-id','query-docs','serena_find_symbol','serena_repository_status','serena_find_references','serena_symbols_overview','serena_search_pattern'}==set(selected[0]['tools'])
    result = request('mcpServer/tool/call', {'threadId': tid, 'server': 'docker-mcp-gateway',
                                           'tool': 'get_current_time',
                                           'arguments': {'timezone': 'Europe/Paris'}})
    assert not result.get('isError'), result
    print(json.dumps({'binary': binary, 'time_call': result, 'model_turns': 0}, ensure_ascii=False), flush=True)
    result=request('mcpServer/tool/call',{'threadId':tid,'server':'docker-mcp-gateway','tool':'serena_find_symbol','arguments':{'repository':'FloVisor/mac-ia-local','name_path_pattern':'main','relative_path':'mcp/local-llm-mcp/local-llm-mcp.py','include_body':True}})
    assert not result.get('isError'),result
    print(json.dumps({'serena_call':result,'model_turns':0}),flush=True)

finally:
    p.terminate()
    p.wait(timeout=10)
