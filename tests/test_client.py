"""Tests for the Client class: input validation."""

import pytest

from wealth_analytics.client import Client, RiskProfile


def test_a_valid_client_keeps_its_details() -> None:
    client = Client(
        client_id=1, name="Tremblay Family Trust", risk=RiskProfile.BALANCED
    )

    assert client.name == "Tremblay Family Trust"
    assert client.risk is RiskProfile.BALANCED


def test_blank_name_is_rejected() -> None:
    with pytest.raises(ValueError):
        Client(client_id=1, name=" ", risk=RiskProfile.GROWTH)


def test_risk_must_be_a_risk_profile() -> None:
    with pytest.raises(TypeError):
        Client(client_id=1, name="Tremblay Family Trust", risk="Growth")
