# ADR-007: Quantile and Tail Risk Conventions

## Status
Accepted

## Context
Discrepancies in quantitative libraries arise from differing conventions regarding whether risk metrics report losses as positive numbers and which tail quantile definition is employed.

## Decision
1. Standardize on **loss as a positive value**:
   - Value at Risk ($\text{VaR}_\alpha$) represents the minimum expected loss at confidence level $\alpha$ (e.g., $\alpha = 0.95$ or $0.99$).
   - Expected Shortfall ($\text{ES}_\alpha$) represents the conditional expected loss given that loss exceeds $\text{VaR}_\alpha$.
2. Implement explicit sample size gates before computing parametric or empirical tail statistics to avoid false precision on sparse time series.
