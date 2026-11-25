"""Provider licence registry with default-deny policy."""

from dataclasses import dataclass
from enum import Enum


class LicenceStatus(str, Enum):
    """Approval status for a market/reference data provider."""

    APPROVED = "APPROVED"
    UNAPPROVED = "UNAPPROVED"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True)
class ProviderConfig:
    """Licence and usage configuration for a data provider."""

    name: str
    status: LicenceStatus
    commercial_allowed: bool
    attribution_required: bool
    notes: str = ""


PROVIDERS: dict[str, ProviderConfig] = {
    "synthetic": ProviderConfig(
        name="synthetic",
        status=LicenceStatus.APPROVED,
        commercial_allowed=True,
        attribution_required=False,
        notes="Internal deterministic synthetic dataset generator",
    ),
    "twelvedata": ProviderConfig(
        name="twelvedata",
        status=LicenceStatus.UNAPPROVED,
        commercial_allowed=False,
        attribution_required=True,
        notes="UNAPPROVED pending commercial quote",
    ),
    "eodhd": ProviderConfig(
        name="eodhd",
        status=LicenceStatus.UNAPPROVED,
        commercial_allowed=False,
        attribution_required=True,
        notes="UNAPPROVED pending commercial quote",
    ),
}


def get_provider(provider_name: str) -> ProviderConfig | None:
    """Look up a provider configuration by name (case-insensitive)."""
    return PROVIDERS.get(provider_name.strip().lower())


def can_use(provider_name: str, commercial: bool = True) -> bool:
    """Return True only if the provider is registered and permitted for the requested usage."""
    config = get_provider(provider_name)
    if config is None:
        return False
    if config.status == LicenceStatus.UNAPPROVED:
        return False
    if commercial and not config.commercial_allowed:
        return False
    return config.status in (LicenceStatus.APPROVED, LicenceStatus.RESTRICTED)
