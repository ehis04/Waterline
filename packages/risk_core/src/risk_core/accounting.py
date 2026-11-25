"""Portfolio accounting, bitemporal ledger fold, FX conversion, and valuation snapshot."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Mapping

from risk_core.types import Money, Position, Result, ValuationSnapshot, WarningMessage, Severity


class LedgerEventType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    BUY = "BUY"
    SELL = "SELL"
    SPLIT = "SPLIT"
    DIVIDEND = "DIVIDEND"
    FEE = "FEE"


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    effective_at: str
    event_type: LedgerEventType
    instrument_id: str | None
    quantity: Decimal = Decimal("0")
    price: Decimal = Decimal("0")
    currency: str = "EUR"
    fee: Decimal = Decimal("0")
    split_ratio: Decimal = Decimal("1.0")


def round_money(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fold_ledger(
    events: list[LedgerEvent],
    base_currency: str,
    prices: Mapping[str, Decimal],
    fx_rates: Mapping[tuple[str, str], Decimal],  # (from_ccy, to_ccy) -> rate
) -> Result[ValuationSnapshot, str]:
    """Fold an ordered sequence of ledger events and compute a ValuationSnapshot."""
    sorted_events = sorted(events, key=lambda e: e.effective_at)

    cash_balances: dict[str, Decimal] = {}
    share_holdings: dict[str, Decimal] = {}
    cost_bases: dict[str, Decimal] = {}
    instrument_currencies: dict[str, str] = {}
    warnings: list[WarningMessage] = []

    for ev in sorted_events:
        ccy = ev.currency
        cash_balances.setdefault(ccy, Decimal("0"))

        if ev.event_type == LedgerEventType.DEPOSIT:
            cash_balances[ccy] += ev.quantity
        elif ev.event_type == LedgerEventType.WITHDRAWAL:
            cash_balances[ccy] -= ev.quantity
        elif ev.event_type == LedgerEventType.FEE:
            cash_balances[ccy] -= ev.fee
        elif ev.event_type == LedgerEventType.DIVIDEND:
            cash_balances[ccy] += ev.quantity * ev.price
        elif ev.event_type == LedgerEventType.BUY:
            inst = ev.instrument_id
            if not inst:
                continue
            instrument_currencies[inst] = ccy
            cost = ev.quantity * ev.price + ev.fee
            cash_balances[ccy] -= cost
            prev_qty = share_holdings.get(inst, Decimal("0"))
            prev_cost = cost_bases.get(inst, Decimal("0"))
            share_holdings[inst] = prev_qty + ev.quantity
            cost_bases[inst] = prev_cost + cost
        elif ev.event_type == LedgerEventType.SELL:
            inst = ev.instrument_id
            if not inst:
                continue
            proceeds = ev.quantity * ev.price - ev.fee
            cash_balances[ccy] += proceeds
            prev_qty = share_holdings.get(inst, Decimal("0"))
            new_qty = prev_qty - ev.quantity
            if new_qty < Decimal("0"):
                warnings.append(
                    WarningMessage(
                        code="NEGATIVE_HOLDING",
                        message=f"Sell resulted in negative shares for {inst}",
                        severity=Severity.WARNING,
                    )
                )
            share_holdings[inst] = max(Decimal("0"), new_qty)
            if prev_qty > Decimal("0") and new_qty > Decimal("0"):
                cost_bases[inst] = cost_bases[inst] * (new_qty / prev_qty)
            else:
                cost_bases[inst] = Decimal("0")
        elif ev.event_type == LedgerEventType.SPLIT:
            inst = ev.instrument_id
            if inst and inst in share_holdings:
                ratio = ev.split_ratio
                share_holdings[inst] = share_holdings[inst] * ratio
                # Total cost basis remains unchanged, per-share cost scales inversely

    def get_fx(from_c: str, to_c: str) -> Decimal:
        if from_c == to_c:
            return Decimal("1.0")
        pair = (from_c, to_c)
        if pair in fx_rates:
            return fx_rates[pair]
        inv_pair = (to_c, from_c)
        if inv_pair in fx_rates:
            return Decimal("1.0") / fx_rates[inv_pair]
        warnings.append(
            WarningMessage(
                code="MISSING_FX_RATE",
                message=f"Missing FX rate for {from_c}->{to_c}; assumed 1.0",
                severity=Severity.ERROR,
            )
        )
        return Decimal("1.0")

    # Value cash in base currency
    total_cash_base = Decimal("0")
    for ccy, amt in cash_balances.items():
        total_cash_base += amt * get_fx(ccy, base_currency)

    # Value positions
    positions: list[Position] = []
    total_holdings_val_base = Decimal("0")
    priced_holdings_val_base = Decimal("0")

    for inst, qty in share_holdings.items():
        if qty <= Decimal("0"):
            continue
        inst_ccy = instrument_currencies.get(inst, base_currency)
        rate = get_fx(inst_ccy, base_currency)
        cost_basis = cost_bases.get(inst, Decimal("0"))

        if inst in prices:
            price = prices[inst]
            mkt_val = qty * price
            mkt_val_base = mkt_val * rate
            priced_holdings_val_base += mkt_val_base
            total_holdings_val_base += mkt_val_base
            positions.append(
                Position(
                    instrument_id=inst,
                    quantity=qty,
                    cost_basis=cost_basis,
                    current_price=price,
                    market_value=round_money(mkt_val),
                    currency=inst_ccy,
                )
            )
        else:
            warnings.append(
                WarningMessage(
                    code="UNPRICED_INSTRUMENT",
                    message=f"Instrument {inst} has no price; excluded from priced coverage",
                    severity=Severity.WARNING,
                )
            )
            positions.append(
                Position(
                    instrument_id=inst,
                    quantity=qty,
                    cost_basis=cost_basis,
                    current_price=Decimal("0"),
                    market_value=Decimal("0"),
                    currency=inst_ccy,
                )
            )

    total_portfolio_value = round_money(total_cash_base + total_holdings_val_base)
    denom = total_cash_base + total_holdings_val_base
    coverage = (
        (total_cash_base + priced_holdings_val_base) / denom
        if denom > Decimal("0")
        else Decimal("1.0")
    )

    snapshot = ValuationSnapshot(
        as_of=sorted_events[-1].effective_at if sorted_events else "",
        base_currency=base_currency,
        positions=positions,
        cash=round_money(total_cash_base),
        total_market_value=total_portfolio_value,
        coverage_ratio=coverage.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP),
    )
    return Result.ok(snapshot, warnings=warnings)
