"""Route-specific context policy. LiteLLM 1.104.5 deployment callback.

No prompt or credential logging. Other deployments are returned unchanged.
"""
from litellm.integrations.custom_logger import CustomLogger
from litellm.llms.ollama.chat.transformation import OllamaChatConfig

TARGET = 'ollama_chat/qwen3:4b-instruct'
BASE = 'http://172.29.2.27:11434'
CONTEXT = 8192


class QwenContext(CustomLogger):
    async def async_pre_call_deployment_hook(self, kwargs, call_type):
        if kwargs.get('model') != TARGET or kwargs.get('api_base', '').rstrip('/') != BASE:
            return kwargs
        # Executed after Router has merged deployment defaults and caller kwargs.
        kwargs['num_ctx'] = CONTEXT
        # Extra-body fields can be merged after provider transformation.
        for container in (kwargs, kwargs.get('extra_body')):
            if not isinstance(container, dict):
                continue
            if 'num_ctx' in container:
                container['num_ctx'] = CONTEXT
            options = container.get('options')
            if isinstance(options, dict):
                options['num_ctx'] = CONTEXT
        drops = kwargs.get('additional_drop_params')
        if isinstance(drops, list):
            kwargs['additional_drop_params'] = [p for p in drops if p != 'num_ctx']
        messages = kwargs.get('messages') or []
        if any(m.get('tool_calls') for m in messages):
            # LiteLLM 1.104.5 drops IDs from assistant tool_calls, although
            # Ollama supports them. Keep its conversion and restore only IDs
            # and tool names through the supported post-transform extra_body.
            native = OllamaChatConfig().transform_request(
                'qwen3:4b-instruct', messages, {}, {}, {})['messages']
            for source, target in zip(messages, native, strict=True):
                calls = source.get('tool_calls') or []
                for old, new in zip(calls, target.get('tool_calls') or [], strict=True):
                    new['id'] = old['id']
                if source.get('role') == 'tool' and source.get('name'):
                    target['tool_name'] = source['name']
            extra = dict(kwargs.get('extra_body') or {})
            extra['messages'] = native
            kwargs['extra_body'] = extra
        return kwargs


policy = QwenContext()
