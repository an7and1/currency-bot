"""Smoke-проверка проекта. Запуск: python smoke_test.py"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


async def run_checks() -> int:
    errors: list[str] = []

    if not Path(".env").exists():
        errors.append("Нет файла .env (скопируйте .env.example → .env)")
    else:
        load_dotenv()
        if not os.getenv("VK_TOKEN"):
            errors.append("VK_TOKEN не задан в .env")

    try:
        from app.db.session import SessionLocal, init_db
        from app.db import repository

        await init_db()
    except Exception as exc:
        errors.append(f"БД не инициализирована: {exc}")
        _report(errors)
        return 1

    try:
        test_id = 999_999_999
        async with SessionLocal() as session:
            await repository.set_favorite_pair(session, test_id, "USD->RUB")
        async with SessionLocal() as session:
            pair = await repository.get_favorite_pair(session, test_id)
        if pair != "USD->RUB":
            errors.append("БД не сохраняет любимую пару")
    except Exception as exc:
        errors.append(f"Тест БД: {exc}")

    try:
        from app.services.validators import parse_conversion_input

        amount, f_cur, t_cur = parse_conversion_input("100 USD RUB")
        assert amount == 100.0 and f_cur == "USD" and t_cur == "RUB"
    except Exception as exc:
        errors.append(f"Валидаторы: {exc}")

    api_ok = False
    try:
        from app.services.external_api import ExternalAPI

        api = ExternalAPI()
        try:
            data = await asyncio.wait_for(api.get_rates("USD"), timeout=20)
            if "rates" not in data or "RUB" not in data["rates"]:
                errors.append("Внешнее API вернуло неожиданный формат")
            api_ok = True
        finally:
            await api.close()
    except asyncio.TimeoutError:
        print("Внешнее API: таймаут (сеть недоступна)")
    except Exception as exc:
        print(f"Внешнее API недоступно: {exc}")

    if errors:
        _report(errors)
        return 1

    print("Все проверки пройдены" + ("" if api_ok else " (без проверки внешнего API)"))
    return 0


def _report(errors: list[str]) -> None:
    print("Обнаружены проблемы:")
    for err in errors:
        print(f"  - {err}")


if __name__ == "__main__":
    sys.exit(asyncio.run(run_checks()))
