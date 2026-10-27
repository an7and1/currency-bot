import pytest
from app.services.validators import parse_conversion_input, validate_currency, validate_amount


def test_currency():
    assert validate_currency("usd") == "USD"
    with pytest.raises(ValueError):
        validate_currency("US")
    with pytest.raises(ValueError):
        validate_currency("US1")


def test_amount():
    assert validate_amount("100") == 100.0
    assert validate_amount("100,50") == 100.5
    with pytest.raises(ValueError):
        validate_amount("abc")
    with pytest.raises(ValueError):
        validate_amount("-5")


def test_parse_conversion():
    assert parse_conversion_input("100 USD RUB") == (100.0, "USD", "RUB")
    assert parse_conversion_input("50 EUR") == (50.0, "EUR", "RUB")
    assert parse_conversion_input("1000") == (1000.0, "USD", "RUB")
    with pytest.raises(ValueError):
        parse_conversion_input("100 USD USD")
    with pytest.raises(ValueError):
        parse_conversion_input("")
