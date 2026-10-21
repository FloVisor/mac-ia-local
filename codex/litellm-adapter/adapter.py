#!/usr/bin/env python3
"""Loopback DIRECT bridge. No GPT routing, MCP, retries, or provider fallback."""
import argparse
import email.utils
import hmac
import hashlib
import http.client
import http.server
import json
import os
from pathlib import Path
import secrets
import select
import socket
import stat
import threading
import time
import urllib.error
import urllib.request
import urllib.parse

BUDGETS = {'low': 512, 'medium': 2048, 'high': 8192, 'max': 16384}
EFFORTS = ['none', 'minimal', 'low', 'medium', 'high', 'max']
OMLX = 'local-omlx/mlx-community--Qwen3.6-35B-A3B-4bit'
OLLAMA = 'local-ollama/qwen3:4b-instruct'


class Rejected(Exception):
    def __init__(self, message, status=400, retry_after=None):
        self.status = status
        self.retry_after = retry_after
        super().__init__(message)


def retry_hint(value):
    """Forward a valid delay/date only, without inventing a retry policy."""
    if not isinstance(value, str) or len(value) > 128 or '\r' in value or '\n' in value:
        return None
    if value.isascii() and value.isdigit():
        return value
    try:
        email.utils.parsedate_to_datetime(value)
        return value
    except (ValueError, TypeError, OverflowError):
        return None


def private_file(path):
    fd = os.open(Path(path).expanduser(), os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as source:
        st = os.fstat(source.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            raise Rejected('credential_not_private', 503)
        value = source.read().strip()
    if not value:
        raise Rejected('credential_empty', 503)
    return value


def api(base, suffix, key, body=None, cancelled=None):
    if cancelled is not None:
        target = urllib.parse.urlsplit(base.rstrip('/') + suffix)
        conn_type = http.client.HTTPSConnection if target.scheme == 'https' else http.client.HTTPConnection
        conn = conn_type(target.hostname, target.port, timeout=300)
        result, errors = [], []
        done,abort = threading.Event(),threading.Event()
        def work():
            try:
                conn.connect()
                if abort.is_set():
                    raise Rejected('client_disconnected',499)
                conn.request('POST', target.path, json.dumps(body).encode(),
                    {'Authorization':'Bearer '+key,'Content-Type':'application/json'})
                response = conn.getresponse()
                if response.status != 200:
                    raise Rejected('litellm_http_error', response.status,
                                   retry_hint(response.getheader('Retry-After')))
                result.append((json.load(response), {k:v for k,v in response.getheaders()
                    if k.lower().startswith('x-litellm')}))
            except Exception as exc:
                errors.append(exc)
            finally:
                conn.close()
                done.set()
        worker=threading.Thread(target=work,daemon=True)
        worker.start()
        while not done.wait(.1):
            if cancelled():
                abort.set()
                if conn.sock:
                    try:conn.sock.shutdown(socket.SHUT_RDWR)
                    except OSError:pass
                conn.close()
                done.wait(2)
                raise Rejected('client_disconnected',499)
        if errors:
            raise errors[0]
        return result[0]
    req = urllib.request.Request(base.rstrip('/') + suffix,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    # No urllib retries, no redirects carrying credentials to another origin.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    with urllib.request.build_opener(NoRedirect).open(req, timeout=300) as response:
        return json.load(response), {k: v for k, v in response.headers.items()
                                    if k.lower().startswith('x-litellm')}


def inventory(tools):
    flattened, mapping = [], {}
    def visit(entries, namespace=None):
        for entry in entries:
            kind=entry.get('type')
            if kind=='namespace':
                visit(entry.get('tools',[]),entry['name'])
                continue
            if kind=='web_search':
                # Desktop attaches its OpenAI-hosted tool even when this model
                # declares supports_search_tool=false. Never forward or emulate
                # it on third-party routes; ordinary function tools remain.
                continue
            if kind not in ('function','custom'):
                raise Rejected('unsupported_tool_type:'+str(kind))
            original=entry['name']
            wire=(namespace+'__' if namespace else '')+original
            if len(wire)>64:wire='tool_'+hashlib.sha256(wire.encode()).hexdigest()[:48]
            if wire in mapping:raise Rejected('tool_name_collision')
            mapping[wire]={'name':original,'namespace':namespace,'custom':kind=='custom'}
            function={k:entry[k] for k in ('description','parameters','strict') if k in entry}
            function['name']=wire
            if kind=='custom':
                function['parameters']={'type':'object','properties':{'input':{'type':'string'}},'required':['input'],'additionalProperties':False}
            flattened.append({'type':'function','function':function})
    visit(tools)
    return flattened,mapping


def messages(payload, mapping):
    ollama = payload.get('model') == OLLAMA
    pending, seen = {}, set()
    result = []
    if payload.get('instructions'):
        result.append({'role': 'system', 'content': payload['instructions']})
    items = payload.get('input', [])
    if isinstance(items, str):
        items = [{'role': 'user', 'content': items}]
    for item in items:
        kind = item.get('type', 'message')
        if ollama and kind == 'custom_tool_call':
            item = dict(item, arguments=json.dumps({'input': item['input']}))
            kind = 'function_call'
        elif ollama and kind == 'custom_tool_call_output':
            kind = 'function_call_output'
        if kind == 'message':
            content = item.get('content', '')
            if isinstance(content, list):
                if any(p.get('type') not in ('input_text', 'output_text', 'text') for p in content):
                    raise Rejected('non_text_input_not_supported')
                content = '\n'.join(p.get('text', '') for p in content)
            role = item.get('role', 'user')
            result.append({'role': 'system' if role == 'developer' else role, 'content': content})
        elif kind == 'function_call':
            name=item['name']
            name=next((wire for wire,spec in mapping.items() if spec['name']==name and spec['namespace']==item.get('namespace')),name)
            call = {
                'id': item['call_id'], 'type': 'function',
                'function': {'name': name, 'arguments': item['arguments']}}
            if ollama:
                if item['call_id'] in seen:
                    raise Rejected('duplicate_tool_call_id')
                seen.add(item['call_id'])
                pending[item['call_id']] = name
            # Responses text and calls are items of one assistant tool turn.
            # Never merge two assistant text messages or discard content.
            if result and result[-1].get('role') == 'assistant' and (ollama or result[-1].get('tool_calls')):
                result[-1].setdefault('tool_calls', [])
                result[-1]['tool_calls'].append(call)
            else:
                result.append({'role': 'assistant', 'content': None, 'tool_calls': [call]})
        elif kind == 'function_call_output':
            output = item['output']
            tool_message = {'role': 'tool', 'tool_call_id': item['call_id'],
                            'content': output if isinstance(output, str) else json.dumps(output)}
            if ollama:
                if item['call_id'] not in pending:
                    raise Rejected('unmatched_or_duplicate_tool_result')
                tool_message['name'] = pending.pop(item['call_id'])
            result.append(tool_message)
        elif kind in ('reasoning', 'additional_tools'):
            # Encrypted native reasoning is neither portable nor re-submitted.
            continue
        else:
            raise Rejected('unsupported_input_item:' + kind)
    if ollama and pending:
        raise Rejected('missing_tool_result')
    return result


def history_structure(items):
    """Types, roles and association IDs only; no text, arguments or results."""
    if isinstance(items, str):
        return [{'type': 'message', 'role': 'user'}]
    return [{**{k: item[k] for k in ('type', 'role', 'call_id', 'tool_call_id', 'phase') if k in item},
             **({'tool_call_ids': [c.get('id') for c in item['tool_calls']]} if item.get('tool_calls') else {})}
            for item in items]


def chat_request(payload, policy):
    effort = (payload.get('reasoning') or {}).get('effort')
    if effort is not None and effort not in EFFORTS:
        raise Rejected('unsupported_reasoning_effort:' + str(effort))
    model = payload['model']
    tools,mapping=inventory(payload.get('tools') or [])
    body = {'model': model, 'messages': messages(payload,mapping), 'stream': False}
    for field in ('temperature', 'top_p', 'parallel_tool_calls'):
        if field in payload:
            body[field] = payload[field]
    answer_tokens = payload.get('max_output_tokens')
    if answer_tokens is None:
        answer_tokens = 2048
    if type(answer_tokens) is not int or answer_tokens <= 0:
        raise Rejected('invalid_max_output_tokens')
    body['max_tokens'] = answer_tokens
    if tools:
        body['tools'] = tools
    choice = payload.get('tool_choice')
    if choice is not None:
        body['tool_choice'] = ({'type': 'function', 'function': {'name': choice['name']}}
                              if isinstance(choice, dict) else choice)
    fmt = (payload.get('text') or {}).get('format') or {}
    if fmt.get('type') == 'json_object':
        body['response_format'] = {'type': 'json_object'}
    elif fmt.get('type') == 'json_schema':
        body['response_format'] = {'type': 'json_schema', 'json_schema': {
            k: v for k, v in fmt.items() if k != 'type'}}
    trace = {'requested_effort': effort, 'adapter_sent_effort': None,
             'expected_downstream_effort': None, 'applied_effort': None,
             'thinking_budget': None, 'conversion_basis': 'installed-component-audit'}
    if model.startswith('local-ollama/') and 'parallel_tool_calls' in body:
        del body['parallel_tool_calls']
        trace['omitted_parameters']=['parallel_tool_calls']
    if model == OMLX:
        effort = effort or 'high'
        body['chat_template_kwargs'] = {'enable_thinking': effort not in ('none', 'minimal')}
        if effort in BUDGETS:
            body['thinking_budget'] = BUDGETS[effort]
            # oMLX counts thinking and the answer in the same allowance.
            body['max_tokens'] += BUDGETS[effort]
        trace.update(thinking_budget=body.get('thinking_budget'),
                     enable_thinking=body['chat_template_kwargs']['enable_thinking'])
    elif effort is not None:
        if model.startswith('local-ollama/'):
            raise Rejected('reasoning_not_qualified_for_ollama')
        # Preserve original request. Conversion is downstream, never silently
        # relabelled as applied. No oMLX numeric budgets reach cloud providers.
        body['reasoning_effort'] = effort
        trace['adapter_sent_effort'] = effort
        if model.startswith('free-mistral/'):
            trace['conversion'] = 'freellmapi_drops_effort'
        elif model.startswith('free-groq/'):
            trace['expected_downstream_effort'] = {'none': 'low', 'minimal': 'low', 'max': 'high'}.get(effort, effort)
        elif model.startswith('free-openrouter/'):
            trace['expected_downstream_effort'] = 'high' if effort == 'max' else effort
        elif model.startswith('free/task-'):
            trace['conversion'] = 'pool_member_dependent'
        elif model.startswith('paid'):
            trace['expected_downstream_effort'] = 'xhigh' if effort == 'max' else effort
    # Match the existing client admission windows; no silent input truncation.
    # Count the transformed instructions, history and actual tool schemas, not
    # only the user text. UTF-8 bytes are a conservative estimate, not a tokenizer.
    context = 131072 if model == OMLX else 8192
    input_fields = {k: body[k] for k in
                    ('messages', 'tools', 'tool_choice', 'response_format') if k in body}
    input_bound = len(json.dumps(input_fields, ensure_ascii=False).encode('utf-8')) + 256
    trace['context_budget'] = {'window': context, 'input_bound': input_bound,
                               'generation_reserved': body['max_tokens'],
                               'answer_reserved': answer_tokens,
                               'estimator': 'utf8_bytes_plus_256'}
    if input_bound + body['max_tokens'] > context:
        raise Rejected('context_budget_exceeded_return_to_codex')
    return body, trace


def response_object(chat, model, mapping=None):
    message = chat['choices'][0]['message']
    output = []
    if message.get('content'):
        output.append({'type': 'message', 'id': 'msg_' + secrets.token_hex(12),
                       'status': 'completed', 'role': 'assistant', 'content': [{
                           'type': 'output_text', 'text': message['content'], 'annotations': []}]})
    for call in message.get('tool_calls') or []:
        spec=(mapping or {}).get(call['function']['name'],{'name':call['function']['name']})
        item={'type': 'function_call', 'id': 'fc_' + secrets.token_hex(12),
                       'status': 'completed', 'call_id': call['id'],
                       'name': spec['name'], 'arguments': call['function']['arguments']}
        if spec.get('namespace'):item['namespace']=spec['namespace']
        if spec.get('custom'):
            item['type']='custom_tool_call'
            item['input']=json.loads(item.pop('arguments'))['input']
        output.append(item)
    usage = chat.get('usage') or {}
    output_details = dict(usage.get('completion_tokens_details') or {})
    if model == OLLAMA and output_details.get('reasoning_tokens') is None:
        # Required by Desktop; a protocol default, not measured effort.
        output_details['reasoning_tokens'] = 0
    incomplete = chat['choices'][0].get('finish_reason') == 'length'
    return {'id': 'resp_' + secrets.token_hex(12), 'object': 'response',
            'created_at': int(time.time()), 'model': model,
            'status': 'incomplete' if incomplete else 'completed', 'output': output,
            'error': None, 'incomplete_details': {'reason': 'max_output_tokens'} if incomplete else None,
            'usage': {'input_tokens': usage.get('prompt_tokens', 0),
                      'output_tokens': usage.get('completion_tokens', 0),
                      'total_tokens': usage.get('total_tokens', 0),
                      'output_tokens_details': output_details}}


def events(response):
    empty = dict(response, output=[], status='in_progress', usage=None)
    yield {'type': 'response.created', 'response': empty}
    yield {'type': 'response.in_progress', 'response': empty}
    for i, item in enumerate(response['output']):
        initial = dict(item, status='in_progress')
        if item['type'] == 'message':
            initial['content'] = []
        elif item['type']=='function_call':
            initial['arguments'] = ''
        else:
            initial['input']=''
        yield {'type': 'response.output_item.added', 'output_index': i, 'item': initial}
        if item['type'] == 'message':
            part = item['content'][0]
            base = {'item_id': item['id'], 'output_index': i, 'content_index': 0}
            yield dict(base, type='response.content_part.added', part=dict(part, text=''))
            yield dict(base, type='response.output_text.delta', delta=part['text'])
            yield dict(base, type='response.output_text.done', text=part['text'])
            yield dict(base, type='response.content_part.done', part=part)
        elif item['type']=='function_call':
            base = {'item_id': item['id'], 'output_index': i}
            yield dict(base, type='response.function_call_arguments.delta', delta=item['arguments'])
            yield dict(base, type='response.function_call_arguments.done', arguments=item['arguments'])
        else:
            base={'item_id':item['id'],'output_index':i}
            yield dict(base,type='response.custom_tool_call_input.delta',delta=item['input'])
            yield dict(base,type='response.custom_tool_call_input.done',input=item['input'])
        yield {'type': 'response.output_item.done', 'output_index': i, 'item': item}
    yield {'type': 'response.incomplete' if response['status'] == 'incomplete' else 'response.completed',
           'response': response}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path != '/health':
            return self.reply(404, {'error': 'not_found'})
        self.reply(200, {'status': 'ok', 'mode': 'DIRECT', 'gpt_routing': False})

    def reply(self, status, data, retry_after=None):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        if retry_after is not None:
            self.send_header('Retry-After', retry_after)
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        started = time.time()
        record = {'time': started, 'request_id': secrets.token_hex(12), 'identity': 'codex-direct'}
        admitted=False
        try:
            config = json.loads(Path(self.server.config_path).read_text())
            if not hmac.compare_digest(self.headers.get('Authorization', ''),
                                       'Bearer ' + private_file(config['ingress_key_file'])):
                raise Rejected('adapter_auth_required', 401)
            if self.path != '/v1/responses':
                raise Rejected('unsupported_endpoint', 404)
            admitted=self.server.slots.acquire(blocking=False)
            if not admitted:
                raise Rejected('adapter_busy_no_retry',429)
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > 32 * 1024 * 1024:
                raise Rejected('invalid_body_size', 413)
            payload = json.loads(self.rfile.read(length))
            model = payload.get('model')
            record['model'] = model
            record['omitted_native_tools']=[t['type'] for t in payload.get('tools',[]) if t.get('type')=='web_search']
            policy = config['models'].get(model)
            if policy is None:
                raise Rejected('model_not_approved', 403)
            body, trace = chat_request(payload, policy)
            record.update(trace)
            if model == OLLAMA:
                record['input_structure'] = history_structure(payload.get('input', []))
                record['chat_structure'] = history_structure(body['messages'])
            tier = policy['tier']
            if tier == 'paid' and not config.get('paid_identity_verified'):
                raise Rejected('paid_identity_budget_not_verified', 403)
            # No incoming ChatGPT credential/header/body metadata is forwarded.
            key = private_file(config['key_files'][tier])
            body['metadata'] = {'client': 'codex-desktop-direct', 'adapter_request_id': record['request_id']}
            record['transmitted'] = {k: body[k] for k in
                ('model', 'reasoning_effort', 'thinking_budget', 'chat_template_kwargs', 'max_tokens') if k in body}
            def cancelled():
                ready,_,_=select.select([self.connection],[],[],0)
                if not ready:return False
                try:return self.connection.recv(1,socket.MSG_PEEK)==b''
                except OSError:return True
            chat, headers = api(config['litellm_url'], '/chat/completions', key, body, cancelled)
            record.update(upstream_id=chat.get('id'), upstream_model=chat.get('model'),
                          usage=chat.get('usage'), upstream_headers=headers)
            _,mapping=inventory(payload.get('tools') or [])
            response = response_object(chat, model,mapping)
            record['response_id'] = response['id']
            if model == OLLAMA:
                record['output_structure'] = history_structure(response['output'])
                record['finish_reason'] = chat['choices'][0].get('finish_reason')
                details = (chat.get('usage') or {}).get('completion_tokens_details') or {}
                record['reasoning_tokens_protocol_default'] = details.get('reasoning_tokens') is None
            if not payload.get('stream'):
                self.reply(200, response)
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'close')
                self.end_headers()
                for n, event in enumerate(events(response)):
                    event['sequence_number'] = n
                    self.wfile.write(('event: ' + event['type'] + '\ndata: ' + json.dumps(event) + '\n\n').encode())
                self.wfile.flush()
            record['status'] = 200
        except Rejected as exc:
            record.update(status=exc.status, error=str(exc))
            self.reply(exc.status, {'error': {'message': str(exc), 'type': 'invalid_request_error'}}, exc.retry_after)
        except urllib.error.HTTPError as exc:
            # Provider payloads can contain prompts/credentials: never log or echo.
            record.update(status=exc.code, error='litellm_http_error')
            self.reply(exc.code, {'error': {'message': 'LiteLLM rejected request (see server)', 'type': 'upstream_error'}}, retry_hint(exc.headers.get('Retry-After')))
        except (BrokenPipeError, ConnectionResetError):
            record.update(status=499, error='client_disconnected')
        except Exception as exc:
            record.update(status=502, error=type(exc).__name__)
            self.reply(502, {'error': {'message': 'adapter_failed:' + type(exc).__name__, 'type': 'upstream_error'}})
        finally:
            if admitted:self.server.slots.release()
            record['duration_ms'] = round((time.time() - started) * 1000)
            with self.server.log_lock:
                with open(self.server.config['activity_log'], 'a') as log:
                    log.write(json.dumps(record) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    os.umask(0o077)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', config['port']), Handler)
    server.config, server.log_lock = config, threading.Lock()
    server.config_path, server.slots = args.config, threading.BoundedSemaphore(2)
    server.serve_forever()


if __name__ == '__main__':
    main()
