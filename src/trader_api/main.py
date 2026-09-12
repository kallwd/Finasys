from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from trader_api.broker import MockBroker
from trader_api.candles import CandleDataError, load_candles
from trader_api.config import POLICY, RiskPolicy
from trader_api.finlab_service import finlab_status, start_finlab_login
from trader_api.ledger import PaperLedger
from trader_api.market_calendar import TAIPEI, market_session
from trader_api.modeling import package_status, run_demo_model
from trader_api.models import HealthResponse, PortfolioSnapshot, PreviewRequest, PreviewResponse
from trader_api.preview import PolicyViolation, create_preview
from trader_api.security import LocalOnlyMiddleware
from trader_api.ui import dashboard_html


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ledger = PaperLedger(PROJECT_ROOT / ".runtime" / "paper_trader.db", POLICY.capital_limit)
broker = MockBroker()

app = FastAPI(
    title="Finasys API",
    version="0.2.0",
    description="本機模擬與 FinLab 研究；不連接券商持股，也不提供真實下單端點。",
)
app.add_middleware(LocalOnlyMiddleware)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    return HTMLResponse(content=dashboard_html())


@app.get("/reports", response_class=HTMLResponse, include_in_schema=False)
def reports_index() -> HTMLResponse:
    report_dir = PROJECT_ROOT / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        (path for path in report_dir.glob("????-??-??-*.md") if path.is_file()),
        reverse=True,
    )
    items = "".join(
        f'<li><a href="/reports/{path.name}">{path.name}</a></li>' for path in files
    ) or "<li>尚無每日報告。</li>"
    return HTMLResponse(
        "<!doctype html><html lang='zh-Hant'><meta charset='utf-8'>"
        "<title>Finasys 每日報告</title><style>body{max-width:820px;margin:48px auto;"
        "padding:0 20px;font-family:Segoe UI,Microsoft JhengHei,sans-serif;color:#172033}"
        "a{color:#172554}li{margin:12px 0}</style><body><h1>Finasys 每日報告</h1>"
        f"<ul>{items}</ul><p><a href='/'>回首頁</a></p></body></html>"
    )


@app.get("/reports/{filename}", response_class=PlainTextResponse, include_in_schema=False)
def report_file(filename: str) -> PlainTextResponse:
    if not filename.endswith(".md") or "/" in filename or "\\" in filename:
        return PlainTextResponse("報告不存在。", status_code=404)
    path = PROJECT_ROOT / "report" / filename
    if not path.is_file() or not path.name[:10].replace("-", "").isdigit():
        return PlainTextResponse("報告不存在。", status_code=404)
    return PlainTextResponse(path.read_text(encoding="utf-8"), media_type="text/markdown")


@app.exception_handler(PolicyViolation)
async def policy_violation_handler(_request: Request, exc: PolicyViolation) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(broker_mode=POLICY.broker_mode, trading_enabled=False)


@app.get("/v1/system/status")
def system_status() -> dict:
    ml = package_status()
    finlab = finlab_status()
    snapshot = ledger.snapshot(POLICY.capital_limit - POLICY.investable_capital)
    return {
        "market": market_session().to_dict(),
        "policy": POLICY.model_dump(),
        "ledger": snapshot,
        "finlab": finlab,
        "ml_packages": ml,
        "readiness": [
            {"label": "本機操作 UI", "ready": True},
            {"label": "200,000 元模擬帳本", "ready": True},
            {"label": "台股 2026 開休市與交易時段", "ready": True},
            {"label": "T+2 保守交割控制", "ready": True},
            {"label": "scikit-learn / LightGBM / HMM", "ready": all(v["installed"] for v in ml.values())},
            {"label": "FinLab 登入憑證", "ready": bool(finlab["credentials_saved"])},
            {"label": "券商持股隔離（完全不連接）", "ready": True},
            {"label": "真實下單安全鎖（已關閉）", "ready": True},
        ],
    }


@app.get("/v1/market/session")
def get_market_session() -> dict:
    return market_session().to_dict()


@app.get("/v1/market/candles/{symbol}")
def get_market_candles(symbol: str, limit: int = Query(default=120, ge=20, le=500)) -> dict:
    try:
        return load_candles(symbol, limit)
    except CandleDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/v1/policy", response_model=RiskPolicy)
def get_policy() -> RiskPolicy:
    return POLICY


@app.get("/v1/portfolio/current", response_model=PortfolioSnapshot)
def get_current_portfolio() -> PortfolioSnapshot:
    return broker.get_portfolio()


@app.post("/v1/orders/preview", response_model=PreviewResponse)
def preview_orders(request: PreviewRequest) -> PreviewResponse:
    return create_preview(request=request, broker=broker, policy=POLICY)


@app.post("/v1/paper/initialize")
def initialize_paper_ledger() -> dict:
    ledger.initialize()
    return {"status": "ok", "message": "模擬帳本已就緒；重複初始化不會重設既有資料。"}


@app.post("/v1/paper/settle")
def settle_paper_ledger() -> dict:
    settled = ledger.settle_due(datetime.now(TAIPEI).date())
    return {"status": "ok", "settled_count": settled, "message": f"已結算 {settled} 筆到期模擬款項。"}


@app.post("/v1/finlab/login")
def login_finlab() -> dict:
    return start_finlab_login(PROJECT_ROOT)


@app.get("/v1/models/packages")
def get_model_packages() -> dict:
    return package_status()


@app.post("/v1/models/self-test")
def model_self_test() -> dict:
    return run_demo_model()
