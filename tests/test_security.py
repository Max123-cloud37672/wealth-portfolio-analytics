"""Tests for the Security class: input validation."""

import pytest

from wealth_analytics.security import AssetType, Security


def make_security(**overrides: object) -> Security:
    """Build a valid RY security, replacing any fields given in overrides."""
    fields: dict[str, object] = {
        "ticker": "RY",
        "name": "Royal Bank of Canada",
        "asset_type": AssetType.STOCK,
        "sector": "Financials",
    }
    fields.update(overrides)
    return Security(**fields)


def test_a_valid_security_keeps_its_details() -> None:
    assert make_security().sector == "Financials"


@pytest.mark.parametrize("field_name", ["ticker", "name", "sector"])
def test_blank_text_fields_are_rejected(field_name: str) -> None:
    with pytest.raises(ValueError):
        make_security(**{field_name: ""})


def test_asset_type_must_be_an_asset_type() -> None:
    with pytest.raises(TypeError):
        make_security(asset_type="Stock")
