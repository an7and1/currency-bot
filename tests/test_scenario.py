from app.domain.scenario import format_conversion, format_rates_table, _currency_label


def test_currency_label_known():
    assert "доллар" in _currency_label("USD")


def test_currency_label_unknown():
    assert _currency_label("XYZ") == "XYZ"


def test_format_conversion():
    out = format_conversion(100, "USD", "RUB", 92.5, 9250, "2026-10-25")
    assert "USD" in out
    assert "RUB" in out
    assert "9,250.00" in out or "9250.00" in out
    assert "92.5" in out


def test_format_rates_table():
    rates = {"USD": 1.0, "RUB": 92.5, "EUR": 0.92, "GBP": 0.79}
    out = format_rates_table(rates, base="USD", date="2026-10-25")
    assert "RUB" in out
    assert "EUR" in out
