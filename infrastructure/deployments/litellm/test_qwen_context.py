"""Pure tests: no request is sent to a provider."""
import asyncio
import copy
import unittest
from qwen_context import policy, TARGET, BASE
from litellm.utils import get_optional_params
from litellm.llms.ollama.chat.transformation import OllamaChatConfig

class PolicyTest(unittest.TestCase):
    def test_client_overrides(self):
        for requested in (None, 4096, 131072):
            with self.subTest(requested=requested):
                kw={'model': TARGET, 'api_base': BASE, 'num_ctx': requested,
                    'extra_body': {'num_ctx': requested, 'options': {'num_ctx': requested}},
                    'additional_drop_params': ['num_ctx', 'seed']}
                result=asyncio.run(policy.async_pre_call_deployment_hook(kw, 'acompletion'))
                self.assertEqual(result['num_ctx'],8192)
                self.assertEqual(result['extra_body']['num_ctx'],8192)
                self.assertEqual(result['extra_body']['options']['num_ctx'],8192)
                self.assertNotIn('num_ctx',result['additional_drop_params'])
    def test_other_models_unchanged(self):
        for model in ('ollama/embeddinggemma:latest','openai/mlx-community--Qwen3.6-35B-A3B-4bit','openrouter/test'):
            kw={'model':model,'api_base':BASE,'num_ctx':2048};before=copy.deepcopy(kw)
            self.assertIs(asyncio.run(policy.async_pre_call_deployment_hook(kw,'acompletion')),kw)
            self.assertEqual(kw,before)
    def test_tool_ids_survive_native_transport(self):
        messages=[{'role':'user','content':'synthetic'},
            {'role':'assistant','content':'explanation','tool_calls':[
                {'id':'call-a','type':'function','function':{'name':'lookup','arguments':'{}'}},
                {'id':'call-b','type':'function','function':{'name':'lookup','arguments':'{}'}}]},
            {'role':'tool','tool_call_id':'call-b','name':'lookup','content':'result-b'},
            {'role':'tool','tool_call_id':'call-a','name':'lookup','content':'result-a'}]
        # Demonstrate the installed provider converter's ID loss first.
        original=OllamaChatConfig().transform_request('qwen3:4b-instruct',messages,{}, {}, {})
        self.assertNotIn('id', original['messages'][1]['tool_calls'][0])
        result=asyncio.run(policy.async_pre_call_deployment_hook(
            {'model':TARGET,'api_base':BASE,'num_ctx':131072,'messages':messages},'acompletion'))
        # Same post-transform extra_body overlay used by custom_httpx handler.
        original.update(result['extra_body'])
        self.assertEqual([c['id'] for c in original['messages'][1]['tool_calls']],['call-a','call-b'])
        self.assertEqual([m['tool_call_id'] for m in original['messages'][2:]],['call-b','call-a'])
        self.assertEqual([m['tool_name'] for m in original['messages'][2:]],['lookup','lookup'])
        self.assertEqual(original['messages'][1]['content'],'explanation')
        self.assertEqual([m['content'] for m in original['messages'][2:]],['result-b','result-a'])
        self.assertEqual(result['num_ctx'],8192)

    def test_provider_transform(self):
        kw=asyncio.run(policy.async_pre_call_deployment_hook({'model':TARGET,'api_base':BASE,'num_ctx':131072},'acompletion'))
        p=get_optional_params(model='qwen3:4b-instruct', custom_llm_provider='ollama_chat',num_ctx=kw['num_ctx'])
        body=OllamaChatConfig().transform_request('qwen3:4b-instruct',[{'role':'user','content':'not sent'}],p,{}, {})
        self.assertEqual(body['options']['num_ctx'],8192)

if __name__=='__main__':unittest.main()
