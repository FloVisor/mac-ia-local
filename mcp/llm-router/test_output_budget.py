"""Output reserves and bounded truncation recovery; no model inference."""
import unittest
import time
from unittest.mock import patch

import router
import test_router as fixtures


class OutputBudgetTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.Tests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.Tests.tearDownClass.__func__)
    setUp = fixtures.Tests.setUp
    tearDown = fixtures.Tests.tearDown
    args = fixtures.Tests.args
    run_task = fixtures.Tests.run_task

    def budget(self, **kw):
        return router.output_budget(self.args(**kw), router.LOCAL)

    def test_medium_high_max_preserve_entire_answer_and_boundary(self):
        for level in ('medium', 'high', 'max'):
            for reserve in (1, 700, 1200):
                with self.subTest(level=level, reserve=reserve):
                    budget = self.budget(reasoning=level, max_output_tokens=reserve)
                    self.assertEqual(budget['mode'], 'hard')
                    self.assertEqual(budget['source'], 'caller')
                    self.assertEqual(budget['requested_answer_tokens'], reserve)
                    self.assertEqual(budget['answer_tokens'], reserve)
                    self.assertEqual(budget['thinking_tokens'], router.LEVELS[level])
                    self.assertEqual(budget['thinking_boundary_tokens'], 1)
                    self.assertEqual(budget['max_tokens_sent'], reserve + router.LEVELS[level] + 1)

    def test_explicit_effort_and_default_across_client_identities(self):
        # Literal contract values catch accidental changes to LEVELS too.
        expected = {'off': 0, 'minimal': 0, 'low': 512, 'medium': 2048,
                    'high': 8192, 'max': 16384, 'ultra': 8192}
        for identity in ('codex', 'openclaw-pro', 'openclaw-perso'):
            engine = router.Engine(self.config | {
                'identity': identity, 'state_dir': self.tmp.name + '/' + identity})
            try:
                for level, tokens in list(expected.items()) + [(None, 2048)]:
                    with self.subTest(identity=identity, level=level):
                        args = self.args(task_type='review', complexity='standard')
                        if level is not None:
                            args['reasoning'] = level
                        with patch.object(router, 'stream_chat', return_value=self.completion('stop')) as stream:
                            tid = engine.submit(args)['task_id']
                            engine.run_one()
                        status = engine.status(tid)
                        self.assertEqual(status['state'], 'completed')
                        self.assertEqual(status['reasoning']['requested'], level or 'medium')
                        body = stream.call_args.args[2]
                        self.assertEqual(body.get('thinking_budget', 0), tokens)
                        self.assertEqual(body['max_tokens'], 3072 + tokens + int(tokens > 0))
                        self.assertEqual(body['chat_template_kwargs']['enable_thinking'], tokens > 0)
            finally:
                engine.db.close()

    def test_explicit_effort_survives_size_recovery(self):
        for level, tokens in [('low', 512), ('high', 8192), ('max', 16384)]:
            with self.subTest(level=level):
                with patch.object(router, 'stream_chat', side_effect=[self.completion('length'), self.completion('stop')]) as stream:
                    status = self.run_task(reasoning=level, task_type='review')
                self.assertEqual(status['state'], 'completed')
                self.assertEqual(stream.call_count, 2)
                for call, answer in zip(stream.call_args_list, (3072, 6144)):
                    self.assertEqual(call.args[2]['thinking_budget'], tokens)
                    self.assertEqual(call.args[2]['max_tokens'], answer + tokens + 1)

    def test_auto_small_hint_uses_analysis_policy(self):
        budget = self.budget(task_type='diagnosis', output_budget_mode='auto', max_output_tokens=700)
        self.assertEqual(budget['requested_answer_tokens'], 700)
        self.assertEqual(budget['answer_tokens'], 3072)
        self.assertEqual(budget['mode'], 'auto')

    def test_automatic_task_floors(self):
        for task_type, reserve in [('review', 3072), ('analysis', 3072), ('diagnosis', 3072),
                                   ('comparison', 3072), ('synthesis', 3072), ('architecture', 3072),
                                   ('documentation', 3072), ('coding', 4096), ('testing', 2048)]:
            with self.subTest(task_type=task_type):
                budget = self.budget(task_type=task_type)
                self.assertEqual(budget['answer_tokens'], reserve)
                self.assertEqual(budget['source'], 'task_policy')

    def test_long_utf8_task_has_larger_reserve(self):
        args = self.args(task_type='diagnosis')
        args['task'] = 'é' * 6000
        self.assertEqual(router.output_budget(args, router.LOCAL)['answer_tokens'], 6144)

    def test_explicit_hard_cap_survives_long_task(self):
        args = self.args(max_output_tokens=700, output_budget_mode='hard')
        args['task'] = 'audio ' * 2500
        self.assertEqual(router.output_budget(args, router.LOCAL)['answer_tokens'], 700)

    def test_invalid_mode_and_oversized_automatic_hint_rejected(self):
        for args, error in [({'output_budget_mode': 'hard'}, 'invalid_output_budget_mode'),
                            ({'output_budget_mode': 'invalid'}, 'invalid_output_budget_mode')]:
            with self.subTest(args=args), self.assertRaisesRegex(router.Fault, error):
                # Invalid contracts are rejected at the public submission boundary.
                self.engine.submit(self.args(**args))
        # The automatic ceiling belongs to LOCAL, only known during selection.
        with self.assertRaisesRegex(router.Fault, 'auto_output_budget_too_large'):
            self.budget(output_budget_mode='auto', max_output_tokens=8193)

    def test_cloud_limits_unchanged(self):
        for level in ('medium', 'high', 'max'):
            args = self.args(reasoning=level, max_output_tokens=700, output_budget_mode='auto')
            budget = router.output_budget(args, 'free/individual')
            self.assertEqual(budget['answer_tokens'], 700)
            self.assertEqual(budget['max_tokens_sent'], 700)
            self.assertEqual(budget['thinking_tokens'], 0)
        self.assertEqual(router.output_budget(self.args(), 'free/individual')['max_tokens_sent'], 2048)

    @staticmethod
    def completion(finish):
        return {'model': 'actual/local', 'choices': [{'finish_reason': finish,
                'message': {'content': 'Analyse audio : moteur identifié, preuves et contrôle français.'}}],
                'usage': {'prompt_tokens': 40, 'completion_tokens': 30}}, None

    def test_local_auto_truncation_has_one_targeted_larger_retry(self):
        with patch.object(router, 'stream_chat', side_effect=[self.completion('length'), self.completion('stop')]) as stream:
            status = self.run_task(task_type='diagnosis')
        self.assertEqual(status['state'], 'completed')
        self.assertEqual(stream.call_count, 2)
        first, second = [call.args[2] for call in stream.call_args_list]
        self.assertEqual(first['max_tokens'], 3072 + router.LEVELS['medium'] + 1)
        self.assertEqual(second['max_tokens'], 6144 + router.LEVELS['medium'] + 1)
        self.assertEqual(first['thinking_budget'], second['thinking_budget'])

    def test_actual_payload_keeps_answer_when_thinking_uses_budget_and_boundary(self):
        for level in ('medium', 'high', 'max'):
            with self.subTest(level=level):
                response, cost = self.completion('stop')
                used = router.LEVELS[level] + 1
                response['usage'] = {'completion_tokens': used + 1500,
                    'completion_tokens_details': {'reasoning_tokens': used}}
                with patch.object(router, 'stream_chat', return_value=(response, cost)) as stream:
                    status = self.run_task(task_type='review', reasoning=level)
                self.assertEqual(status['state'], 'completed')
                sent = stream.call_args.args[2]
                self.assertEqual(sent['max_tokens'] - used, 3072)
                self.assertEqual(sent['thinking_budget'], router.LEVELS[level])

    def test_recovery_keeps_original_request_and_dedupe(self):
        args = self.args(task_type='review')
        tid = self.engine.submit(args)['task_id']
        with patch.object(router, 'stream_chat', side_effect=[self.completion('length'), self.completion('stop')]):
            self.engine.run_one()
        import json
        self.assertEqual(json.loads(self.engine.get(tid)['request']), args)
        self.assertEqual(self.engine.submit(args)['task_id'], tid)
        status = self.engine.status(tid)
        self.assertEqual(status['generation_limits']['source'], 'recovery_policy')
        self.assertEqual(status['generation_limits']['answer_tokens'], 6144)
        self.assertEqual(status['attempts'][0]['error'], 'completion_truncated')

    def test_internal_reserve_override_cannot_be_supplied_by_client(self):
        with self.assertRaisesRegex(router.Fault, 'unsupported_argument'):
            self.engine.submit(self.args(_auto_answer_tokens=999999))

    def test_explicit_hard_contract_explains_blocked_recovery(self):
        with patch.object(router, 'stream_chat', return_value=self.completion('length')):
            status = self.run_task(max_output_tokens=700)
        self.assertEqual(status['recovery_blocked'], 'caller_hard_cap')
        self.assertEqual(status['generation_limits']['source'], 'caller')
        self.assertEqual(status['next_action'], 'resubmit_without_cap_or_explicitly_choose_auto')

    def test_auto_ceiling_has_no_useless_same_size_retry(self):
        with patch.object(router, 'stream_chat', return_value=self.completion('length')) as stream:
            status = self.run_task(output_budget_mode='auto', max_output_tokens=8192)
        self.assertEqual(status['error'], 'completion_truncated')
        self.assertEqual(status['recovery_blocked'], 'automatic_answer_ceiling')
        self.assertEqual(stream.call_count, 1)

    def test_second_truncation_is_terminal(self):
        with patch.object(router, 'stream_chat', return_value=self.completion('length')) as stream:
            status = self.run_task(task_type='diagnosis')
        self.assertEqual(status['state'], 'failed')
        self.assertEqual(status['error'], 'completion_truncated')
        self.assertEqual(stream.call_count, 2)

    def test_recovery_caps_answer_at_8192(self):
        with patch.object(router, 'stream_chat', side_effect=[self.completion('length'), self.completion('stop')]) as stream:
            status = self.run_task(task_type='diagnosis', output_budget_mode='auto', max_output_tokens=6144)
        self.assertEqual(status['state'], 'completed')
        self.assertEqual(stream.call_args_list[1].args[2]['max_tokens'], 8192 + router.LEVELS['medium'] + 1)

    def test_context_readmission_prevents_second_dispatch(self):
        self.config['models'][router.LOCAL]['context'] = 6500
        with patch.object(router, 'stream_chat', return_value=self.completion('length')) as stream:
            status = self.run_task(task_type='diagnosis')
        self.assertEqual(status['state'], 'failed')
        self.assertEqual(status['error'], 'completion_truncated')
        self.assertEqual(stream.call_count, 1)

    def test_hard_small_reserve_never_retried(self):
        with patch.object(router, 'stream_chat', return_value=self.completion('length')) as stream:
            status = self.run_task(max_output_tokens=700)
        self.assertEqual(status['state'], 'failed')
        self.assertEqual(status['error'], 'completion_truncated')
        self.assertEqual(stream.call_count, 1)
        self.assertEqual(stream.call_args.args[2]['max_tokens'], 700 + router.LEVELS['medium'] + 1)

    def test_explicit_model_does_not_authorize_recovery(self):
        with patch.object(router, 'stream_chat', return_value=self.completion('length')) as stream:
            status = self.run_task(model=router.LOCAL)
        self.assertEqual(status['error'], 'completion_truncated')
        self.assertEqual(stream.call_count, 1)

    def test_cancellation_after_truncation_prevents_second_dispatch(self):
        tid = self.engine.submit(self.args(task_type='diagnosis'))['task_id']
        def truncated(*args, **kw):
            self.engine.cancel(tid)
            return self.completion('length')
        with patch.object(router, 'stream_chat', side_effect=truncated) as stream:
            self.engine.run_one()
        self.assertEqual(self.engine.status(tid)['state'], 'cancelled')
        self.assertEqual(stream.call_count, 1)

    def test_expired_deadline_after_truncation_prevents_second_dispatch(self):
        deadline = time.time() + 60
        clock = patch.object(router.time, 'time', return_value=deadline + 1)
        def truncated(*args, **kw):
            clock.start()
            return self.completion('length')
        try:
            with patch.object(router, 'stream_chat', side_effect=truncated) as stream:
                status = self.run_task(task_type='diagnosis', deadline=deadline)
        finally:
            clock.stop()
        self.assertEqual(status['error'], 'deadline_expired')
        self.assertEqual(stream.call_count, 1)

    def test_recovery_catalogue_auth_failure_prevents_second_dispatch(self):
        select = self.engine.select
        selected = False
        def selection(*args, **kw):
            nonlocal selected
            if selected:
                raise router.Fault('http_403', status=403)
            selected = True
            return select(*args, **kw)
        with patch.object(self.engine, 'select', side_effect=selection), \
             patch.object(router, 'stream_chat', return_value=self.completion('length')) as stream:
            status = self.run_task(task_type='diagnosis')
        self.assertEqual(status['error'], 'http_403')
        self.assertEqual(stream.call_count, 1)


if __name__ == '__main__':
    unittest.main()
