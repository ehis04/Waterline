# ADR-006: ISIN-First Instrument Model

## Status
Accepted

## Context
Retail investors frequently trade European UCITS ETFs that have multiple cross-listings on different exchanges (e.g., LSE, Xetra, Euronext Amsterdam) trading in different currencies (GBP, EUR, USD) under varying ticker symbols, while representing the identical underlying security fund pool.

## Decision
1. Treat **ISIN** (International Securities Identification Number, ISO 6166) as the primary instrument identifier.
2. Model market access via associated `listings` records capturing Market Identifier Code (MIC, ISO 10383), exchange ticker, and trading currency.
3. Decouple fund holdings and core risk look-through from exchange-specific listing tickers.
