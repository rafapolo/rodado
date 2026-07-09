#!/usr/bin/env python3
"""
Shared monthly scan-quota tracker for BigQuery Sandbox free tier (~1TB/month, no billing).

State persists in ~/.bq_sandbox_quota.json as {"month": "YYYY-MM", "bytes_used": N}.
Resets automatically when the calendar month rolls over. Any script doing bq query
against the public basedosdados project should call reserve() with the dry-run byte
estimate *before* running the real query, and stop for the month if it returns False.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path.home() / ".bq_sandbox_quota.json"
# Stay under the real ~1TB Sandbox cap with headroom for estimate error and other usage.
MONTHLY_BUDGET_BYTES = 900 * 1024**3  # 900GB


def _current_month():
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _load():
    if not STATE_FILE.exists():
        return {"month": _current_month(), "bytes_used": 0}
    try:
        data = json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {"month": _current_month(), "bytes_used": 0}
    if data.get("month") != _current_month():
        return {"month": _current_month(), "bytes_used": 0}
    return data


def _save(data):
    STATE_FILE.write_text(json.dumps(data))


def remaining_bytes():
    data = _load()
    return max(0, MONTHLY_BUDGET_BYTES - data["bytes_used"])


def reserve(bytes_needed):
    """Reserve bytes against this month's budget. Returns False if it would exceed
    the budget (caller should skip/defer, not run the query)."""
    data = _load()
    if data["bytes_used"] + bytes_needed > MONTHLY_BUDGET_BYTES:
        return False
    data["bytes_used"] += bytes_needed
    _save(data)
    return True


def status():
    data = _load()
    used_gb = data["bytes_used"] / 1024**3
    budget_gb = MONTHLY_BUDGET_BYTES / 1024**3
    return f"{data['month']}: {used_gb:.2f}GB / {budget_gb:.0f}GB used, {budget_gb - used_gb:.2f}GB remaining"


if __name__ == "__main__":
    print(status())
