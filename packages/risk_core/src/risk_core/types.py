"""Fundamental types, typed Result container, and financial primitives."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class WarningMessage:
    code: str
    message: str
    severity: Severity = Severity.WARNING
    context: dict[str, str] = field(default_factory=dict)


@dataclass
class Result(Generic[T, E]):
    value: T | None = None
    error: E | None = None
    warnings: list[WarningMessage] = field(default_factory=list)

    @property
    def is_ok(self) -> bool:
        return self.error is None and self.value is not None

    @property
    def is_err(self) -> bool:
        return self.error is not None

    @classmethod
    def ok(cls, value: T, warnings: list[WarningMessage] | None = None) -> "Result[T, E]":
        return cls(value=value, warnings=warnings or [])

    @classmethod
    def err(cls, error: E, warnings: list[WarningMessage] | None = None) -> "Result[T, E]":
        return cls(error=error, warnings=warnings or [])


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))
        if len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError(f"Currency must be 3-letter ISO code, got '{self.currency}'")


@dataclass(frozen=True)
class Position:
    instrument_id: str
    quantity: Decimal
    cost_basis: Decimal
    current_price: Decimal
    market_value: Decimal
    currency: str


@dataclass(frozen=True)
class ValuationSnapshot:
    as_of: str
    base_currency: str
    positions: list[Position]
    cash: Decimal
    total_market_value: Decimal
    coverage_ratio: Decimal  # 0.0 to 1.0 (proportion of holdings with valid pricing)
