"""Метрики оценки качества/эффективности агента.

Метрики (согласно ДЗ):
  1. success   - завершился ли запрос успешно (без ошибки API и без
                 срабатывания guardrail);
  2. latency_s - время выполнения запроса в секундах;
  3. cost_usd  - приблизительная стоимость запроса (по числу токенов).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Приблизительные цены Claude Sonnet, $ за 1M токенов - только для оценки
# порядка величины стоимости запроса, не для точного биллинга.
PRICE_PER_MTOK_INPUT = 3.0
PRICE_PER_MTOK_OUTPUT = 15.0


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * PRICE_PER_MTOK_INPUT + (output_tokens / 1_000_000) * PRICE_PER_MTOK_OUTPUT


@dataclass
class RunRecord:
    request: str
    success: bool
    latency_s: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    retries: int
    guardrail_triggered: bool
    guardrail_reason: str | None
    reply: str


@dataclass
class MetricsSummary:
    records: list[RunRecord] = field(default_factory=list)

    def add(self, record: RunRecord) -> None:
        self.records.append(record)

    def report(self) -> str:
        n = len(self.records)
        if n == 0:
            return "Нет данных для отчёта."

        success_count = sum(r.success for r in self.records)
        avg_latency = sum(r.latency_s for r in self.records) / n
        total_cost = sum(r.cost_usd for r in self.records)
        guardrail_hits = sum(r.guardrail_triggered for r in self.records)

        lines = [
            f"Запросов всего:          {n}",
            f"Успешных:                {success_count}/{n} ({100 * success_count / n:.0f}%)",
            f"Средняя задержка:        {avg_latency:.2f} c",
            f"Суммарная стоимость:     ${total_cost:.5f}",
            f"Срабатываний guardrail:  {guardrail_hits}",
        ]
        return "\n".join(lines)
