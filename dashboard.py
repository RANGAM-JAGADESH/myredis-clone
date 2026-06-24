"""
dashboard.py — MyRedis Monitoring Dashboard
============================================
CHANGE FROM ORIGINAL:
  REMOVED:  from server import store, pubsub
  REMOVED:  _collect_live() which read store.* attributes directly
  ADDED:    collect_metrics() calls load_metrics() from metrics.py
            which reads metrics.json from disk — no TCP server import.

UI (HTML/CSS/JS) is UNCHANGED.

Run independently:
    python dashboard.py     → http://localhost:8000
    python server.py        → TCP :6379, writes metrics.json
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from metrics import load_metrics             # CHANGED (was: from server import store, pubsub)

app = FastAPI(title="MyRedis Dashboard", docs_url=None, redoc_url=None)


def collect_metrics() -> dict:
    return load_metrics()


@app.get("/api/metrics")
def get_metrics():
    return JSONResponse(content=collect_metrics())


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MyRedis Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #0f1117; --surface: #1a1d27; --surface2: #22263a;
    --border: rgba(255,255,255,0.08); --text: #e8eaf0; --muted: #7a7f9a;
    --accent: #6c63ff; --green: #22c55e; --amber: #f59e0b; --red: #ef4444;
    --blue: #3b82f6; --teal: #14b8a6; --purple: #a855f7;
    --font: "SF Mono","Fira Code","Consolas",monospace;
  }
  body { background:var(--bg); color:var(--text); font-family:"Inter","Segoe UI",system-ui,sans-serif; font-size:14px; line-height:1.5; min-height:100vh; }
  .header { display:flex; align-items:center; justify-content:space-between; padding:16px 24px; border-bottom:1px solid var(--border); background:var(--surface); }
  .header-left { display:flex; align-items:center; gap:12px; }
  .logo { width:36px; height:36px; border-radius:8px; background:var(--accent); display:flex; align-items:center; justify-content:center; font-weight:700; font-size:16px; color:#fff; font-family:var(--font); }
  .header h1 { font-size:16px; font-weight:600; letter-spacing:-0.3px; }
  .header-meta { display:flex; align-items:center; gap:16px; color:var(--muted); font-size:12px; }
  .mode-badge { padding:3px 10px; border-radius:20px; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.6px; }
  .mode-badge.live { background:rgba(34,197,94,0.15); color:var(--green); }
  .mode-badge.demo { background:rgba(245,158,11,0.15); color:var(--amber); }
  .status-dot { width:8px; height:8px; border-radius:50%; background:var(--green); animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
  .container { padding:20px 24px; max-width:1400px; margin:0 auto; }
  .section-title { font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:1px; color:var(--muted); margin:20px 0 10px; }
  .grid-4 { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
  .grid-3 { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
  .grid-2 { display:grid; grid-template-columns:repeat(2,1fr); gap:12px; }
  .grid-2-1 { display:grid; grid-template-columns:2fr 1fr; gap:12px; }
  .stat-card { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:16px; position:relative; overflow:hidden; }
  .stat-card::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--accent-color,var(--accent)); }
  .stat-label { font-size:11px; color:var(--muted); font-weight:500; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; }
  .stat-value { font-size:26px; font-weight:700; font-family:var(--font); line-height:1; }
  .stat-sub { font-size:11px; color:var(--muted); margin-top:6px; }
  .stat-icon { position:absolute; right:14px; top:14px; font-size:20px; opacity:0.15; }
  .progress-wrap { margin-top:8px; }
  .progress-track { height:5px; background:var(--border); border-radius:4px; overflow:hidden; margin-top:4px; }
  .progress-fill { height:100%; border-radius:4px; transition:width 0.5s ease; }
  .progress-label { font-size:11px; color:var(--muted); display:flex; justify-content:space-between; }
  .status-card { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:16px; }
  .status-row { display:flex; align-items:center; justify-content:space-between; padding:8px 0; border-bottom:1px solid var(--border); }
  .status-row:last-child { border-bottom:none; }
  .status-key { color:var(--muted); font-size:12px; }
  .status-val { font-family:var(--font); font-size:12px; font-weight:600; }
  .badge { padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }
  .badge.green { background:rgba(34,197,94,0.12); color:var(--green); }
  .badge.amber { background:rgba(245,158,11,0.12); color:var(--amber); }
  .badge.red   { background:rgba(239,68,68,0.12);  color:var(--red); }
  .badge.blue  { background:rgba(59,130,246,0.12); color:var(--blue); }
  .badge.muted { background:var(--border); color:var(--muted); }
  .chart-card { background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:16px; }
  .chart-card h3 { font-size:12px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:12px; }
  .chart-wrap { position:relative; height:180px; }
  .repl-row { display:flex; align-items:center; gap:8px; margin-top:4px; }
  .repl-node { flex:1; background:var(--surface2); border:1px solid var(--border); border-radius:8px; padding:10px 12px; text-align:center; }
  .repl-node .label { font-size:10px; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; }
  .repl-node .val { font-family:var(--font); font-size:13px; font-weight:600; margin-top:4px; }
  .repl-arrow { color:var(--muted); font-size:18px; flex-shrink:0; }
  .lag-value { text-align:center; margin-top:8px; font-size:11px; color:var(--muted); }
  #uptime-display { font-size:11px; color:var(--muted); font-family:var(--font); }
  #offline-banner { display:none; background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); color:var(--red); text-align:center; padding:8px; font-size:12px; }
  @media (max-width:900px) { .grid-4,.grid-3 { grid-template-columns:repeat(2,1fr); } .grid-2-1 { grid-template-columns:1fr; } }
  @media (max-width:560px) { .grid-4,.grid-3,.grid-2 { grid-template-columns:1fr; } }
</style>
</head>
<body>

<div id="offline-banner">&#9888; metrics.json not updating &mdash; is server.py running? Last seen: <span id="offline-ts">&#8212;</span></div>

<header class="header">
  <div class="header-left">
    <div class="logo">R</div>
    <div>
      <h1>MyRedis Dashboard</h1>
      <div id="uptime-display">loading...</div>
    </div>
  </div>
  <div class="header-meta">
    <span>Last update: <span id="last-update">&#8212;</span></span>
    <span id="mode-badge" class="mode-badge live">live</span>
    <div class="status-dot"></div>
  </div>
</header>

<div class="container">

  <div class="section-title">System overview</div>
  <div class="grid-4">
    <div class="stat-card" style="--accent-color:var(--accent)">
      <div class="stat-icon">&#128452;</div>
      <div class="stat-label">Total keys</div>
      <div class="stat-value" id="total-keys">&#8212;</div>
      <div class="stat-sub">in-memory store</div>
    </div>
    <div class="stat-card" style="--accent-color:var(--blue)">
      <div class="stat-icon">&#9889;</div>
      <div class="stat-label">Commands executed</div>
      <div class="stat-value" id="commands-executed">&#8212;</div>
      <div class="stat-sub">since server start</div>
    </div>
    <div class="stat-card" style="--accent-color:var(--amber)">
      <div class="stat-icon">&#8987;</div>
      <div class="stat-label">TTL keys</div>
      <div class="stat-value" id="ttl-keys">&#8212;</div>
      <div class="stat-sub">auto-expiring</div>
    </div>
    <div class="stat-card" style="--accent-color:var(--teal)">
      <div class="stat-icon">&#128230;</div>
      <div class="stat-label">Cache usage</div>
      <div class="stat-value" id="cache-usage">&#8212;</div>
      <div class="progress-wrap">
        <div class="progress-label"><span>0</span><span id="cache-max">&#8212;</span></div>
        <div class="progress-track">
          <div class="progress-fill" id="cache-progress" style="background:var(--teal);width:0%"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="section-title">Network &amp; replication</div>
  <div class="grid-3">
    <div class="status-card">
      <div class="section-title" style="margin:0 0 8px">Network</div>
      <div class="status-row"><span class="status-key">Connected clients</span><span class="status-val" id="connected-clients">&#8212;</span></div>
      <div class="status-row"><span class="status-key">Active connections</span><span class="status-val" id="active-connections">&#8212;</span></div>
      <div class="status-row"><span class="status-key">Total requests</span><span class="status-val" id="total-requests">&#8212;</span></div>
    </div>
    <div class="status-card" style="grid-column:span 2">
      <div class="section-title" style="margin:0 0 10px">Replication</div>
      <div class="repl-row">
        <div class="repl-node"><div class="label">Master</div><div class="val"><span id="master-badge" class="badge muted">&#8212;</span></div></div>
        <div class="repl-arrow">&#8594;</div>
        <div class="repl-node"><div class="label">Replica</div><div class="val"><span id="replica-badge" class="badge muted">&#8212;</span></div></div>
      </div>
      <div class="lag-value">Replication lag: <span id="repl-lag" style="font-family:var(--font)">&#8212;</span></div>
    </div>
  </div>

  <div class="section-title">Pub/Sub &amp; cache</div>
  <div class="grid-2-1">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="stat-card" style="--accent-color:var(--green)">
        <div class="stat-icon">&#10003;</div>
        <div class="stat-label">Cache hits</div>
        <div class="stat-value" id="cache-hits">&#8212;</div>
        <div class="stat-sub">hit rate: <span id="hit-rate">&#8212;</span>%</div>
      </div>
      <div class="stat-card" style="--accent-color:var(--red)">
        <div class="stat-icon">&#10007;</div>
        <div class="stat-label">Cache misses</div>
        <div class="stat-value" id="cache-misses">&#8212;</div>
        <div class="stat-sub">LRU evictions: <span id="lru-evictions">&#8212;</span></div>
      </div>
      <div class="stat-card" style="--accent-color:var(--purple);grid-column:span 2">
        <div class="stat-label">Pub/Sub</div>
        <div style="display:flex;gap:24px;align-items:flex-end;flex-wrap:wrap">
          <div><div class="stat-value" id="total-channels">&#8212;</div><div class="stat-sub">channels</div></div>
          <div><div class="stat-value" id="active-subscribers">&#8212;</div><div class="stat-sub">subscribers</div></div>
          <div><div class="stat-value" id="messages-published">&#8212;</div><div class="stat-sub">messages published</div></div>
        </div>
      </div>
    </div>
    <div class="chart-card">
      <h3>Cache hit vs miss</h3>
      <div class="chart-wrap"><canvas id="donut-chart"></canvas></div>
    </div>
  </div>

  <div class="section-title">Persistence</div>
  <div class="grid-3">
    <div class="status-card" style="grid-column:span 2">
      <div class="section-title" style="margin:0 0 8px">dump.json</div>
      <div class="status-row"><span class="status-key">Status</span><span id="dump-status" class="badge muted">&#8212;</span></div>
      <div class="status-row"><span class="status-key">Last save time</span><span class="status-val" id="last-save-time" style="font-family:var(--font);font-size:11px">&#8212;</span></div>
      <div class="status-row"><span class="status-key">Persistence enabled</span><span id="persistence-enabled" class="badge muted">&#8212;</span></div>
      <div class="status-row"><span class="status-key">File size</span><span class="status-val" id="dump-size">&#8212;</span></div>
    </div>
    <div class="stat-card" style="--accent-color:var(--blue)">
      <div class="stat-label">Server uptime</div>
      <div class="stat-value" id="uptime-stat">&#8212;</div>
      <div class="stat-sub" id="uptime-unit">seconds</div>
    </div>
  </div>

</div>

<script>
const donutCtx = document.getElementById('donut-chart').getContext('2d');
const donutChart = new Chart(donutCtx, {
  type: 'doughnut',
  data: {
    labels: ['Hits','Misses'],
    datasets: [{ data:[0,0], backgroundColor:['#22c55e','#ef4444'], borderWidth:0, hoverOffset:4 }]
  },
  options: {
    cutout: '72%',
    plugins: { legend: { position:'bottom', labels:{ color:'#7a7f9a', font:{size:11}, padding:12 } } },
    animation: { duration:500 }
  }
});

function set(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }

function fmtUptime(secs) {
  if (secs < 60)    return [secs, 'seconds'];
  if (secs < 3600)  return [Math.floor(secs/60), 'minutes'];
  if (secs < 86400) return [Math.floor(secs/3600), 'hours'];
  return [Math.floor(secs/86400), 'days'];
}

function statusBadge(id, val, map) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = val;
  el.className = 'badge ' + (map[val] || 'muted');
}

let lastTimestamp = null;
let staleCount    = 0;

async function update() {
  let m;
  try {
    const res = await fetch('/api/metrics');
    m = await res.json();
  } catch(e) { return; }

  if (m.timestamp === lastTimestamp) {
    staleCount++;
    if (staleCount >= 3) {
      document.getElementById('offline-banner').style.display = 'block';
      document.getElementById('offline-ts').textContent = m.timestamp;
    }
  } else {
    staleCount = 0;
    document.getElementById('offline-banner').style.display = 'none';
  }
  lastTimestamp = m.timestamp;

  set('total-keys',        (m.total_keys        ?? 0).toLocaleString());
  set('commands-executed', (m.commands_executed  ?? 0).toLocaleString());
  set('ttl-keys',           m.ttl_keys           ?? 0);
  set('cache-usage',        m.cache_usage        ?? 0);
  set('cache-max',          m.max_cache_size     ?? 128);
  const pct = m.max_cache_size > 0 ? Math.round(((m.cache_usage??0)/m.max_cache_size)*100) : 0;
  document.getElementById('cache-progress').style.width = pct + '%';

  set('connected-clients',  m.connected_clients  ?? 0);
  set('active-connections', m.connected_clients  ?? 0);
  set('total-requests',    (m.total_requests     ?? 0).toLocaleString());

  statusBadge('master-badge', m.master_status ?? 'unknown',
    { online:'green', offline:'red', unknown:'muted' });
  statusBadge('replica-badge', m.replica_status ?? 'unknown',
    { syncing:'blue', online:'green', offline:'red', unknown:'muted', 'not configured':'muted' });
  set('repl-lag', (m.replication_lag_ms ?? 0) + ' ms');

  set('total-channels',     m.total_channels     ?? 0);
  set('active-subscribers', m.active_subscribers ?? 0);
  set('messages-published',(m.messages_published ?? 0).toLocaleString());

  set('cache-hits',   (m.cache_hit_count  ?? 0).toLocaleString());
  set('cache-misses', (m.cache_miss_count ?? 0).toLocaleString());
  set('hit-rate',      m.cache_hit_rate   ?? 0);
  set('lru-evictions', m.lru_evictions    ?? 0);
  donutChart.data.datasets[0].data = [m.cache_hit_count??0, m.cache_miss_count??0];
  donutChart.update();

  statusBadge('dump-status', m.dump_json_status ?? 'unknown',
    { ok:'green', missing:'red', unknown:'muted' });
  set('last-save-time', m.last_save_time ?? 'never');
  statusBadge('persistence-enabled', (m.dump_json_status==='ok') ? 'yes' : 'no',
    { yes:'green', no:'amber' });
  set('dump-size', (m.dump_size_kb??0) > 0 ? m.dump_size_kb + ' KB' : '\u2014');

  const [val, unit] = fmtUptime(m.uptime_seconds ?? 0);
  set('uptime-stat', val);
  set('uptime-unit', unit);
  set('uptime-display', 'uptime ' + (m.uptime_seconds??0) + 's');
  set('last-update', m.timestamp ?? '\u2014');
}

update();
setInterval(update, 3000);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    print("""
+----------------------------------------------+
|       MyRedis Monitoring Dashboard           |
+----------------------------------------------+
|  URL    ->  http://localhost:8000            |
|  API    ->  http://localhost:8000/api/metrics|
|  Source ->  metrics.json (written by         |
|             server.py, read by dashboard)    |
+----------------------------------------------+
""")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")