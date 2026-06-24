"""
metrics.py
──────────
Central metrics store for MyRedis.

Every module (datastore, server, pubsub, replica) imports this and
calls update_metrics() to write their current state.

dashboard.py reads metrics.json directly — it never imports server.py.

Usage in any module:
    from metrics import metrics_manager
    metrics_manager.update({ "total_keys": 42 })
    metrics_manager.save()
"""

import json
import os
import time
from datetime import datetime
from threading import Lock

METRICS_FILE = "metrics.json"

# ── Default schema ────────────────────────────────────────────────────────────
# Every key the dashboard reads must exist here with a safe default.
# dashboard.py will never crash on a missing key.

_DEFAULTS = {
    # Store
    "total_keys":        0,
    "commands_executed": 0,
    "ttl_keys":          0,
    "cache_usage":       0,
    "max_cache_size":    128,

    # Network
    "connected_clients": 0,
    "total_requests":    0,

    # LRU / Cache
    "cache_hit_count":   0,
    "cache_miss_count":  0,
    "cache_hit_rate":    0.0,
    "lru_evictions":     0,

    # Pub/Sub
    "total_channels":    0,
    "active_subscribers":0,
    "messages_published":0,

    # Replication
    "master_status":     "unknown",
    "replica_status":    "unknown",
    "replication_lag_ms":0,

    # Persistence
    "dump_json_status":  "unknown",
    "last_save_time":    "never",
    "dump_size_kb":      0.0,

    # System
    "uptime_seconds":    0,
    "timestamp":         "",
    "mode":              "live",
}


class MetricsManager:
    def __init__(self):
        self._data = dict(_DEFAULTS)
        self._lock = Lock()
        self._start_time = time.time()
        self._load_existing()

    # ── Load any previously saved metrics on startup ──────────────────────────

    def _load_existing(self):
        if os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, "r") as f:
                    saved = json.load(f)
                # Only restore counters that accumulate across restarts
                for key in ("commands_executed", "total_requests",
                            "cache_hit_count", "cache_miss_count",
                            "lru_evictions", "messages_published"):
                    if key in saved:
                        self._data[key] = saved[key]
            except Exception:
                pass  # corrupt file — start fresh

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, partial: dict):
        """
        Merge a partial metrics dict into the current state.
        Call this from datastore, pubsub, replica, server — then call save().

        Example:
            metrics_manager.update({"total_keys": len(store), "ttl_keys": 5})
        """
        with self._lock:
            self._data.update(partial)

    def save(self):
        """
        Write current metrics to metrics.json atomically.
        Safe to call from multiple threads.
        """
        with self._lock:
            # Always refresh system fields before writing
            uptime = int(time.time() - self._start_time)
            self._data["uptime_seconds"] = uptime
            self._data["timestamp"] = datetime.now().strftime("%H:%M:%S")

            # Recalculate hit rate
            hits   = self._data["cache_hit_count"]
            misses = self._data["cache_miss_count"]
            total  = hits + misses
            self._data["cache_hit_rate"] = (
                round((hits / total) * 100, 1) if total > 0 else 0.0
            )

            snapshot = dict(self._data)

        # Write to a temp file then rename — prevents dashboard reading a
        # half-written file on Windows or Linux
        tmp = METRICS_FILE + ".tmp"
        try:
            with open(tmp, "w") as f:
                json.dump(snapshot, f, indent=2)
            os.replace(tmp, METRICS_FILE)
        except Exception:
            pass

    def get(self, key, default=None):
        with self._lock:
            return self._data.get(key, default)

    def snapshot(self) -> dict:
        """Return a full copy of current metrics."""
        with self._lock:
            return dict(self._data)


# ── Module-level singleton ────────────────────────────────────────────────────
# Every file does:  from metrics import metrics_manager
# They all share the same object within one Python process (server.py).

metrics_manager = MetricsManager()


# ── Standalone helpers used by individual modules ─────────────────────────────

def load_metrics() -> dict:
    """
    Read metrics.json from disk.
    Used by dashboard.py — it runs in a separate process.
    Returns _DEFAULTS if the file is missing or corrupt.
    """
    if not os.path.exists(METRICS_FILE):
        return dict(_DEFAULTS)
    try:
        with open(METRICS_FILE, "r") as f:
            data = json.load(f)
        # Fill in any keys missing from an older metrics.json
        for k, v in _DEFAULTS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(_DEFAULTS)


def save_metrics(data: dict):
    """Write a metrics dict to disk. Used for one-off saves."""
    tmp = METRICS_FILE + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, METRICS_FILE)
    except Exception:
        pass