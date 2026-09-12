from datetime import datetime, timezone
from typing import Protocol

from trader_api.models import Holding, PortfolioSnapshot


class ReadOnlyBroker(Protocol):
    """The first-stage broker boundary deliberately exposes no order method."""

    def get_portfolio(self) -> PortfolioSnapshot: ...


class MockBroker:
    """Deterministic sample data for the independent paper portfolio."""

    def get_portfolio(self) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            broker_mode="mock",
            data_source="mock_not_live_market_data",
            as_of=datetime.now(timezone.utc),
            cash_balance=191_150,
            holdings=[
                Holding(
                    symbol="0050",
                    quantity=15,
                    average_cost=180,
                    market_price=190,
                ),
                Holding(
                    symbol="2330",
                    quantity=5,
                    average_cost=1_100,
                    market_price=1_200,
                ),
            ],
        )
