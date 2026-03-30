"""
CUE Meta Pull — Fetch campaign performance data from Meta Marketing API.

Read-only operations only (safe per ads-api-safety.md).
All credentials loaded from C:\\credentials\\.env.
"""
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

from pathlib import Path

import requests
from dotenv import load_dotenv

_local_env = Path(r"C:\credentials\.env")
if _local_env.exists():
    load_dotenv(_local_env)

# --- Config ---------------------------------------------------------------
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN")
META_AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID")  # format: act_XXXXX
API_VERSION = "v23.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

# Rate limit tracking (ads-api-safety.md: max 4500 points per 300s)
_call_log = []
MAX_POINTS_PER_WINDOW = 4500
WINDOW_SECONDS = 300


def _check_rate_limit(points=1):
    """Enforce rate limiting per ads-api-safety.md."""
    now = time.time()
    _call_log.append((now, points))
    # Prune old entries
    cutoff = now - WINDOW_SECONDS
    while _call_log and _call_log[0][0] < cutoff:
        _call_log.pop(0)
    total = sum(p for _, p in _call_log)
    if total > MAX_POINTS_PER_WINDOW:
        raise RuntimeError(f"Rate limit exceeded: {total}/{MAX_POINTS_PER_WINDOW} points in {WINDOW_SECONDS}s window. Pausing.")
    return total


def _check_credentials():
    """Validate required credentials are present."""
    missing = []
    if not META_ACCESS_TOKEN:
        missing.append("META_ACCESS_TOKEN")
    if not META_AD_ACCOUNT_ID:
        missing.append("META_AD_ACCOUNT_ID")
    if missing:
        raise EnvironmentError(
            f"Missing required credentials in C:\\credentials\\.env: {', '.join(missing)}. "
            f"Add them and restart."
        )


def _api_get(endpoint, params=None):
    """Make a GET request to Meta Graph API with rate limiting and error handling."""
    _check_credentials()
    _check_rate_limit(points=1)

    if params is None:
        params = {}
    params["access_token"] = META_ACCESS_TOKEN

    url = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, params=params, timeout=30)

    if resp.status_code == 429:
        raise RuntimeError("HTTP 429: Rate limited by Meta. Waiting 60s before retry per ads-api-safety.md.")

    if resp.status_code != 200:
        error_data = resp.json().get("error", {})
        code = error_data.get("code", "unknown")
        msg = error_data.get("message", resp.text[:200])
        # Circuit breaker codes per ads-api-safety.md
        if code in [17, 80001, 80002, 80003, 80004]:
            raise RuntimeError(f"Meta API rate/throttle error (code {code}): {msg}. Exponential backoff required.")
        raise RuntimeError(f"Meta API error {resp.status_code} (code {code}): {msg}")

    return resp.json()


# --- Public Functions -----------------------------------------------------

def list_campaigns(status_filter=None):
    """List campaigns in the ad account. Returns list of {id, name, status, objective}."""
    _check_credentials()
    params = {
        "fields": "id,name,status,objective,created_time,updated_time",
        "limit": 50,
    }
    if status_filter:
        params["filtering"] = json.dumps([{"field": "status", "operator": "IN", "value": [status_filter]}])

    data = _api_get(f"{META_AD_ACCOUNT_ID}/campaigns", params)
    return data.get("data", [])


def list_ads(campaign_id=None):
    """List ads, optionally filtered by campaign. Returns list of ad objects."""
    _check_credentials()
    params = {
        "fields": "id,name,status,campaign_id,adset_id,creative{id,name,thumbnail_url}",
        "limit": 50,
    }
    endpoint = f"{campaign_id}/ads" if campaign_id else f"{META_AD_ACCOUNT_ID}/ads"
    data = _api_get(endpoint, params)
    return data.get("data", [])


def get_ad_insights(ad_id, date_preset="last_7d", time_increment=1):
    """Fetch performance insights for a specific ad.

    Returns list of daily snapshots with all available video + conversion metrics.
    """
    _check_credentials()
    params = {
        "fields": ",".join([
            "impressions", "reach", "frequency",
            "clicks", "ctr", "cpc", "cpm", "spend",
            "video_p25_watched_actions", "video_p50_watched_actions",
            "video_p75_watched_actions", "video_p100_watched_actions",
            "video_play_actions", "video_thruplay_watched_actions",
            "actions", "cost_per_action_type",
            "date_start", "date_stop",
        ]),
        "date_preset": date_preset,
        "time_increment": time_increment,  # daily breakdowns
        "limit": 30,
    }
    data = _api_get(f"{ad_id}/insights", params)
    return data.get("data", [])


def get_campaign_insights(campaign_id, date_preset="last_7d"):
    """Fetch aggregate performance for an entire campaign."""
    _check_credentials()
    params = {
        "fields": ",".join([
            "impressions", "reach", "frequency",
            "clicks", "ctr", "cpc", "cpm", "spend",
            "video_thruplay_watched_actions", "video_p100_watched_actions",
            "actions", "cost_per_action_type",
            "date_start", "date_stop",
        ]),
        "date_preset": date_preset,
    }
    data = _api_get(f"{campaign_id}/insights", params)
    return data.get("data", [])


def insights_to_cue_metrics(insight_row):
    """Convert a Meta insights API row into CUE performance_data metrics format.

    Maps Meta field names to CUE schema field names.
    """
    metrics = {
        "impressions": int(insight_row.get("impressions", 0)),
        "reach": int(insight_row.get("reach", 0)) if insight_row.get("reach") else None,
        "frequency": float(insight_row.get("frequency", 0)) if insight_row.get("frequency") else None,
        "ctr": float(insight_row.get("ctr", 0)) / 100.0 if insight_row.get("ctr") else None,  # Meta returns %, CUE uses decimal
        "cpc": float(insight_row.get("cpc", 0)) if insight_row.get("cpc") else None,
        "cpm": float(insight_row.get("cpm", 0)) if insight_row.get("cpm") else None,
        "spend": float(insight_row.get("spend", 0)) if insight_row.get("spend") else None,
    }

    # Video metrics
    video_plays = insight_row.get("video_play_actions")
    if video_plays and isinstance(video_plays, list):
        metrics["video_views"] = int(video_plays[0].get("value", 0))
    else:
        metrics["video_views"] = None

    # Completion rate from thruplay / total plays
    thruplay = insight_row.get("video_thruplay_watched_actions")
    if thruplay and isinstance(thruplay, list) and metrics.get("video_views"):
        thru_count = int(thruplay[0].get("value", 0))
        metrics["video_completion_rate"] = thru_count / metrics["video_views"] if metrics["video_views"] > 0 else None
    else:
        metrics["video_completion_rate"] = None

    # Hook rate approximation: p25 watched / impressions
    p25 = insight_row.get("video_p25_watched_actions")
    if p25 and isinstance(p25, list):
        p25_count = int(p25[0].get("value", 0))
        metrics["hook_rate_3s"] = p25_count / metrics["impressions"] if metrics["impressions"] > 0 else None
    else:
        metrics["hook_rate_3s"] = None

    # Hold rate approximation: p50 watched / impressions
    p50 = insight_row.get("video_p50_watched_actions")
    if p50 and isinstance(p50, list):
        p50_count = int(p50[0].get("value", 0))
        metrics["hold_rate_15s"] = p50_count / metrics["impressions"] if metrics["impressions"] > 0 else None
    else:
        metrics["hold_rate_15s"] = None

    # Conversions (app installs or other actions)
    actions = insight_row.get("actions")
    conversions = None
    conversion_rate = None
    cost_per_conversion = None
    if actions and isinstance(actions, list):
        for action in actions:
            atype = action.get("action_type", "")
            if atype in ["mobile_app_install", "app_install", "offsite_conversion", "purchase", "lead"]:
                conversions = int(action.get("value", 0))
                break
        if conversions and metrics["impressions"] > 0:
            conversion_rate = conversions / metrics["impressions"]
        cost_actions = insight_row.get("cost_per_action_type")
        if cost_actions and isinstance(cost_actions, list):
            for ca in cost_actions:
                if ca.get("action_type") in ["mobile_app_install", "app_install", "offsite_conversion", "purchase", "lead"]:
                    cost_per_conversion = float(ca.get("value", 0))
                    break
    metrics["conversions"] = conversions
    metrics["conversion_rate"] = conversion_rate
    metrics["cost_per_conversion"] = cost_per_conversion

    return metrics


def pull_and_save(ad_id, meta_ad_id, context_id="none", date_preset="last_7d"):
    """Pull insights for a Meta ad and save as CUE performance snapshot.

    Args:
        ad_id: CUE ad ID (e.g., "wiom_001")
        meta_ad_id: Meta ad ID (numeric string from Meta Ads Manager)
        context_id: CUE context ID to link to
        date_preset: Meta date preset (last_7d, last_14d, last_30d, etc.)

    Returns:
        list of (ok, message) tuples for each day saved
    """
    from harness import save_performance_data, next_perf_id

    insights = get_ad_insights(meta_ad_id, date_preset=date_preset)
    results = []

    for row in insights:
        metrics = insights_to_cue_metrics(row)

        # Calculate days live from date_start
        start_date = datetime.strptime(row["date_start"], "%Y-%m-%d")
        days_live = (datetime.now() - start_date).days

        data = {
            "perf_id": next_perf_id(ad_id),
            "ad_id": ad_id,
            "context_id": context_id,
            "snapshot_date": row["date_start"],
            "days_live": days_live,
            "metrics": metrics,
            "platform_data": {
                "source": "meta_marketing_api",
                "meta_ad_id": meta_ad_id,
                "date_start": row.get("date_start"),
                "date_stop": row.get("date_stop"),
            },
        }

        ok, msg = save_performance_data(data)
        results.append((ok, msg))

    return results


# --- CLI ------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python meta_pull.py campaigns              # List campaigns")
        print("  python meta_pull.py ads [campaign_id]       # List ads")
        print("  python meta_pull.py insights <meta_ad_id>   # Get insights")
        print("  python meta_pull.py pull <cue_ad_id> <meta_ad_id> [date_preset]  # Pull & save")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "campaigns":
        for c in list_campaigns():
            print(f"  {c['id']}  {c['name']}  [{c['status']}]  {c.get('objective','')}")

    elif cmd == "ads":
        cid = sys.argv[2] if len(sys.argv) > 2 else None
        for a in list_ads(cid):
            print(f"  {a['id']}  {a['name']}  [{a['status']}]")

    elif cmd == "insights":
        meta_ad_id = sys.argv[2]
        preset = sys.argv[3] if len(sys.argv) > 3 else "last_7d"
        rows = get_ad_insights(meta_ad_id, date_preset=preset)
        for r in rows:
            m = insights_to_cue_metrics(r)
            print(f"  {r['date_start']}: imp={m['impressions']:,} ctr={m['ctr'] or 0:.4f} vcr={m['video_completion_rate'] or 0:.3f} conv={m['conversions'] or '-'}")

    elif cmd == "pull":
        cue_id = sys.argv[2]
        meta_id = sys.argv[3]
        preset = sys.argv[4] if len(sys.argv) > 4 else "last_7d"
        results = pull_and_save(cue_id, meta_id, date_preset=preset)
        for ok, msg in results:
            print(f"  {'OK' if ok else 'FAIL'}: {msg}")
