from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


TAIPEI = ZoneInfo("Asia/Taipei")

# TWSE 115 年市場開休市日期（2026）。這些日期來自證交所公開行事曆。
# 2/12、2/13 是「市場無交易，僅辦理結算交割作業」，因此只關閉交易。
TWSE_2026_CLOSED = {
    date(2026, 1, 1),
    date(2026, 2, 16),
    date(2026, 2, 17),
    date(2026, 2, 18),
    date(2026, 2, 19),
    date(2026, 2, 20),
    date(2026, 2, 27),
    date(2026, 4, 3),
    date(2026, 4, 6),
    date(2026, 5, 1),
    date(2026, 6, 19),
    date(2026, 9, 25),
    date(2026, 9, 28),
    date(2026, 10, 9),
    date(2026, 10, 26),
    date(2026, 12, 25),
}
TWSE_2026_MARKET_ONLY_CLOSED = {date(2026, 2, 12), date(2026, 2, 13)}


@dataclass(frozen=True, slots=True)
class MarketSession:
    state: str
    label: str
    reason: str
    now: str
    order_acceptance: str = "08:30–13:30"
    regular_trading: str = "09:00–13:30"
    intraday_odd_lot: str = "09:00–13:30（09:10 首次撮合，其後每 5 秒）"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _closed_dates(year: int) -> set[date]:
    if year == 2026:
        return TWSE_2026_CLOSED | TWSE_2026_MARKET_ONLY_CLOSED
    return set()


def _settlement_closed_dates(year: int) -> set[date]:
    if year == 2026:
        return TWSE_2026_CLOSED
    return set()


def is_trading_day(day: date) -> bool:
    return day.weekday() < 5 and day not in _closed_dates(day.year)


def is_settlement_day(day: date) -> bool:
    return day.weekday() < 5 and day not in _settlement_closed_dates(day.year)


def settlement_date(trade_day: date, offset: int = 2) -> date:
    if offset < 0:
        raise ValueError("settlement offset must be non-negative")

    candidate = trade_day
    counted = 0
    while counted < offset:
        candidate += timedelta(days=1)
        if is_settlement_day(candidate):
            counted += 1
    return candidate


def market_session(now: datetime | None = None) -> MarketSession:
    current = now or datetime.now(TAIPEI)
    if current.tzinfo is None:
        current = current.replace(tzinfo=TAIPEI)
    else:
        current = current.astimezone(TAIPEI)

    day = current.date()
    stamp = current.isoformat(timespec="seconds")
    if day.weekday() >= 5:
        return MarketSession("closed", "休市", "週六、週日休市", stamp)
    if day in _closed_dates(day.year):
        reason = "證交所休市日"
        if day in TWSE_2026_MARKET_ONLY_CLOSED:
            reason = "市場無交易，僅辦理結算交割作業"
        return MarketSession("closed", "休市", reason, stamp)

    clock = current.timetz().replace(tzinfo=None)
    if clock < time(8, 30):
        return MarketSession("pre_open", "開盤前", "08:30 開始接受委託", stamp)
    if clock < time(9, 0):
        return MarketSession("order_acceptance", "接受委託", "09:00 開始交易", stamp)
    if clock <= time(13, 30):
        return MarketSession("open", "交易中", "台股一般交易時段", stamp)
    return MarketSession("closed", "已收盤", "13:30 收盤", stamp)
