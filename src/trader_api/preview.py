from dataclasses import dataclass

from trader_api.broker import ReadOnlyBroker
from trader_api.config import RiskPolicy
from trader_api.models import (
    OrderLine,
    PreviewRequest,
    PreviewResponse,
    TargetAllocation,
)


@dataclass(slots=True)
class PolicyViolation(ValueError):
    detail: str

    def __str__(self) -> str:
        return self.detail


def _validate_request(request: PreviewRequest, policy: RiskPolicy) -> None:
    symbols = [allocation.symbol for allocation in request.allocations]
    if len(symbols) != len(set(symbols)):
        raise PolicyViolation("目標配置包含重複股票代號。")

    if len(symbols) > policy.max_positions:
        raise PolicyViolation(f"目標持股數不可超過 {policy.max_positions} 檔。")

    total_weight = sum(allocation.target_weight for allocation in request.allocations)
    maximum_weight = 1 - policy.cash_reserve_ratio
    if total_weight > maximum_weight + 1e-9:
        raise PolicyViolation(
            f"目標權重合計 {total_weight:.2%} 超過上限 {maximum_weight:.2%}。"
        )

    for allocation in request.allocations:
        requested_value = policy.capital_limit * allocation.target_weight
        if requested_value > policy.max_position_value + 1e-9:
            raise PolicyViolation(
                f"{allocation.symbol} 目標金額 {requested_value:,.0f} 元超過"
                f"單一持股上限 {policy.max_position_value:,} 元。"
            )


def _target_quantity(allocation: TargetAllocation, policy: RiskPolicy) -> int:
    target_value = policy.capital_limit * allocation.target_weight
    return int(target_value // allocation.reference_price)


def create_preview(
    request: PreviewRequest,
    broker: ReadOnlyBroker,
    policy: RiskPolicy,
) -> PreviewResponse:
    _validate_request(request, policy)
    snapshot = broker.get_portfolio()

    allocations = {allocation.symbol: allocation for allocation in request.allocations}
    current = {holding.symbol: holding for holding in snapshot.holdings}
    managed = set(request.managed_symbols) | set(allocations)
    ignored = sorted(set(current) - managed)

    warnings = ["目前使用獨立模擬持股與模擬價格，不連接任何券商帳務或下單系統。"]
    if ignored:
        warnings.append("未納入策略管理的既有持股已忽略，不會產生賣出預覽。")

    orders: list[OrderLine] = []
    target_market_value = 0.0
    estimated_buy_value = 0.0
    estimated_sell_value = 0.0

    for symbol in sorted(managed):
        allocation = allocations.get(symbol)
        holding = current.get(symbol)
        current_quantity = holding.quantity if holding else 0

        if allocation:
            reference_price = allocation.reference_price
            target_quantity = _target_quantity(allocation, policy)
        else:
            if holding is None:
                continue
            reference_price = holding.market_price
            target_quantity = 0

        delta = target_quantity - current_quantity
        order_value = round(abs(delta) * reference_price, 2)
        if order_value > policy.max_order_value + 1e-9:
            raise PolicyViolation(
                f"{symbol} 預估委託金額 {order_value:,.0f} 元超過"
                f"單筆上限 {policy.max_order_value:,} 元。"
            )

        action = "BUY" if delta > 0 else "SELL" if delta < 0 else "HOLD"
        target_market_value += target_quantity * reference_price
        if action == "BUY":
            estimated_buy_value += order_value
        elif action == "SELL":
            estimated_sell_value += order_value

        orders.append(
            OrderLine(
                symbol=symbol,
                action=action,
                current_quantity=current_quantity,
                target_quantity=target_quantity,
                quantity_delta=delta,
                reference_price=reference_price,
                estimated_order_value=order_value,
            )
        )

    if target_market_value > policy.investable_capital + 1e-9:
        raise PolicyViolation("目標持股市值超過可投資資金上限。")

    if estimated_buy_value > snapshot.cash_balance + estimated_sell_value + 1e-9:
        warnings.append("模擬帳戶現金可能不足；正式階段必須再次查詢交割款。")

    if any(
        allocation.reference_price > policy.max_position_value
        for allocation in request.allocations
    ):
        warnings.append("部分股票價格高於單一持股上限，目標股數會是 0。")

    return PreviewResponse(
        capital_limit=policy.capital_limit,
        investable_capital=policy.investable_capital,
        minimum_cash_reserve=policy.capital_limit - policy.investable_capital,
        requested_target_weight=round(
            sum(allocation.target_weight for allocation in request.allocations), 6
        ),
        target_market_value=round(target_market_value, 2),
        estimated_buy_value=round(estimated_buy_value, 2),
        estimated_sell_value=round(estimated_sell_value, 2),
        orders=orders,
        ignored_unmanaged_holdings=ignored,
        warnings=warnings,
    )
