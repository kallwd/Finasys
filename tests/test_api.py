from fastapi.testclient import TestClient

from trader_api.main import app


client = TestClient(app)


def test_health_is_read_only_mock_mode() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "service": "finasys",
        "status": "ok",
        "broker_mode": "mock",
        "trading_enabled": False,
    }


def test_home_page_is_an_operable_safe_dashboard() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Finasys" in response.text
    assert "200,000 元模擬資金" in response.text
    assert "不送真單" in response.text
    assert "開啟 FinLab 登入" in response.text
    assert "每日紀錄報告" in response.text
    assert "顯示 K 線" in response.text


def test_reports_page_is_available() -> None:
    response = client.get("/reports")
    assert response.status_code == 200
    assert "Finasys 每日報告" in response.text


def test_system_status_reports_installed_engines_and_safety() -> None:
    response = client.get("/v1/system/status")
    assert response.status_code == 200
    status = response.json()
    assert status["policy"]["capital_limit"] == 200_000
    assert status["policy"]["trading_enabled"] is False
    assert status["ledger"]["initial_capital"] == 200_000
    assert all(item["installed"] for item in status["ml_packages"].values())
    assert any(item["label"] == "券商持股隔離（完全不連接）" for item in status["readiness"])


def test_policy_caps_capital_and_reserves_cash() -> None:
    policy = client.get("/v1/policy").json()
    assert policy["capital_limit"] == 200_000
    assert policy["cash_reserve_ratio"] == 0.20
    assert policy["max_position_value"] == 40_000
    assert policy["trading_enabled"] is False


def test_current_portfolio_is_explicitly_mock_data() -> None:
    portfolio = client.get("/v1/portfolio/current").json()
    assert portfolio["broker_mode"] == "mock"
    assert portfolio["data_source"] == "mock_not_live_market_data"


def test_preview_creates_odd_lot_share_deltas_within_limits() -> None:
    response = client.post(
        "/v1/orders/preview",
        json={
            "allocations": [
                {"symbol": "0050", "target_weight": 0.20, "reference_price": 190},
                {"symbol": "2330", "target_weight": 0.20, "reference_price": 1200},
                {"symbol": "2317", "target_weight": 0.20, "reference_price": 200},
                {"symbol": "2454", "target_weight": 0.20, "reference_price": 1500},
            ],
            "managed_symbols": ["0050", "2330"],
        },
    )
    assert response.status_code == 200
    preview = response.json()
    assert preview["mode"] == "preview_only"
    assert preview["trading_enabled"] is False
    assert preview["requested_target_weight"] == 0.8
    assert preview["target_market_value"] <= preview["investable_capital"]
    assert all(line["estimated_order_value"] <= 40_000 for line in preview["orders"])


def test_preview_rejects_weight_above_cash_reserve_limit() -> None:
    response = client.post(
        "/v1/orders/preview",
        json={
            "allocations": [
                {"symbol": "0050", "target_weight": 0.50, "reference_price": 190},
                {"symbol": "2330", "target_weight": 0.35, "reference_price": 1200},
            ]
        },
    )
    assert response.status_code == 422


def test_model_self_test_uses_synthetic_data() -> None:
    response = client.post("/v1/models/self-test")
    assert response.status_code == 200
    result = response.json()
    assert result["data"] == "synthetic_self_test_only"
    assert 0 <= result["classifier_accuracy"] <= 1
    assert result["latest_hmm_regime"] in {"偏多", "盤整", "偏空"}
