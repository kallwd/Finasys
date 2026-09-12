from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from trader_api.finlab_service import finlab_status
from trader_api.market_calendar import TAIPEI


class CandleDataError(RuntimeError):
    pass


def normalize_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not re.fullmatch(r"[0-9A-Z]{2,10}", symbol):
        raise CandleDataError("請輸入有效的台股代碼，例如 2330 或 0050。")
    return symbol


def load_candles(symbol: str, limit: int = 120) -> dict:
    symbol = normalize_symbol(symbol)
    if limit < 20 or limit > 500:
        raise CandleDataError("K 線範圍必須介於 20 到 500 個交易日。")

    status = finlab_status()
    if not status["credentials_saved"]:
        raise CandleDataError("FinLab 本機尚未完成登入，請先按「開啟 FinLab 登入」。")

    try:
        from finlab import data

        data.set_market("tw")
        opened, high, low, closed, volume = data.gets(
            "price:開盤價",
            "price:最高價",
            "price:最低價",
            "price:收盤價",
            "price:成交股數",
        )
        if symbol not in closed.columns:
            raise CandleDataError(f"找不到台股代碼 {symbol}。")

        frame = pd.DataFrame(
            {
                "open": opened[symbol],
                "high": high[symbol],
                "low": low[symbol],
                "close": closed[symbol],
                "volume": volume[symbol],
            }
        ).dropna(subset=["open", "high", "low", "close"])
        frame = frame.tail(limit)
        if frame.empty:
            raise CandleDataError(f"{symbol} 沒有可用的日 K 資料。")

        candles = [
            {
                "date": timestamp.strftime("%Y-%m-%d"),
                "open": round(float(row.open), 4),
                "high": round(float(row.high), 4),
                "low": round(float(row.low), 4),
                "close": round(float(row.close), 4),
                "volume": int(row.volume) if pd.notna(row.volume) else 0,
            }
            for timestamp, row in frame.iterrows()
        ]
        return {
            "symbol": symbol,
            "source": "FinLab",
            "fetched_at": datetime.now(TAIPEI).isoformat(timespec="seconds"),
            "first_date": candles[0]["date"],
            "last_date": candles[-1]["date"],
            "count": len(candles),
            "candles": candles,
        }
    except CandleDataError:
        raise
    except Exception as exc:
        raise CandleDataError(f"K 線資料讀取失敗：{exc}") from exc
