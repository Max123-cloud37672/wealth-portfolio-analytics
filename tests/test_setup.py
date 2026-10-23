"""Smoke test: checks the project is set up so tests can import our package."""


def test_wealth_analytics_package_can_be_imported() -> None:
    import wealth_analytics

    assert wealth_analytics.__name__ == "wealth_analytics"
