"""Пример выполнения пайплайна: 4 заявки, покрывающие обе ветки и эскалацию.

Запуск (из папки lesson16/hw):
    python -m ticket_agent.demo

Требования: .env в корне репозитория (ANTHROPIC_AUTH_TOKEN,
ANTHROPIC_BASE_URL, ANTHROPIC_MODEL, CERT_PATH).
"""

from __future__ import annotations

import sys

from .pipeline import run_pipeline

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# (client_id, текст обращения):
#   1. technical, решение есть в базе знаний
#   2. billing, счёт найден -> без эскалации
#   3. other -> сразу эскалация
#   4. technical повторно от client_1 -> в шаге 1 видно найденную историю
TICKETS = [
    ("client_1", "Не могу подключиться к хранилищу, всё время connection timeout."),
    ("client_2", "Почему мне опять пришёл счёт? Проверьте мой последний платёж."),
    ("client_3", "Хочу оставить отзыв о вашем сервисе - всё супер, спасибо!"),
    ("client_1", "У меня снова зависли файлы в статусе pending, ничего не помогает."),
]


def main() -> None:
    for i, (client_id, text) in enumerate(TICKETS, start=1):
        print("=" * 80)
        print(f"ЗАЯВКА {i}/{len(TICKETS)}")
        print("=" * 80)
        run_pipeline(client_id, text)
        print()


if __name__ == "__main__":
    main()
