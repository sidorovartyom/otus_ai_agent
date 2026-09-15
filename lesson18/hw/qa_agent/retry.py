"""Ограничение агентного цикла: ограниченное число повторов с backoff.

Защищает от двух проблем: (1) временного сбоя API (retry), (2)
неограниченного числа попыток и, как следствие, неограниченной
стоимости/времени (max_attempts - жёсткий лимит).
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def with_retry(fn: Callable[[], T], *, max_attempts: int = 3, backoff_base: float = 0.5) -> tuple[T, int]:
    """Вызывает fn() до max_attempts раз. Возвращает (результат, число_повторов).

    Между попытками - экспоненциальная задержка (backoff_base * 2**attempt).
    Если все попытки исчерпаны - пробрасывает последнее исключение;
    вызывающий код сам решает, как его залогировать/обработать.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn(), attempt
        except Exception as exc:  # агент должен пережить любой сбой инструмента/API, а не упасть
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(backoff_base * (2 ** attempt))
    assert last_exc is not None
    raise last_exc
