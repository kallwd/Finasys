from datetime import date, datetime

import pytest

from trader_api.ledger import PaperLedger
from trader_api.market_calendar import (
    TAIPEI,
    is_settlement_day,
    is_trading_day,
    market_session,
    settlement_date,
)


def test_twse_2026_schedule_and_market_hours() -> None:
    assert is_trading_day(date(2026, 2, 11))
    assert not is_trading_day(date(2026, 2, 12))
    assert is_settlement_day(date(2026, 2, 12))
    assert not is_trading_day(date(2026, 2, 20))
    assert is_trading_day(date(2026, 2, 23))

    assert market_session(datetime(2026, 8, 17, 8, 45, tzinfo=TAIPEI)).state == "order_acceptance"
    assert market_session(datetime(2026, 8, 17, 9, 10, tzinfo=TAIPEI)).state == "open"
    assert market_session(datetime(2026, 8, 15, 10, 0, tzinfo=TAIPEI)).state == "closed"


def test_t_plus_two_counts_settlement_business_days() -> None:
    assert settlement_date(date(2026, 2, 11)) == date(2026, 2, 13)
    assert settlement_date(date(2026, 8, 14)) == date(2026, 8, 18)


def test_ledger_reserves_buy_cash_and_delays_sell_proceeds(tmp_path) -> None:
    ledger = PaperLedger(tmp_path / "paper.db", initial_capital=50_000)
    ledger.initialize()

    ledger.record_fill(
        symbol="0050",
        side="BUY",
        quantity=10,
        price=100,
        cash_effect=1000,
        trade_day=date(2026, 2, 11),
    )
    after_buy = ledger.snapshot()
    assert after_buy["settled_cash"] == 50_000
    assert after_buy["reserved_cash"] == 1_000
    assert after_buy["orderable_cash"] == 39_000
    assert ledger.settle_due(date(2026, 2, 12)) == 0
    assert ledger.settle_due(date(2026, 2, 13)) == 1

    ledger.record_fill(
        symbol="0050",
        side="SELL",
        quantity=5,
        price=120,
        cash_effect=600,
        trade_day=date(2026, 2, 23),
    )
    after_sell = ledger.snapshot()
    assert after_sell["settled_cash"] == 49_000
    assert after_sell["available_cash"] == 49_000
    assert ledger.settle_due(date(2026, 2, 24)) == 0
    assert ledger.settle_due(date(2026, 2, 25)) == 1
    assert ledger.snapshot()["settled_cash"] == 49_600


def test_ledger_rejects_weekend_fills(tmp_path) -> None:
    ledger = PaperLedger(tmp_path / "paper.db", initial_capital=50_000)
    with pytest.raises(ValueError, match="trading days"):
        ledger.record_fill(
            symbol="0050",
            side="BUY",
            quantity=1,
            price=100,
            cash_effect=100,
            trade_day=date(2026, 8, 15),
        )
