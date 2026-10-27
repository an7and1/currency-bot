from app.services.external_api import ExternalAPI

POPULAR_CURRENCIES = ["USD", "EUR", "RUB", "GBP", "CNY", "JPY", "KZT", "TRY"]

CURRENCY_NAMES = {
    "USD": "доллар США", "EUR": "евро", "RUB": "российский рубль",
    "GBP": "фунт стерлингов", "CNY": "китайский юань", "JPY": "японская иена",
    "KZT": "казахстанский тенге", "TRY": "турецкая лира",
    "BYN": "белорусский рубль", "UAH": "украинская гривна",
}


def _currency_label(code: str) -> str:
    name = CURRENCY_NAMES.get(code)
    return f"{code} ({name})" if name else code


def format_conversion(
    amount: float, from_cur: str, to_cur: str, rate: float, result: float, date: str = ""
) -> str:
    lines = [
        "💱 Конвертация",
        "",
        f"{amount:,.2f} {_currency_label(from_cur)}",
        f"= {result:,.2f} {_currency_label(to_cur)}",
        "",
        f"Курс: 1 {from_cur} = {rate:.4f} {to_cur}",
    ]
    if date:
        lines.append(f"Обновлено: {date}")
    return "\n".join(lines)


def format_rates_table(rates: dict[str, float], base: str = "USD", date: str = "") -> str:
    lines = [f"📊 Курсы к {base}", ""]
    for cur in POPULAR_CURRENCIES:
        if cur == base:
            continue
        r = rates.get(cur)
        if r is None:
            continue
        lines.append(f"• 1 {base} = {r:.4f} {cur}")
    if date:
        lines.append("")
        lines.append(f"Обновлено: {date}")
    return "\n".join(lines)


async def handle_convert(
    api: ExternalAPI, amount: float, from_cur: str, to_cur: str
) -> str:
    data = await api.get_rates(base=from_cur)
    rates = data["rates"]
    rate = rates.get(to_cur)
    if rate is None:
        raise ValueError(f"Валюта {to_cur} не поддерживается сервисом.")
        
    result = amount * rate
    return format_conversion(amount, from_cur, to_cur, rate, result, data.get("date", ""))


async def handle_rates(api: ExternalAPI) -> str:
    data = await api.get_rates(base="USD")
    return format_rates_table(data["rates"], base=data["base"], date=data.get("date", ""))
