# Finasys 移植與接手說明

## 1. 專案定位

Finasys 是本機專用的台股研究與虛擬交易系統。它不連接券商、不讀取真實持倉、不送出真實委託；核心工作是取得台股資料、產生量化分析、維護不可作弊的虛擬帳本，並透過本機網頁 UI 顯示結果。

產品名稱固定為 **Finasys**。FinLab 只是可替換的資料與量化研究來源，不是產品名稱。

## 2. 不得更改的交易規則

- 初始虛擬資金：NT$200,000。
- 至少保留 NT$40,000 已交割現金；策略可用資金上限 NT$160,000。
- 單一標的與單筆交易上限 NT$40,000，最多同時持有 5 檔。
- 冒險類部位總上限 NT$40,000；預設停損 8%，最長持有 10 個交易日。
- 穩健類部位總上限 NT$120,000；預設停損 5%，最長持有 20 個交易日。
- 「穩健約 7%」是年化研究目標，不是每月或每筆報酬，也不是保證。
- 禁止融資、融券、放空、期貨、選擇權及任何槓桿。
- 買進成交後立即鎖住完整成本；賣出所得到台股交易日 T+2 才可重新使用。
- 未交割賣款不得拿來買股；資金不足時必須不交易。
- 允許全數持有現金，「今天不交易」是正常且有效的決策。

## 3. 每日分析範圍

優先研究：

- 台灣科技巨頭。
- AI 與半導體生態。
- IC 設計、EDA 與電子設計。
- AI 基礎設施、伺服器與散熱。
- 通訊、網路設備與光通訊。
- 機器人、自動化與關鍵零組件。

其他產業只有在資料與風險條件合格時才能提出，並須說明納入原因。

每日候選標的分成：

1. **冒險**：高波動、高潛力，受嚴格金額、停損與持有期限制。
2. **穩健**：品質、趨勢、估值及流動性較完整，以年化約 7% 為研究目標。
3. **別碰**：不配置、不放空；資料不足、重大事件風險、流動性不佳或模型分歧時優先列入。

## 4. 不可作弊規則

- 開盤前決策只能使用決策截止時間以前已公開的資料。
- 每日決策以附時間戳的報告保存，建立後不得覆寫或刪除。
- 開盤前只能建立待成交計畫，不能把尚未成交的價格寫成成交價。
- 開盤後依實際可取得價格核對，禁止事後選擇當日最低買價或最高賣價。
- 只有日資料時，以開盤價加不利滑價及完整費稅估算。
- 跳空穿越停損時，以較差的實際開盤／可成交價計算。
- 所有成交、費用、交割與現金變化只追加，不得回填美化績效。
- FinLab 未登入、資料中斷、資料不足或 AI 額度為零時，停止新增分析與交易，不得猜測。

完整政策位於 `STRATEGY_POLICY.md`。

## 5. 已完成的功能

- FastAPI 本機 UI，僅綁定 `127.0.0.1:17888`。
- 台北時間每秒更新，並每分鐘向伺服器重新同步。
- 台股開盤、收盤、週末及休市狀態顯示。
- NT$200,000 SQLite 虛擬帳本與保守 T+2 結算。
- scikit-learn、LightGBM、hmmlearn 安裝與模型自我檢查。
- FinLab 2.x 瀏覽器／Google 登入及本機憑證狀態顯示。
- 手動輸入台股代碼查看 60、120 或 250 個交易日的日 K 線。
- K 線使用 FinLab 真實 OHLCV 資料，台灣慣例紅漲綠跌。
- `report` 子資料夾與 UI 報告入口。
- 週一至週五 08:20 的 Codex 開盤前 heartbeat 自動化。
- 完整測試目前為 14 項通過。

## 6. 尚未完成或不得誤認為完成

- 現有 LightGBM／HMM 按鈕使用合成資料做程式自我檢查，不代表生產模型已有預測力。
- 尚需建立正式的歷史資料特徵工程、walk-forward 驗證、因子穩定性分析及避免前視偏誤的完整訓練流程。
- 尚需建立每日收盤後的成交核對自動化與 `YYYY-MM-DD-close.md`。
- 尚未建立公司名稱模糊搜尋；目前 K 線以股票代碼搜尋。
- 尚未建立 macOS 的 `.command` 或 `.app` 一鍵啟動器。
- 永遠不得新增真實券商下單端點，除非使用者日後重新明確授權並另行設計安全流程。

## 7. 專案結構

```text
Finasys/
├─ src/trader_api/          核心程式與 UI
├─ scripts/                 Windows 啟動腳本
├─ tests/                   自動測試
├─ report/                  每日不可覆寫報告
├─ .runtime/                SQLite 帳本與本機執行紀錄
├─ .venv/                   目前 Windows Python 環境
├─ pyproject.toml           Python 相依套件
├─ uv.lock                  鎖定版本
├─ STRATEGY_POLICY.md       交易與報告規則
├─ FINASYS_HANDOFF.md       本文件
└─ 啟動 Finasys.vbs        Windows 一鍵啟動
```

不要把 FinLab Token、Google 登入資訊、密碼或其他憑證寫入專案。

## 8. Windows 使用方式

一般使用者直接雙擊：

```text
啟動 Finasys.vbs
```

UI 位址：

```text
http://127.0.0.1:17888/
```

重新建立環境：

```powershell
uv python install 3.12
uv sync --dev
.\scripts\start_trader.ps1
```

執行測試：

```powershell
$env:LOKY_MAX_CPU_COUNT = "1"
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp .test-tmp\pytest-current
```

## 9. 搬到 macOS

不要把 Windows 的 `.venv` 直接拿到 Mac 使用。複製原始碼、`pyproject.toml`、`uv.lock`、政策文件及需要保留的 `report`／`.runtime` 後，在 Mac 重新建立環境：

```bash
brew install uv
uv python install 3.12
uv sync --dev
uv run python -m finlab login
uv run uvicorn trader_api.main:app --app-dir src --host 127.0.0.1 --port 17888
```

FinLab 登入憑證與 Google 登入狀態不會隨專案自動搬移，應在新電腦重新登入。Windows 的 `.vbs`／PowerShell 啟動器不能直接在 macOS 使用。

## 10. 搬到另一個 AI／Codex 帳號

Finasys 核心不綁定 AI 帳號。複製專案後即可操作本機 UI、K 線、資料、模型及帳本。若要讓新的 Codex 帳號繼續開發或建立晨報，可另外安裝 FinLab skill：

```bash
npx skills add https://github.com/koreal6803/finlab-ai --skill finlab
```

Skill 只是教 AI 如何使用 FinLab，不包含股票資料。新的電腦仍須安裝 FinLab Python 套件並完成 FinLab 登入。Codex 的 heartbeat／自動化屬於帳號與任務設定，搬移專案後必須在新帳號重新建立。

## 11. 沒有 AI 的電腦

沒有 AI 仍可使用：

- 本機 UI。
- FinLab 資料下載與 K 線。
- 固定規則、因子、LightGBM／HMM 模型。
- 回測、虛擬帳本與 T+2 結算。
- 既有每日報告。

沒有 AI 時不會有新聞語意整理、自然語言晨報或由 AI 主動提出產業論點。建議讓量化核心負責可重現的數值決策，AI 只作為可替換的新聞解讀與說明層。

## 12. 每日報告格式

所有報告固定寫入 `report/`：

- `YYYY-MM-DD-premarket.md`：開盤前不可變更的分析與待成交計畫。
- `YYYY-MM-DD-close.md`：收盤後成交、停損、現金與 T+2 核對。

每份報告至少包含：產生時間、資料截止時間、資料來源、三類名單、進出條件、虛擬股數與金額、停損、失效條件、現金、持倉及 T+2 未交割款。

同名報告存在時不得覆寫；補充資料另建附時間戳的新檔。

## 13. 接手後的優先順序

1. 驗證 FinLab 登入與資料最後日期。
2. 讀取 `STRATEGY_POLICY.md`，確認不得更動的資金與防作弊規則。
3. 建立無前視偏誤的正式資料集與候選股票池。
4. 完成 walk-forward 回測，納入手續費、證交稅、滑價與零股限制。
5. 將每日開盤前計畫與收盤後核對寫入 `report/`。
6. 維持完全模擬模式，不連接券商。

任何無法驗證的資料、價格或新聞，都必須明確標示缺失並選擇不交易。
