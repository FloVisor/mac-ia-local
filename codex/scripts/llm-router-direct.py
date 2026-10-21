#!/usr/bin/env python3
"""Explicit DIRECT route. Process overrides only; no Codex config/auth changes."""
import argparse,json,os,pathlib,stat,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
def command(model,extra):
 policies=json.loads((ROOT/'infrastructure/deployments/litellm/client-policies.json').read_text())['policies']
 allowed=policies['LOCAL']+policies['FREE']+policies['PAID']['models']
 if model not in allowed or 'embeddinggemma' in model:raise ValueError('Unapproved chat model')
 tier='paid' if model in policies['PAID']['models'] else 'local-free'
 overrides={'model':model,'model_provider':'litellm-direct',
 'model_providers.litellm-direct.name':'LiteLLM DIRECT '+('CLOUD PAID OpenRouter' if tier=='paid' else 'LOCAL / CLOUD FREE'),
 'model_providers.litellm-direct.base_url':'http://127.0.0.1:11439/v1',
 'model_providers.litellm-direct.wire_api':'responses',
 'model_providers.litellm-direct.env_key':'LLM_ROUTER_CODEX_DIRECT_KEY',
 'model_providers.litellm-direct.requires_openai_auth':False,
 'model_context_window':131072 if model.startswith('local-omlx/') else 8192,
 'model_auto_compact_token_limit':100000 if model.startswith('local-omlx/') else 7000}
 args=['codex','--strict-config']
 for k,v in overrides.items():args+=['-c',k+'='+json.dumps(v)]
 return args+extra,tier
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--show-command',action='store_true');p.add_argument('args',nargs=argparse.REMAINDER);a=p.parse_args()
 extra=a.args[1:] if a.args[:1]==['--'] else a.args
 args,tier=command(a.model,extra)
 if a.show_command:print(json.dumps({'mode':'DIRECT','tier':tier,'argv':args},indent=2));sys.exit(0)
 config=json.loads((pathlib.Path.home()/'.config/codex-litellm-adapter/config.json').read_text())
 key=pathlib.Path(config['ingress_key_file']).expanduser();s=key.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid() or s.st_mode&0o077:raise SystemExit('Unsafe credential file')
 env=os.environ.copy();env['LLM_ROUTER_CODEX_DIRECT_KEY']=key.read_text().strip()
 os.execvpe(args[0],args,env)
