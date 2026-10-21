"""End-to-end worker policy simulations: no external HTTP or credentials."""
import tempfile
import time
import unittest
from unittest.mock import patch

import router


class ContextAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config = dict(identity='isolated-test', state_dir=self.tmp.name,
                           allow_cloud=True, models={
            'local/8k': dict(enabled=True, kind='chat', backend='local', context=8192),
            'paid/test': dict(enabled=True, kind='chat', backend='paid', context=131072)})
        self.engine = router.Engine(self.config)
        self.catalogue = patch.object(self.engine, 'catalogue', side_effect=lambda: [
            value | {'id': key} for key, value in self.config['models'].items()])
        self.catalogue.start()

    def tearDown(self):
        self.catalogue.stop()
        self.engine.db.close()
        self.tmp.cleanup()

    def run_task(self, **kwargs):
        tid = self.engine.submit(dict(profile='testing', task='x' * 4000,
                                      reasoning='off', max_output_tokens=1000) | kwargs)['task_id']
        self.engine.run_one()
        return self.engine.status(tid)

    def test_8k_task_fits_without_truncating(self):
        with patch.object(self.engine, 'infer', return_value=('OK', {})) as infer:
            state = self.run_task()
        self.assertEqual(state['state'], 'completed')
        self.assertEqual(infer.call_args.args[0]['task'], 'x' * 4000)
        self.assertEqual(infer.call_args.args[1]['id'], 'local/8k')

    def test_over_8k_returns_to_codex_without_paid_dispatch(self):
        with patch.object(self.engine, 'infer') as infer:
            state = self.run_task(task='x' * 8193, allow_cloud=True,
                                  confidentiality='cloud-approved')
        self.assertEqual(state['error'], 'no_compatible_authorized_model')
        self.assertTrue(state['return_to_gpt'])
        infer.assert_not_called()

    def test_unavailable_model_returns_without_dispatch(self):
        self.config['models'].clear()
        with patch.object(self.engine, 'infer') as infer:
            state = self.run_task()
        self.assertTrue(state['return_to_gpt'])
        infer.assert_not_called()

    def test_429_respects_retry_after_without_retry_or_fallback(self):
        until = time.time() + 60
        with patch.object(self.engine, 'infer', side_effect=router.Fault('http_429', 429, until)) as infer:
            state = self.run_task()
        self.assertEqual(infer.call_count, 1)
        self.assertTrue(state['return_to_gpt'])
        self.assertEqual(self.engine.blocked('credential:isolated-test')['expires'], until)

    def test_exhausted_quota_without_hint_remains_blocked(self):
        with patch.object(self.engine, 'infer', side_effect=router.Fault('http_429', 429)) as infer:
            self.run_task()
        self.assertEqual(infer.call_count, 1)
        self.assertIsNone(self.engine.blocked('credential:isolated-test')['expires'])

    def test_tool_transport_refused_instead_of_omitted(self):
        with self.assertRaisesRegex(router.Fault, 'structured_tools_or_vision_input_not_supported'):
            self.engine.submit(dict(profile='testing', task='read only', required_capabilities=['tools']))

    def test_caller_estimate_cannot_hide_input(self):
        with patch.object(self.engine, 'infer') as infer:
            state = self.run_task(task='x' * 8193, context_tokens=1)
        self.assertTrue(state['return_to_gpt'])
        infer.assert_not_called()
