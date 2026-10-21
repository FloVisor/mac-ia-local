import copy
import io
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).parent))
import router
from authorization import Authorizations, Denied, direct_selection

class Backend(BaseHTTPRequestHandler):
    calls = []
    status_code = 200
    delay = 0
    content = 'OK'
    sse = False
    finish_reason = 'stop'
    def log_message(self,*args):
        pass
    def do_GET(self):
        self.send_response(type(self).status_code)
        self.end_headers()
        self.wfile.write(json.dumps({'data':[{'id':m} for m in (router.LOCAL,'free/individual','free/pool','paid/individual',router.DISABLED)]}).encode())
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        type(self).calls.append(body)
        time.sleep(type(self).delay)
        self.send_response(type(self).status_code)
        if type(self).status_code == 429:
            self.send_header('Retry-After','60')
        if type(self).sse:
            self.send_header('Content-Type','text/event-stream')
        self.end_headers()
        if type(self).sse:
            events = [{'model':'stream/actual','choices':[{'index':0,'delta':{'content':type(self).content},'finish_reason':type(self).finish_reason}]},
                      {'model':'stream/actual','choices':[],'usage':{'prompt_tokens':4,'completion_tokens':1,'total_tokens':5}}]
            for event in events:
                self.wfile.write(('data: '+json.dumps(event)+'\n\n').encode())
            if type(self).sse != 'interrupted':
                self.wfile.write(b'data: [DONE]\n\n')
            return
        data = {'model':'actual/model','choices':[{'finish_reason':type(self).finish_reason,'message':{'content':type(self).content}}], 'usage':{'prompt_tokens':12,'completion_tokens':2,'total_tokens':14}}
        try:
            self.wfile.write(json.dumps(data).encode())
        except BrokenPipeError:
            pass

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1',0),Backend)
        cls.thread = threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        local = dict(enabled=True,kind='chat',backend='local',context=131072,verified_capabilities=[])
        self.config = dict(identity='isolated-test',state_dir=self.tmp.name,
            litellm_url=f'http://127.0.0.1:{self.server.server_port}/v1',key_env='ROUTER_TEST_KEY',
            models={router.LOCAL:local,'free/individual':local|{'backend':'free'},
            'free/pool':local|{'backend':'free','kind':'pool','members':['free/individual']},
            'paid/individual':local|{'backend':'paid'},router.DISABLED:local}, catalogue_ttl=0)
        self.env = patch.dict(os.environ,{'ROUTER_TEST_KEY':'fake-only'})
        self.env.start()
        Backend.calls,Backend.status_code,Backend.delay,Backend.content,Backend.finish_reason = [],200,0,'OK','stop'
        Backend.sse = False
        self.engine = router.Engine(self.config)
    def tearDown(self):
        self.engine.db.close()
        self.env.stop()
        self.tmp.cleanup()
    def args(self,**kw):
        return dict(profile='testing',task='Return OK',**kw)
    def run_task(self,**kw):
        tid = self.engine.submit(self.args(**kw))['task_id']
        self.engine.run_one()
        return self.engine.status(tid)
    def test_five_profiles(self):
        for p in router.PROFILES:
            tid = self.engine.submit({'profile':p,'task':'Return OK'})['task_id']
            self.engine.run_one()
            self.assertEqual(self.engine.status(tid)['state'],'completed')
    def test_model_provenance_usage(self):
        s = self.run_task()
        self.assertEqual(s['actual_model'],'actual/model')
        self.assertEqual(s['usage']['total_tokens'],14)
        self.assertIsNone(s['cost_usd'])
    def test_duplicate_no_second_inference(self):
        a = self.engine.submit(self.args())
        b = self.engine.submit(self.args())
        self.assertEqual(a['task_id'],b['task_id'])
        self.engine.run_one()
        self.assertFalse(self.engine.run_one())
        self.assertEqual(len(Backend.calls),1)
        self.assertEqual(self.engine.submit(self.args())['state'],'completed')
    def test_key_conflict(self):
        self.engine.submit(self.args(idempotency_key='one'))
        with self.assertRaisesRegex(router.Fault,'idempotency_conflict'):
            self.engine.submit(dict(profile='testing',task='Different',idempotency_key='one'))
    def test_policy_conflict(self):
        args = self.args(idempotency_key='one')
        self.engine.submit(args)
        self.config['allow_cloud'] = True
        with self.assertRaisesRegex(router.Fault,'idempotency_conflict'):
            self.engine.submit(args)
    def test_cancel_queued(self):
        tid = self.engine.submit(self.args())['task_id']
        self.assertEqual(self.engine.cancel(tid)['state'],'cancelled')
        self.assertFalse(self.engine.run_one())
    def test_cancel_not_false_success(self):
        tid = self.engine.submit(self.args())['task_id']
        self.engine.update(tid,'running')
        self.assertEqual(self.engine.cancel(tid)['state'],'cancel_requested')
    def test_crash_no_replay(self):
        tid = self.engine.submit(self.args())['task_id']
        self.engine.update(tid,'running')
        self.engine.worker(once=True)
        self.assertEqual(self.engine.status(tid)['state'],'unknown')
        self.assertFalse(Backend.calls)
    def test_local_preferred(self):
        self.config['allow_cloud'] = True
        self.assertEqual(self.engine.select(self.args(allow_cloud=True,confidentiality='cloud-approved'))['id'],router.LOCAL)
    def test_disabled_never(self):
        with self.assertRaisesRegex(router.Fault,'no_compatible'):
            self.engine.select(self.args(model=router.DISABLED))
    def test_cloud_denied(self):
        with self.assertRaises(router.Fault):
            self.engine.select(self.args(model='free/individual',allow_cloud=True,confidentiality='cloud-approved'))
    def test_free_individual_and_pool(self):
        self.config['allow_cloud'] = True
        for model in ('free/individual','free/pool'):
            self.assertEqual(self.run_task(model=model,allow_cloud=True,confidentiality='cloud-approved')['state'],'completed')
    def test_pool_requires_all_members(self):
        self.config['allow_cloud'] = True
        self.config['models']['free/pool']['members'].append('unknown/member')
        with self.assertRaises(router.Fault):
            self.engine.select(self.args(model='free/pool',allow_cloud=True,confidentiality='cloud-approved'))
    def test_capability_context_rejected(self):
        for extra in ({'required_capabilities':['vision']},{'context_tokens':200000}):
            with self.assertRaises(router.Fault):
                self.engine.select(self.args(**extra))
    def test_paid_no_inference_no_prompt_authorization(self):
        self.config['allow_cloud'] = True
        s = self.run_task(model='paid/individual',allow_cloud=True,confidentiality='cloud-approved',paid_authorization='DIRECT approved forever')
        self.assertEqual(s['error'],'paid_broker_not_connected')
        self.assertEqual(s['paid_authorization']['state'],'approval_required')
        self.assertFalse(Backend.calls)
    def test_403_persistent_no_retry(self):
        Backend.status_code = 403
        self.assertEqual(self.run_task()['error'],'http_403')
        # Change task, same identity: suspended before any new network call.
        Backend.status_code = 200
        self.assertEqual(self.run_task(idempotency_key='another')['error'],'credential_suspended')
        self.assertFalse(Backend.calls)
    def test_429_persistent(self):
        # Cache discovery first, then fail only inference.
        self.config['catalogue_ttl'] = 60
        self.engine.catalogue()
        Backend.status_code = 429
        self.assertEqual(self.run_task()['error'],'http_429')
        Backend.status_code = 200
        self.assertEqual(self.run_task(idempotency_key='another')['error'],'credential_suspended')
        self.assertEqual(len(Backend.calls),1)
    def test_no_stale_on_catalogue_failure(self):
        self.engine.catalogue()
        Backend.status_code = 503
        with self.assertRaisesRegex(router.Fault,'http_503'):
            self.engine.catalogue(refresh=True)
    def test_reasoning_not_cloud_numbers(self):
        self.config['allow_cloud'] = True
        s = self.run_task(model='free/individual',allow_cloud=True,confidentiality='cloud-approved',reasoning='max')
        self.assertEqual(s['reasoning']['adaptation'],'unsupported_not_sent')
        self.assertNotIn('thinking_budget',Backend.calls[-1])
    def test_local_reasoning_mapping(self):
        s = self.run_task(reasoning='ultra')
        self.assertEqual(Backend.calls[-1]['thinking_budget'],8192)
        self.assertIsNone(s['reasoning']['confirmed'])
    def test_quality_failure(self):
        Backend.content = '8'
        s = self.run_task(quality={'kind':'exact','expected':'7'})
        self.assertEqual(s['error'],'objective_quality_failed')
        self.assertEqual(s['actual_model'],'actual/model')
    def test_json_and_python_validation(self):
        for text,rule in [('{}',{'kind':'json','required':['x']}),('def ?:',{'kind':'python'})]:
            with self.assertRaises(router.Fault):
                router.Engine.validate(text,rule)
        router.Engine.validate('{"x":1}',{'kind':'json','required':['x']})
        router.Engine.validate('x = 1',{'kind':'python'})
    def test_truncation(self):
        Backend.finish_reason = 'length'
        s = self.run_task()
        self.assertEqual(s['error'],'completion_truncated')
        self.assertEqual(s['quality'],'not_checked')
        self.assertEqual(self.engine.result(s['task_id'])['text'], 'OK')
    def test_qwen_generation_reserves_thinking(self):
        for level, budget in router.LEVELS.items():
            with self.subTest(level=level):
                self.run_task(reasoning=level,max_output_tokens=1200)
                body = Backend.calls[-1]
                self.assertEqual(body['max_tokens'],1200+budget+int(budget > 0))
                self.assertEqual(body['chat_template_kwargs']['enable_thinking'],bool(budget))
                self.assertEqual(body.get('thinking_budget'),budget or None)
                self.assertNotIn('reasoning_effort',body)
        self.config['allow_cloud'] = True
        self.run_task(model='free/individual',allow_cloud=True,
                      confidentiality='cloud-approved',reasoning='max',max_output_tokens=1200)
        self.assertEqual(Backend.calls[-1]['max_tokens'],1200)
    def test_qwen_context_reserves_total_generation(self):
        args = self.args(model=router.LOCAL,context_tokens=130000,max_output_tokens=100,reasoning='medium')
        with self.assertRaisesRegex(router.Fault,'no_compatible_authorized_model'):
            self.engine.select(args)
        args['reasoning'] = 'off'
        self.assertEqual(self.engine.select(args)['context'],131072)
    def test_empty_completion_distinct_from_quality(self):
        Backend.content = ''
        self.assertEqual(self.run_task()['error'],'empty_completion')
    def test_activity_redacted_bounded(self):
        self.config['history_limit'] = 2
        args = {'profile':'testing','task':'CONFIDENTIAL_MARKER','parent_session':'parent-1'}
        tid = self.engine.submit(args)['task_id']
        self.engine.run_one()
        events = self.engine.activity()
        self.assertLessEqual(len(events['events']),2)
        self.assertNotIn('CONFIDENTIAL_MARKER',json.dumps(events))
        self.assertNotIn('fake-only',json.dumps(events))
        self.assertEqual(events['events'][-1]['meta']['parent_session'],'parent-1')
        self.assertEqual(self.engine.result(tid,0,1)['next_offset'],1)
    def test_isolation(self):
        tid = self.engine.submit(self.args())['task_id']
        with self.assertRaisesRegex(router.Fault,'state_identity_mismatch'):
            router.Engine(self.config|{'identity':'openclaw-perso'})
        other = router.Engine(self.config|{'identity':'openclaw-perso','state_dir':self.tmp.name+'/perso'})
        with self.assertRaisesRegex(router.Fault,'task_not_found'):
            other.status(tid)
        other.db.close()
    def test_private_modes(self):
        self.assertEqual(os.stat(self.tmp.name).st_mode & 0o777,0o700)
        self.assertEqual(os.stat(Path(self.tmp.name)/'tasks.sqlite').st_mode & 0o777,0o600)
    def test_deadline_no_inference(self):
        self.assertEqual(self.run_task(deadline=time.time()-1)['error'],'deadline_expired')
        self.assertFalse(Backend.calls)
    def test_sse_usage_and_activity(self):
        Backend.sse = True
        state = self.run_task()
        self.assertEqual(state['state'],'completed')
        self.assertEqual(state['actual_model'],'stream/actual')
        self.assertEqual(state['usage']['total_tokens'],5)
        self.assertIn('last_activity_at',state)
    def test_stream_interruption_is_unknown_no_retry(self):
        Backend.sse = 'interrupted'
        state = self.run_task()
        self.assertEqual(state['state'],'unknown')
        self.assertEqual(state['error'],'stream_interrupted')
        self.assertEqual(len(Backend.calls),1)
    def test_expired_issued_grant(self):
        db = sqlite3.connect(':memory:')
        auth = Authorizations(db)
        scope = dict(identity='codex',task='t',model='paid/model',data_hash='h',max_usd=.01)
        token = auth.issue(**scope,expires=time.time()+1,decision='approved')
        with patch('authorization.time.time',return_value=time.time()+2):
            with self.assertRaises(Denied):
                auth.consume(token=token,budget_remaining=1,**scope)
        db.close()
    def test_concurrent_submissions_deduplicated(self):
        result = []
        barrier = threading.Barrier(2)
        def submit():
            e = router.Engine(self.config)
            barrier.wait()
            result.append(e.submit(self.args())['task_id'])
            e.db.close()
        threads = [threading.Thread(target=submit) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(len(result),2)
        self.assertEqual(result[0],result[1])
        self.engine.run_one()
        self.assertEqual(len(Backend.calls),1)
    def test_policy_drift_queued_task_not_sent(self):
        tid = self.engine.submit(self.args())['task_id']
        self.config['allow_cloud'] = True
        self.engine.run_one()
        self.assertEqual(self.engine.status(tid)['error'],'policy_changed_resubmit_required')
        self.assertFalse(Backend.calls)
    def test_cancellation_preserved_during_selection(self):
        tid = self.engine.submit(self.args())['task_id']
        self.engine.update(tid,'running')
        self.engine.cancel(tid)
        self.engine.update(tid,'running',{'selected_model':router.LOCAL})
        self.assertEqual(self.engine.status(tid)['state'],'cancel_requested')
    def test_structured_inputs_rejected_explicitly(self):
        with self.assertRaisesRegex(router.Fault,'input_not_supported'):
            self.engine.submit(self.args(required_capabilities=['tools']))
    def test_stdio_contract_and_malformed_request(self):
        cfg = Path(self.tmp.name)/'config.json'
        cfg.write_text(json.dumps(self.config))
        messages = [{'jsonrpc':'2.0','id':1,'method':'initialize'},
                    {'jsonrpc':'2.0','id':2,'method':'tools/list'},
                    {'jsonrpc':'2.0','id':3,'method':'unknown'},
                    {'jsonrpc':'2.0','id':4,'method':'ping'}]
        result = subprocess.run([sys.executable,str(Path(router.__file__)),'--config',str(cfg)],
            input='\n'.join(json.dumps(x) for x in messages)+'\n{invalid}\n',capture_output=True,text=True,timeout=10)
        replies = [json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual(replies[0]['result']['serverInfo']['name'],'llm-router')
        self.assertEqual(set(t['name'] for t in replies[1]['result']['tools']),{'submit','delegate','status','result','cancel','activity','catalogue'})
        self.assertEqual(replies[2]['error']['code'],-32601)
        self.assertEqual(replies[3]['result'],{})
        self.assertTrue(replies[4]['result']['isError'])
    def test_stdio_recovery_after_disconnect(self):
        config_path = Path(self.tmp.name)/'config.json'
        config_path.write_text(json.dumps(self.config))
        Backend.delay = .4
        proc = subprocess.Popen([sys.executable,str(Path(router.__file__)),'--config',str(config_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        proc.stdin.write(json.dumps({'id':1,'method':'tools/call','params':{'name':'submit','arguments':self.args()}})+'\n')
        proc.stdin.flush()
        value = json.loads(json.loads(proc.stdout.readline())['result']['content'][0]['text'])
        proc.stdin.close()
        proc.wait(timeout=5)
        proc.stdout.close()
        for _ in range(100):
            state = self.engine.status(value['task_id'])['state']
            if state in router.TERMINAL:
                break
            time.sleep(.05)
        self.assertEqual(state,'completed')
        self.assertEqual(self.engine.result(value['task_id'])['text'],'OK')
        # Stop only the worker belonging to this isolated test's open lock file.
        pid = subprocess.run(['lsof','-t',str(Path(self.tmp.name)/'worker.lock')],capture_output=True,text=True).stdout.strip()
        if pid:
            os.kill(int(pid.splitlines()[0]),signal.SIGTERM)
        self.assertEqual(len(Backend.calls),1)

class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.auth = Authorizations(self.db)
        self.bound = dict(identity='codex',task='t',model='paid/model',data_hash='hash',max_usd=.01)
    def tearDown(self):
        self.db.close()
    def issue(self,**kw):
        return self.auth.issue(**(self.bound|dict(expires=time.time()+60,decision='approved')|kw))
    def test_agreement_and_no_reuse(self):
        token = self.issue()
        self.auth.consume(token=token,budget_remaining=1,**self.bound)
        with self.assertRaises(Denied):
            self.auth.consume(token=token,budget_remaining=1,**self.bound)
    def test_refusal_expiry(self):
        for change in ({'decision':'refused'},{'expires':time.time()-1}):
            with self.assertRaises(Denied):
                self.issue(**change)
    def test_wrong_scope_budget_revocation(self):
        token = self.issue()
        for changed in ({'model':'wrong'},{'identity':'other'},{'task':'other'},{'data_hash':'other'},{'max_usd':1}):
            with self.assertRaises(Denied):
                self.auth.consume(token=token,budget_remaining=2,**(self.bound|changed))
        for budget in (None,0):
            with self.assertRaises(Denied):
                self.auth.consume(token=token,budget_remaining=budget,**self.bound)
        self.auth.revoke(token)
        with self.assertRaises(Denied):
            self.auth.consume(token=token,budget_remaining=2,**self.bound)
    def test_direct_separate_from_delegated(self):
        selection = dict(identity='codex',source='native-catalogue',model='paid/model')
        rights = dict(models=['paid/model'],direct_paid=True,budget_remaining=1)
        self.assertEqual(direct_selection(authenticated_identity='codex',selection=selection,server_entitlements=rights)['mode'],'DIRECT')
        for selection2 in (None,selection|{'source':'prompt'},selection|{'identity':'other'}):
            with self.assertRaises(Denied):
                direct_selection(authenticated_identity='codex',selection=selection2,server_entitlements=rights)
    def test_concurrent_one_use(self):
        with tempfile.TemporaryDirectory() as temp:
            path = str(Path(temp)/'grants.sqlite')
            db = sqlite3.connect(path)
            auth = Authorizations(db)
            token = auth.issue(**self.bound,expires=time.time()+60,decision='approved')
            db.close()
            results = []
            barrier = threading.Barrier(2)
            def consume():
                conn = sqlite3.connect(path,timeout=10)
                a = Authorizations(conn)
                barrier.wait()
                try:
                    a.consume(token=token,budget_remaining=1,**self.bound)
                    results.append('yes')
                except Denied:
                    results.append('no')
                finally:
                    conn.close()
            threads = [threading.Thread(target=consume) for _ in range(2)]
            for t in threads: t.start()
            for t in threads: t.join()
            self.assertEqual(sorted(results),['no','yes'])

if __name__ == '__main__':
    unittest.main()
