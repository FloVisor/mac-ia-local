"""Read-only characterization of installed LiteLLM; no inference or database calls.

Run inside the existing LiteLLM runtime. All budget IO is replaced in this process
by mocks. False guarantees are reported as false, never presented as a passed cap.
"""
import asyncio
import inspect
import json
from unittest.mock import AsyncMock, patch
from litellm.proxy.spend_tracking import budget_reservation as b
from litellm.proxy._types import UserAPIKeyAuth


async def qualify():
    body = {'model': 'paid/task-advanced', 'messages': [{'role': 'user', 'content': 'synthetic'}], 'max_tokens': 1}
    common = dict(request_body=body, route='/v1/chat/completions', llm_router=None,
                  valid_token=UserAPIKeyAuth(api_key='synthetic-not-a-credential'),
                  team_object=None, user_object=None, prisma_client=None,
                  user_api_key_cache=None, proxy_logging_obj=None,
                  fail_closed_budget_enforcement=True)
    counter = object()  # Must never be inspected: no price means no reservation.
    reserve = AsyncMock(side_effect=AssertionError('Unexpected counter write'))
    with patch.object(b, '_get_budget_counters', AsyncMock(return_value=[counter])), \
         patch.object(b, 'count_request_input_tokens', AsyncMock(return_value={})), \
         patch.object(b, 'estimate_request_max_cost', return_value=None), \
         patch.object(b, '_reserve_counter', reserve):
        result = await b.reserve_budget_for_request(**common)
    # A protected operation requires a rejection when its price is unknown.
    unknown_price_rejected = False  # Reached without a refusal exception.
    assert result is None, 'Installed behavior changed; requalify rather than assuming the old limit'
    assert reserve.await_count == 0
    pricing = {'input_cost_per_token': .001, 'output_cost_per_token': .002, 'max_output_tokens': 100}
    cheap = b._max_cost_for_cost_info(request_body=body, route=common['route'], model='synthetic', model_info=pricing, input_tokens=2)
    dear = b._max_cost_for_cost_info(request_body=body | {'max_cost_usd': .0001}, route=common['route'], model='synthetic', model_info=pricing, input_tokens=2)
    assert cheap == dear and cheap > .0001
    print(json.dumps({
        'mode': 'installed_runtime_characterization_with_mocked_budget_io',
        'inference_calls': 0, 'database_writes': 0,
        'unknown_price_with_fail_closed_true': {'returned': result, 'counter_writes': reserve.await_count, 'request_rejected': unknown_price_rejected},
        'caller_max_cost_usd_enforced_by_estimator': False,
        'estimate_usd': cheap, 'requested_cap_usd': .0001,
        'reservation_api_has_operation_usd_cap': any(k in inspect.signature(b.reserve_budget_for_request).parameters for k in ['max_cost_usd', 'max_request_cost', 'operation_max_usd']),
        'paid_delegated_activation': 'BLOCKED',
    }, indent=2))


if __name__ == '__main__':
    asyncio.run(qualify())
