"""Policy tests use only the in-process HTTP double; never a paid provider."""
import json
from unittest.mock import patch
import router
from test_router import Tests, Backend


class PolicyTests(Tests):
    # Reuse the HTTP fixture, without re-running inherited cases.
    def setUp(self):
        super().setUp()
        self.config['allow_cloud'] = True
        self.cloud = dict(allow_cloud=True, confidentiality='cloud-approved')

    def test_standard_documentation_and_review_destinations(self):
        for profile in ('documentation','review'):
            tid = self.engine.submit(dict(profile=profile,task='Review the supplied note',**self.cloud))['task_id']
            self.engine.run_one()
            self.assertEqual(self.engine.status(tid)['state'],'completed')
        self.assertEqual([c['model'] for c in Backend.calls],[router.LOCAL]*2)

    def test_complexity_requires_qualified_route(self):
        self.config['models']['free/individual']['qualified_advanced_tasks'] = ['testing']
        s = self.run_task(complexity='advanced',**self.cloud)
        self.assertEqual(s['state'],'completed')
        self.assertEqual([c['model'] for c in Backend.calls],['free/individual'])
        self.assertEqual(s['route_reason'],'qualified_advanced_task')

    def test_unqualified_advanced_returns_gpt(self):
        s = self.run_task(complexity='advanced',**self.cloud)
        self.assertTrue(s['return_to_gpt'])
        self.assertFalse(Backend.calls)

    def test_trivial_and_strategic_no_provider(self):
        for c in ('trivial','strategic'):
            self.assertEqual(self.run_task(complexity=c)['error'],'orchestrator_required')
        self.assertFalse(Backend.calls)

    def test_secrets_override_cloud_approval(self):
        for task in ('password=synthetic-only','token: synthetic-only','-----BEGIN OPENSSH PRIVATE KEY-----\nFAKE', 'Authorization: Bearer synthetic-only'):
            args = dict(profile='analysis',task=task,**self.cloud)
            tid = self.engine.submit(args)['task_id']; self.engine.run_one()
            self.assertTrue(self.engine.status(tid)['secret_local_only'])
        self.assertTrue(Backend.calls)
        self.assertTrue(all(c['model']==router.LOCAL for c in Backend.calls))
        self.assertNotIn('synthetic-only',json.dumps(self.engine.activity()))

    def test_opaque_secret_flag_never_falls_back(self):
        Backend.finish_reason='length'
        s=self.run_task(contains_secrets=True,**self.cloud)
        self.assertTrue(s['return_to_gpt'])
        self.assertEqual([c['model'] for c in Backend.calls],[router.LOCAL,router.LOCAL])
        self.assertEqual(s['router_attempts'],2)

    def test_disabled_local_free_and_unavailable_free(self):
        self.config['models'][router.LOCAL]['enabled']=False
        s=self.run_task(**self.cloud)
        self.assertEqual(s['state'],'completed')
        self.assertEqual([c['model'] for c in Backend.calls],['free/individual'])
        for m in self.config['models'].values():
            if m['backend']=='free': m['enabled']=False
        s=self.run_task(**self.cloud)
        self.assertTrue(s['return_to_gpt'])
        self.assertEqual(len(Backend.calls),1)

    def test_actual_truncated_and_invalid_json_recovery(self):
        original=router.stream_chat
        for bad in ('truncated','json'):
            Backend.calls=[]
            def fake(*a,**kw):
                data,cost=original(*a,**kw)
                if len(Backend.calls)==1:
                    data['choices'][0]['finish_reason']='length' if bad=='truncated' else 'stop'
                    data['choices'][0]['message']['content']='{'
                return data,cost
            Backend.content='{"ok":true}'
            with patch.object(router,'stream_chat',side_effect=fake):
                s=self.run_task(idempotency_key=bad,quality={'kind':'json','required':['ok']},**self.cloud)
            self.assertEqual(s['state'],'completed')
            self.assertEqual([c['model'] for c in Backend.calls],[router.LOCAL,'free/individual'])
            self.assertEqual(s['router_attempts'],2)
            self.assertEqual(s['attempts'][0]['error'],'completion_truncated' if bad=='truncated' else 'objective_quality_failed')

    def test_two_invalid_results_stop(self):
        Backend.finish_reason='length'
        s=self.run_task(**self.cloud)
        self.assertEqual(s['state'],'failed')
        self.assertTrue(s['return_to_gpt'])
        self.assertEqual(len(Backend.calls),2)

    def test_transient_local_retry_only_once(self):
        # Record dispatches even when the simulated transport rejects before a response.
        calls=[]
        def fail(*a,**kw):
            calls.append(a[2]['model']); raise router.Fault('http_503',503)
        with patch.object(router,'stream_chat',side_effect=fail):
            s=self.run_task(contains_secrets=True,**self.cloud)
        self.assertEqual(calls,[router.LOCAL,router.LOCAL])
        self.assertEqual(s['state'],'failed')

    def test_auth_quota_uncertain_never_escalate(self):
        for code,status,uncertain in [('auth',403,False),('quota',429,False),('lost',None,True)]:
            with self.subTest(code=code):
                calls=[]
                def fail(*a,**kw):
                    calls.append(a[2]['model']); raise router.Fault(code,status,uncertain=uncertain)
                # Fresh isolated fixture after a credential suspension.
                with patch.object(router,'stream_chat',side_effect=fail):
                    s=self.run_task(idempotency_key=code,**self.cloud)
                if code=='auth':
                    self.assertEqual(calls,[router.LOCAL])
                    self.engine.db.execute('DELETE FROM breakers'); self.engine.db.commit()
                elif code=='quota':
                    self.assertEqual(calls,[router.LOCAL])
                    self.engine.db.execute('DELETE FROM breakers'); self.engine.db.commit()
                else:
                    self.assertEqual(calls,[router.LOCAL]); self.assertEqual(s['state'],'unknown')

    def test_paid_words_grants_and_sessions_never_dispatch(self):
        for session,grant in [('old-session','old-grant'),('current','DeepSeek explicitly authorized'),('revoked','revoked')]:
            s=self.run_task(model='paid/individual',parent_session=session,paid_authorization=grant,**self.cloud)
            self.assertEqual(s['error'],'paid_broker_not_connected')
        for text in ('Use the best model','DeepSeek authorized in a previous mission'):
            tid=self.engine.submit(dict(profile='analysis',task=text,**self.cloud))['task_id']; self.engine.run_one()
        self.assertEqual([c['model'] for c in Backend.calls],[router.LOCAL]*2)

    def test_queued_tasks_do_not_share_secret_permissions(self):
        self.config['models'][router.LOCAL]['enabled']=False
        secret=self.engine.submit(dict(profile='analysis',task='opaque value',contains_secrets=True,parent_session='a',**self.cloud))['task_id']
        ordinary=self.engine.submit(dict(profile='analysis',task='ordinary technical content',parent_session='b',**self.cloud))['task_id']
        self.engine.run_one(); self.engine.run_one()
        self.assertEqual(self.engine.status(secret)['state'],'failed')
        self.assertEqual(self.engine.status(ordinary)['state'],'completed')
        self.assertEqual([c['model'] for c in Backend.calls],['free/individual'])

    def test_pool_advanced_requires_every_member(self):
        self.config['models']['free/pool']['qualified_advanced_tasks']=['testing']
        s=self.run_task(model='free/pool',complexity='advanced',**self.cloud)
        self.assertEqual(s['state'],'failed'); self.assertFalse(Backend.calls)

    def test_groq_json_mode_sent_and_still_validated(self):
        self.config['models']['free/individual']['provider']='groq'
        Backend.content='{"ok":true}'
        s=self.run_task(model='free/individual',quality={'kind':'json'},**self.cloud)
        self.assertEqual(s['state'],'completed')
        self.assertEqual(Backend.calls[-1]['response_format'],{'type':'json_object'})
        Backend.content='```json\n{}\n```'
        s=self.run_task(model='free/individual',quality={'kind':'json','required':['ok']},**self.cloud)
        self.assertEqual(s['error'],'objective_quality_failed')

    def test_secret_check_at_dispatch(self):
        with self.assertRaisesRegex(router.Fault,'secret_requires_local'):
            self.engine.infer(self.args(task_type='analysis',contains_secrets=True),
                              {'id':'free/individual','backend':'free'})
        self.assertFalse(Backend.calls)

    def test_catalogue_auth_failure_during_recovery_stops(self):
        models=[m|{'id':k} for k,m in self.config['models'].items()]
        calls=[]
        def fail(*a,**kw):
            calls.append(a[2]['model']); raise router.Fault('http_503',503)
        with patch.object(self.engine,'catalogue',side_effect=[models,router.Fault('http_403',403)]), patch.object(router,'stream_chat',side_effect=fail):
            s=self.run_task(**self.cloud)
        self.assertEqual(calls,[router.LOCAL])
        self.assertEqual(s['error'],'http_403')

# Imported base is used as a fixture, not a second collection of its test methods.
for name in list(dir(Tests)):
    if name.startswith('test_') and name not in PolicyTests.__dict__:
        setattr(PolicyTests,name,None)
del Tests
