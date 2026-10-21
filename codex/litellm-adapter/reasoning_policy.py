"""Reviewed picker contracts, not claims of measured model reasoning.

Evidence reviewed 2026-10-21:
https://console.groq.com/docs/reasoning
https://openrouter.ai/api/v1/models (exact model IDs below)
artifacts/llm-router-p3a/reasoning-audit/parameter-components.json
artifacts/llm-router-p3a/reasoning-audit/litellm-transform.json

Only identity-preserving, documented cloud efforts are selectable. Requalify
when an upstream model, converter or pool membership changes. Unknown entries
fail closed; never pad a two-level model to initialize Desktop's slider.
"""
from adapter import BUDGETS, EFFORTS, OMLX


def reasoning_policy(slug):
    policy = {'status': 'unqualified', 'levels': [], 'default': None,
              'excluded': {}, 'applied': 'NOT_MEASURED',
              'note': 'contrôle de raisonnement non qualifié sur ce chemin'}
    if slug == OMLX:
        policy.update(status='calibrated_local', default='high',
                      note='Off/Minimal désactivés ; budgets oMLX 512/2048/8192/16384')
        policy['levels'] = [
            {'effort': e, 'description':
             ('Off — thinking disabled' if e == 'none' else
              'Minimal — thinking disabled' if e == 'minimal' else
              f'{e.title()} — {BUDGETS[e]} thinking tokens')}
            for e in EFFORTS]
    elif slug in ('free-groq/gpt-oss-120b', 'free-groq/qwen3.8-27b'):
        policy.update(status='documented_provider', default='medium',
                      note='Low/Medium/High documentés ; application moteur non mesurée',
                      excluded={'none': 'converted_to_low', 'minimal': 'converted_to_low',
                                'max': 'degraded_to_high'})
        policy['levels'] = _cloud_levels(('low', 'medium', 'high'))
    elif slug in ('paid-openrouter/deepseek-v4.1-flash-1017',
                  'paid-openrouter/glm-5.3'):
        deepseek = slug.endswith('deepseek-v4.1-flash-1017')
        policy.update(status='documented_provider', default='high',
                      note='efforts documentés OpenRouter ; application moteur non mesurée',
                      excluded={'minimal': 'not_advertised_by_model',
                                'medium': 'not_advertised_by_model',
                                'max': 'converted_to_xhigh_not_qualified'})
        if not deepseek:
            policy['excluded']['none'] = 'mandatory_reasoning'
        policy['levels'] = _cloud_levels(('none', 'low', 'high') if deepseek else ('low', 'high'))
    elif slug in ('free-mistral/ministral-8b-2512', 'free-mistral/codestral-2508'):
        policy.update(status='no_control', note='effort supprimé par FreeLLMAPI',
                      excluded={e: 'dropped_by_gateway' for e in EFFORTS})
    elif slug.startswith(('free/task-', 'paid/task-')):
        # A pool name or one historical route does not establish the current
        # intersection of every possible member and its converter.
        policy.update(status='unqualified_pool',
                      note='capacités communes de tous les membres du pool non qualifiées')
    elif slug.startswith('free-openrouter/'):
        policy['note'] = 'paramètre reasoning annoncé ; niveaux précis non qualifiés'
    elif slug.startswith('local-ollama/'):
        policy['note'] = 'effort explicite refusé par l’adaptateur ; chemin non qualifié'
    return policy


def _cloud_levels(efforts):
    return [{'effort': e, 'description':
             f'{"Off" if e == "none" else e.title()} → reasoning_effort={e}; '
             'documented provider control, application not measured'} for e in efforts]
