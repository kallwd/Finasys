from pydantic import BaseModel, ConfigDict, Field


class RiskPolicy(BaseModel):
    """Hard limits for the 200,000 TWD paper-trading strategy sleeve."""

    model_config = ConfigDict(frozen=True)

    capital_limit: int = Field(default=200_000, gt=0)
    cash_reserve_ratio: float = Field(default=0.20, ge=0, lt=1)
    max_position_value: int = Field(default=40_000, gt=0)
    max_order_value: int = Field(default=40_000, gt=0)
    max_positions: int = Field(default=5, ge=1)
    aggressive_bucket_limit: int = Field(default=40_000, ge=0)
    steady_bucket_limit: int = Field(default=120_000, ge=0)
    aggressive_stop_loss: float = Field(default=0.08, gt=0, lt=1)
    steady_stop_loss: float = Field(default=0.05, gt=0, lt=1)
    aggressive_max_holding_days: int = Field(default=10, ge=1)
    steady_max_holding_days: int = Field(default=20, ge=1)
    broker_mode: str = "mock"
    trading_enabled: bool = False
    allow_margin: bool = False
    allow_short: bool = False
    allow_futures: bool = False
    allow_leverage: bool = False

    @property
    def investable_capital(self) -> int:
        return int(self.capital_limit * (1 - self.cash_reserve_ratio))


POLICY = RiskPolicy()
