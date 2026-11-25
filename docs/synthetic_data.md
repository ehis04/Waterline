# Synthetic Market Dataset Pack (DATA-001)

## Overview

The synthetic dataset pack provides a completely reproducible, fictional financial market environment designed to test and benchmark all Waterline quantitative risk, look-through, and scenario analysis features without proprietary vendor licensing constraints or privacy concerns.

## Dataset Specifications

- **Identifier Standard**: ISO 6166 ISIN with Luhn modulo-10 check digits using the unassigned country prefix `ZZ`.
- **Companies**: 40 fictional companies spanning 8 major economic sectors (Technology, Financials, Healthcare, Consumer Discretionary, Industrials, Energy, Materials, Utilities) and 6 jurisdictions (US, UK, DE, FR, JP, IE).
- **Funds**: 8 UCITS-style ETF structures covering global developed equities, US large-cap, tech titans, European select, UK core, emerging markets, and aggregate fixed income. Constituents sum exactly to 100% weight (`1.000000`).
- **Listings**: Multi-currency exchange listings across XETR (EUR), XLON (GBP), and XAMS (EUR).
- **Time Series**: Deterministic daily price history with multi-regime simulation (market drift, volatility clustering, 2022 interest rate shock regime).
- **Corporate Actions**: Stock splits and dividend events to test bitemporal adjustment accounting.
- **Demo Portfolios**:
  1. *Overlapping ETFs*: Demonstrates hidden single-stock and technology sector concentration across three popular ETF products.
  2. *UK Wrapper Split*: Spans multiple wrapper types (SIPP and ISA).
  3. *Student Starter*: Periodic monthly purchases.
- **Broker Import Presets**: Includes sample CSV files in Trading 212 and Degiro export formats.

## License

Open Data Commons Public Domain Dedication (fictional market data only; not derived from any real-world exchange feed).
