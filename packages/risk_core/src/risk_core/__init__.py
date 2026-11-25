"""Pure quantitative financial risk library for Waterline."""

from risk_core.types import (
    Money,
    Position,
    Result,
    ValuationSnapshot,
    WarningMessage,
    Severity,
)
from risk_core.accounting import (
    LedgerEvent,
    LedgerEventType,
    fold_ledger,
)
from risk_core.returns import (
    CashFlow,
    calculate_twr,
    calculate_modified_dietz,
    calculate_mwr_irr,
)
from risk_core.metrics import (
    calculate_mdd,
    calculate_historical_var_es,
    calculate_gaussian_var_es,
    calculate_ewma_volatility,
    calculate_hhi,
    calculate_diversification_ratio,
)
from risk_core.euler import (
    calculate_portfolio_volatility,
    calculate_euler_contributions,
)
from risk_core.risk_diff import (
    RiskDiffResult,
    calculate_risk_diff,
)

__version__ = "0.1.0"

__all__ = [
    "Money",
    "Position",
    "Result",
    "ValuationSnapshot",
    "WarningMessage",
    "Severity",
    "LedgerEvent",
    "LedgerEventType",
    "fold_ledger",
    "CashFlow",
    "calculate_twr",
    "calculate_modified_dietz",
    "calculate_mwr_irr",
    "calculate_mdd",
    "calculate_historical_var_es",
    "calculate_gaussian_var_es",
    "calculate_ewma_volatility",
    "calculate_hhi",
    "calculate_diversification_ratio",
    "calculate_portfolio_volatility",
    "calculate_euler_contributions",
    "RiskDiffResult",
    "calculate_risk_diff",
]
