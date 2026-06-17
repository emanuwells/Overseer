from __future__ import annotations

import pytest

from overseer_sdk.validator import DataValidator


@pytest.fixture()
def validator() -> DataValidator:
    return DataValidator()


# ------------------------------------------------------------------
# validate_indicator
# ------------------------------------------------------------------


def test_validate_indicator_valid(validator: DataValidator) -> None:
    ok, errors = validator.validate_indicator({"id": "IND-1", "url_table": "https://example.com/data"})
    assert ok is True
    assert errors == []


def test_validate_indicator_missing_id(validator: DataValidator) -> None:
    ok, errors = validator.validate_indicator({"url_table": "https://example.com"})
    assert ok is False
    assert any("indicator_id" in e for e in errors)


def test_validate_indicator_empty_id(validator: DataValidator) -> None:
    ok, errors = validator.validate_indicator({"id": "  ", "url_table": "https://example.com"})
    assert ok is False
    assert any("indicator_id" in e for e in errors)


def test_validate_indicator_missing_url(validator: DataValidator) -> None:
    ok, errors = validator.validate_indicator({"id": "IND-1"})
    assert ok is False
    assert any("url_table" in e for e in errors)


def test_validate_indicator_empty_url(validator: DataValidator) -> None:
    ok, errors = validator.validate_indicator({"id": "IND-1", "url_table": ""})
    assert ok is False
    assert any("url_table" in e for e in errors)


def test_validate_indicator_invalid_url(validator: DataValidator) -> None:
    ok, errors = validator.validate_indicator({"id": "IND-1", "url_table": "not-a-url"})
    assert ok is False
    assert any("url_table inv" in e for e in errors)


def test_validate_indicator_both_missing(validator: DataValidator) -> None:
    ok, errors = validator.validate_indicator({})
    assert ok is False
    assert len(errors) == 2


# ------------------------------------------------------------------
# validate_payload
# ------------------------------------------------------------------


def test_validate_payload_valid(validator: DataValidator) -> None:
    ok, errors = validator.validate_payload({"key": "value"})
    assert ok is True
    assert errors == []


def test_validate_payload_none(validator: DataValidator) -> None:
    ok, errors = validator.validate_payload(None)
    assert ok is False
    assert any("None" in e for e in errors)


def test_validate_payload_not_dict(validator: DataValidator) -> None:
    ok, errors = validator.validate_payload([1, 2, 3])
    assert ok is False
    assert any("dict" in e for e in errors)


def test_validate_payload_empty_dict(validator: DataValidator) -> None:
    ok, errors = validator.validate_payload({})
    assert ok is False
    assert any("vazio" in e for e in errors)


def test_validate_payload_string(validator: DataValidator) -> None:
    ok, errors = validator.validate_payload("hello")
    assert ok is False
    assert any("str" in e for e in errors)


# ------------------------------------------------------------------
# validate_source_url
# ------------------------------------------------------------------


def test_validate_source_url_valid(validator: DataValidator) -> None:
    ok, errors = validator.validate_source_url("https://data.example.com/api")
    assert ok is True
    assert errors == []


def test_validate_source_url_none(validator: DataValidator) -> None:
    ok, errors = validator.validate_source_url(None)
    assert ok is False
    assert any("ausente" in e for e in errors)


def test_validate_source_url_empty(validator: DataValidator) -> None:
    ok, errors = validator.validate_source_url("")
    assert ok is False
    assert any("ausente" in e for e in errors)


def test_validate_source_url_invalid(validator: DataValidator) -> None:
    ok, errors = validator.validate_source_url("ftp://bad.protocol")
    assert ok is False
    assert any("inv" in e.lower() for e in errors)


def test_validate_source_url_http(validator: DataValidator) -> None:
    ok, errors = validator.validate_source_url("http://insecure.example.com/data")
    assert ok is True
    assert errors == []


# ------------------------------------------------------------------
# _is_valid_url
# ------------------------------------------------------------------


def test_is_valid_url_https() -> None:
    assert DataValidator._is_valid_url("https://example.com") is True


def test_is_valid_url_http() -> None:
    assert DataValidator._is_valid_url("http://example.com/path?q=1") is True


def test_is_valid_url_no_scheme() -> None:
    assert DataValidator._is_valid_url("example.com") is False


def test_is_valid_url_ftp() -> None:
    assert DataValidator._is_valid_url("ftp://files.example.com") is False


def test_is_valid_url_with_whitespace() -> None:
    assert DataValidator._is_valid_url("  https://example.com  ") is True


# ------------------------------------------------------------------
# is_local_or_test_url
# ------------------------------------------------------------------


def test_is_local_localhost() -> None:
    assert DataValidator.is_local_or_test_url("http://localhost:8080") is True


def test_is_local_127() -> None:
    assert DataValidator.is_local_or_test_url("http://127.0.0.1:3000/api") is True


def test_is_local_127_subnet() -> None:
    assert DataValidator.is_local_or_test_url("http://127.0.0.2/test") is True


def test_is_local_ipv6_loopback() -> None:
    assert DataValidator.is_local_or_test_url("http://[::1]:9090") is True


def test_is_local_0000() -> None:
    assert DataValidator.is_local_or_test_url("http://0.0.0.0:5000") is True


def test_is_local_file_scheme() -> None:
    assert DataValidator.is_local_or_test_url("file:///tmp/data.csv") is True


def test_is_local_example_com() -> None:
    assert DataValidator.is_local_or_test_url("https://example.com") is True


def test_is_local_example_org() -> None:
    assert DataValidator.is_local_or_test_url("https://example.org") is True


def test_is_local_test_tld() -> None:
    assert DataValidator.is_local_or_test_url("https://myapp.test") is True


def test_is_local_invalid_tld() -> None:
    assert DataValidator.is_local_or_test_url("https://api.invalid") is True


def test_is_not_local_real_domain() -> None:
    assert DataValidator.is_local_or_test_url("https://api.production.com") is False


def test_is_local_empty_string() -> None:
    assert DataValidator.is_local_or_test_url("") is True


def test_is_local_none() -> None:
    assert DataValidator.is_local_or_test_url(None) is True
