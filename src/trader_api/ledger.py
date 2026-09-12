from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from trader_api.market_calendar import is_trading_day, settlement_date


Side = Literal["BUY", "SELL"]


class PaperLedger:
    """Conservative cash ledger: buys reserve cash now; sells release cash on T+2."""

    def __init__(self, path: Path, initial_capital: int = 200_000) -> None:
        self.path = path
        self.initial_capital = initial_capital

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS account (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    initial_capital INTEGER NOT NULL,
                    settled_cash REAL NOT NULL,
                    reserved_cash REAL NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS positions (
                    symbol TEXT PRIMARY KEY,
                    quantity INTEGER NOT NULL CHECK (quantity >= 0),
                    average_cost REAL NOT NULL CHECK (average_cost >= 0)
                );
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    price REAL NOT NULL CHECK (price > 0),
                    cash_effect REAL NOT NULL CHECK (cash_effect > 0),
                    trade_date TEXT NOT NULL,
                    settlement_date TEXT NOT NULL,
                    settled INTEGER NOT NULL DEFAULT 0 CHECK (settled IN (0, 1)),
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_paper_trades_due
                ON paper_trades(settled, settlement_date);
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO account
                    (id, initial_capital, settled_cash, reserved_cash, created_at)
                VALUES (1, ?, ?, 0, ?)
                """,
                (self.initial_capital, self.initial_capital, datetime.now().isoformat()),
            )
            account = connection.execute("SELECT * FROM account WHERE id = 1").fetchone()
            old_capital = int(account["initial_capital"])
            if old_capital != self.initial_capital:
                delta = self.initial_capital - old_capital
                connection.execute(
                    """
                    UPDATE account
                    SET initial_capital = ?, settled_cash = settled_cash + ?
                    WHERE id = 1
                    """,
                    (self.initial_capital, delta),
                )
            connection.execute("PRAGMA optimize")

    def snapshot(self, reserve_floor: float = 10_000) -> dict:
        self.initialize()
        with self._connect() as connection:
            account = connection.execute("SELECT * FROM account WHERE id = 1").fetchone()
            positions = connection.execute(
                "SELECT symbol, quantity, average_cost FROM positions ORDER BY symbol"
            ).fetchall()
            unsettled = connection.execute(
                """
                SELECT id, symbol, side, quantity, price, cash_effect,
                       trade_date, settlement_date
                FROM paper_trades
                WHERE settled = 0
                ORDER BY settlement_date, id
                """
            ).fetchall()

        settled_cash = float(account["settled_cash"])
        reserved_cash = float(account["reserved_cash"])
        available_cash = max(0.0, settled_cash - reserved_cash)
        return {
            "initial_capital": int(account["initial_capital"]),
            "settled_cash": round(settled_cash, 2),
            "reserved_cash": round(reserved_cash, 2),
            "available_cash": round(available_cash, 2),
            "orderable_cash": round(max(0.0, available_cash - reserve_floor), 2),
            "reserve_floor": round(reserve_floor, 2),
            "positions": [dict(row) for row in positions],
            "unsettled": [dict(row) for row in unsettled],
        }

    def record_fill(
        self,
        *,
        symbol: str,
        side: Side,
        quantity: int,
        price: float,
        cash_effect: float,
        trade_day: date,
        reserve_floor: float = 10_000,
    ) -> int:
        """Record a simulated fill. cash_effect must already include fees and taxes."""
        self.initialize()
        symbol = symbol.strip().upper()
        if not symbol or quantity <= 0 or price <= 0 or cash_effect <= 0:
            raise ValueError("invalid paper fill")
        if not is_trading_day(trade_day):
            raise ValueError("paper fills are only allowed on TWSE trading days")

        due = settlement_date(trade_day)
        with self._connect() as connection:
            account = connection.execute("SELECT * FROM account WHERE id = 1").fetchone()
            position = connection.execute(
                "SELECT * FROM positions WHERE symbol = ?", (symbol,)
            ).fetchone()
            old_quantity = int(position["quantity"]) if position else 0
            old_average = float(position["average_cost"]) if position else 0.0

            if side == "BUY":
                available = float(account["settled_cash"]) - float(account["reserved_cash"])
                if cash_effect > max(0.0, available - reserve_floor) + 1e-9:
                    raise ValueError("insufficient T+2-safe orderable cash")
                new_quantity = old_quantity + quantity
                new_average = ((old_quantity * old_average) + cash_effect) / new_quantity
                connection.execute(
                    "UPDATE account SET reserved_cash = reserved_cash + ? WHERE id = 1",
                    (cash_effect,),
                )
                connection.execute(
                    """
                    INSERT INTO positions(symbol, quantity, average_cost)
                    VALUES (?, ?, ?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        quantity = excluded.quantity,
                        average_cost = excluded.average_cost
                    """,
                    (symbol, new_quantity, new_average),
                )
            elif side == "SELL":
                if quantity > old_quantity:
                    raise ValueError("paper position is insufficient")
                remaining = old_quantity - quantity
                if remaining:
                    connection.execute(
                        "UPDATE positions SET quantity = ? WHERE symbol = ?",
                        (remaining, symbol),
                    )
                else:
                    connection.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
            else:
                raise ValueError("side must be BUY or SELL")

            cursor = connection.execute(
                """
                INSERT INTO paper_trades(
                    symbol, side, quantity, price, cash_effect,
                    trade_date, settlement_date, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    side,
                    quantity,
                    price,
                    cash_effect,
                    trade_day.isoformat(),
                    due.isoformat(),
                    datetime.now().isoformat(),
                ),
            )
            return int(cursor.lastrowid)

    def settle_due(self, through: date) -> int:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, side, cash_effect FROM paper_trades
                WHERE settled = 0 AND settlement_date <= ?
                ORDER BY settlement_date, id
                """,
                (through.isoformat(),),
            ).fetchall()
            for row in rows:
                amount = float(row["cash_effect"])
                if row["side"] == "BUY":
                    connection.execute(
                        """
                        UPDATE account
                        SET settled_cash = settled_cash - ?,
                            reserved_cash = reserved_cash - ?
                        WHERE id = 1
                        """,
                        (amount, amount),
                    )
                else:
                    connection.execute(
                        "UPDATE account SET settled_cash = settled_cash + ? WHERE id = 1",
                        (amount,),
                    )
                connection.execute(
                    "UPDATE paper_trades SET settled = 1 WHERE id = ?", (row["id"],)
                )
            return len(rows)
