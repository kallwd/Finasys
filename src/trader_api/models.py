from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Holding(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    quantity: int = Field(ge=0, description="Shares, including odd-lot shares")
    average_cost: float = Field(ge=0)
    market_price: float = Field(gt=0)

    @property
    def market_value(self) -> float:
        return round(self.quantity * self.market_price, 2)


class PortfolioSnapshot(BaseModel):
    broker_mode: Literal["mock"]
    data_source: str
    as_of: datetime
    cash_balance: float = Field(ge=0)
    holdings: list[Holding]


class TargetAllocation(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    target_weight: float = Field(gt=0, le=1)
    reference_price: float = Field(gt=0)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class PreviewRequest(BaseModel):
    allocations: list[TargetAllocation] = Field(min_length=1)
    managed_symbols: list[str] = Field(default_factory=list)

    @field_validator("managed_symbols")
    @classmethod
    def normalize_managed_symbols(cls, values: list[str]) -> list[str]:
        return sorted({value.strip().upper() for value in values if value.strip()})


class OrderLine(BaseModel):
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    current_quantity: int = Field(ge=0)
    target_quantity: int = Field(ge=0)
    quantity_delta: int
    reference_price: float = Field(gt=0)
    estimated_order_value: float = Field(ge=0)


class PreviewResponse(BaseModel):
    mode: Literal["preview_only"] = "preview_only"
    trading_enabled: Literal[False] = False
    capital_limit: int
    investable_capital: int
    minimum_cash_reserve: int
    requested_target_weight: float
    target_market_value: float
    estimated_buy_value: float
    estimated_sell_value: float
    orders: list[OrderLine]
    ignored_unmanaged_holdings: list[str]
    warnings: list[str]


class HealthResponse(BaseModel):
    service: Literal["finasys"] = "finasys"
    status: Literal["ok"] = "ok"
    broker_mode: str
    trading_enabled: bool
