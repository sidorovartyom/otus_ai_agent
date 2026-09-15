"""Агент верхнего уровня: вызывает LLM с retry, замеряет метрики,
проверяет ответ guardrail-ом и логирует результат каждого запроса.
"""

from __future__ import annotations

import time

from .guardrails import FALLBACK_MESSAGE, validate_response
from .llm import call_llm
from .logger import log_run
from .metrics import RunRecord, estimate_cost_usd
from .retry import with_retry


def ask(user_text: str, *, max_attempts: int = 3) -> RunRecord:
    started = time.monotonic()

    try:
        (text, input_tokens, output_tokens), retries = with_retry(
            lambda: call_llm(user_text), max_attempts=max_attempts
        )
        api_success = True
    except Exception as exc:  # исчерпаны все попытки retry
        text, input_tokens, output_tokens = f"Ошибка вызова LLM: {exc}", 0, 0
        retries = max_attempts - 1
        api_success = False

    latency_s = time.monotonic() - started
    cost_usd = estimate_cost_usd(input_tokens, output_tokens)

    ok, reason = validate_response(text) if api_success else (False, "сбой вызова API после всех попыток")
    reply = text if ok else FALLBACK_MESSAGE

    record = RunRecord(
        request=user_text,
        success=api_success and ok,
        latency_s=latency_s,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
        retries=retries,
        guardrail_triggered=api_success and not ok,
        guardrail_reason=reason if api_success and not ok else None,
        reply=reply,
    )
    log_run(record)
    return record
