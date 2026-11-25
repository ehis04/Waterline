"""Domain dataclasses for synthetic market dataset generation."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class AssetType(str, Enum):
    EQUITY = "EQUITY"
    ETF = "ETF"
    BOND = "BOND"
    COMMODITY = "COMMODITY"


class DistributionPolicy(str, Enum):
    ACCUMULATING = "ACCUMULATING"
    DISTRIBUTING = "DISTRIBUTING"


class ActionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    SPLIT = "SPLIT"
    FEE = "FEE"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


@dataclass(frozen=True)
class Company:
    isin: str
    name: str
    ticker: str
    sector: str
    country: str
    currency: str
    base_market_cap: Decimal
    base_volatility: Decimal


@dataclass(frozen=True)
class FundListing:
    isin: str
    mic: str
    ticker: str
    currency: str


@dataclass(frozen=True)
class FundConstituent:
    constituent_isin: str
    name: str
    weight: Decimal
    asset_type: AssetType
    sector: str
    country: str


@dataclass(frozen=True)
class SyntheticFund:
    isin: str
    name: str
    category: str
    domicile: str
    base_currency: str
    distribution_policy: DistributionPolicy
    is_currency_hedged: bool
    hedge_currency: str | None
    ter_bps: int
    listings: list[FundListing]
    constituents: list[FundConstituent]


@dataclass(frozen=True)
class PriceBar:
    isin: str
    mic: str
    date: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    currency: str


@dataclass(frozen=True)
class CorporateAction:
    isin: str
    action_type: ActionType
    effective_date: str
    ratio: Decimal | None = None
    cash_amount: Decimal | None = None
    currency: str | None = None


@dataclass(frozen=True)
class PortfolioTransaction:
    transaction_id: str
    portfolio_id: str
    account_name: str
    timestamp: str
    action: ActionType
    isin: str | None
    ticker: str | None
    shares: Decimal
    price: Decimal
    currency: str
    fee: Decimal
    total_amount: Decimal


@dataclass
class SyntheticMarketPack:
    version: str
    seed: int
    companies: list[Company] = field(default_factory=list)
    funds: list[SyntheticFund] = field(default_factory=list)
    daily_prices: dict[str, list[PriceBar]] = field(default_factory=dict)
    corporate_actions: list[CorporateAction] = field(default_factory=list)
    portfolios: dict[str, list[PortfolioTransaction]] = field(default_factory=dict)
