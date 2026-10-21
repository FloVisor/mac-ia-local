import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import manage
from adapter import chat_request, OMLX
from reasoning_policy import reasoning_policy


class ReasoningPolicyTests(unittest.TestCase):
    def test_only_documented_identity_efforts_are_advertised(self):
        expected = {
            OMLX: ['none', 'minimal', 'low', 'medium', 'high', 'max'],
            'free-groq/gpt-oss-120b': ['low', 'medium', 'high'],
            'free-groq/qwen3.8-27b': ['low', 'medium', 'high'],
            'paid-openrouter/deepseek-v4.1-flash-1017': ['none', 'low', 'high'],
            'paid-openrouter/glm-5.3': ['low', 'high'],
        }
        for slug, efforts in expected.items():
            with self.subTest(slug=slug):
                policy = reasoning_policy(slug)
                self.assertEqual([v['effort'] for v in policy['levels']], efforts)
                self.assertIn(policy['default'], efforts)
                for effort in efforts:
                    body, trace = chat_request({'model': slug, 'input': 'offline test',
                                                'reasoning': {'effort': effort}}, {})
                    if slug != OMLX:
                        self.assertEqual(body['reasoning_effort'], effort)
                        self.assertEqual(trace['expected_downstream_effort'], effort)
                        self.assertNotIn('thinking_budget', body)
                    self.assertIsNone(trace['applied_effort'])
                self.assertFalse(set(efforts) & set(policy['excluded']))

    def test_unknown_models_and_pools_fail_closed_without_padding(self):
        for slug in ['new/model', 'free/task-fast', 'free/task-coding',
                     'free/task-reasoning', 'free/task-long-context', 'paid/task-advanced',
                     'free-openrouter/dots-3-note-preview:free',
                     'free-openrouter/north-mini-code:free', 'local-ollama/qwen3:4b-instruct']:
            with self.subTest(slug=slug):
                self.assertEqual(reasoning_policy(slug)['levels'], [])
                self.assertIn('unqualified', reasoning_policy(slug)['status'])
        for slug in ['free-mistral/ministral-8b-2512', 'free-mistral/codestral-2508']:
            self.assertEqual(reasoning_policy(slug)['status'], 'no_control')
            self.assertEqual(reasoning_policy(slug)['levels'], [])

    def test_sync_preserves_routes_names_context_and_gpt_across_cycles(self):
        ids = {OMLX, 'free-groq/gpt-oss-120b', 'free-mistral/codestral-2508',
               'paid-openrouter/glm-5.3', 'free/task-coding'}
        gpt = {'slug': 'gpt-6.1-sol', 'display_name': 'GPT-6.1-Sol',
               'supported_reasoning_levels': [{'effort': 'ultra'}], 'context_window': 272000}
        template = {'slug': OMLX, 'context_window': 131072, 'max_context_window': 131072,
                    'supported_reasoning_levels': [], 'default_reasoning_level': 'high'}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); state = root/'state'; state.mkdir()
            conf = root/'conf'; conf.mkdir(); cat = root/'cat'; routes = root/'routes'
            manage.atomic(cat, {'models': [gpt, template]})
            manage.atomic(routes, {'models': [{'slug': 'gpt-6.1-sol', 'upstream': 'unchanged'}]})
            manage.atomic(conf/'config.json', {'models': {}, 'port': 11439})
            with patch.multiple(manage, STATE=state, CONF=conf, CATALOG=cat, ROUTES=routes), \
                 patch.object(manage, 'approved', return_value=(ids-{'paid-openrouter/glm-5.3'}, {'paid-openrouter/glm-5.3'})), \
                 patch.object(manage, 'api', return_value=({'data': [{'id': x} for x in ids]}, {})), \
                 patch.object(manage, 'private_file', return_value='offline-dummy'), \
                 patch.object(manage, 'native_catalogue', return_value={'models': [gpt]}):
                manage.sync()
                first = manage.read(state/'candidate-catalogue.json')
                first_routes = manage.read(state/'candidate-routes.json')
                first_config = manage.read(conf/'config.json')
                manage.sync()
                self.assertEqual(manage.read(state/'candidate-catalogue.json'), first)
                self.assertEqual(manage.read(state/'candidate-routes.json'), first_routes)
                self.assertEqual(manage.read(conf/'config.json'), first_config)
            models = {m['slug']: m for m in first['models']}
            self.assertEqual(models['gpt-6.1-sol'], gpt)
            self.assertEqual(models[OMLX]['context_window'], 131072)
            self.assertEqual(models[OMLX]['max_context_window'], 131072)
            for slug in ids:
                self.assertEqual(models[slug]['display_name'], manage.display_name(slug))
                self.assertEqual(models[slug]['supported_reasoning_levels'], reasoning_policy(slug)['levels'])
                if slug != OMLX:
                    self.assertEqual(models[slug]['context_window'], 8192)
            self.assertEqual(first_routes['models'][0], {'slug': 'gpt-6.1-sol', 'upstream': 'unchanged'})
            self.assertEqual(len(models['paid-openrouter/glm-5.3']['supported_reasoning_levels']), 2)


class RollbackTests(unittest.TestCase):
    def test_targeted_rollback_preserves_foreign_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cat=root/'catalogue';routes=root/'routes';state=root/'state';state.mkdir()
            original={'models':[{'slug':'gpt-6.1-sol','value':'old'},{'slug':'qwen36-omlx','value':'old'}]}
            active={'models':[{'slug':'gpt-6.1-sol','value':'old'},{'slug':'qwen36-omlx','value':'new'},{'slug':'paid/task-advanced'}]}
            before={'catalogue':original,'routes':original}
            owned={'models':['qwen36-omlx','paid/task-advanced'],'catalogue':active,'routes':active}
            manage.atomic(state/'before.json',before);manage.atomic(state/'owned.json',owned)
            foreign=copy.deepcopy(active);foreign['models'][0]['value']='concurrent';foreign['models'].append({'slug':'foreign'})
            manage.atomic(cat,foreign);manage.atomic(routes,foreign)
            with patch.multiple(manage,STATE=state,CATALOG=cat,ROUTES=routes),patch.object(manage,'stop_service') as stop:
                manage.rollback()
                self.assertEqual(stop.call_count,2)
            result=manage.read(cat)['models']
            self.assertIn({'slug':'foreign'},result)
            self.assertIn({'slug':'gpt-6.1-sol','value':'concurrent'},result)
            self.assertIn({'slug':'qwen36-omlx','value':'old'},result)
            self.assertNotIn({'slug':'paid/task-advanced'},result)

    def test_conflicting_owned_entry_refuses_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);cat=root/'cat';routes=root/'routes'
            before={'models':[{'slug':'qwen36-omlx','value':'old'}]}
            owned={'models':['qwen36-omlx'],'catalogue':before,'routes':before}
            manage.atomic(root/'before.json',{'catalogue':before,'routes':before});manage.atomic(root/'owned.json',owned)
            changed={'models':[{'slug':'qwen36-omlx','value':'concurrent'}]}
            manage.atomic(cat,changed);manage.atomic(routes,before)
            with patch.multiple(manage,STATE=root,CATALOG=cat,ROUTES=routes),patch.object(manage,'stop_service') as stop:
                with self.assertRaisesRegex(RuntimeError,'owned_entries_changed'):manage.rollback()
                stop.assert_not_called()
            self.assertEqual(manage.read(cat),changed)
