import re


def validate_currency(value: str) -> str:
    v = value.strip().upper()
    if not re.fullmatch(r"^[A-Z]{3}$", v):
        raise ValueError("Код валюты — 3 латинские буквы (например, USD, EUR, RUB).")
    return v


def validate_amount(value: str) -> float:
    v = value.strip().replace(",", ".")
    try:
        amount = float(v)
    except ValueError:
        raise ValueError("Сумма должна быть числом, например 100 или 100.50.")
    if amount <= 0:
        raise ValueError("Сумма должна быть больше нуля.")
    if amount > 1_000_000_000:
        raise ValueError("Слишком большая сумма.")
    return amount


def parse_conversion_input(text: str) -> tuple[float, str, str]:
    parts = text.strip().split()
    if not parts:
        raise ValueError("Пустой ввод. Напишите, например: 100 USD RUB.")
    if len(parts) > 3:
        raise ValueError("Формат: <сумма> [FROM] [TO], например: 100 USD RUB.")

    amount = validate_amount(parts[0])
    from_cur = validate_currency(parts[1]) if len(parts) >= 2 else "USD"
    to_cur = validate_currency(parts[2]) if len(parts) >= 3 else "RUB"
    if from_cur == to_cur:
        raise ValueError("Валюты FROM и TO совпадают.")
    return amount, from_cur, to_cur
