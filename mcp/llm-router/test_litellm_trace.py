"""New regression only: private recovery of rejected content and honest provenance."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from router import Engine

class FinalizationTraceTests(unittest.TestCase):
    def test_reasoning_usage_preserved_without_reasoning_text(self):
        with tempfile.TemporaryDirectory() as root:
            engine=Engine({'identity':'isolated-test','state_dir':root,
                'litellm_url':'https://unused.invalid/v1','models':{}})
            response={'model':'actual/model','choices':[{'finish_reason':'stop',
                'message':{'content':'{"ok":true}'}}],
                'usage':{'prompt_tokens':10,'completion_tokens':2100,'total_tokens':2110,
                         'completion_tokens_details':{'reasoning_tokens':2048}}}
            with patch.object(engine,'key',return_value='synthetic-only'),patch('router.stream_chat',return_value=(response,None)) as call:
                from router import LOCAL
                text,meta=engine.infer({'profile':'testing','task':'synthetic',
                    'reasoning':'medium','max_output_tokens':1200,
                    'quality':{'kind':'json','required':['ok']}}, {'id':LOCAL,'backend':'local'})
            self.assertEqual(call.call_args.args[2]['max_tokens'],3249)
            self.assertEqual(meta['usage']['completion_tokens_details']['reasoning_tokens'],2048)
            self.assertEqual(meta['quality'],'passed')
            engine.db.close()

    def test_rejected_content_private_and_alias_not_provider_proof(self):
        with tempfile.TemporaryDirectory() as root:
            key=Path(root)/'key'
            key.write_text('synthetic-only')
            key.chmod(0o600)
            alias='free/qualified-test'
            config={'identity':'isolated-test','state_dir':root+'/state','key_file':str(key),
                'litellm_url':'https://unused.invalid/v1','models':{alias:{'enabled':True,'kind':'chat','backend':'free'}}}
            engine=Engine(config)
            secret_marker='PRIVATE_REJECTED_CONTENT'
            content='```json\n{"ok":"'+secret_marker+'"}\n```'
            args={'profile':'testing','task':'Synthetic only','model':alias,
                  'quality':{'kind':'json','required':['ok']},'reasoning':'off'}
            tid=engine.submit(args)['task_id']
            response={'id':'synthetic-request-id','model':alias,
                '_routing_headers':{'x-litellm-model-id':'synthetic-deployment-id'},
                'choices':[{'finish_reason':'stop','message':{'content':content}}],
                'usage':{'prompt_tokens':3,'completion_tokens':5,'total_tokens':8}}
            with patch.object(engine,'select',return_value=config['models'][alias]|{'id':alias}),patch('router.stream_chat',return_value=(response,None)):
                engine.run_one()
            status=engine.status(tid)
            self.assertEqual(status['state'],'failed')
            self.assertEqual(status['error'],'objective_quality_failed')
            self.assertEqual(engine.result(tid)['text'],content)
            self.assertNotIn(secret_marker,str(engine.activity()))
            self.assertIsNone(status['actual_model'])
            self.assertEqual(status['response_model'],alias)
            self.assertEqual(status['request_id'],'synthetic-request-id')
            self.assertEqual(status['routing_headers']['x-litellm-model-id'],'synthetic-deployment-id')
            engine.db.close()

if __name__=='__main__':unittest.main()
