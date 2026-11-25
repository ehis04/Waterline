"""Tests for the provider licence registry."""

from data_adapters.providers.registry import (
    PROVIDERS,
    LicenceStatus,
    ProviderConfig,
    can_use,
    get_provider,
)


def test_synthetic_provider_is_approved_and_usable():
    assert can_use("synthetic") is True
    assert can_use("SYNTHETIC") is True
    assert can_use("synthetic", commercial=False) is True

    cfg = get_provider("synthetic")
    assert cfg is not None
    assert cfg.status == LicenceStatus.APPROVED
    assert cfg.commercial_allowed is True


def test_unapproved_providers_are_denied():
    for provider in ("twelvedata", "eodhd"):
        cfg = get_provider(provider)
        assert cfg is not None
        assert cfg.status == LicenceStatus.UNAPPROVED
        assert can_use(provider) is False
        assert can_use(provider, commercial=False) is False


def test_unknown_provider_default_deny():
    assert get_provider("nonexistent_provider") is None
    assert can_use("nonexistent_provider") is False
    assert can_use("nonexistent_provider", commercial=False) is False
    assert can_use("") is False


def test_restricted_provider_respects_commercial_flag(monkeypatch):
    restricted = ProviderConfig(
        name="academic_feed",
        status=LicenceStatus.RESTRICTED,
        commercial_allowed=False,
        attribution_required=True,
        notes="Non-commercial research only",
    )
    monkeypatch.setitem(PROVIDERS, "academic_feed", restricted)

    assert can_use("academic_feed", commercial=True) is False
    assert can_use("academic_feed", commercial=False) is True
