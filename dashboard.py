"""
dashboard.py — MyRedis Monitoring Dashboard
============================================
Run with:
    pip install fastapi uvicorn
    python dashboard.py

Opens at http://localhost:8000

HOW METRICS ARE COLLECTED
--------------------------
This dashboard imports your existing MyRedis modules and reads their
internal state directly — no network calls, no polling overhead.

Import the objects your server.py already instantiates:
    from server import store, pubsub, replication_manager

If you run the dashboard as a standalone process (separate from the
TCP server), switch /api/metrics to call a lightweight status endpoint
on your TCP server instead. The structure below makes that easy —
just replace the `collect_metrics()` body.

MODULES ASSUMED
---------------
store           — your DataStore instance (KV + TTL + LRU)
pubsub          — your PubSub instance
replication     — your ReplicationManager instance (optional)
persistence     — your Persistence instance (optional)

Adjust attribute names to match your actual implementation.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

# ─── Attempt to import your MyRedis modules ─────────────────────────────────
# Replace these with your actual module/class imports.
# If running as a standalone file for demo, the fallback mock data is used.

try:
    from server import store, pubsub  # noqa: F401  — adjust to your imports
    LIVE_MODE = True
except ImportError:
    LIVE_MODE = False  # runs in demo mode with simulated metrics


# ─── Demo/mock metrics (used when LIVE_MODE = False) ────────────────────────

_demo_state = {
    "commands_executed": 0,
    "cache_hits": 142,
    "cache_misses": 38,
    "lru_evictions": 7,
    "total_requests": 0,
    "start_time": time.time(),
}


def _increment_demo():
    """Simulate live traffic for demo mode."""
    import random
    _demo_state["commands_executed"] += random.randint(1, 5)
    _demo_state["total_requests"] += random.randint(1, 8)
    _demo_state["cache_hits"] += random.randint(0, 3)
    _demo_state["cache_misses"] += random.randint(0, 1)


# ─── Metric collection ───────────────────────────────────────────────────────

def collect_metrics() -> dict:
    """
    Central metrics collector.

    In LIVE_MODE: reads directly from your imported MyRedis objects.
    In demo mode: returns realistic-looking simulated data.

    Extend this function as you add features to MyRedis.
    Each key here maps to a dashboard widget below.
    """

    if LIVE_MODE:
        return _collect_live()
    else:
        _increment_demo()
        return _collect_demo()


def _collect_live() -> dict:
    """
    Read metrics from actual MyRedis module instances.

    Attribute names here (store.data, store.ttl_map, etc.) must match
    your actual DataStore implementation — adjust as needed.
    """

    # ── KV Store ─────────────────────────────────────────────────────────────
    all_keys = list(store.data.keys()) if hasattr(store, "data") else []
    total_keys = len(all_keys)

    # ── TTL ──────────────────────────────────────────────────────────────────
    ttl_map = getattr(store, "ttl_map", {})
    now = time.time()
    ttl_keys = sum(1 for exp in ttl_map.values() if exp > now)

    # ── LRU Cache ────────────────────────────────────────────────────────────
    max_cache_size = getattr(store, "capacity", 100)
    lru_evictions = getattr(store, "eviction_count", 0)
    cache_hits = getattr(store, "hit_count", 0)
    cache_misses = getattr(store, "miss_count", 0)

    # ── Network / TCP Server ─────────────────────────────────────────────────
    connected_clients = getattr(store, "connected_clients", 0)
    commands_executed = getattr(store, "command_count", 0)
    total_requests = getattr(store, "request_count", commands_executed)

    # ── Pub/Sub ───────────────────────────────────────────────────────────────
    channels = getattr(pubsub, "channels", {})
    total_channels = len(channels)
    active_subscribers = sum(len(subs) for subs in channels.values())
    messages_published = getattr(pubsub, "message_count", 0)

    # ── Replication ───────────────────────────────────────────────────────────
    try:
        from server import replication_manager  # noqa: F401
        master_status = getattr(replication_manager, "master_status", "unknown")
        replica_status = getattr(replication_manager, "replica_status", "unknown")
        replication_lag = getattr(replication_manager, "lag_ms", 0)
    except ImportError:
        master_status = "not configured"
        replica_status = "not configured"
        replication_lag = 0

    # ── Persistence ───────────────────────────────────────────────────────────
    dump_path = Path("dump.json")
    persistence_enabled = dump_path.exists()
    last_save_time = (
        datetime.fromtimestamp(dump_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        if persistence_enabled else "never"
    )
    dump_size_kb = round(dump_path.stat().st_size / 1024, 1) if persistence_enabled else 0

    return {
        # System overview
        "total_keys": total_keys,
        "commands_executed": commands_executed,
        "ttl_keys": ttl_keys,
        "max_cache_size": max_cache_size,
        "current_cache_usage": total_keys,

        # Network
        "connected_clients": connected_clients,
        "active_connections": connected_clients,
        "total_requests": total_requests,

        # Replication
        "master_status": master_status,
        "replica_status": replica_status,
        "replication_lag_ms": replication_lag,

        # Pub/Sub
        "total_channels": total_channels,
        "active_subscribers": active_subscribers,
        "messages_published": messages_published,

        # Cache
        "lru_evictions": lru_evictions,
        "cache_hit_count": cache_hits,
        "cache_miss_count": cache_misses,
        "cache_hit_rate": _hit_rate(cache_hits, cache_misses),

        # Persistence
        "dump_json_status": "ok" if persistence_enabled else "missing",
        "last_save_time": last_save_time,
        "persistence_enabled": persistence_enabled,
        "dump_size_kb": dump_size_kb,

        # Meta
        "uptime_seconds": int(time.time() - getattr(store, "start_time", time.time())),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "mode": "live",
    }


def _collect_demo() -> dict:
    """Simulated metrics for demo/development mode."""
    import random
    s = _demo_state
    uptime = int(time.time() - s["start_time"])
    total_keys = 84
    max_cache = 128
    hits = s["cache_hits"]
    misses = s["cache_misses"]

    dump_path = Path("dump.json")
    persistence_enabled = dump_path.exists()
    last_save = (
        datetime.fromtimestamp(dump_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        if persistence_enabled else "never"
    )
    dump_size_kb = round(dump_path.stat().st_size / 1024, 1) if persistence_enabled else 0

    return {
        # System overview
        "total_keys": total_keys,
        "commands_executed": s["commands_executed"],
        "ttl_keys": 12,
        "max_cache_size": max_cache,
        "current_cache_usage": total_keys,

        # Network
        "connected_clients": random.randint(2, 6),
        "active_connections": random.randint(1, 4),
        "total_requests": s["total_requests"],

        # Replication
        "master_status": "online",
        "replica_status": "syncing",
        "replication_lag_ms": random.randint(2, 18),

        # Pub/Sub
        "total_channels": 3,
        "active_subscribers": random.randint(4, 9),
        "messages_published": random.randint(200, 300),

        # Cache
        "lru_evictions": s["lru_evictions"],
        "cache_hit_count": hits,
        "cache_miss_count": misses,
        "cache_hit_rate": _hit_rate(hits, misses),

        # Persistence
        "dump_json_status": "ok" if persistence_enabled else "missing",
        "last_save_time": last_save,
        "persistence_enabled": persistence_enabled,
        "dump_size_kb": dump_size_kb,

        # Meta
        "uptime_seconds": uptime,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "mode": "demo",
    }


def _hit_rate(hits: int, misses: int) -> float:
    total = hits + misses
    return round((hits / total) * 100, 1) if total > 0 else 0.0


# ─── FastAPI app ─────────────────────────────────────────────────────────────

app = FastAPI(title="MyRedis Dashboard", docs_url=None, redoc_url=None)


@app.get("/api/metrics")
def get_metrics():
    """JSON endpoint — poll this from the dashboard JS every N seconds."""
    return JSONResponse(content=collect_metrics())


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)


# ─── Dashboard HTML ───────────────────────────────────────────────────────────
# Single-file: HTML + CSS + JS all inline.
# JavaScript polls /api/metrics every 3 seconds and updates the DOM.
# Chart.js renders the cache hit/miss doughnut and command rate sparkline.

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
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #22263a;
    --border: rgba(255,255,255,0.08);
    --text: #e8eaf0;
    --muted: #7a7f9a;
    --accent: #6c63ff;
    --green: #22c55e;
    --amber: #f59e0b;
    --red: #ef4444;
    --blue: #3b82f6;
    --teal: #14b8a6;
    --purple: #a855f7;
    --font: "SF Mono", "Fira Code", "Consolas", monospace;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: "Inter", "Segoe UI", system-ui, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    min-height: 100vh;
  }

  /* ── Header ── */
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }
  .header-left { display: flex; align-items: center; gap: 12px; }
  .logo {
    width: 36px; height: 36px; border-radius: 8px;
    background: var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 16px; color: #fff; font-family: var(--font);
  }
  .header h1 { font-size: 16px; font-weight: 600; letter-spacing: -0.3px; }
  .header-meta { display: flex; align-items: center; gap: 16px; color: var(--muted); font-size: 12px; }
  .mode-badge {
    padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.6px;
  }
  .mode-badge.live { background: rgba(34,197,94,0.15); color: var(--green); }
  .mode-badge.demo { background: rgba(245,158,11,0.15); color: var(--amber); }
  .status-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--green); animation: pulse 2s infinite;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* ── Layout ── */
  .container { padding: 20px 24px; max-width: 1400px; margin: 0 auto; }
  .section-title {
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 1px; color: var(--muted); margin: 20px 0 10px;
  }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
  .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
  .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .grid-2-1 { display: grid; grid-template-columns: 2fr 1fr; gap: 12px; }

  /* ── Stat card ── */
  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    position: relative;
    overflow: hidden;
  }
  .stat-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--accent-color, var(--accent));
  }
  .stat-label { font-size: 11px; color: var(--muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .stat-value { font-size: 26px; font-weight: 700; font-family: var(--font); line-height: 1; }
  .stat-sub { font-size: 11px; color: var(--muted); margin-top: 6px; }
  .stat-icon { position: absolute; right: 14px; top: 14px; font-size: 20px; opacity: 0.15; }

  /* ── Progress bar ── */
  .progress-wrap { margin-top: 8px; }
  .progress-track { height: 5px; background: var(--border); border-radius: 4px; overflow: hidden; margin-top: 4px; }
  .progress-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
  .progress-label { font-size: 11px; color: var(--muted); display: flex; justify-content: space-between; }

  /* ── Status card ── */
  .status-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }
  .status-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
  }
  .status-row:last-child { border-bottom: none; }
  .status-key { color: var(--muted); font-size: 12px; }
  .status-val { font-family: var(--font); font-size: 12px; font-weight: 600; }
  .badge {
    padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;
  }
  .badge.green { background: rgba(34,197,94,0.12); color: var(--green); }
  .badge.amber { background: rgba(245,158,11,0.12); color: var(--amber); }
  .badge.red   { background: rgba(239,68,68,0.12);  color: var(--red); }
  .badge.blue  { background: rgba(59,130,246,0.12); color: var(--blue); }
  .badge.muted { background: var(--border); color: var(--muted); }

  /* ── Chart card ── */
  .chart-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
  }
  .chart-card h3 { font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
  .chart-wrap { position: relative; height: 180px; }

  /* ── Replication row ── */
  .repl-row { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
  .repl-node {
    flex: 1; background: var(--surface2); border: 1px solid var(--border);
    border-radius: 8px; padding: 10px 12px; text-align: center;
  }
  .repl-node .label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; }
  .repl-node .val { font-family: var(--font); font-size: 13px; font-weight: 600; margin-top: 4px; }
  .repl-arrow { color: var(--muted); font-size: 18px; flex-shrink: 0; }
  .lag-value { text-align: center; margin-top: 8px; font-size: 11px; color: var(--muted); }

  /* ── Uptime ── */
  #uptime-display { font-size: 11px; color: var(--muted); font-family: var(--font); }

  /* ── Responsive ── */
  @media (max-width: 900px) {
    .grid-4, .grid-3 { grid-template-columns: repeat(2, 1fr); }
    .grid-2-1 { grid-template-columns: 1fr; }
  }
  @media (max-width: 560px) {
    .grid-4, .grid-3, .grid-2 { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

<!-- Header -->
<header class="header">
  <div class="header-left">
    <div class="logo">R</div>
    <div>
      <h1>MyRedis Dashboard</h1>
      <div id="uptime-display">loading...</div>
    </div>
  </div>
  <div class="header-meta">
    <span>Last update: <span id="last-update">—</span></span>
    <span id="mode-badge" class="mode-badge demo">demo</span>
    <div class="status-dot"></div>
  </div>
</header>

<div class="container">

  <!-- ── System Overview ────────────────────────────────── -->
  <div class="section-title">System overview</div>
  <div class="grid-4">
    <div class="stat-card" style="--accent-color: var(--accent)">
      <div class="stat-icon">🗄</div>
      <div class="stat-label">Total keys</div>
      <div class="stat-value" id="total-keys">—</div>
      <div class="stat-sub">in-memory store</div>
    </div>
    <div class="stat-card" style="--accent-color: var(--blue)">
      <div class="stat-icon">⚡</div>
      <div class="stat-label">Commands executed</div>
      <div class="stat-value" id="commands-executed">—</div>
      <div class="stat-sub">since server start</div>
    </div>
    <div class="stat-card" style="--accent-color: var(--amber)">
      <div class="stat-icon">⏱</div>
      <div class="stat-label">TTL keys</div>
      <div class="stat-value" id="ttl-keys">—</div>
      <div class="stat-sub">auto-expiring</div>
    </div>
    <div class="stat-card" style="--accent-color: var(--teal)">
      <div class="stat-icon">📦</div>
      <div class="stat-label">Cache usage</div>
      <div class="stat-value" id="cache-usage">—</div>
      <div class="progress-wrap">
        <div class="progress-label">
          <span>0</span><span id="cache-max">—</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" id="cache-progress" style="background:var(--teal);width:0%"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── Network + Replication ───────────────────────────── -->
  <div class="section-title">Network &amp; replication</div>
  <div class="grid-3">

    <!-- Network -->
    <div class="status-card">
      <div class="section-title" style="margin:0 0 8px">Network</div>
      <div class="status-row">
        <span class="status-key">Connected clients</span>
        <span class="status-val" id="connected-clients">—</span>
      </div>
      <div class="status-row">
        <span class="status-key">Active connections</span>
        <span class="status-val" id="active-connections">—</span>
      </div>
      <div class="status-row">
        <span class="status-key">Total requests</span>
        <span class="status-val" id="total-requests">—</span>
      </div>
    </div>

    <!-- Replication -->
    <div class="status-card" style="grid-column: span 2">
      <div class="section-title" style="margin:0 0 10px">Replication</div>
      <div class="repl-row">
        <div class="repl-node">
          <div class="label">Master</div>
          <div class="val"><span id="master-badge" class="badge muted">—</span></div>
        </div>
        <div class="repl-arrow">→</div>
        <div class="repl-node">
          <div class="label">Replica</div>
          <div class="val"><span id="replica-badge" class="badge muted">—</span></div>
        </div>
      </div>
      <div class="lag-value">Replication lag: <span id="repl-lag" style="font-family:var(--font)">—</span></div>
    </div>
  </div>

  <!-- ── Pub/Sub + Cache ─────────────────────────────────── -->
  <div class="section-title">Pub/Sub &amp; cache</div>
  <div class="grid-2-1">

    <!-- Cache chart + hit/miss cards -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div class="stat-card" style="--accent-color: var(--green)">
        <div class="stat-icon">✓</div>
        <div class="stat-label">Cache hits</div>
        <div class="stat-value" id="cache-hits">—</div>
        <div class="stat-sub">hit rate: <span id="hit-rate">—</span>%</div>
      </div>
      <div class="stat-card" style="--accent-color: var(--red)">
        <div class="stat-icon">✗</div>
        <div class="stat-label">Cache misses</div>
        <div class="stat-value" id="cache-misses">—</div>
        <div class="stat-sub">LRU evictions: <span id="lru-evictions">—</span></div>
      </div>
      <div class="stat-card" style="--accent-color: var(--purple); grid-column: span 2">
        <div class="stat-label">Pub/Sub</div>
        <div style="display:flex;gap:24px;align-items:flex-end;flex-wrap:wrap">
          <div>
            <div class="stat-value" id="total-channels">—</div>
            <div class="stat-sub">channels</div>
          </div>
          <div>
            <div class="stat-value" id="active-subscribers">—</div>
            <div class="stat-sub">subscribers</div>
          </div>
          <div>
            <div class="stat-value" id="messages-published">—</div>
            <div class="stat-sub">messages published</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Doughnut chart -->
    <div class="chart-card">
      <h3>Cache hit vs miss</h3>
      <div class="chart-wrap">
        <canvas id="donut-chart"></canvas>
      </div>
    </div>
  </div>

  <!-- ── Persistence ────────────────────────────────────── -->
  <div class="section-title">Persistence</div>
  <div class="grid-3">
    <div class="status-card" style="grid-column: span 2">
      <div class="section-title" style="margin:0 0 8px">dump.json</div>
      <div class="status-row">
        <span class="status-key">Status</span>
        <span id="dump-status" class="badge muted">—</span>
      </div>
      <div class="status-row">
        <span class="status-key">Last save time</span>
        <span class="status-val" id="last-save-time" style="font-family:var(--font);font-size:11px">—</span>
      </div>
      <div class="status-row">
        <span class="status-key">Persistence enabled</span>
        <span id="persistence-enabled" class="badge muted">—</span>
      </div>
      <div class="status-row">
        <span class="status-key">File size</span>
        <span class="status-val" id="dump-size">—</span>
      </div>
    </div>

    <!-- Uptime card -->
    <div class="stat-card" style="--accent-color: var(--blue)">
      <div class="stat-label">Server uptime</div>
      <div class="stat-value" id="uptime-stat">—</div>
      <div class="stat-sub" id="uptime-unit">seconds</div>
    </div>
  </div>

</div><!-- /container -->

<script>
// ── Chart setup ────────────────────────────────────────────────────────────
const donutCtx = document.getElementById('donut-chart').getContext('2d');
const donutChart = new Chart(donutCtx, {
  type: 'doughnut',
  data: {
    labels: ['Hits', 'Misses'],
    datasets: [{
      data: [0, 0],
      backgroundColor: ['#22c55e', '#ef4444'],
      borderWidth: 0,
      hoverOffset: 4
    }]
  },
  options: {
    cutout: '72%',
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: '#7a7f9a', font: { size: 11 }, padding: 12 }
      }
    },
    animation: { duration: 500 }
  }
});

// ── DOM helpers ────────────────────────────────────────────────────────────
function set(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function fmtUptime(secs) {
  if (secs < 60)   return [secs, 'seconds'];
  if (secs < 3600) return [Math.floor(secs / 60), 'minutes'];
  if (secs < 86400) return [Math.floor(secs / 3600), 'hours'];
  return [Math.floor(secs / 86400), 'days'];
}

function statusBadge(id, val, map) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = val;
  el.className = 'badge ' + (map[val] || 'muted');
}

// ── Fetch and update ───────────────────────────────────────────────────────
async function update() {
  let m;
  try {
    const res = await fetch('/api/metrics');
    m = await res.json();
  } catch (e) {
    console.error('metrics fetch failed', e);
    return;
  }

  // Mode badge
  const mb = document.getElementById('mode-badge');
  mb.textContent = m.mode;
  mb.className = 'mode-badge ' + m.mode;

  // System overview
  set('total-keys', m.total_keys.toLocaleString());
  set('commands-executed', m.commands_executed.toLocaleString());
  set('ttl-keys', m.ttl_keys);
  set('cache-usage', m.current_cache_usage);
  set('cache-max', m.max_cache_size);
  const cachePercent = m.max_cache_size > 0
    ? Math.round((m.current_cache_usage / m.max_cache_size) * 100)
    : 0;
  document.getElementById('cache-progress').style.width = cachePercent + '%';

  // Network
  set('connected-clients', m.connected_clients);
  set('active-connections', m.active_connections);
  set('total-requests', m.total_requests.toLocaleString());

  // Replication
  statusBadge('master-badge', m.master_status, {
    online: 'green', offline: 'red', 'not configured': 'muted'
  });
  statusBadge('replica-badge', m.replica_status, {
    syncing: 'blue', online: 'green', offline: 'red', 'not configured': 'muted'
  });
  set('repl-lag', m.replication_lag_ms + ' ms');

  // Pub/Sub
  set('total-channels', m.total_channels);
  set('active-subscribers', m.active_subscribers);
  set('messages-published', m.messages_published.toLocaleString());

  // Cache
  set('cache-hits', m.cache_hit_count.toLocaleString());
  set('cache-misses', m.cache_miss_count.toLocaleString());
  set('hit-rate', m.cache_hit_rate);
  set('lru-evictions', m.lru_evictions);

  // Update doughnut
  donutChart.data.datasets[0].data = [m.cache_hit_count, m.cache_miss_count];
  donutChart.update();

  // Persistence
  statusBadge('dump-status', m.dump_json_status, { ok: 'green', missing: 'red' });
  set('last-save-time', m.last_save_time);
  statusBadge('persistence-enabled', m.persistence_enabled ? 'yes' : 'no', { yes: 'green', no: 'amber' });
  set('dump-size', m.dump_size_kb > 0 ? m.dump_size_kb + ' KB' : '—');

  // Uptime
  const [val, unit] = fmtUptime(m.uptime_seconds);
  set('uptime-stat', val);
  set('uptime-unit', unit);
  set('uptime-display', 'uptime ' + m.uptime_seconds + 's');

  // Timestamp
  set('last-update', m.timestamp);
}

update();
setInterval(update, 3000);  // refresh every 3 seconds
</script>
</body>
</html>
"""

# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    mode = "LIVE" if LIVE_MODE else "DEMO (import your MyRedis modules to enable live mode)"
    print(f"""
╔══════════════════════════════════════════╗
║       MyRedis Monitoring Dashboard       ║
╠══════════════════════════════════════════╣
║  URL   →  http://localhost:8000          ║
║  API   →  http://localhost:8000/api/metrics
║  Mode  →  {mode:<32}║
╚══════════════════════════════════════════╝
""")

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")