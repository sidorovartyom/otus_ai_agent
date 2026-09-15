"""Воспроизводимый сценарий взаимодействия с агентом.

Запуск (из папки lesson09/hw):
    python -m context_streaming_agent.demo

Требования: .env в корне репозитория (ANTHROPIC_AUTH_TOKEN,
ANTHROPIC_BASE_URL, ANTHROPIC_MODEL, CERT_PATH) - тот же файл, что
используется в lesson04 и lesson06.
"""

from __future__ import annotations

from .agent import stream_reply

# Сценарий фиксированный (без input()), чтобы демонстрация была
# воспроизводима один в один при повторном запуске и на записи экрана.
SCRIPT = [
    "Какие тарифы есть у Otus Cloud и чем они отличаются?",
    "А какой SLA по аптайму у тарифа Business?",
    "Как связаться с поддержкой, если сервис упал ночью?",
    "Сколько будет стоить перенос базы данных на 500 ГБ?",  # ответа нет в базе знаний
]


def main() -> None:
    print("=" * 80)
    print("ДЕМО: агент с подключённым контекстом + streaming (Otus Cloud support)")
    print("=" * 80)

    messages: list[dict] = []
    for turn, user_text in enumerate(SCRIPT, start=1):
        print(f"\n--- Вопрос {turn}/{len(SCRIPT)} ---")
        print(f"Пользователь: {user_text}")
        messages.append({"role": "user", "content": user_text})

        print("Агент: ", end="", flush=True)
        full_text = stream_reply(messages)
        print()  # перенос строки после потокового вывода
        messages.append({"role": "assistant", "content": full_text})

    print("\n" + "=" * 80)
    print(f"Сценарий завершён. Ходов диалога: {len(SCRIPT)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
