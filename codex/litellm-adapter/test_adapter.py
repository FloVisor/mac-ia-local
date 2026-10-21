"""Focused new bridge tests only; no provider calls."""
import copy
import unittest
import http.server
import json
import pathlib
import tempfile
import threading
import urllib.request
import urllib.error
import time
from adapter import BUDGETS, OMLX, Rejected, Handler, api, chat_request, events, response_object, inventory, retry_hint


class AdapterTests(unittest.TestCase):
    def test_retry_hint_validation(self):
        for value in ['60', 'Wed, 21 Oct 2026 17:00:00 GMT']:
            self.assertEqual(retry_hint(value), value)
        for value in [None, '-1', 'unknown', '60\r\nX-Test: injected']:
            self.assertIsNone(retry_hint(value))

    def test_upstream_429_preserves_delay_without_retry(self):
        calls = []
        class Gateway(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                calls.append(1)
                self.send_response(429)
                self.send_header('Retry-After', '60')
                self.end_headers()
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Gateway)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with self.assertRaises(Rejected) as err:
                api('http://127.0.0.1:' + str(server.server_port), '/chat/completions',
                    'synthetic', {}, cancelled=lambda: False)
            self.assertEqual(err.exception.status, 429)
            self.assertEqual(err.exception.retry_after, '60')
            self.assertEqual(calls, [1])
        finally:
            server.shutdown(); server.server_close()

    def test_local_generation_reserves_answer_and_thinking(self):
        for effort in ['none','minimal',*BUDGETS]:
            with self.subTest(effort=effort):
                body,trace=chat_request({'model':OMLX,'input':'test','reasoning':{'effort':effort},'max_output_tokens':32}, {})
                self.assertEqual(body['max_tokens'],32+BUDGETS.get(effort,0))
                self.assertEqual(body.get('thinking_budget'),BUDGETS.get(effort))
                self.assertEqual(body['chat_template_kwargs']['enable_thinking'],effort in BUDGETS)
                self.assertNotIn('reasoning_effort',body)
                self.assertIsNone(trace['applied_effort'])

    def test_context_admission_counts_tools_and_preserves_input(self):
        payload = {'model': 'local-ollama/qwen3:4b-instruct', 'input': 'x' * 4000,
                   'max_output_tokens': 1000}
        body, trace = chat_request(payload, {})
        self.assertEqual(body['messages'][-1]['content'], payload['input'])
        self.assertLessEqual(trace['context_budget']['input_bound'] + 1000, 8192)
        for extra in [{'input': 'x' * 8193},
                      {'tools': [{'type': 'function', 'name': 'read',
                                  'description': 'x' * 8193, 'parameters': {}}]}]:
            with self.assertRaisesRegex(Rejected, 'context_budget_exceeded_return_to_codex'):
                chat_request(payload | extra, {})

    def test_omlx_context_reserves_reasoning_before_dispatch(self):
        payload = {'model': OMLX, 'input': 'x' * 120000,
                   'reasoning': {'effort': 'max'}, 'max_output_tokens': 1000}
        with self.assertRaisesRegex(Rejected, 'context_budget_exceeded'):
            chat_request(payload, {})
        body, _ = chat_request(payload | {'reasoning': {'effort': 'none'}}, {})
        self.assertEqual(body['max_tokens'], 1000)

    def test_invalid_generation_budget_is_rejected(self):
        for value in [0, -1, True, '2048']:
            with self.assertRaisesRegex(Rejected, 'invalid_max_output_tokens'):
                chat_request({'model': OMLX, 'input': 'test', 'max_output_tokens': value}, {})
        body, _ = chat_request({'model': OMLX, 'input': 'test',
                                'reasoning': {'effort': 'none'}, 'max_output_tokens': None}, {})
        self.assertEqual(body['max_tokens'], 2048)

    def test_cloud_request_preserved_without_omlx_parameters(self):
        for model,expected in [('free-groq/qwen3.8-27b','high'),('free-mistral/codestral-2508',None),('paid/task-advanced','xhigh')]:
            body,trace=chat_request({'model':model,'input':'test','reasoning':{'effort':'max'},'thinking_budget':16384,'chat_template_kwargs':{'enable_thinking':True}}, {})
            self.assertEqual(body['reasoning_effort'],'max')
            self.assertEqual(trace['expected_downstream_effort'],expected)
            self.assertNotIn('thinking_budget',body)
            self.assertNotIn('chat_template_kwargs',body)
            self.assertIsNone(trace['applied_effort'])

    def test_tool_roundtrip_and_event_completion(self):
        chat={'choices':[{'message':{'tool_calls':[{'id':'call1','function':{'name':'lookup','arguments':'{"x":1}'}}]},'finish_reason':'tool_calls'}]}
        response=response_object(chat,OMLX)
        replay=response['output']+[{'type':'function_call_output','call_id':'call1','output':'value'}]
        body,_=chat_request({'model':OMLX,'input':replay},{})
        self.assertEqual(body['messages'][0]['tool_calls'][0]['id'],'call1')
        self.assertEqual(body['messages'][1],{'role':'tool','tool_call_id':'call1','content':'value'})
        emitted=list(events(response))
        self.assertEqual(emitted[-1]['type'],'response.completed')
        self.assertEqual(next(e for e in emitted if e['type']=='response.function_call_arguments.done')['arguments'],'{"x":1}')

    def test_unsupported_input_and_levels_rejected(self):
        for patch in [{'reasoning':{'effort':'ultra'}},{'input':[{'type':'computer_call'}]},{'tools':[{'type':'image_generation'}]}]:
            payload={'model':OMLX,'input':'test'}|patch
            with self.assertRaises(Rejected):chat_request(payload,{})

    def test_length_does_not_claim_completed(self):
        response=response_object({'choices':[{'message':{'content':'partial'},'finish_reason':'length'}]},OMLX)
        self.assertEqual(response['status'],'incomplete')
        self.assertEqual(list(events(response))[-1]['type'],'response.incomplete')

    def test_ollama_unsupported_parallel_option_is_route_scoped(self):
        payload={'model':'local-ollama/qwen3:4b-instruct','input':'test','parallel_tool_calls':True}
        body,trace=chat_request(payload,{})
        self.assertNotIn('parallel_tool_calls',body)
        self.assertEqual(trace['omitted_parameters'],['parallel_tool_calls'])
        other,_=chat_request(payload|{'model':'free-mistral/ministral-8b-2512'},{})
        self.assertTrue(other['parallel_tool_calls'])

    def test_namespace_custom_and_parallel_history(self):
        tools=[{'type':'namespace','name':'functions','tools':[
            {'type':'function','name':'lookup','parameters':{'type':'object'}},
            {'type':'custom','name':'apply_patch'}]},{'type':'web_search'}]
        flattened,mapping=inventory(tools)
        self.assertEqual(len(flattened),2)
        result=response_object({'choices':[{'message':{'tool_calls':[{
            'id':'p','function':{'name':'functions__apply_patch','arguments':'{"input":"patch"}'}}]},'finish_reason':'tool_calls'}]},OMLX,mapping)
        self.assertEqual(result['output'][0]['input'],'patch')
        self.assertEqual(result['output'][0]['namespace'],'functions')
        self.assertIn('response.custom_tool_call_input.done',[e['type'] for e in events(result)])
        payload={'model':OMLX,'tools':tools,'input':[{'type':'function_call','name':'lookup','namespace':'functions','call_id':c,'arguments':'{}'} for c in ['a','b']]}
        body,_=chat_request(payload,{})
        self.assertEqual(len(body['messages']),1)
        self.assertEqual(len(body['messages'][0]['tool_calls']),2)

    def test_cancellation_closes_amont_without_inference(self):
        entered,closed=threading.Event(),threading.Event()
        class Gateway(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                entered.set()
                self.connection.settimeout(3)
                if self.connection.recv(1)==b'':closed.set()
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Gateway)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            with self.assertRaises(Rejected) as err:
                api('http://127.0.0.1:'+str(server.server_port),'/chat/completions','synthetic',{},cancelled=entered.is_set)
            self.assertEqual(err.exception.status,499)
            self.assertTrue(closed.wait(2))
        finally:server.shutdown();server.server_close()

    def test_paid_gate_does_not_reach_gateway(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);key=root/'key';key.write_text('synthetic');key.chmod(0o600)
            config={'ingress_key_file':str(key),'models':{'paid/task-advanced':{'tier':'paid'}},'paid_identity_verified':False,'activity_log':str(root/'activity')}
            path=root/'config';path.write_text(json.dumps(config))
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
            server.config=config;server.config_path=str(path);server.slots=threading.BoundedSemaphore(2);server.log_lock=threading.Lock()
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                req=urllib.request.Request('http://127.0.0.1:'+str(server.server_port)+'/v1/responses',data=json.dumps({'model':'paid/task-advanced','input':'test'}).encode(),headers={'Authorization':'Bearer synthetic'})
                with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(req,timeout=3)
                self.assertEqual(err.exception.code,403)
                err.exception.close()
            finally:server.shutdown();server.server_close()


if __name__=='__main__':unittest.main()
