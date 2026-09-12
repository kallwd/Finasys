from __future__ import annotations


def dashboard_html() -> str:
    return """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Finasys</title>
  <style>
    :root { --ink:#172033; --muted:#667085; --line:#e4e8ef; --paper:#fff;
      --ground:#f4f6f9; --green:#0c7c59; --green-soft:#eaf8f2;
      --amber:#b36a00; --amber-soft:#fff5df; --red:#b42318; --navy:#172554; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:var(--ground);
      font-family:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif; }
    header { background:var(--navy); color:#fff; padding:28px 5vw 62px; }
    .header-inner { max-width:1120px; margin:auto; display:flex; justify-content:space-between;
      align-items:flex-start; gap:24px; }
    h1 { margin:8px 0 6px; font-size:clamp(28px,4vw,42px); letter-spacing:-1px; }
    header p { margin:0; color:#cbd5e1; }
    .pill { display:inline-flex; align-items:center; gap:7px; padding:7px 11px;
      border-radius:999px; font-weight:700; font-size:13px; background:#ffffff1c; }
    .dot { width:8px; height:8px; border-radius:50%; background:#51d7a5; }
    main { max-width:1120px; margin:-34px auto 64px; padding:0 20px; }
    .grid { display:grid; grid-template-columns:repeat(12,1fr); gap:18px; }
    .card { grid-column:span 4; background:var(--paper); border:1px solid var(--line);
      border-radius:16px; padding:22px; box-shadow:0 8px 24px rgba(23,32,51,.05); }
    .wide { grid-column:span 8; } .full { grid-column:1/-1; }
    .eyebrow { color:var(--muted); font-size:13px; font-weight:750; letter-spacing:.08em;
      text-transform:uppercase; margin-bottom:10px; }
    .metric { font-size:32px; font-weight:780; letter-spacing:-1px; margin:4px 0 6px; }
    .sub { color:var(--muted); font-size:14px; line-height:1.55; }
    .status { display:inline-flex; padding:5px 9px; border-radius:999px; font-size:13px;
      font-weight:700; background:var(--green-soft); color:var(--green); }
    .status.wait { background:var(--amber-soft); color:var(--amber); }
    .money-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:14px; margin-top:18px; }
    .money-grid div { padding:13px; border-radius:11px; background:#f7f8fb; }
    .money-grid strong { display:block; font-size:20px; margin-top:4px; }
    .checklist { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; margin-top:16px; }
    .check { border:1px solid var(--line); border-radius:11px; padding:12px 13px;
      display:flex; align-items:center; gap:10px; font-size:14px; }
    .icon { width:23px; height:23px; display:grid; place-items:center; border-radius:50%;
      flex:0 0 auto; background:var(--green-soft); color:var(--green); font-weight:900; }
    .icon.no { background:#fff0ef; color:var(--red); }
    .actions { display:flex; flex-wrap:wrap; gap:10px; margin-top:18px; }
    button, a.button { border:0; border-radius:10px; padding:11px 15px; font:inherit;
      font-weight:720; cursor:pointer; text-decoration:none; background:var(--navy); color:#fff; }
    button.secondary, a.secondary { background:#eef1f6; color:var(--ink); }
    button:disabled { opacity:.55; cursor:wait; }
    .notice { background:var(--amber-soft); border-left:4px solid #d99a28; border-radius:9px;
      padding:13px 15px; color:#6e4800; line-height:1.55; margin-top:16px; }
    .strategy-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:14px; }
    .strategy { border:1px solid var(--line); border-radius:12px; padding:15px; }
    .strategy strong { display:block; font-size:18px; margin-bottom:6px; }
    .chart-toolbar { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:14px 0; }
    input, select { border:1px solid var(--line); border-radius:10px; padding:11px 13px;
      font:inherit; background:#fff; color:var(--ink); }
    input { min-width:200px; flex:1; }
    .chart-wrap { position:relative; width:100%; min-height:390px; border:1px solid var(--line);
      border-radius:12px; background:#101827; overflow:hidden; }
    #candleChart { display:block; width:100%; height:390px; }
    .chart-empty { position:absolute; inset:0; display:grid; place-items:center; color:#9ca3af;
      pointer-events:none; padding:30px; text-align:center; }
    pre { white-space:pre-wrap; background:#111827; color:#d1fae5; border-radius:12px;
      padding:15px; min-height:70px; overflow:auto; font-size:13px; }
    .footer { color:var(--muted); text-align:center; margin-top:24px; font-size:13px; }
    @media (max-width:820px) { .card,.wide { grid-column:1/-1; }
      .header-inner { flex-direction:column; } .checklist { grid-template-columns:1fr; } }
    @media (max-width:680px) { .strategy-grid { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <header><div class="header-inner">
    <div><span class="pill"><span class="dot"></span>本機模擬模式</span>
      <h1>Finasys</h1>
      <p>200,000 元模擬資金 · T+2 保守帳本 · 不連券商、不融資、不送真單</p></div>
    <div class="pill" id="clock">讀取台北時間…</div>
  </div></header>
  <main><div class="grid">
    <section class="card"><div class="eyebrow">市場狀態</div>
      <span class="status wait" id="marketBadge">讀取中</span>
      <div class="metric" id="marketLabel">—</div><div class="sub" id="marketReason">—</div>
      <div class="sub" style="margin-top:12px">委託 08:30–13:30<br>交易 09:00–13:30</div></section>
    <section class="card wide"><div class="eyebrow">模擬資金與 T+2</div>
      <div class="metric" id="capital">NT$ 200,000</div><div class="sub">獨立 SQLite 帳本；賣出款在交割前不可再用。</div>
      <div class="money-grid">
        <div><span class="sub">可下單現金</span><strong id="orderable">—</strong></div>
        <div><span class="sub">保留現金</span><strong id="reserve">—</strong></div>
        <div><span class="sub">已保留待交割</span><strong id="reserved">—</strong></div>
        <div><span class="sub">未交割筆數</span><strong id="unsettled">—</strong></div>
      </div></section>
    <section class="card"><div class="eyebrow">FinLab</div>
      <span class="status wait" id="finlabBadge">檢查中</span>
      <div class="metric" style="font-size:24px" id="finlabVersion">—</div>
      <div class="sub">登入只走 FinLab 官方瀏覽器流程；憑證不顯示在本頁。</div>
      <div class="actions"><button onclick="finlabLogin()">開啟 FinLab 登入</button></div></section>
    <section class="card wide"><div class="eyebrow">模型引擎</div>
      <div class="metric" style="font-size:24px">Ranking + HMM</div>
      <div class="sub" id="packages">檢查套件中…</div>
      <div class="actions"><button class="secondary" onclick="modelTest()">執行合成資料自我檢查</button></div></section>
    <section class="card full"><div class="eyebrow">手動股票 K 線</div>
      <div class="metric" style="font-size:24px">搜尋台股代碼</div>
      <div class="chart-toolbar">
        <input id="stockSymbol" inputmode="text" maxlength="10" value="2330" placeholder="例如 2330 或 0050" aria-label="台股代碼" onkeydown="if(event.key==='Enter')loadCandles()">
        <select id="candleLimit" aria-label="K 線期間">
          <option value="60">60 個交易日</option><option value="120" selected>120 個交易日</option><option value="250">250 個交易日</option>
        </select>
        <button id="candleButton" onclick="loadCandles()">顯示 K 線</button>
      </div>
      <div class="chart-wrap"><canvas id="candleChart"></canvas><div class="chart-empty" id="chartEmpty">輸入股票代碼後按「顯示 K 線」</div></div>
      <div class="sub" id="chartStatus" style="margin-top:10px">日 K 資料來源會顯示在這裡；紅色上漲、綠色下跌。</div>
    </section>
    <section class="card full"><div class="eyebrow">每日開盤前分級</div>
      <div class="strategy-grid">
        <div class="strategy"><strong>1. 冒險</strong><div class="sub">高風險／高潛力；總額上限 NT$40,000，預設停損 8%，最長持有 10 個交易日。</div></div>
        <div class="strategy"><strong>2. 穩健</strong><div class="sub">以年化約 7% 為研究目標、不是保證；總額上限 NT$120,000，預設停損 5%。</div></div>
        <div class="strategy"><strong>3. 別碰</strong><div class="sub">不配置、不放空。資料不足、流動性不佳或風險不合格時直接列入。</div></div>
      </div>
      <div class="sub" style="margin-top:13px">優先觀察：科技巨頭、AI／半導體生態、電子設計、AI 基礎設施、通訊與機器人；其他標的須說明納入原因。</div>
    </section>
    <section class="card full"><div class="eyebrow">系統完成度</div>
      <div class="checklist" id="readiness"></div>
      <div class="notice">目前是研究與模擬階段。模型自我檢查使用合成資料，不代表報酬，也不會產生投資建議或委託。</div>
      <div class="actions"><button onclick="refreshAll()">重新整理</button>
        <button class="secondary" onclick="initializeLedger()">初始化 200,000 元帳本</button>
        <button class="secondary" onclick="settleLedger()">結算到期模擬款項</button>
        <a class="button secondary" href="/reports">每日紀錄報告</a>
        <a class="button secondary" href="/docs">API 文件</a></div>
      <pre id="output">系統訊息會顯示在這裡。</pre></section>
  </div><div class="footer">Codex 額度歸零時停止新的開發工作；這個本機模擬器本身不消耗 Codex 額度。</div></main>
  <script>
    let clockBaseMs = null;
    let clockSyncedAtMs = null;
    const taipeiClock = new Intl.DateTimeFormat('sv-SE', {
      timeZone:'Asia/Taipei', year:'numeric', month:'2-digit', day:'2-digit',
      hour:'2-digit', minute:'2-digit', second:'2-digit', hourCycle:'h23'
    });
    function renderClock(){
      if(clockBaseMs===null) return;
      const now = new Date(clockBaseMs + (Date.now() - clockSyncedAtMs));
      document.getElementById('clock').textContent = taipeiClock.format(now) + '+08:00';
    }
    function syncClock(value){
      clockBaseMs = Date.parse(value);
      clockSyncedAtMs = Date.now();
      renderClock();
    }
    const money = value => new Intl.NumberFormat('zh-TW',{style:'currency',currency:'TWD',maximumFractionDigits:0}).format(value);
    const out = value => document.getElementById('output').textContent = typeof value === 'string' ? value : JSON.stringify(value,null,2);
    let lastCandleData = null;
    function drawCandles(payload){
      lastCandleData=payload;
      const canvas=document.getElementById('candleChart');
      const wrap=canvas.parentElement;
      const dpr=window.devicePixelRatio||1;
      const width=Math.max(320,wrap.clientWidth), height=390;
      canvas.width=Math.floor(width*dpr); canvas.height=Math.floor(height*dpr);
      const ctx=canvas.getContext('2d'); ctx.setTransform(dpr,0,0,dpr,0,0);
      ctx.clearRect(0,0,width,height); ctx.fillStyle='#101827'; ctx.fillRect(0,0,width,height);
      const rows=payload.candles, pad={l:58,r:18,t:22,b:42};
      const chartW=width-pad.l-pad.r, chartH=height-pad.t-pad.b;
      const min=Math.min(...rows.map(d=>d.low)), max=Math.max(...rows.map(d=>d.high));
      const span=Math.max(max-min,0.01), y=v=>pad.t+(max-v)/span*chartH;
      ctx.strokeStyle='#263244'; ctx.lineWidth=1; ctx.fillStyle='#94a3b8'; ctx.font='12px Segoe UI';
      for(let i=0;i<=4;i++){const yy=pad.t+chartH*i/4;ctx.beginPath();ctx.moveTo(pad.l,yy);ctx.lineTo(width-pad.r,yy);ctx.stroke();const p=max-span*i/4;ctx.fillText(p.toFixed(p>=100?1:2),6,yy+4);}
      const step=chartW/rows.length, body=Math.max(1,Math.min(9,step*.62));
      rows.forEach((d,i)=>{const x=pad.l+step*(i+.5), up=d.close>=d.open, color=up?'#ef4444':'#10b981';ctx.strokeStyle=color;ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(x,y(d.high));ctx.lineTo(x,y(d.low));ctx.stroke();const top=Math.min(y(d.open),y(d.close)), h=Math.max(1,Math.abs(y(d.open)-y(d.close)));ctx.fillRect(x-body/2,top,body,h);});
      const labelCount=Math.min(6,rows.length), labelStep=Math.max(1,Math.floor((rows.length-1)/(labelCount-1)));
      ctx.fillStyle='#94a3b8'; ctx.textAlign='center';
      for(let i=0;i<rows.length;i+=labelStep){const x=pad.l+step*(i+.5);ctx.fillText(rows[i].date.slice(5),x,height-16);} ctx.textAlign='left';
      const latest=rows[rows.length-1];
      document.getElementById('chartEmpty').style.display='none';
      document.getElementById('chartStatus').textContent=`${payload.symbol} · ${payload.count} 個交易日 · ${payload.first_date} 至 ${payload.last_date} · 最新 O ${latest.open} / H ${latest.high} / L ${latest.low} / C ${latest.close} · 來源 ${payload.source}`;
    }
    async function loadCandles(){
      const input=document.getElementById('stockSymbol'), button=document.getElementById('candleButton');
      const symbol=input.value.trim().toUpperCase(), limit=document.getElementById('candleLimit').value;
      if(!/^[0-9A-Z]{2,10}$/.test(symbol)){document.getElementById('chartStatus').textContent='請輸入有效代碼，例如 2330 或 0050。';return;}
      input.value=symbol;button.disabled=true;button.textContent='讀取中…';document.getElementById('chartStatus').textContent='正在取得 FinLab 日 K 資料…';
      try{drawCandles(await call(`/v1/market/candles/${encodeURIComponent(symbol)}?limit=${limit}`));}
      catch(e){document.getElementById('chartStatus').textContent=e.message;document.getElementById('chartEmpty').style.display='grid';document.getElementById('chartEmpty').textContent='目前無法顯示 K 線';}
      finally{button.disabled=false;button.textContent='顯示 K 線';}
    }
    async function call(url, options={}) { const r=await fetch(url,options); const body=await r.json(); if(!r.ok) throw new Error(body.detail||r.statusText); return body; }
    async function refreshAll(){
      try { const s=await call('/v1/system/status');
        syncClock(s.market.now);
        document.getElementById('marketLabel').textContent=s.market.label;
        document.getElementById('marketReason').textContent=s.market.reason;
        const mb=document.getElementById('marketBadge'); mb.textContent=s.market.state==='open'?'市場開放':'市場關閉'; mb.className='status '+(s.market.state==='open'?'':'wait');
        document.getElementById('capital').textContent=money(s.ledger.initial_capital);
        document.getElementById('orderable').textContent=money(s.ledger.orderable_cash);
        document.getElementById('reserve').textContent=money(s.ledger.reserve_floor);
        document.getElementById('reserved').textContent=money(s.ledger.reserved_cash);
        document.getElementById('unsettled').textContent=s.ledger.unsettled.length+' 筆';
        const fb=document.getElementById('finlabBadge'); fb.textContent=s.finlab.status; fb.className='status '+(s.finlab.credentials_saved?'':'wait');
        document.getElementById('finlabVersion').textContent='FinLab '+s.finlab.version;
        document.getElementById('packages').textContent=Object.entries(s.ml_packages).map(([k,v])=>k.replace('_',' ')+' '+(v.installed?v.version:'未安裝')).join(' · ');
        const list=document.getElementById('readiness'); list.textContent='';
        s.readiness.forEach(item=>{const row=document.createElement('div');row.className='check';const icon=document.createElement('span');icon.className='icon '+(item.ready?'':'no');icon.textContent=item.ready?'✓':'×';const label=document.createElement('span');label.textContent=item.label;row.append(icon,label);list.append(row);});
      } catch(e){out('重新整理失敗：'+e.message)} }
    async function finlabLogin(){try{out(await call('/v1/finlab/login',{method:'POST'}));}catch(e){out(e.message)}}
    async function modelTest(){try{out('模型自我檢查中…');out(await call('/v1/models/self-test',{method:'POST'}));}catch(e){out(e.message)}}
    async function initializeLedger(){try{out(await call('/v1/paper/initialize',{method:'POST'}));await refreshAll();}catch(e){out(e.message)}}
    async function settleLedger(){try{out(await call('/v1/paper/settle',{method:'POST'}));await refreshAll();}catch(e){out(e.message)}}
    setInterval(renderClock,1000);
    setInterval(refreshAll,60000);
    window.addEventListener('resize',()=>{if(lastCandleData)drawCandles(lastCandleData)});
    refreshAll();
  </script>
</body></html>"""
