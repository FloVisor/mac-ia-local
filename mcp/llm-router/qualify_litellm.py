"""Minimal phase-2 real qualification. Exactly two non-paid tasks, no provisioning.

Configuration/credential stay outside repository. Does not register any MCP client.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

class Client:
    def __init__(self, config):
        self.proc = subprocess.Popen([sys.executable,str(Path(__file__).with_name('router.py')),
            '--config',str(config)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,text=True)
        self.seq = 0
    def call(self,name,args):
        self.seq += 1
        self.proc.stdin.write(json.dumps(dict(jsonrpc='2.0',id=self.seq,method='tools/call',params={'name':name,'arguments':args}))+'\n')
        self.proc.stdin.flush()
        reply=json.loads(self.proc.stdout.readline())
        result=reply['result']
        value=json.loads(result['content'][0]['text'])
        if 'error' in value and 'task_id' not in value:
            raise RuntimeError(value['error'])
        return value
    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)
        self.proc.stdout.close()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,default=Path.home()/'.config/llm-router/config.json')
    parser.add_argument('--report',type=Path,required=True)
    opts=parser.parse_args()
    client=Client(opts.config)
    tasks={}
    try:
        tasks['local']=client.call('submit',dict(profile='testing',task='Reply with exactly OK.',
            reasoning='off',quality={'kind':'exact','expected':'OK'},max_output_tokens=64,
            parent_session='llm-router-phase2-qualification',idempotency_key='qualification-local-20261021'))
        tasks['free']=client.call('submit',dict(profile='testing',task="Extract the code from 'code=FREE42'. Respond only FREE42.",
            model='free-groq/qwen3.8-27b',allow_cloud=True,confidentiality='cloud-approved',
            reasoning='off',quality={'kind':'exact','expected':'FREE42'},max_output_tokens=256,
            parent_session='llm-router-phase2-qualification',idempotency_key='qualification-free-20261021'))
    finally:
        client.close()
    # The submitting client is gone. Another stdio connection recovers the work.
    reader=Client(opts.config)
    report={'submitting_client_closed':True,'tasks':{}}
    try:
        observation_until=time.monotonic()+120
        for name,task in tasks.items():
            while True:
                status=reader.call('status',{'task_id':task['task_id']})
                if status['state'] in ('completed','failed','unknown','cancelled'):
                    break
                if time.monotonic()>observation_until:
                    raise RuntimeError('Observation window elapsed; task retained, no resubmission')
                time.sleep(.25)
            result=reader.call('result',{'task_id':task['task_id']})
            report['tasks'][name]={'status':status,'result':result}
        report['activity']=reader.call('activity',{'limit':50})
    finally:
        reader.close()
    opts.report.parent.mkdir(parents=True,exist_ok=True)
    opts.report.write_text(json.dumps(report,indent=2)+'\n')
    # Only synthetic test content and structured public metadata, never credentials.
    print(json.dumps(report,indent=2))
    if any(t['status']['state']!='completed' for t in report['tasks'].values()):
        raise SystemExit('STOP real delegation did not complete; do not retry')

if __name__=='__main__':
    main()
