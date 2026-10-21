"""Ollama-only regressions; synthetic histories and no model inference."""
import copy
import json
import unittest
from adapter import OLLAMA, OMLX, Rejected, chat_request, response_object, events, history_structure


class OllamaHistoryTests(unittest.TestCase):
    def test_completed_usage_accepts_absent_none_and_real_breakdowns(self):
        for detail in (None, {}, {'reasoning_tokens': 7}):
            chat = {'choices': [{'message': {'content': 'synthetic'}, 'finish_reason': 'stop'}],
                    'usage': {'completion_tokens_details': detail}}
            response = response_object(chat, OLLAMA)
            self.assertEqual(response['usage']['output_tokens_details']['reasoning_tokens'],
                             7 if detail else 0)
            self.assertEqual(list(events(response))[-1]['response'], response)
            # Known-working routes retain their original wire shape.
            for model in (OMLX, 'free-mistral/ministral-8b-2512'):
                self.assertEqual(response_object(chat, model)['usage']['output_tokens_details'], detail or {})

    def test_parallel_calls_results_and_custom_roundtrip(self):
        tools = [{'type': 'namespace', 'name': 'functions', 'tools': [
            {'type': 'function', 'name': 'lookup', 'parameters': {'type': 'object'}},
            {'type': 'custom', 'name': 'patch'}]}]
        items = [
            {'role': 'user', 'content': 'synthetic'},
            {'type': 'message', 'role': 'assistant', 'content': 'explanation'},
            {'type': 'function_call', 'name': 'lookup', 'namespace': 'functions', 'call_id': 'a', 'arguments': '{"x":1}'},
            {'type': 'custom_tool_call', 'name': 'patch', 'namespace': 'functions', 'call_id': 'b', 'input': 'synthetic patch'},
            {'type': 'custom_tool_call_output', 'call_id': 'b', 'output': 'custom result'},
            {'type': 'function_call_output', 'call_id': 'a', 'output': 'function result'},
            {'role': 'assistant', 'content': 'final'},
            {'role': 'user', 'content': 'next question'}]
        body, _ = chat_request({'model': OLLAMA, 'tools': tools, 'input': items}, {})
        m = body['messages']
        self.assertEqual([x['role'] for x in m], ['user', 'assistant', 'tool', 'tool', 'assistant', 'user'])
        self.assertEqual(m[1]['content'], 'explanation')
        self.assertEqual([c['id'] for c in m[1]['tool_calls']], ['a', 'b'])
        self.assertEqual(m[1]['tool_calls'][1]['function']['arguments'], json.dumps({'input': 'synthetic patch'}))
        self.assertEqual([(x['tool_call_id'], x['name'], x['content']) for x in m[2:4]],
                         [('b', 'functions__patch', 'custom result'), ('a', 'functions__lookup', 'function result')])

    def test_no_blind_merge_of_incident_assistant_tail(self):
        items = [{'role': 'user', 'content': 'synthetic'},
                 {'role': 'assistant', 'content': 'first'}, {'role': 'assistant', 'content': 'second'}]
        before = copy.deepcopy(items)
        body, _ = chat_request({'model': OLLAMA, 'input': items}, {})
        self.assertEqual(body['messages'], before)
        self.assertEqual(items, before)
        # Backend prefill constraint: this tail is invalid. Repair completed
        # response parsing, not the user's history by joining/deleting messages.
        self.assertEqual([m['role'] for m in body['messages'][-2:]], ['assistant', 'assistant'])

    def test_unmatched_duplicate_and_missing_results_fail_explicitly(self):
        call = {'type': 'function_call', 'name': 'lookup', 'call_id': 'a', 'arguments': '{}'}
        result = {'type': 'function_call_output', 'call_id': 'a', 'output': 'value'}
        for history in ([result], [call, call, result], [call], [call, result, result]):
            with self.subTest(history=history), self.assertRaises(Rejected):
                chat_request({'model': OLLAMA, 'input': history}, {})

    def test_trace_contains_no_contents(self):
        trace = history_structure([{'type': 'message', 'role': 'user', 'content': 'SECRET_PROMPT'},
                                   {'role': 'assistant', 'content': 'SECRET_TEXT', 'tool_calls': [
                                       {'id': 'opaque_id', 'function': {'arguments': 'SECRET_ARGS'}}]},
                                   {'role': 'tool', 'tool_call_id': 'opaque_id', 'content': 'SECRET_RESULT'}])
        self.assertNotIn('SECRET', json.dumps(trace))
        self.assertEqual(trace[-1]['tool_call_id'], 'opaque_id')


if __name__ == '__main__':
    unittest.main()
