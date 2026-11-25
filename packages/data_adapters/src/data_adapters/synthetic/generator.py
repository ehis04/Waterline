"""Deterministic synthetic market dataset generator for Waterline."""

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import math
import random
from typing import Any

from data_adapters.synthetic.isin import make_isin
from data_adapters.synthetic.models import (
    ActionType,
    AssetType,
    Company,
    CorporateAction,
    DistributionPolicy,
    FundConstituent,
    FundListing,
    PortfolioTransaction,
    PriceBar,
    SyntheticFund,
    SyntheticMarketPack,
)

SECTORS = [
    "Technology",
    "Financials",
    "Healthcare",
    "Consumer Discretionary",
    "Industrials",
    "Energy",
    "Materials",
    "Utilities",
]

COUNTRIES = [
    ("US", "USD"),
    ("UK", "GBP"),
    ("DE", "EUR"),
    ("FR", "EUR"),
    ("JP", "JPY"),
    ("IE", "EUR"),
]


def _round_dec(val: float | Decimal, places: int = 4) -> Decimal:
    d = Decimal(str(val)) if isinstance(val, float) else val
    fmt = Decimal("10") ** -places
    return d.quantize(fmt, rounding=ROUND_HALF_UP)


class SyntheticMarketGenerator:
    """Generates a complete, deterministic fictional universe of companies, funds, prices, and portfolios."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = random.Random(seed)

    def generate_companies(self) -> list[Company]:
        """Generate 40 fictional companies with ZZ country prefix."""
        companies: list[Company] = []
        company_specs = [
            # Tech (8)
            ("Aether Technologies", "AETH", "Technology", "US", 180.0, 0.28),
            ("Boreas Systems", "BORS", "Technology", "US", 210.0, 0.26),
            ("Cipher Cloud Dynamics", "CCLD", "Technology", "US", 95.0, 0.32),
            ("Delta Semiconductor", "DSMC", "Technology", "US", 140.0, 0.30),
            ("Epsilon Software AG", "EPSG", "Technology", "DE", 68.0, 0.22),
            ("Fuji Robotics KK", "FROB", "Technology", "JP", 45.0, 0.25),
            ("Galileo AI Labs", "GAIL", "Technology", "UK", 55.0, 0.35),
            ("Helios Microdevices", "HMIC", "Technology", "US", 120.0, 0.29),
            # Financials (6)
            ("Imperial Midland Bank", "IMBK", "Financials", "UK", 85.0, 0.20),
            ("Nordic Rhine Capital", "NRHC", "Financials", "DE", 110.0, 0.18),
            ("Pacific Sovereign Assurance", "PSOV", "Financials", "JP", 60.0, 0.17),
            ("Caledonia Mutual Corp", "CMUT", "Financials", "UK", 40.0, 0.19),
            ("Atlantic Trust Ireland", "ATIR", "Financials", "IE", 32.0, 0.21),
            ("Apex Global Bancorp", "APEX", "Financials", "US", 130.0, 0.22),
            # Healthcare (5)
            ("Vanguard BioTherapeutics", "VBIO", "Healthcare", "US", 160.0, 0.24),
            ("Zenith Pharmaceuticals", "ZPHM", "Healthcare", "UK", 90.0, 0.19),
            ("Rhone Pasteur Laboratories", "RPLB", "Healthcare", "FR", 78.0, 0.20),
            ("Nippon Care Diagnostics", "NCDG", "Healthcare", "JP", 50.0, 0.18),
            ("Eire Genomics", "EGEN", "Healthcare", "IE", 28.0, 0.27),
            # Consumer Discretionary (5)
            ("Orion Global Retail", "ORGL", "Consumer Discretionary", "US", 175.0, 0.25),
            ("Krona Motors Europa", "KMTR", "Consumer Discretionary", "DE", 65.0, 0.26),
            ("Lumiere Fashion Brands", "LUMI", "Consumer Discretionary", "FR", 140.0, 0.21),
            ("Sakura Leisure Holdings", "SLSR", "Consumer Discretionary", "JP", 38.0, 0.23),
            ("Veritas Entertainment", "VERT", "Consumer Discretionary", "US", 88.0, 0.28),
            # Industrials (5)
            ("Atlas Heavy Logistics", "AHLG", "Industrials", "DE", 92.0, 0.21),
            ("Concorde Aerospace Systems", "CASC", "Industrials", "FR", 105.0, 0.23),
            ("Meridian Freight Marine", "MFRT", "Industrials", "UK", 48.0, 0.24),
            ("Keystone Infrastructure", "KYST", "Industrials", "US", 82.0, 0.20),
            ("Shinkansen Heavy Tech", "SHNK", "Industrials", "JP", 72.0, 0.19),
            # Energy (4)
            ("North Sea Wind & Energy", "NSWE", "Energy", "UK", 64.0, 0.27),
            ("Equator Hydrocarbons", "EQHC", "Energy", "US", 115.0, 0.29),
            ("Alps Clean Power", "ALPW", "Energy", "DE", 52.0, 0.24),
            ("Kyoto Green Generation", "KYGR", "Energy", "JP", 44.0, 0.22),
            # Materials (4)
            ("Bavaria Specialty Chemicals", "BSCH", "Materials", "DE", 75.0, 0.23),
            ("Saxon Lithium Mining", "SLMN", "Materials", "UK", 36.0, 0.34),
            ("Gallia Sustainable Paper", "GSPP", "Materials", "FR", 30.0, 0.21),
            ("Pacific Polymetals", "PPLY", "Materials", "JP", 58.0, 0.26),
            # Utilities (3)
            ("Celtic Water & Grid", "CWGD", "Utilities", "IE", 25.0, 0.15),
            ("Thames Valley Power", "TVPW", "Utilities", "UK", 42.0, 0.14),
            ("Rheinland Netz AG", "RNAG", "Utilities", "DE", 54.0, 0.16),
        ]

        for i, (name, ticker, sector, country, cap, vol) in enumerate(company_specs, start=101):
            nsin = f"EQ{i:04d}001"
            isin = make_isin("ZZ", nsin)
            ccy = next(curr for c, curr in COUNTRIES if c == country)
            companies.append(
                Company(
                    isin=isin,
                    name=name,
                    ticker=ticker,
                    sector=sector,
                    country=country,
                    currency=ccy,
                    base_market_cap=_round_dec(cap, 2),
                    base_volatility=_round_dec(vol, 4),
                )
            )
        return companies

    def generate_funds(self, companies: list[Company]) -> list[SyntheticFund]:
        """Generate 8 UCITS funds with overlapping constituents summing exactly to 100%."""
        tech_co = [c for c in companies if c.sector == "Technology"]
        us_co = [c for c in companies if c.country == "US"]
        uk_co = [c for c in companies if c.country == "UK"]
        europe_co = [c for c in companies if c.country in ("DE", "FR", "IE")]

        def _make_constituents(selected_cos: list[Company], weights: list[float]) -> list[FundConstituent]:
            total_weight = sum(weights)
            norm_weights = [w / total_weight for w in weights]
            res: list[FundConstituent] = []
            running_sum = Decimal("0")
            for i, (c, w) in enumerate(zip(selected_cos, norm_weights)):
                if i == len(selected_cos) - 1:
                    dec_w = Decimal("1.000000") - running_sum
                else:
                    dec_w = _round_dec(w, 6)
                    running_sum += dec_w
                res.append(
                    FundConstituent(
                        constituent_isin=c.isin,
                        name=c.name,
                        weight=dec_w,
                        asset_type=AssetType.EQUITY,
                        sector=c.sector,
                        country=c.country,
                    )
                )
            return res

        funds: list[SyntheticFund] = []

        # 1. Global Developed World Tracker (ACC)
        top10_global = companies[:10]
        f1_const = _make_constituents(top10_global, [15, 14, 12, 10, 9, 8, 8, 8, 8, 8])
        f1_isin = make_isin("ZZ", "ET0000001")
        funds.append(
            SyntheticFund(
                isin=f1_isin,
                name="Plumbline Global Developed Core UCITS ETF (Acc)",
                category="Global Equity",
                domicile="IE",
                base_currency="USD",
                distribution_policy=DistributionPolicy.ACCUMULATING,
                is_currency_hedged=False,
                hedge_currency=None,
                ter_bps=12,
                listings=[
                    FundListing(f1_isin, "XETR", "PDEV", "EUR"),
                    FundListing(f1_isin, "XLON", "PDEV", "GBP"),
                    FundListing(f1_isin, "XAMS", "PDEV", "EUR"),
                ],
                constituents=f1_const,
            )
        )

        # 2. Global Developed World Tracker (DIST)
        f2_isin = make_isin("ZZ", "ET0000002")
        funds.append(
            SyntheticFund(
                isin=f2_isin,
                name="Plumbline Global Developed Income UCITS ETF (Dist)",
                category="Global Equity",
                domicile="IE",
                base_currency="USD",
                distribution_policy=DistributionPolicy.DISTRIBUTING,
                is_currency_hedged=False,
                hedge_currency=None,
                ter_bps=12,
                listings=[
                    FundListing(f2_isin, "XLON", "PDVD", "GBP"),
                    FundListing(f2_isin, "XETR", "PDVD", "EUR"),
                ],
                constituents=f1_const,
            )
        )

        # 3. US Large-Cap Leaders ETF (ACC, EUR Hedged)
        f3_const = _make_constituents(us_co[:7], [22, 20, 16, 14, 11, 9, 8])
        f3_isin = make_isin("ZZ", "ET0000003")
        funds.append(
            SyntheticFund(
                isin=f3_isin,
                name="Plumbline US Large Cap 100 EUR-Hedged UCITS ETF (Acc)",
                category="US Equity",
                domicile="IE",
                base_currency="EUR",
                distribution_policy=DistributionPolicy.ACCUMULATING,
                is_currency_hedged=True,
                hedge_currency="EUR",
                ter_bps=15,
                listings=[
                    FundListing(f3_isin, "XETR", "PUS5", "EUR"),
                    FundListing(f3_isin, "XAMS", "PUS5", "EUR"),
                ],
                constituents=f3_const,
            )
        )

        # 4. Global Technology Titans ETF (ACC)
        f4_const = _make_constituents(tech_co, [18, 16, 15, 14, 11, 10, 8, 8])
        f4_isin = make_isin("ZZ", "ET0000004")
        funds.append(
            SyntheticFund(
                isin=f4_isin,
                name="Plumbline Global Technology Titans UCITS ETF (Acc)",
                category="Sector Technology",
                domicile="IE",
                base_currency="USD",
                distribution_policy=DistributionPolicy.ACCUMULATING,
                is_currency_hedged=False,
                hedge_currency=None,
                ter_bps=30,
                listings=[
                    FundListing(f4_isin, "XETR", "PTCH", "EUR"),
                    FundListing(f4_isin, "XLON", "PTCH", "GBP"),
                ],
                constituents=f4_const,
            )
        )

        # 5. Europe Stoxx Select ETF (DIST)
        f5_const = _make_constituents(europe_co[:8], [16, 15, 14, 13, 12, 11, 10, 9])
        f5_isin = make_isin("ZZ", "ET0000005")
        funds.append(
            SyntheticFund(
                isin=f5_isin,
                name="Plumbline Europe Stoxx Select UCITS ETF (Dist)",
                category="European Equity",
                domicile="IE",
                base_currency="EUR",
                distribution_policy=DistributionPolicy.DISTRIBUTING,
                is_currency_hedged=False,
                hedge_currency=None,
                ter_bps=18,
                listings=[
                    FundListing(f5_isin, "XETR", "PEUR", "EUR"),
                    FundListing(f5_isin, "XAMS", "PEUR", "EUR"),
                ],
                constituents=f5_const,
            )
        )

        # 6. UK Core Equity ETF (DIST)
        f6_const = _make_constituents(uk_co[:6], [24, 20, 18, 15, 12, 11])
        f6_isin = make_isin("ZZ", "ET0000006")
        funds.append(
            SyntheticFund(
                isin=f6_isin,
                name="Plumbline UK Core Equity UCITS ETF (Dist)",
                category="UK Equity",
                domicile="IE",
                base_currency="GBP",
                distribution_policy=DistributionPolicy.DISTRIBUTING,
                is_currency_hedged=False,
                hedge_currency=None,
                ter_bps=14,
                listings=[
                    FundListing(f6_isin, "XLON", "PUKC", "GBP"),
                ],
                constituents=f6_const,
            )
        )

        # 7. Emerging Markets Stars ETF (ACC)
        em_cos = [c for c in companies if c.country == "JP"]  # Proxy fictional non-Western
        f7_const = _make_constituents(em_cos, [22, 20, 18, 16, 14, 10])
        f7_isin = make_isin("ZZ", "ET0000007")
        funds.append(
            SyntheticFund(
                isin=f7_isin,
                name="Plumbline Emerging Market Stars UCITS ETF (Acc)",
                category="Emerging Markets",
                domicile="IE",
                base_currency="USD",
                distribution_policy=DistributionPolicy.ACCUMULATING,
                is_currency_hedged=False,
                hedge_currency=None,
                ter_bps=28,
                listings=[
                    FundListing(f7_isin, "XETR", "PEMG", "EUR"),
                    FundListing(f7_isin, "XLON", "PEMG", "GBP"),
                ],
                constituents=f7_const,
            )
        )

        # 8. Global Aggregate Bond ETF (EUR Hedged, DIST)
        f8_isin = make_isin("ZZ", "ET0000008")
        bond_const = [
            FundConstituent(make_isin("ZZ", "BD0000001"), "Govt Bond 1-3Y", Decimal("0.350000"), AssetType.BOND, "Government", "DE"),
            FundConstituent(make_isin("ZZ", "BD0000002"), "Govt Bond 5-10Y", Decimal("0.400000"), AssetType.BOND, "Government", "FR"),
            FundConstituent(make_isin("ZZ", "BD0000003"), "Corporate Bond A-AAA", Decimal("0.250000"), AssetType.BOND, "Corporate", "US"),
        ]
        funds.append(
            SyntheticFund(
                isin=f8_isin,
                name="Plumbline Global Aggregate Bond EUR-Hedged UCITS ETF (Dist)",
                category="Fixed Income",
                domicile="IE",
                base_currency="EUR",
                distribution_policy=DistributionPolicy.DISTRIBUTING,
                is_currency_hedged=True,
                hedge_currency="EUR",
                ter_bps=16,
                listings=[
                    FundListing(f8_isin, "XETR", "PBND", "EUR"),
                    FundListing(f8_isin, "XLON", "PBND", "GBP"),
                ],
                constituents=bond_const,
            )
        )

        return funds

    def generate_prices(
        self,
        companies: list[Company],
        funds: list[SyntheticFund],
        start_date: str = "2021-01-04",
        end_date: str = "2026-01-02",
    ) -> tuple[dict[str, list[PriceBar]], list[CorporateAction]]:
        """Generate daily prices with realistic regimes, volatility, and corporate actions."""
        prices: dict[str, list[PriceBar]] = {}
        corp_actions: list[CorporateAction] = []

        cur_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()

        trading_days: list[date] = []
        while cur_dt <= end_dt:
            if cur_dt.weekday() < 5:  # Monday to Friday
                trading_days.append(cur_dt)
            cur_dt += timedelta(days=1)

        # Base company prices starting at 100.0
        company_state: dict[str, float] = {c.isin: 100.0 for c in companies}
        
        # Track simulated factor regimes
        # 2022 rate shock period: 2022-01-01 to 2022-10-31
        rate_shock_start = date(2022, 1, 1)
        rate_shock_end = date(2022, 10, 31)

        for d in trading_days:
            d_str = d.isoformat()
            
            # Regime drift
            is_shock = rate_shock_start <= d <= rate_shock_end
            mkt_drift = -0.0008 if is_shock else 0.0004
            mkt_vol = 0.018 if is_shock else 0.009
            mkt_return = self.rng.gauss(mkt_drift, mkt_vol)

            for c in companies:
                vol = float(c.base_volatility) / math.sqrt(252)
                stock_return = mkt_return + self.rng.gauss(0.0, vol)
                new_price = max(1.0, company_state[c.isin] * (1.0 + stock_return))
                company_state[c.isin] = new_price

                p_dec = _round_dec(new_price, 2)
                p_bar = PriceBar(
                    isin=c.isin,
                    mic="XETR" if c.currency == "EUR" else ("XLON" if c.currency == "GBP" else "XNAS"),
                    date=d_str,
                    open=p_dec,
                    high=_round_dec(float(p_dec) * 1.01, 2),
                    low=_round_dec(float(p_dec) * 0.99, 2),
                    close=p_dec,
                    volume=self.rng.randint(50000, 2000000),
                    currency=c.currency,
                )
                prices.setdefault(c.isin, []).append(p_bar)

            # Fund prices as weighted average of constituent prices (NAV)
            for f in funds:
                nav = 0.0
                for item in f.constituents:
                    if item.constituent_isin in company_state:
                        nav += company_state[item.constituent_isin] * float(item.weight)
                    else:
                        nav += 100.0 * float(item.weight)
                nav_dec = _round_dec(nav, 2)
                for l in f.listings:
                    f_bar = PriceBar(
                        isin=f.isin,
                        mic=l.mic,
                        date=d_str,
                        open=nav_dec,
                        high=_round_dec(float(nav_dec) * 1.005, 2),
                        low=_round_dec(float(nav_dec) * 0.995, 2),
                        close=nav_dec,
                        volume=self.rng.randint(10000, 300000),
                        currency=l.currency,
                    )
                    prices.setdefault(f.isin, []).append(f_bar)

        # Corporate action: 2-for-1 stock split for Aether Technologies on 2023-06-15
        aeth_isin = companies[0].isin
        corp_actions.append(
            CorporateAction(
                isin=aeth_isin,
                action_type=ActionType.SPLIT,
                effective_date="2023-06-15",
                ratio=Decimal("2.0"),
            )
        )

        return prices, corp_actions

    def generate_demo_portfolios(
        self, companies: list[Company], funds: list[SyntheticFund]
    ) -> dict[str, list[PortfolioTransaction]]:
        """Generate three realistic demo portfolios with complete transaction records."""
        portfolios: dict[str, list[PortfolioTransaction]] = {}

        # 1. "Three Overlapping ETFs" Portfolio
        # Holds: Global Core (f1), US Large Cap (f3), Global Tech (f4), and direct Aether Technologies (c0)
        f1 = funds[0]
        f3 = funds[2]
        f4 = funds[3]
        c0 = companies[0]

        p1_txs = [
            PortfolioTransaction("tx_101", "p_overlapping", "Trading 212 ISA", "2023-01-10T09:30:00Z", ActionType.BUY, f1.isin, "PDEV", Decimal("150"), Decimal("78.50"), "EUR", Decimal("0.00"), Decimal("11775.00")),
            PortfolioTransaction("tx_102", "p_overlapping", "Trading 212 ISA", "2023-01-10T09:35:00Z", ActionType.BUY, f3.isin, "PUS5", Decimal("100"), Decimal("82.10"), "EUR", Decimal("0.00"), Decimal("8210.00")),
            PortfolioTransaction("tx_103", "p_overlapping", "Trading 212 ISA", "2023-01-10T09:40:00Z", ActionType.BUY, f4.isin, "PTCH", Decimal("80"), Decimal("112.40"), "EUR", Decimal("0.00"), Decimal("8992.00")),
            PortfolioTransaction("tx_104", "p_overlapping", "Trading 212 ISA", "2023-03-15T11:00:00Z", ActionType.BUY, c0.isin, "AETH", Decimal("50"), Decimal("95.00"), "EUR", Decimal("0.00"), Decimal("4750.00")),
            PortfolioTransaction("tx_105", "p_overlapping", "Trading 212 ISA", "2023-11-20T14:15:00Z", ActionType.BUY, f1.isin, "PDEV", Decimal("40"), Decimal("84.20"), "EUR", Decimal("0.00"), Decimal("3368.00")),
        ]
        portfolios["overlapping_etfs"] = p1_txs

        # 2. "UK Wrapper Split" Portfolio (SIPP and ISA)
        f6 = funds[5]  # UK Core
        f8 = funds[7]  # Bond
        p2_txs = [
            PortfolioTransaction("tx_201", "p_uk_split", "Interactive Investor SIPP", "2022-04-06T10:00:00Z", ActionType.BUY, f1.isin, "PDEV", Decimal("200"), Decimal("68.00"), "GBP", Decimal("9.99"), Decimal("13609.99")),
            PortfolioTransaction("tx_202", "p_uk_split", "Interactive Investor SIPP", "2022-04-06T10:05:00Z", ActionType.BUY, f8.isin, "PBND", Decimal("120"), Decimal("95.00"), "GBP", Decimal("9.99"), Decimal("11409.99")),
            PortfolioTransaction("tx_203", "p_uk_split", "Trading 212 ISA", "2022-05-10T09:00:00Z", ActionType.BUY, f6.isin, "PUKC", Decimal("300"), Decimal("45.50"), "GBP", Decimal("0.00"), Decimal("13650.00")),
            PortfolioTransaction("tx_204", "p_uk_split", "Trading 212 ISA", "2023-06-01T09:00:00Z", ActionType.BUY, f4.isin, "PTCH", Decimal("60"), Decimal("98.00"), "GBP", Decimal("0.00"), Decimal("5880.00")),
        ]
        portfolios["uk_wrapper_split"] = p2_txs

        # 3. "Student Starter" Portfolio
        p3_txs = [
            PortfolioTransaction("tx_301", "p_student", "Degiro Basic", "2024-01-15T12:00:00Z", ActionType.BUY, f1.isin, "PDEV", Decimal("10"), Decimal("85.00"), "EUR", Decimal("1.00"), Decimal("851.00")),
            PortfolioTransaction("tx_302", "p_student", "Degiro Basic", "2024-02-15T12:00:00Z", ActionType.BUY, f1.isin, "PDEV", Decimal("10"), Decimal("86.20"), "EUR", Decimal("1.00"), Decimal("863.00")),
            PortfolioTransaction("tx_303", "p_student", "Degiro Basic", "2024-03-15T12:00:00Z", ActionType.BUY, f4.isin, "PTCH", Decimal("5"), Decimal("125.00"), "EUR", Decimal("1.00"), Decimal("626.00")),
        ]
        portfolios["student_starter"] = p3_txs

        return portfolios

    def generate_all(self) -> SyntheticMarketPack:
        """Run complete deterministic generation."""
        companies = self.generate_companies()
        funds = self.generate_funds(companies)
        prices, actions = self.generate_prices(companies, funds)
        portfolios = self.generate_demo_portfolios(companies, funds)

        return SyntheticMarketPack(
            version="1.0.0",
            seed=self.seed,
            companies=companies,
            funds=funds,
            daily_prices=prices,
            corporate_actions=actions,
            portfolios=portfolios,
        )
