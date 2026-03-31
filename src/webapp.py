"""
CUE Web App — Browser-based UI for the CUE pipeline.
Run: python src/webapp.py
Opens at: http://localhost:5100
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Load local credentials file if present (dev only)
from dotenv import load_dotenv
_local_env = Path(r"C:\credentials\.env")
if _local_env.exists():
    load_dotenv(_local_env)

sys.path.insert(0, str(Path(__file__).parent))
from harness import (
    ROOT, WIOM_DIR, CONTEXTS_DIR, SCORECARDS_DIR, SUGGESTIONS_DIR,
    PERFORMANCE_DIR, OPTIMIZATIONS_DIR, HISTORY_DIR, PLAYBOOK_JSON,
    MAPPINGS_DIR, UPLOADS_DIR,
    get_state, get_progress_bar, get_weight_profile, get_priority_patterns,
    adjust_pattern_relevance,
    save_campaign_context, load_campaign_context, next_context_id,
    save_performance_data, next_perf_id, load_performance_history,
    detect_fatigue, load_history, export_dashboard_data, load_index,
    save_campaign_mapping, load_campaign_mapping, load_all_mappings,
)

from flask import Flask, request, jsonify, redirect, session
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cue-dev-secret-change-in-prod")

# ---------------------------------------------------------------------------
# Password gate — set CUE_PASSWORD env var to enable
# ---------------------------------------------------------------------------
CUE_PASSWORD = os.environ.get("CUE_PASSWORD")

def _require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not CUE_PASSWORD:
            return f(*args, **kwargs)  # No password set — open access (local dev)
        if session.get("authed"):
            return f(*args, **kwargs)
        if request.method == "POST" and request.path == "/login":
            return f(*args, **kwargs)
        return redirect("/login")
    return decorated

# Apply auth to all routes
app.before_request_funcs.setdefault(None, [])

@app.before_request
def check_auth():
    if not CUE_PASSWORD:
        return
    if request.path in ("/login", "/static"):
        return
    if request.path.startswith("/static/"):
        return
    if not session.get("authed"):
        if request.path == "/login" and request.method == "POST":
            return
        return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if request.form.get("password") == CUE_PASSWORD:
            session["authed"] = True
            return redirect("/")
        error = "Wrong password."
    html = f'''<!DOCTYPE html><html><head><title>CUE Login</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',sans-serif;background:#0f1117;color:#e4e7f0;display:flex;align-items:center;justify-content:center;min-height:100vh}}
    input{{width:100%;padding:10px 14px;background:#242836;border:1px solid #2d3148;border-radius:6px;color:#e4e7f0;font-size:14px;margin-bottom:12px}}
    button{{width:100%;padding:10px;border-radius:6px;border:none;background:#6366f1;color:white;font-size:14px;font-weight:500;cursor:pointer}}</style></head>
    <body><div style="background:#1a1d27;border:1px solid #2d3148;border-radius:12px;padding:40px;width:320px;text-align:center">
    <h1 style="color:#818cf8;font-size:24px;margin-bottom:4px">CUE</h1>
    <p style="color:#8b91a8;font-size:12px;margin-bottom:24px;text-transform:uppercase;letter-spacing:1px">Creative Understanding Experiment</p>
    <form method="POST"><input type="password" name="password" placeholder="Password" autofocus>
    {"<p style='color:#ef4444;font-size:13px;margin-bottom:12px'>" + error + "</p>" if error else ""}
    <button type="submit">Enter</button></form></div></body></html>'''
    return html


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _esc(s):
    """Minimal HTML escaping."""
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _chip(text, color="blue"):
    colors = {
        "green": "background:#22c55e22;color:#22c55e",
        "amber": "background:#f59e0b22;color:#f59e0b",
        "red":   "background:#ef444422;color:#ef4444",
        "blue":  "background:#3b82f622;color:#3b82f6",
        "gray":  "background:#6b728022;color:#9ca3af",
    }
    st = colors.get(color, colors["blue"])
    return f'<span style="display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:500;margin-right:4px;{st}">{_esc(text)}</span>'


def _format_label(label):
    """Capitalize acronyms like CTR, CTA, CPC, CPM, VCR, USP properly."""
    acronyms = {"ctr": "CTR", "cta": "CTA", "cpc": "CPC", "cpm": "CPM", "vcr": "VCR",
                "usp": "USP", "kpi": "KPI", "api": "API"}
    words = label.split()
    return " ".join(acronyms.get(w.lower(), w) for w in words)


def _dim_label(raw_key):
    """Convert a dimension key like 'ctr_drivers' to 'CTR Drivers'."""
    return _format_label(raw_key.replace("_", " ").title())


def _bar_row(label, score, max_score=5):
    pct = (score / max_score) * 100 if max_score else 0
    c = "#22c55e" if score >= 4 else "#f59e0b" if score >= 3 else "#ef4444"
    return f'''<div style="display:flex;align-items:center;margin-bottom:10px">
      <span style="width:150px;font-size:12px;color:#8b91a8">{_esc(_format_label(label))}</span>
      <div style="flex:1;height:8px;background:#242836;border-radius:4px;margin:0 10px">
        <div style="height:8px;border-radius:4px;width:{pct}%;background:{c}"></div>
      </div>
      <span style="width:30px;font-size:12px;font-weight:600;text-align:right">{score}/{max_score}</span>
    </div>'''


def _gauge(score):
    color = "#ef4444" if score < 40 else "#f59e0b" if score < 65 else "#22c55e"
    label_color = "#ef4444" if score < 40 else "#f59e0b" if score < 65 else "#22c55e"
    return f'''<div style="width:100px;height:100px;border-radius:50%;margin:0 auto 8px;
      background:conic-gradient({color} {score*3.6}deg,#242836 0);
      display:flex;align-items:center;justify-content:center;position:relative">
      <div style="width:76px;height:76px;border-radius:50%;background:#1a1d27;position:absolute"></div>
      <span style="position:relative;z-index:1;font-size:20px;font-weight:700;color:{label_color}">{score}</span>
    </div>'''


def _card(content, extra_style=""):
    return f'<div style="background:#1a1d27;border:1px solid #2d3148;border-radius:10px;padding:24px;margin-bottom:20px;{extra_style}">{content}</div>'


def _stat(num, label):
    return _card(f'<div style="text-align:center;padding:16px"><div style="font-size:28px;font-weight:700;color:#818cf8">{num}</div><div style="font-size:11px;color:#8b91a8;text-transform:uppercase;letter-spacing:1px;margin-top:4px">{label}</div></div>', "padding:8px;margin-bottom:12px")


def _next_step(title, body, href, cta_text):
    """A next-step CTA banner guiding users through the flow."""
    return f'''<div style="background:#6366f118;border:1px solid #6366f140;border-radius:10px;padding:16px 20px;margin-bottom:24px;display:flex;justify-content:space-between;align-items:center;gap:16px">
      <div>
        <div style="font-size:13px;font-weight:600;color:#818cf8;margin-bottom:2px">Next step: {_esc(title)}</div>
        <div style="font-size:12px;color:#8b91a8">{_esc(body)}</div>
      </div>
      {_btn(cta_text, href, True, True)}
    </div>'''


def _btn(text, href="#", primary=True, small=False):
    bg = "#6366f1" if primary else "#242836"
    bd = "" if primary else "border:1px solid #2d3148;"
    sz = "padding:6px 14px;font-size:12px" if small else "padding:10px 20px;font-size:14px"
    return f'<a href="{href}" style="display:inline-block;{sz};border-radius:6px;font-weight:500;text-decoration:none;color:#e4e7f0;background:{bg};{bd}">{text}</a>'


def _ad_name(ad_id):
    """Get human-readable ad name from metadata."""
    path = WIOM_DIR / f"{ad_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        name = meta.get("campaign", "") or meta.get("description", "")[:60]
        adv = meta.get("advertiser", "")
        return f"{adv} — {name}" if adv and name else ad_id
    return ad_id


def _page(title, content, active="home"):
    state = get_state()
    nav_items = [
        ("home", "/", "Dashboard"),
        ("library", "/library", f"Ad Library ({state['library']['total_ads']})"),
        ("add_url", "/library/add-url", "+ Add Ad from URL"),
        ("playbook", "/playbook", "Playbook"),
        ("wiom", "/wiom", f"Ads & Scorecards ({state['wiom_ads']['total']})"),
        ("upload", "/wiom/upload", "+ Upload Ad"),
        ("context", "/context/new", "+ New Context"),
        ("mapping", "/campaign/map", "Campaign Mapping"),
        ("performance", "/performance", f"Performance ({state['performance']['total']})"),
        ("compare", "/compare", "Compare Versions"),
        ("history", "/history", "History"),
    ]
    nav_html = ""
    for key, href, label in nav_items:
        act = "background:#6366f1;color:white;" if key == active else ""
        nav_html += f'<a href="{href}" style="display:block;padding:8px 12px;border-radius:6px;font-size:13px;color:#e4e7f0;margin-bottom:2px;text-decoration:none;{act}">{label}</a>'

    return f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>CUE - {_esc(title)}</title>
<style>
  * {{ margin:0;padding:0;box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif;background:#0f1117;color:#e4e7f0;min-height:100vh; }}
  a {{ color:#818cf8;text-decoration:none; }}
  a:hover {{ text-decoration:underline; }}
  table {{ width:100%;border-collapse:collapse;font-size:13px; }}
  th {{ text-align:left;color:#8b91a8;font-weight:500;padding:8px 12px;border-bottom:1px solid #2d3148;font-size:11px;text-transform:uppercase;letter-spacing:1px; }}
  td {{ padding:10px 12px;border-bottom:1px solid #2d3148; }}
  h2 {{ font-size:22px;font-weight:600;margin-bottom:16px; }}
  h3 {{ font-size:16px;font-weight:600;margin-bottom:12px; }}
  input,select,textarea {{ width:100%;padding:10px 14px;background:#242836;border:1px solid #2d3148;border-radius:6px;color:#e4e7f0;font-size:14px;font-family:inherit; }}
  input:focus,select:focus,textarea:focus {{ outline:none;border-color:#6366f1; }}
  textarea {{ min-height:80px;resize:vertical; }}
  .sep {{ border-top:1px solid #2d3148;margin:24px 0; }}
  #cue-nav {{ width:240px;background:#1a1d27;border-right:1px solid #2d3148;padding:24px 16px;position:fixed;top:0;left:0;bottom:0;overflow-y:auto;z-index:100; }}
  #cue-main {{ margin-left:240px;padding:32px 40px;flex:1;max-width:1100px; }}
  #nav-toggle {{ display:none;position:fixed;top:12px;right:16px;z-index:200;background:#6366f1;border:none;color:white;padding:6px 12px;border-radius:6px;font-size:18px;cursor:pointer; }}
  @media(max-width:768px){{
    #cue-nav {{ width:100%;height:auto;position:static;border-right:none;border-bottom:1px solid #2d3148;padding:12px 16px;display:none; }}
    #cue-nav.open {{ display:block; }}
    #cue-main {{ margin-left:0;padding:16px 14px; }}
    #nav-toggle {{ display:block; }}
    table {{ font-size:12px; }}
    th,td {{ padding:8px; }}
  }}
</style>
</head><body>
<button id="nav-toggle" onclick="document.getElementById('cue-nav').classList.toggle('open')">☰</button>
<div style="display:flex;min-height:100vh">
  <nav id="cue-nav">
    <h1 style="font-size:18px;font-weight:700;color:#818cf8;margin-bottom:4px">CUE</h1>
    <div style="font-size:11px;color:#8b91a8;margin-bottom:24px;text-transform:uppercase;letter-spacing:1px">Creative Understanding Experiment</div>
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#8b91a8;margin-bottom:8px">Pipeline</div>
    {nav_html}
  </nav>
  <main id="cue-main">
    {content}
  </main>
</div>
<div id="cue-toast" style="display:none;position:fixed;bottom:28px;right:28px;z-index:9999;
  background:#1e2235;border:1px solid #6366f140;border-radius:10px;padding:14px 20px;
  box-shadow:0 4px 24px #00000060;display:flex;align-items:center;gap:12px;font-size:13px;
  max-width:340px;animation:slideIn .25s ease">
  <span id="cue-toast-icon" style="font-size:18px"></span>
  <span id="cue-toast-msg"></span>
</div>
<style>
@keyframes slideIn {{ from {{ opacity:0;transform:translateY(12px) }} to {{ opacity:1;transform:translateY(0) }} }}
</style>
<script>
(function(){{
  var p = new URLSearchParams(location.search);
  var msg = p.get('toast');
  var type = p.get('toast_type') || 'ok';
  if (msg) {{
    var el = document.getElementById('cue-toast');
    var icon = document.getElementById('cue-toast-icon');
    var txt = document.getElementById('cue-toast-msg');
    el.style.display = 'flex';
    txt.textContent = decodeURIComponent(msg);
    icon.textContent = type === 'error' ? '⚠️' : type === 'warn' ? '⚡' : '✅';
    if (type === 'error') el.style.borderColor = '#ef444440';
    else if (type === 'warn') el.style.borderColor = '#f59e0b40';
    else el.style.borderColor = '#22c55e40';
    setTimeout(function() {{
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(function() {{ el.style.display = 'none'; }}, 400);
    }}, 3500);
    // Clean URL so toast doesn't reappear on refresh
    var clean = location.pathname + (p.toString().replace(/&?toast[^&]*/g,'').replace(/&?toast_type[^&]*/g,'').replace(/^\?$/,'') ? '?' + p.toString().replace(/&?toast=[^&]*/g,'').replace(/&?toast_type=[^&]*/g,'').replace(/^&/,'') : '');
    history.replaceState(null,'',clean);
  }}
}})();
</script>
</body></html>'''


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    from datetime import timedelta
    state = get_state()

    # Load all scorecards
    scorecards = {}
    for f in SCORECARDS_DIR.glob("*_scorecard.json"):
        ad_id = f.stem.replace("_scorecard", "")
        with open(f, "r", encoding="utf-8") as fh:
            scorecards[ad_id] = json.load(fh)

    # Weekly activity — scorecards reviewed in last 7 days
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    reviewed_this_week = [
        sc for sc in scorecards.values()
        if sc.get("date_reviewed", "") >= str(week_ago)
    ]

    # Avg score + simple trend (this week vs older)
    all_scores = [sc.get("overall_score", 0) for sc in scorecards.values()]
    avg_score = round(sum(all_scores) / len(all_scores)) if all_scores else None
    week_scores = [sc.get("overall_score", 0) for sc in reviewed_this_week]
    older_scores = [sc.get("overall_score", 0) for sc in scorecards.values() if sc not in reviewed_this_week]
    if week_scores and older_scores:
        trend_delta = round(sum(week_scores)/len(week_scores) - sum(older_scores)/len(older_scores))
        trend_arrow = ("↑ " + str(abs(trend_delta)) + " vs prev") if trend_delta > 0 else ("↓ " + str(abs(trend_delta)) + " vs prev") if trend_delta < 0 else "→ stable"
        trend_color = "#22c55e" if trend_delta > 0 else "#ef4444" if trend_delta < 0 else "#8b91a8"
    else:
        trend_arrow, trend_color = "", "#8b91a8"

    # Recommended action
    phase = state["current_phase"]
    phase_map = {
        "scout":         ("Build the reference library", "Add best-in-class competitor ads so CUE has patterns to learn from.", "/library/add-url", "Add Ad from URL →"),
        "deconstruct":   ("Deconstruct library ads", "New ads need to be deconstructed before the playbook can be updated.", "/library", "View Library →"),
        "pattern":       ("Generate the playbook", "Run /cue-pattern to extract patterns from deconstructed ads.", "/playbook", "View Playbook →"),
        "load_wiom_ads": ("Upload a Wiom ad", "Library is ready. Now upload a Wiom ad to review.", "/wiom/upload", "Upload Ad →"),
        "review":        ("Review Wiom ads", "Set campaign context then click Review on your ads.", "/wiom", "Go to Ads →"),
        "suggest":       ("Generate suggestions", "Scorecards ready. Generate improvement suggestions.", "/wiom", "Go to Ads →"),
        "complete":      ("Add performance data", "Add live Meta data to unlock campaign optimization.", "/performance", "Add Performance →"),
    }
    rec_html = _next_step(*phase_map[phase]) if phase in phase_map else ""

    # --- Summary row ---
    score_display = f'<span style="font-size:32px;font-weight:700;color:{"#22c55e" if avg_score and avg_score>=65 else "#f59e0b" if avg_score and avg_score>=40 else "#ef4444"}">{avg_score}</span><span style="font-size:13px;color:#8b91a8">/100</span>' if avg_score is not None else '<span style="font-size:20px;color:#4b5563">—</span>'
    trend_html = f'<div style="font-size:12px;color:{trend_color};margin-top:4px">{trend_arrow}</div>' if trend_arrow else ""

    summary_cards = f'''<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px">
      {_card(f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#8b91a8;margin-bottom:8px">Avg Score</div>{score_display}{trend_html}', "padding:20px;margin-bottom:0")}
      {_card(f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#8b91a8;margin-bottom:8px">Reviewed This Week</div><span style="font-size:32px;font-weight:700;color:#818cf8">{len(reviewed_this_week)}</span><div style="font-size:12px;color:#8b91a8;margin-top:4px">{state["scorecards"]["total"]} total</div>', "padding:20px;margin-bottom:0")}
      {_card(f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#8b91a8;margin-bottom:8px">Wiom Ads</div><span style="font-size:32px;font-weight:700;color:#818cf8">{state["wiom_ads"]["total"]}</span><div style="font-size:12px;color:#8b91a8;margin-top:4px">{state["library"]["total_ads"]} in library</div>', "padding:20px;margin-bottom:0")}
      {_card(f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#8b91a8;margin-bottom:8px">Perf Snapshots</div><span style="font-size:32px;font-weight:700;color:#818cf8">{state["performance"]["total"]}</span><div style="font-size:12px;color:#8b91a8;margin-top:4px">{state["contexts"]["total"]} contexts set</div>', "padding:20px;margin-bottom:0")}
    </div>'''

    html = f'<h2 style="margin-bottom:20px">Dashboard</h2>{rec_html}{summary_cards}'

    # Scored ads summary — compact table
    if scorecards:
        rows = ""
        for ad_id, sc in sorted(scorecards.items(), key=lambda x: -x[1].get("overall_score", 0)):
            s = sc.get("overall_score", 0)
            sc_color = "#22c55e" if s >= 65 else "#f59e0b" if s >= 40 else "#ef4444"
            top_gap = sc.get("priority_gaps", [{}])[0].get("description", "—")[:60] if sc.get("priority_gaps") else "—"
            rows += f'''<tr>
              <td><a href="/wiom" style="color:#e4e7f0;font-weight:500">{_esc(_ad_name(ad_id))}</a><div style="font-size:11px;color:#8b91a8">{ad_id}</div></td>
              <td><strong style="color:{sc_color}">{s}</strong></td>
              <td>{_chip(sc.get("campaign_objective","default"), "blue")}</td>
              <td style="font-size:12px;color:#8b91a8">{_esc(top_gap)}</td>
              <td>{_btn("Review", f"/wiom", False, True)}</td>
            </tr>'''
        html += f'<h3>Scored Ads</h3>{_card(f"<table><tr><th>Ad</th><th>Score</th><th>Objective</th><th>Top Gap</th><th></th></tr>{rows}</table>", "padding:0;overflow:hidden")}'

    # Top suggestions — one card, collapsed list
    suggestions = {}
    for f in SUGGESTIONS_DIR.glob("*_suggestions.json"):
        ad_id = f.stem.replace("_suggestions", "")
        with open(f, "r", encoding="utf-8") as fh:
            suggestions[ad_id] = json.load(fh)

    if suggestions:
        sug_rows = ""
        for ad_id, sug in suggestions.items():
            for s in sug.get("suggestions", [])[:2]:
                pc = "red" if s["priority"] == "high" else "amber" if s["priority"] == "medium" else "green"
                sug_rows += f'<tr><td style="font-size:12px;color:#8b91a8">{_esc(_ad_name(ad_id))}</td><td>{_chip(_dim_label(s.get("dimension","")), "blue")}</td><td style="font-size:12px">{_esc(s.get("suggested_change","")[:80])}</td><td>{_chip(s["priority"], pc)}</td></tr>'
        html += f'<h3 style="margin-top:24px">Top Suggestions</h3>{_card(f"<table><tr><th>Ad</th><th>Dimension</th><th>Change</th><th>Priority</th></tr>{sug_rows}</table>", "padding:0;overflow:hidden")}'

    return _page("Dashboard", html, "home")


@app.route("/library")
def library():
    index = load_index()
    verticals = len(set(ad.get("vertical", "") for ad in index))
    decon_count = sum(1 for ad in index if ad.get("deconstructed"))

    # Next step banner
    next_step = ""
    if len(index) < 10:
        next_step = _next_step("Add more reference ads", "Spot a great competitor ad? Add it to the library so CUE can learn from it.", "/library/add-url", "Add Ad from URL")
    elif decon_count < len(index):
        next_step = _next_step("Deconstruct remaining ads", f"{len(index) - decon_count} ads haven't been deconstructed yet. Deconstruct them to strengthen the playbook.", "/playbook", "View Playbook")
    else:
        next_step = _next_step("Library is complete", "All ads deconstructed. The playbook is fully informed. Go review a Wiom ad.", "/wiom", "Review Wiom Ads →")

    # Stats bar
    html = f'''<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px">
      <div><h2 style="margin-bottom:4px">Best-in-Class Ad Library</h2>
      <p style="color:#8b91a8">{len(index)} reference ads · {verticals} verticals · {decon_count} deconstructed</p></div>
      <div style="display:flex;gap:8px">
        {_btn("+ Add Ad from URL", "/library/add-url")}
        <span style="padding:8px 14px;border-radius:6px;font-size:12px;color:#8b91a8;border:1px solid #2d3148;cursor:not-allowed">Meta Ad Library API (coming soon)</span>
      </div>
    </div>'''

    html += next_step

    rows = ""
    for ad in index:
        tc = "green" if ad.get("tier") == "exceptional" else "amber" if ad.get("tier") == "strong" else "blue"
        url = ad.get("url", "")
        url_html = f'<a href="{_esc(url)}" target="_blank" style="font-size:11px;color:#818cf8">View ↗</a>' if url else ""
        rows += f'''<tr>
          <td><strong>{_esc(ad["id"])}</strong> {url_html}</td>
          <td>{_esc(ad.get("advertiser",""))}</td>
          <td>{_esc(ad.get("platform",""))}</td>
          <td>{_esc(ad.get("vertical",""))}</td>
          <td>{_chip(ad.get("tier","unrated"), tc)}</td>
          <td>{"✓" if ad.get("deconstructed") else "—"}</td>
        </tr>'''

    html += f'<table><tr><th>ID</th><th>Advertiser</th><th>Platform</th><th>Vertical</th><th>Tier</th><th>Deconstructed</th></tr>{rows}</table>'
    return _page("Ad Library", html, "library")


@app.route("/library/add-url", methods=["GET", "POST"])
def library_add_url():
    """Add a competitor ad to the library by URL."""
    from harness import save_ad, next_ad_id

    if request.method == "POST":
        ad_id = next_ad_id()
        url = request.form.get("url", "").strip()
        advertiser = request.form.get("advertiser", "").strip()
        platform = request.form.get("platform", "")
        vertical = request.form.get("vertical", "ISP/broadband")
        tier = request.form.get("tier", "reference")
        description = request.form.get("description", "").strip()
        tags_raw = request.form.get("tags", "")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        data = {
            "id": ad_id,
            "advertiser": advertiser,
            "platform": platform,
            "vertical": vertical,
            "tier": tier,
            "format": "video",
            "duration_seconds": None,
            "language": request.form.get("language", "Hindi"),
            "region": "India",
            "url": url,
            "description": description,
            "tags": tags,
            "date_found": datetime.now().strftime("%Y-%m-%d"),
            "deconstructed": False,
            "source": "url_submission",
        }

        ok, msg = save_ad(data)
        if ok:
            html = f'''<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">
              Added <strong>{ad_id}</strong> — {_esc(advertiser)} to library
            </div>'''
            html += _next_step("Next: update the playbook", "Now that a new ad is in the library, regenerate the playbook to include its patterns.", "/playbook", "View Playbook")
            html += f'<div style="margin-top:16px;display:flex;gap:8px">{_btn("Add Another", "/library/add-url", False)} {_btn("View Library", "/library", False)}</div>'
        else:
            html = _card(f'<div style="color:#ef4444">{_esc(msg)}</div><div style="margin-top:12px">{_btn("Back", "/library/add-url", False)}</div>')

        return _page("Ad Added", html, "library")

    html = '''<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px">
      <div><h2 style="margin-bottom:4px">Add Ad from URL</h2>
      <p style="color:#8b91a8">Spotted a great competitor ad? Add it to the library so CUE can learn from it.</p></div>
    </div>'''

    html += _card(f'''<h3 style="margin-bottom:16px">Where to find good ads</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">
      <a href="https://www.facebook.com/ads/library/" target="_blank" style="padding:12px;background:#242836;border-radius:8px;display:block;text-decoration:none">
        <div style="font-size:13px;font-weight:600;color:#e4e7f0">Meta Ad Library ↗</div>
        <div style="font-size:11px;color:#8b91a8;margin-top:4px">Search by brand or keyword. Filter: India, Video.</div>
      </a>
      <a href="https://www.youtube.com/ads/transparency/" target="_blank" style="padding:12px;background:#242836;border-radius:8px;display:block;text-decoration:none">
        <div style="font-size:13px;font-weight:600;color:#e4e7f0">YouTube Ads Transparency ↗</div>
        <div style="font-size:11px;color:#8b91a8;margin-top:4px">Search Indian telecom/ISP advertisers.</div>
      </a>
      <a href="https://www.thinkwithgoogle.com/intl/en-apac/" target="_blank" style="padding:12px;background:#242836;border-radius:8px;display:block;text-decoration:none">
        <div style="font-size:13px;font-weight:600;color:#e4e7f0">Think with Google India ↗</div>
        <div style="font-size:11px;color:#8b91a8;margin-top:4px">Case studies and award-winning Indian ads.</div>
      </a>
    </div>''')

    html += f'<form method="POST" action="/library/add-url">'
    html += _card(f'''<h3>Ad Details</h3>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Ad URL *</label>
      <input type="url" name="url" required placeholder="https://www.youtube.com/watch?v=... or Meta Ad Library link">
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Advertiser / Brand *</label>
        <input type="text" name="advertiser" required placeholder="e.g., Airtel, Jio, BSNL">
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Platform *</label>
        <select name="platform" required>
          <option value="YouTube">YouTube</option>
          <option value="Meta">Meta (Facebook/Instagram)</option>
          <option value="Instagram">Instagram</option>
          <option value="TV">TV / Broadcast</option>
          <option value="Other">Other</option>
        </select>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Vertical</label>
        <select name="vertical">
          <option value="ISP/broadband">ISP / Broadband</option>
          <option value="telecom">Telecom</option>
          <option value="OTT/streaming">OTT / Streaming</option>
          <option value="fintech">Fintech</option>
          <option value="edtech">Edtech</option>
          <option value="ecommerce">Ecommerce</option>
          <option value="fmcg">FMCG</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Quality Tier</label>
        <select name="tier">
          <option value="exceptional">Exceptional — best in class</option>
          <option value="strong">Strong — above average</option>
          <option value="reference" selected>Reference — average/benchmark</option>
        </select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Language</label>
        <select name="language">
          <option value="Hindi">Hindi</option>
          <option value="English">English</option>
          <option value="Multilingual">Multilingual</option>
          <option value="Tamil">Tamil</option>
          <option value="Telugu">Telugu</option>
        </select>
      </div>
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Why is this ad good? What stood out? *</label>
      <textarea name="description" required placeholder="e.g., Strong emotional hook using family scene in first 3s. Dialogue-driven with no voiceover — feels authentic. Clear USP in last 5s without being pushy."></textarea>
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Tags (comma-separated)</label>
      <input type="text" name="tags" placeholder="e.g., emotional, family, hindi, tier-2-3, dialogue-driven">
    </div>''')

    html += f'<button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Add to Library</button> {_btn("Cancel", "/library", False)}</form>'

    return _page("Add Ad from URL", html, "library")


@app.route("/playbook")
def playbook():
    if not PLAYBOOK_JSON.exists():
        html = _card('<div style="text-align:center;padding:48px;color:#8b91a8"><h3 style="color:#e4e7f0;margin-bottom:8px">No playbook yet</h3><p>Run /cue-pattern to generate the Creative Playbook.</p></div>')
        return _page("Playbook", html, "playbook")

    with open(PLAYBOOK_JSON, "r", encoding="utf-8") as f:
        pb = json.load(f)

    # Map of pattern IDs → example ad IDs from library (for "seen in" references)
    lib_decons = {}
    for lf in (ROOT / "library" / "metadata").glob("*_decon.json"):
        try:
            with open(lf, "r", encoding="utf-8") as fh:
                ld = json.load(fh)
            lib_decons[lf.stem.replace("_decon", "")] = ld
        except Exception:
            pass

    html = f'''<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
      <div>
        <h2 style="margin-bottom:4px">Creative Playbook</h2>
        <p style="color:#8b91a8;font-size:13px">{pb.get("library_size",0)} ads analyzed &nbsp;·&nbsp; {len(pb.get("patterns",[]))} winning patterns &nbsp;·&nbsp; {len(pb.get("anti_patterns",[]))} anti-patterns to avoid</p>
      </div>
    </div>'''

    # --- Patterns as visual cards ---
    conf_map = {"strong": (100, "#22c55e"), "moderate": (60, "#f59e0b"), "emerging": (30, "#818cf8")}
    freq_map  = {"very_high": 5, "high": 4, "medium": 3, "low": 2, "rare": 1}

    html += f'<h3 style="margin:24px 0 16px">Winning Patterns</h3>'
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">'
    for p in pb.get("patterns", []):
        conf = p.get("confidence", "emerging")
        conf_pct, conf_color = conf_map.get(conf, (30, "#818cf8"))
        freq_dots = "●" * freq_map.get(p.get("frequency",""), 2) + "○" * (5 - freq_map.get(p.get("frequency",""), 2))

        # Which objectives benefit from this pattern
        obj_tags = p.get("best_for_objectives", [])
        obj_html = "".join(_chip(o, "blue") for o in obj_tags[:3]) if obj_tags else ""

        # Example ads that exhibit this pattern (from lib decons — check hook or narrative)
        examples = [aid for aid, ld in lib_decons.items()
                    if p["id"] in str(ld)][:2]
        ex_html = (" ".join(_chip(e, "gray") for e in examples)) if examples else ""

        html += _card(f'''
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
            <div>
              <span style="font-size:10px;color:#8b91a8;font-weight:500">{_esc(p["id"])}</span>
              <div style="font-weight:600;font-size:15px;margin-top:2px">{_esc(p["name"])}</div>
            </div>
            <div style="text-align:right;flex-shrink:0">
              <div style="font-size:11px;color:{conf_color};font-weight:600;text-transform:uppercase">{conf}</div>
              <div style="font-size:11px;color:#8b91a8;letter-spacing:2px;margin-top:2px">{freq_dots}</div>
            </div>
          </div>
          <div style="height:3px;background:#242836;border-radius:2px;margin-bottom:12px">
            <div style="width:{conf_pct}%;height:3px;background:{conf_color};border-radius:2px"></div>
          </div>
          <p style="font-size:13px;color:#c9cde0;margin-bottom:8px;line-height:1.5">{_esc(p.get("description",""))}</p>
          <p style="font-size:12px;color:#8b91a8;font-style:italic;margin-bottom:10px">Why it works: {_esc(p.get("mechanism",""))}</p>
          <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center">
            {obj_html}{ex_html}
          </div>
        ''', "padding:20px;margin-bottom:0")
    html += '</div>'

    # --- Anti-patterns ---
    sev_map = {"high": ("#ef4444", 3), "medium": ("#f59e0b", 2), "low": ("#8b91a8", 1)}
    html += f'<h3 style="margin:32px 0 16px">Anti-Patterns to Avoid</h3>'
    html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">'
    for ap in pb.get("anti_patterns", []):
        sev_color, sev_w = sev_map.get(ap.get("severity","low"), ("#8b91a8",1))
        sev_bars = "▮" * sev_w + "▯" * (3 - sev_w)
        html += _card(f'''
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
            <div>
              <span style="font-size:10px;color:#8b91a8">{_esc(ap["id"])}</span>
              <div style="font-weight:600;font-size:15px;margin-top:2px">{_esc(ap["name"])}</div>
            </div>
            <div style="font-size:13px;color:{sev_color};letter-spacing:1px;font-weight:600">{sev_bars}</div>
          </div>
          <p style="font-size:13px;color:#c9cde0;line-height:1.5">{_esc(ap.get("description",""))}</p>
          {"<p style='font-size:12px;color:#8b91a8;margin-top:8px;font-style:italic'>Fix: " + _esc(ap.get("fix","")) + "</p>" if ap.get("fix") else ""}
        ''', f"padding:20px;margin-bottom:0;border-left:3px solid {sev_color}")
    html += '</div>'

    # --- Scoring rubric (collapsed) ---
    rubric = pb.get("scoring_rubric", {}).get("dimensions", {})
    if rubric:
        rubric_rows = ""
        for dn, dd in rubric.items():
            rubric_rows += f'<tr><td style="font-weight:500">{_dim_label(dn)}</td><td style="color:#818cf8">{int(dd.get("weight",0)*100)}%</td><td style="font-size:12px;color:#8b91a8">{_esc(list(dd.get("scores",{}).values())[-1] if dd.get("scores") else "")}</td></tr>'
        html += f'''<details style="margin-top:28px">
          <summary style="font-size:14px;font-weight:600;cursor:pointer;color:#818cf8;user-select:none;list-style:none">▸ Scoring Rubric (5 dimensions)</summary>
          <div style="margin-top:12px">{_card(f"<table><tr><th>Dimension</th><th>Weight</th><th>Score 5 = </th></tr>{rubric_rows}</table>","padding:0;overflow:hidden")}</div>
        </details>'''

    return _page("Playbook", html, "playbook")


@app.route("/wiom")
def wiom():
    show_archived = request.args.get("archived") == "1"
    all_wiom = []
    for f in sorted(WIOM_DIR.glob("*.json")):
        if f.stem.startswith("_") or f.stem.endswith("_decon"):
            continue
        try:
            with open(f, "r", encoding="utf-8") as fh:
                m = json.load(fh)
            if show_archived or not m.get("archived", False):
                all_wiom.append(f.stem)
        except Exception:
            all_wiom.append(f.stem)
    wiom_ids = sorted(all_wiom)

    scorecards = {}
    for f in SCORECARDS_DIR.glob("*_scorecard.json"):
        ad_id = f.stem.replace("_scorecard", "")
        with open(f, "r", encoding="utf-8") as fh:
            scorecards[ad_id] = json.load(fh)

    contexts_by_ad = {}
    for f in CONTEXTS_DIR.glob("*.json"):
        with open(f, "r", encoding="utf-8") as fh:
            ctx = json.load(fh)
            aid = ctx["ad_id"]
            contexts_by_ad.setdefault(aid, []).append(ctx)

    # Determine next step for this page
    has_context = any((CONTEXTS_DIR / f).exists() for f in [f.name for f in CONTEXTS_DIR.glob("*.json")] if True)
    wiom_count = len(wiom_ids)
    scored_count = len(scorecards)

    if wiom_count == 0:
        wiom_next = _next_step("Upload your first Wiom ad", "Upload a video file to get started. CUE will extract frames automatically.", "/wiom/upload", "Upload Ad →")
    elif scored_count == 0:
        wiom_next = _next_step("Set context then Review", "Before scoring, set the campaign objective so CUE applies the right weights. Then click Review.", "/context/new", "Set Context →")
    elif scored_count < wiom_count:
        wiom_next = _next_step("Review remaining ads", f"{wiom_count - scored_count} ads haven't been reviewed yet. Click Review on each.", "/batch/review", "Batch Review →")
    else:
        wiom_next = _next_step("Add live performance data", "Ads are scored. Now add Meta performance data to unlock Optimize.", "/performance", "Add Performance Data →")

    archive_toggle = _btn("Show Archived", "/wiom?archived=1", False) if not show_archived else _btn("Hide Archived", "/wiom", False)
    html = f'<h2>Wiom Ads & Scorecards</h2><div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap">{_btn("+ Upload Ad", "/wiom/upload")} {_btn("Batch Review", "/batch/review", False)} {_btn("Campaign Mapping", "/campaign/map", False)} {archive_toggle}</div>{wiom_next}'
    for wid in wiom_ids:
        meta_path = WIOM_DIR / f"{wid}.json"
        meta = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as fh:
                meta = json.load(fh)

        desc = f'<p style="font-size:13px;color:#8b91a8">{_esc(meta.get("description",""))}</p>'
        tags = "".join(_chip(t, "blue") for t in meta.get("tags", []))

        # #4 — Transcript preview (collapsed, expandable)
        transcript = meta.get("transcript", "")
        transcript_html = ""
        if transcript:
            preview = _esc(transcript[:160].strip()) + ("…" if len(transcript) > 160 else "")
            transcript_html = f'''<details style="margin-top:10px">
              <summary style="font-size:11px;color:#6366f1;cursor:pointer;user-select:none;list-style:none">
                ▸ Transcript ({len(transcript.split())} words)
              </summary>
              <div style="margin-top:6px;font-size:12px;color:#8b91a8;line-height:1.6;
                background:#242836;border-radius:6px;padding:10px 12px;font-style:italic">
                {preview}
              </div>
            </details>'''

        score_html = ""
        if wid in scorecards:
            sc = scorecards[wid]
            ba_text = ""
            ba = sc.get("brief_alignment")
            if ba:
                ba_text = f'<div style="font-size:12px;color:#8b91a8">Brief: <strong style="color:#e4e7f0">{ba["overall_brief_score"]}/100</strong></div>'

            # #5 — Dimension mini-bars inline on card
            dims = sc.get("dimensions", {})
            dim_bars = ""
            for dn in ["hook", "retention", "ctr_drivers", "cta_conversion", "brand_coherence"]:
                dd = dims.get(dn, {})
                s = dd.get("score", 0)
                bar_color = "#ef4444" if s <= 2 else "#f59e0b" if s <= 3 else "#22c55e"
                bar_w = int(s / 5 * 100)
                short = {"hook": "Hook", "retention": "Hold", "ctr_drivers": "CTR",
                         "cta_conversion": "CTA", "brand_coherence": "Brand"}.get(dn, dn)
                dim_bars += f'''<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                  <span style="font-size:10px;color:#8b91a8;width:32px;flex-shrink:0">{short}</span>
                  <div style="flex:1;height:4px;background:#242836;border-radius:2px">
                    <div style="width:{bar_w}%;height:4px;background:{bar_color};border-radius:2px"></div>
                  </div>
                  <span style="font-size:10px;color:#8b91a8;width:14px;text-align:right">{s}</span>
                </div>'''

            # #7 — Score tooltip: top strength + top gap
            strengths = sc.get("strengths", [])
            gaps = sc.get("priority_gaps", [])
            tooltip_parts = []
            if strengths:
                tooltip_parts.append(f"✓ {strengths[0]}")
            if gaps:
                tooltip_parts.append(f"△ {gaps[0].get('description', '')}")
            tooltip = " | ".join(tooltip_parts)[:200]

            score_html = f'''<div style="margin-top:16px;display:flex;align-items:flex-start;gap:20px">
              <div title="{_esc(tooltip)}" style="cursor:help;flex-shrink:0">
                {_gauge(sc.get("overall_score", 0))}
                <div style="font-size:10px;color:#8b91a8;text-align:center;margin-top:2px">hover for insight</div>
              </div>
              <div style="flex:1">
                <div style="font-size:13px;margin-bottom:2px">Pattern Score: <strong>{sc.get("overall_score",0)}/100</strong></div>
                {ba_text}
                <a href="/context/new?ad_id={wid}" style="display:inline-block;margin-bottom:8px;font-size:12px;font-weight:600;color:#818cf8;background:#6366f118;border:1px solid #6366f140;border-radius:6px;padding:3px 10px;text-decoration:none" title="Click to change objective">⚡ {sc.get("campaign_objective","default")} &nbsp;<span style="font-size:10px;opacity:0.7">change →</span></a>
                {dim_bars}
              </div>
            </div>'''

        ctx_html = ""
        if wid in contexts_by_ad:
            chips = "".join(_chip(f'{c["context_id"]} ({c["objective"]["type"]})', "green") for c in contexts_by_ad[wid])
            ctx_html = f'<div style="margin-top:12px"><span style="font-size:12px;color:#8b91a8">Contexts:</span> {chips}</div>'

        # Check if deconstruction exists
        has_decon = (WIOM_DIR / f"{wid}_decon.json").exists()

        # Single Review button triggers full pipeline (deconstruct if needed → review → suggest)
        review_btn = f'<form method="POST" action="/run/full/{wid}" style="display:inline"><button type="submit" style="padding:6px 14px;border-radius:6px;font-size:12px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Review</button></form>'
        optimize_btn = f'<form method="POST" action="/run/optimize/{wid}" style="display:inline"><button type="submit" style="padding:6px 14px;border-radius:6px;font-size:12px;font-weight:500;cursor:pointer;border:none;background:#22c55e;color:white">Optimize</button></form>' if wid in scorecards else ""

        # Archive / Change Objective / Delete — management actions after scoring
        is_archived = meta.get("archived", False)
        archive_label = "Unarchive" if is_archived else "Archive"
        archive_btn = f'<form method="POST" action="/wiom/{wid}/archive" style="display:inline"><button type="submit" style="padding:6px 12px;border-radius:6px;font-size:12px;font-weight:500;cursor:pointer;border:1px solid #4b5563;background:transparent;color:#9ca3af" title="{"Unarchive" if is_archived else "Archive this ad — hides it from the main list"}">{archive_label}</button></form>'
        delete_btn = f'<form method="POST" action="/wiom/{wid}/delete" style="display:inline" onsubmit="return confirm(\'Delete {wid} and all associated scorecards? This cannot be undone.\')"><button type="submit" style="padding:6px 12px;border-radius:6px;font-size:12px;font-weight:500;cursor:pointer;border:1px solid #7f1d1d;background:transparent;color:#f87171" title="Permanently delete this ad and its data">Delete</button></form>'
        change_obj_btn = _btn("Change Objective", f"/context/new?ad_id={wid}", False, True)

        buttons = f'''<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          {review_btn} {optimize_btn}
          {_btn("+ Context", f"/context/new?ad_id={wid}", False, True)}
          {_btn("+ Performance", f"/performance?ad_id={wid}", False, True)}
          {_btn("Pull from Meta", "/meta/pull", False, True)}
          {_btn("History", f"/history?ad_id={wid}", False, True)}
        </div>
        <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;padding-top:8px;border-top:1px solid #1e2235">
          {change_obj_btn} {archive_btn} {delete_btn}
        </div>'''

        # Pipeline status pills — shows where each ad is in the flow
        has_scored  = wid in scorecards
        has_optim   = (OPTIMIZATIONS_DIR / f"{wid}_opt_001.json").exists() or any(OPTIMIZATIONS_DIR.glob(f"{wid}_opt_*.json"))
        def _pill(label, done, href=None):
            if done:
                st = "background:#22c55e22;color:#22c55e;border:1px solid #22c55e44"
                icon = "✓"
            else:
                st = "background:#24283622;color:#4b5563;border:1px solid #2d3148"
                icon = "○"
            inner = f'<span style="display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500;{st}">{icon} {label}</span>'
            if href and not done:
                return f'<a href="{href}" style="text-decoration:none">{inner}</a>'
            return inner
        status_pills = f'''<div style="display:flex;align-items:center;gap:6px;margin-top:12px;flex-wrap:wrap">
          {_pill("Uploaded", True)}
          <span style="color:#2d3148;font-size:12px">→</span>
          {_pill("Reviewed", has_scored, f"/run/full/{wid}")}
          <span style="color:#2d3148;font-size:12px">→</span>
          {_pill("Optimized", has_optim, f"/performance?ad_id={wid}")}
        </div>'''

        decon_badge = _chip("Deconstructed", "green") if has_decon else ""
        archived_badge = _chip("Archived", "gray") if meta.get("archived") else ""
        ad_title = _ad_name(wid)
        html += _card(f'<h3>{_esc(ad_title)}</h3><div style="font-size:11px;color:#8b91a8;margin-bottom:8px">{wid} &nbsp;{decon_badge} {archived_badge}</div>{desc}<div style="margin-top:8px">{tags}</div>{transcript_html}{status_pills}{score_html}{ctx_html}{buttons}')

    if not wiom_ids:
        def _step(num, title, desc, href, cta, active=True):
            op = "1" if active else "0.4"
            return f'''<div style="display:flex;gap:16px;align-items:flex-start;opacity:{op};margin-bottom:20px">
              <div style="width:32px;height:32px;border-radius:50%;background:#6366f122;border:2px solid #6366f1;
                display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;
                color:#818cf8;flex-shrink:0">{num}</div>
              <div style="flex:1">
                <div style="font-weight:600;margin-bottom:4px">{title}</div>
                <div style="font-size:13px;color:#8b91a8;margin-bottom:8px">{desc}</div>
                {(_btn(cta, href, active, True)) if active else f'<span style="font-size:12px;color:#4b5563">{cta} — complete step {num-1} first</span>'}
              </div>
            </div>'''
        onboarding = f'''<div style="max-width:560px;margin:0 auto;padding:40px 0">
          <h3 style="margin-bottom:6px;font-size:20px">Get started with CUE</h3>
          <p style="color:#8b91a8;font-size:13px;margin-bottom:32px">Three steps to your first ad scorecard</p>
          {_step(1, "Upload a Wiom ad", "Upload a video file — CUE extracts frames and transcribes audio automatically.", "/wiom/upload", "Upload Ad →", True)}
          {_step(2, "Set campaign objective", "Tell CUE what this ad is optimising for. Objective drives the scoring weights.", "/context/new", "Set Objective →", False)}
          {_step(3, "Click Review", "CUE runs the full pipeline — deconstruct → score → suggest — in one click.", "/wiom", "Go to Ads →", False)}
        </div>'''
        html += _card(onboarding)

    return _page("Wiom Ads", html, "wiom")


@app.route("/context/new")
def context_new():
    ad_id = request.args.get("ad_id", "")
    wiom_ids = sorted([f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")])

    opts = "".join(f'<option value="{w}" {"selected" if w == ad_id else ""}>{w}</option>' for w in wiom_ids)

    html = '''<h2>Set Campaign Context</h2>
    <p style="color:#8b91a8;margin-bottom:24px">Context drives how the ad is scored -- objective sets weights, brief enables alignment scoring, targeting adjusts pattern relevance.</p>
    <form method="POST" action="/context/save">'''

    # Section 1: Objective
    html += _card(f'''<h3>1. Campaign Objective {_chip("Required","red")}</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Objective Type</label>
        <select name="objective_type" required>
          <option value="default">Default (balanced weights)</option>
          <option value="awareness">Awareness -- Brand reach & recall</option>
          <option value="completion">Completion -- Video completion rate</option>
          <option value="click">Click -- CTR optimization</option>
          <option value="traffic">Traffic -- Website visits</option>
          <option value="app_download">App Download -- Install optimization</option>
          <option value="conversion">Conversion -- Sign-ups, purchases</option>
          <option value="booking">Booking -- Appointment/order booking</option>
        </select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Ad ID</label>
        <select name="ad_id">{opts}</select>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Primary KPI</label>
        <input type="text" name="primary_kpi" placeholder="e.g., Video completion rate > 60%">
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Secondary KPI (optional)</label>
        <input type="text" name="secondary_kpi" placeholder="e.g., CTR > 1%">
      </div>
    </div>''')

    # Section 2: Brief
    html += _card(f'''<h3>2. Creative Brief {_chip("Recommended","amber")}</h3>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Target Audience</label>
      <textarea name="target_audience" placeholder="e.g., Tier 2-3 families, 25-45, household decision-makers with 2-3 kids"></textarea>
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Key Message</label>
      <input type="text" name="key_message" placeholder="e.g., Wiom broadband -- pay only for what you use, like a meter">
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Tone</label>
        <select name="tone">
          <option value="">-- Skip --</option>
          <option value="informative">Informative</option>
          <option value="emotional">Emotional</option>
          <option value="humorous">Humorous</option>
          <option value="aspirational">Aspirational</option>
          <option value="urgent">Urgent</option>
          <option value="conversational">Conversational</option>
          <option value="bold">Bold</option>
        </select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Desired Action</label>
        <input type="text" name="desired_action" placeholder="e.g., Download the Wiom app">
      </div>
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">USP</label>
      <input type="text" name="usp" placeholder="e.g., Metered broadband -- no fixed monthly plans, pay for what you use">
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Constraints / Brand Guidelines (optional)</label>
      <textarea name="constraints" placeholder="e.g., Must include family setting. No English-heavy dialogue. Max 30s for feed."></textarea>
    </div>''')

    # Section 3: Targeting
    html += _card(f'''<h3>3. Campaign Targeting {_chip("Recommended","amber")}</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Platform</label>
        <select name="platform">
          <option value="">-- Skip --</option>
          <option value="Meta">Meta (Facebook + Instagram)</option>
          <option value="YouTube">YouTube</option>
          <option value="Instagram">Instagram only</option>
          <option value="both_meta_youtube">Both Meta + YouTube</option>
          <option value="all">All platforms</option>
        </select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Budget Tier</label>
        <select name="budget_tier">
          <option value="">-- Skip --</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Placements (comma-separated: feed, stories, reels, pre_roll, shorts, in_stream, explore)</label>
      <input type="text" name="placements" placeholder="e.g., feed, reels, stories">
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Age Range</label>
        <input type="text" name="age_range" placeholder="e.g., 25-45">
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Gender</label>
        <select name="gender"><option value="all">All</option><option value="male">Male</option><option value="female">Female</option></select>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Geography (comma-separated)</label>
        <input type="text" name="geo" placeholder="e.g., Maharashtra, UP, Bihar, MP">
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Audience Tier</label>
        <select name="tier"><option value="">-- Skip --</option><option value="tier_1">Tier 1</option><option value="tier_2">Tier 2</option><option value="tier_3">Tier 3</option><option value="mixed">Mixed</option></select>
      </div>
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Interests (comma-separated)</label>
      <input type="text" name="interests" placeholder="e.g., streaming, family, education, cricket">
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Bid Strategy (optional)</label>
      <input type="text" name="bid_strategy" placeholder="e.g., Lowest cost, Target CPA Rs 50">
    </div>''')

    html += f'''<div style="display:flex;gap:12px;margin-top:16px">
      <button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Save Context & Show Weight Profile</button>
      {_btn("Cancel", "/", False)}
    </div></form>'''

    return _page("New Context", html, "context")


@app.route("/context/save", methods=["POST"])
def context_save():
    form = request.form
    ad_id = form.get("ad_id", "wiom_001")
    objective_type = form.get("objective_type", "default")
    ctx_id = next_context_id(ad_id)

    data = {
        "context_id": ctx_id,
        "ad_id": ad_id,
        "created_at": datetime.now().isoformat(),
        "objective": {
            "type": objective_type,
            "primary_kpi": form.get("primary_kpi") or None,
            "secondary_kpi": form.get("secondary_kpi") or None,
        },
        "brief": None,
        "targeting": None,
    }

    # Save brief if any field is provided (all fields optional)
    brief_fields = ["target_audience", "key_message", "usp", "desired_action", "tone"]
    if any(form.get(f) for f in brief_fields):
        constraints = [c.strip() for c in form.get("constraints", "").split("\n") if c.strip()]
        data["brief"] = {
            "target_audience": form.get("target_audience") or None,
            "key_message": form.get("key_message") or None,
            "tone": form.get("tone") or None,
            "constraints": constraints,
            "usp": form.get("usp") or None,
            "desired_action": form.get("desired_action") or None,
            "brand_guidelines_notes": None,
        }

    # Save targeting if any field is provided
    targeting_fields = ["platform", "placements", "age_range", "geo", "interests", "budget_tier", "bid_strategy", "tier"]
    if any(form.get(f) for f in targeting_fields):
        placements = [p.strip() for p in form.get("placements", "").split(",") if p.strip()]
        geo = [g.strip() for g in form.get("geo", "").split(",") if g.strip()]
        interests = [i.strip() for i in form.get("interests", "").split(",") if i.strip()]
        data["targeting"] = {
            "platform": form.get("platform") or None,
            "placements": placements,
            "audience": {
                "age_range": form.get("age_range") or None,
                "gender": form.get("gender") or None,
                "geo": geo,
                "interests": interests,
                "tier": form.get("tier") or None,
            },
            "budget_tier": form.get("budget_tier") or None,
            "bid_strategy": form.get("bid_strategy") or None,
        }

    ok, msg = save_campaign_context(data)
    if not ok:
        return _page("Error", _card(f'<div style="color:#ef4444">Error: {_esc(msg)}</div>'), "context")

    weights = get_weight_profile(objective_type)
    patterns = get_priority_patterns(objective_type)
    adjusted = None
    if data["targeting"] and data["targeting"].get("placements"):
        adjusted = adjust_pattern_relevance(patterns, data["targeting"]["placements"])

    # Result page
    w_rows = "".join(f'<tr><td>{_dim_label(dn)}</td><td style="font-weight:700;font-family:monospace">{int(w*100)}%</td></tr>' for dn, w in weights.items())
    p_chips = "".join(_chip(p, "blue") for p in patterns)

    adj_html = ""
    if adjusted:
        adj_rows = "".join(f'<tr><td>{pid}</td><td>{score:.2f}x</td></tr>' for pid, score in adjusted)
        adj_html = f'<div class="sep"></div><h3>Placement-Adjusted Relevance</h3><table><tr><th>Pattern</th><th>Relevance</th></tr>{adj_rows}</table>'

    html = f'''<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">
      Context <strong>{ctx_id}</strong> saved for <strong>{ad_id}</strong>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      {_card(f'<h3>Weight Profile for "{objective_type}"</h3><table><tr><th>Dimension</th><th>Weight</th></tr>{w_rows}</table>')}
      {_card(f'<h3>Priority Patterns</h3><p style="font-size:12px;color:#8b91a8;margin-bottom:12px">Patterns evaluated first for "{objective_type}" objective:</p>{p_chips}{adj_html}')}
    </div>
    <div style="margin-top:16px;display:flex;gap:12px">
      {_btn("Create Another Context", f"/context/new?ad_id={ad_id}", False)}
      {_btn("Back to Dashboard", "/")}
    </div>
    <p style="color:#8b91a8;font-size:13px;margin-top:12px">Next: Score the ad with this context.</p>
    <form method="POST" action="/run/review/{ad_id}" style="display:inline;margin-top:8px">
      <button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#22c55e;color:white">Run Review Now</button>
    </form>'''

    return _page("Context Saved", html, "context")


@app.route("/performance")
def performance():
    ad_id = request.args.get("ad_id", "")
    wiom_ids = sorted([f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")])
    opts = "".join(f'<option value="{w}" {"selected" if w == ad_id else ""}>{w}</option>' for w in wiom_ids)

    def _metric_field(label, name, placeholder, input_type="number", step=""):
        step_attr = f'step="{step}"' if step else ""
        return f'''<div style="margin-bottom:16px">
          <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">{label}</label>
          <input type="{input_type}" {step_attr} name="{name}" placeholder="{placeholder}">
        </div>'''

    html = f'''<h2>Performance Data</h2>
    <div style="display:flex;gap:12px;margin-bottom:24px">
      {_btn("Pull from Meta API", "/meta/pull")}
      {_btn("Browse Meta Campaigns", "/meta/campaigns", False)}
      <form method="POST" action="/batch/pull" style="display:inline"><button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#22c55e;color:white">Pull All Mapped Ads</button></form>
    </div>
    <h3>Or Enter Manually</h3>
    <p style="color:#8b91a8;margin-bottom:16px">Paste metrics from Meta Ads Manager or YouTube Studio.</p>
    <form method="POST" action="/performance/save">'''

    html += _card(f'''<h3>Campaign Info</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Ad ID</label>
        <select name="ad_id" required>{opts}</select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Days Live</label>
        <input type="number" name="days_live" required placeholder="e.g., 7">
      </div>
    </div>''')

    html += _card(f'''<h3>Metrics</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
      {_metric_field("Impressions *", "impressions", "e.g., 125000")}
      {_metric_field("Reach", "reach", "e.g., 87000")}
      {_metric_field("Video Views", "video_views", "e.g., 45000")}
      {_metric_field("Hook Rate 3s (%)", "hook_rate_3s", "e.g., 28", step="0.1")}
      {_metric_field("Hold Rate 15s (%)", "hold_rate_15s", "e.g., 12", step="0.1")}
      {_metric_field("Completion Rate (%)", "video_completion_rate", "e.g., 8.5", step="0.1")}
      {_metric_field("CTR (%)", "ctr", "e.g., 0.42", step="0.01")}
      {_metric_field("CPC (Rs)", "cpc", "e.g., 4.20", step="0.01")}
      {_metric_field("CPM (Rs)", "cpm", "e.g., 85", step="0.01")}
      {_metric_field("Conversions", "conversions", "e.g., 312")}
      {_metric_field("Spend (Rs)", "spend", "e.g., 10625", step="0.01")}
      {_metric_field("Frequency", "frequency", "e.g., 1.4", step="0.1")}
    </div>''')

    html += '<button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Save Snapshot</button></form>'

    # Show existing snapshots
    snapshots = {}
    for f in sorted(PERFORMANCE_DIR.glob("*_perf_*.json")):
        aid = f.stem.split("_perf_")[0]
        snapshots.setdefault(aid, [])
        with open(f, "r", encoding="utf-8") as fh:
            snapshots[aid].append(json.load(fh))

    if snapshots:
        html += '<h2 style="margin-top:32px">Performance History</h2>'
        for aid, snaps in snapshots.items():
            rows = ""
            for s in snaps:
                m = s["metrics"]
                rows += f'''<tr>
                  <td>Day {s.get("days_live",0)}</td>
                  <td>{m["impressions"]:,}</td>
                  <td>{(m.get("hook_rate_3s") or 0)*100:.1f}%</td>
                  <td>{(m.get("video_completion_rate") or 0)*100:.1f}%</td>
                  <td>{(m.get("ctr") or 0)*100:.2f}%</td>
                  <td>{m.get("cpc") or 0:.2f}</td>
                  <td>{m.get("conversions") or "-"}</td>
                  <td>{m.get("frequency") or 0:.1f}</td>
                </tr>'''

            fatigue_html = ""
            if len(snaps) >= 2:
                fat = detect_fatigue(snaps)
                fc = "green" if fat["status"] == "no_fatigue" else "amber" if fat["status"] in ["early_signs", "fatiguing"] else "red"
                fatigue_html = f'<div style="margin-top:12px">{_chip("Fatigue: " + fat["status"].replace("_"," ").title(), fc)} <span style="font-size:12px;color:#8b91a8;margin-left:8px">{_esc(fat["evidence"])}</span></div>'

            html += _card(f'''<h3>{_esc(aid)} -- {len(snaps)} snapshots</h3>
            <table><tr><th>Day</th><th>Impressions</th><th>Hook 3s</th><th>VCR</th><th>CTR</th><th>CPC</th><th>Conv</th><th>Freq</th></tr>{rows}</table>
            {fatigue_html}''')

    return _page("Performance", html, "performance")


@app.route("/performance/save", methods=["POST"])
def performance_save():
    form = request.form
    ad_id = form["ad_id"]

    ctx = load_campaign_context(ad_id)
    ctx_id = ctx["context_id"] if ctx else "none"

    metrics = {"impressions": int(form.get("impressions", 0))}
    for field in ["reach", "video_views", "conversions"]:
        v = form.get(field)
        metrics[field] = int(v) if v else None
    for field in ["cpc", "cpm", "spend"]:
        v = form.get(field)
        metrics[field] = float(v) if v else None
    for field in ["hook_rate_3s", "hold_rate_15s", "video_completion_rate", "ctr"]:
        v = form.get(field)
        metrics[field] = float(v) / 100.0 if v else None
    v = form.get("frequency")
    metrics["frequency"] = float(v) if v else None

    data = {
        "perf_id": next_perf_id(ad_id),
        "ad_id": ad_id,
        "context_id": ctx_id,
        "snapshot_date": datetime.now().isoformat(),
        "days_live": int(form.get("days_live", 0)),
        "metrics": metrics,
        "platform_data": None,
    }
    save_performance_data(data)
    return redirect(f"/performance?ad_id={ad_id}&toast=Performance+snapshot+saved&toast_type=ok")


@app.route("/history")
def history_page():
    ad_id = request.args.get("ad_id", "")
    wiom_ids = sorted([f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")])

    target_ids = [ad_id] if ad_id else wiom_ids
    all_history = {}
    for wid in target_ids:
        h = {
            "scorecards": load_history(wid, "scorecards"),
            "suggestions": load_history(wid, "suggestions"),
            "optimizations": load_history(wid, "optimizations"),
        }
        if h["scorecards"] or h["suggestions"] or h["optimizations"]:
            all_history[wid] = h

    html = '<h2>Version History</h2><p style="color:#8b91a8;margin-bottom:24px">Every scorecard, suggestion, and optimization is versioned. View past iterations alongside their campaign context.</p>'

    for wid, hist in all_history.items():
        inner = f'<h3>{_esc(wid)}</h3>'

        if hist["scorecards"]:
            inner += f'<h3 style="margin-top:16px;font-size:14px">Scorecards ({len(hist["scorecards"])} versions)</h3>'
            inner += '<div style="border-left:2px solid #2d3148;margin-left:12px;padding-left:24px">'
            for sc in reversed(hist["scorecards"]):
                ba_text = ""
                if sc.get("brief_alignment"):
                    ba_text = f' | Brief: {sc["brief_alignment"]["overall_brief_score"]}/100'
                ctx_text = f' | Context: {sc["context_id"]}' if sc.get("context_id") else ""
                inner += f'''<div style="margin-bottom:20px;position:relative">
                  <div style="width:10px;height:10px;background:#6366f1;border-radius:50%;position:absolute;left:-30px;top:4px"></div>
                  <div style="font-size:11px;color:#8b91a8">{_esc(sc.get("_history_file",""))}</div>
                  <div style="font-size:13px;margin-top:4px">Score: <strong>{sc.get("overall_score","?")}/100</strong> | Objective: {sc.get("campaign_objective","default")}{ctx_text}{ba_text}</div>
                </div>'''
            inner += '</div>'

        if hist["suggestions"]:
            inner += f'<h3 style="margin-top:16px;font-size:14px">Suggestions ({len(hist["suggestions"])} versions)</h3>'
            inner += '<div style="border-left:2px solid #2d3148;margin-left:12px;padding-left:24px">'
            for sug in reversed(hist["suggestions"]):
                inner += f'''<div style="margin-bottom:20px;position:relative">
                  <div style="width:10px;height:10px;background:#6366f1;border-radius:50%;position:absolute;left:-30px;top:4px"></div>
                  <div style="font-size:11px;color:#8b91a8">{_esc(sug.get("_history_file",""))}</div>
                  <div style="font-size:13px;margin-top:4px">{len(sug.get("suggestions",[]))} suggestions | Score: {sug.get("overall_score","?")}/100</div>
                </div>'''
            inner += '</div>'

        if hist["optimizations"]:
            inner += f'<h3 style="margin-top:16px;font-size:14px">Optimizations ({len(hist["optimizations"])} versions)</h3>'
            inner += '<div style="border-left:2px solid #2d3148;margin-left:12px;padding-left:24px">'
            for opt in reversed(hist["optimizations"]):
                fs = opt.get("fatigue_assessment", {}).get("status", "unknown")
                fc = "green" if fs == "no_fatigue" else "amber" if fs in ["early_signs", "fatiguing"] else "red"
                inner += f'''<div style="margin-bottom:20px;position:relative">
                  <div style="width:10px;height:10px;background:#6366f1;border-radius:50%;position:absolute;left:-30px;top:4px"></div>
                  <div style="font-size:11px;color:#8b91a8">{_esc(opt.get("_history_file", opt.get("opt_id","")))}</div>
                  <div style="font-size:13px;margin-top:4px">{_chip("Fatigue: " + fs.replace("_"," "), fc)} | {len(opt.get("recommendations",[]))} recommendations</div>
                </div>'''
            inner += '</div>'

        html += _card(inner)

    if not all_history:
        html += _card('<div style="text-align:center;padding:48px;color:#8b91a8"><h3 style="color:#e4e7f0;margin-bottom:8px">No history yet</h3><p>Scorecards, suggestions, and optimizations appear here after they are generated.</p></div>')

    return _page("History", html, "history")


# ---------------------------------------------------------------------------
# Action Routes — Run pipeline steps from the browser
# ---------------------------------------------------------------------------

@app.route("/run/full/<ad_id>", methods=["POST"])
def run_full_pipeline(ad_id):
    """Run full pipeline: deconstruct (if needed) → review → suggest."""
    from llm import run_deconstruct, run_review, run_suggest

    steps = []

    # Step 1: Deconstruct if needed
    has_decon = (WIOM_DIR / f"{ad_id}_decon.json").exists()
    if not has_decon:
        try:
            decon, msg = run_deconstruct(ad_id)
            steps.append(("Deconstruct", decon is not None, msg))
            if decon is None:
                # Deconstruct failed — can't review without it, show error clearly
                return _render_pipeline_result(ad_id, steps, None, None)
        except Exception as e:
            steps.append(("Deconstruct", False, str(e)))
            return _render_pipeline_result(ad_id, steps, None, None)
    else:
        steps.append(("Deconstruct", True, "Already deconstructed ✓"))

    # Step 2: Review
    scorecard = None
    try:
        scorecard, msg = run_review(ad_id)
        steps.append(("Review", scorecard is not None, msg))
    except Exception as e:
        steps.append(("Review", False, str(e)))

    # Step 3: Suggest (only if review succeeded)
    suggestions = None
    if scorecard:
        try:
            suggestions, msg = run_suggest(ad_id)
            steps.append(("Suggest", suggestions is not None, msg))
        except Exception as e:
            steps.append(("Suggest", False, str(e)))

    return _render_pipeline_result(ad_id, steps, scorecard, suggestions)


def _render_pipeline_result(ad_id, steps, scorecard, suggestions):
    """Render the full pipeline results page."""
    html = f'<h2>{_esc(_ad_name(ad_id))}</h2>'

    # Steps summary — hide Deconstruct (background step), only show Review + Suggest
    visible_steps = [(name, ok, msg) for name, ok, msg in steps if name != "Deconstruct"]
    # If deconstruct failed, surface that as the error instead
    decon_step = next(((name, ok, msg) for name, ok, msg in steps if name == "Deconstruct"), None)
    if decon_step and not decon_step[1]:
        html += f'<div style="background:#ef444418;border:1px solid #ef444440;border-radius:8px;padding:12px 16px;margin-bottom:20px;font-size:13px;color:#ef4444">Analysis failed: {_esc(decon_step[2])}</div>'
    steps_html = '<div style="display:flex;gap:8px;margin-bottom:24px;align-items:center">'
    for i, (name, ok, msg) in enumerate(visible_steps):
        c = "#22c55e" if ok else "#ef4444"
        icon = "✓" if ok else "✗"
        steps_html += f'<div style="padding:6px 14px;border-radius:20px;font-size:12px;font-weight:500;background:{c}22;color:{c};border:1px solid {c}44">{icon} {name}</div>'
        if i < len(visible_steps) - 1:
            steps_html += '<span style="color:#2d3148">→</span>'
    steps_html += '</div>'
    html += steps_html

    if scorecard:
        # Score gauge + dimensions
        dims = "".join(_bar_row(_dim_label(dn), dd["score"]) for dn, dd in scorecard.get("dimensions", {}).items())

        ba_html = ""
        ba = scorecard.get("brief_alignment")
        if ba:
            ba_html = f'<div class="sep"></div><h3>Brief Alignment: {ba["overall_brief_score"]}/100</h3>'
            ba_html += "".join(_bar_row(_dim_label(bk), ba[bk]) for bk in ["audience_match", "message_delivery", "tone_match", "usp_clarity", "desired_action_driven"])

        strengths = "".join(f'<div style="font-size:13px;color:#22c55e;margin-top:4px">+ {_esc(s)}</div>' for s in scorecard.get("strengths", []))
        gaps = "".join(f'<div style="font-size:13px;color:#f59e0b;margin-top:4px">→ {_esc(g["description"])}</div>' for g in scorecard.get("priority_gaps", []))

        obj = scorecard.get("campaign_objective", "default")
        html += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center">
          <div>{_chip(_format_label(obj), "blue")} {_chip(f"v{scorecard.get('version',1)}", "amber")}</div>
          {_gauge(scorecard.get("overall_score", 0))}
        </div>
        <div style="margin-top:16px">{dims}</div>
        {ba_html}
        <div class="sep"></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
          <div><h3 style="font-size:14px;color:#22c55e;margin-bottom:8px">Strengths</h3>{strengths}</div>
          <div><h3 style="font-size:14px;color:#f59e0b;margin-bottom:8px">Priority Gaps</h3>{gaps}</div>
        </div>''')

    if suggestions:
        sug_items = ""
        for s in suggestions.get("suggestions", []):
            pc = "red" if s["priority"] == "high" else "amber" if s["priority"] == "medium" else "green"
            sug_items += f'''<div style="padding:14px;background:#242836;border-radius:8px;margin-bottom:8px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <strong style="font-size:13px">{_esc(_dim_label(s.get("dimension","")))}</strong>
                {_chip(s["priority"], pc)}
              </div>
              <p style="font-size:13px;color:#818cf8">{_esc(s.get("suggested_change",""))}</p>
              <p style="font-size:12px;color:#8b91a8;margin-top:4px">{_esc(s.get("why_it_works",""))}</p>
            </div>'''

        keeps = "".join(f'<span style="font-size:12px;color:#22c55e;margin-right:12px">✓ {_esc(k)}</span>' for k in suggestions.get("keep", [])[:3])
        html += _card(f'<h3>Suggestions</h3><div style="margin-top:12px">{sug_items}</div>{"<div class=sep></div><div>" + keeps + "</div>" if keeps else ""}')

    html += f'<div style="margin-top:16px;display:flex;gap:8px">'
    if scorecard:
        html += f'<form method="POST" action="/run/optimize/{ad_id}" style="display:inline"><button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#22c55e;color:white">Optimize Campaign</button></form>'
    html += f'{_btn("Back to Ads", "/wiom", False)} {_btn("Compare Versions", f"/compare/{ad_id}", False)}</div>'

    return _page("Review Complete", html, "wiom")


@app.route("/run/deconstruct/<ad_id>", methods=["POST"])
def run_deconstruct_action(ad_id):
    """Run Agent D (deconstruct) for a Wiom ad via Groq LLM."""
    try:
        from llm import run_deconstruct
        decon, msg = run_deconstruct(ad_id)
        if decon:
            html = f'<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">{_esc(msg)}</div>'

            def _decon_row(label, value):
                return f'<tr><td style="color:#8b91a8;font-size:12px;width:180px">{_esc(label)}</td><td style="font-size:13px">{_esc(str(value))}</td></tr>'

            rows = ""
            h = decon.get("hook", {})
            rows += _decon_row("Hook Type", h.get("type", ""))
            rows += _decon_row("Audio Hook", h.get("audio_hook", ""))
            rows += _decon_row("Hook Note", h.get("effectiveness_note", ""))
            n = decon.get("narrative", {})
            rows += _decon_row("Narrative Arc", n.get("arc_type", ""))
            rows += _decon_row("Scenes", n.get("num_scenes", ""))
            p = decon.get("pacing", {})
            rows += _decon_row("Duration", p.get("duration_bucket", ""))
            rows += _decon_row("Cuts/15s", p.get("cuts_per_15s", ""))
            v = decon.get("visual", {})
            rows += _decon_row("Production", v.get("production_quality", ""))
            rows += _decon_row("Talent", v.get("talent_type", ""))
            e = decon.get("emotional", {})
            rows += _decon_row("Primary Emotion", e.get("primary_emotion", ""))
            rows += _decon_row("Language Mix", e.get("hinglish_level", ""))

            html += _card(f'''<h3>{_esc(_ad_name(ad_id))} — Deconstruction</h3>
              <table style="margin-top:12px">{rows}</table>
              <div class="sep"></div>
              <h3 style="font-size:14px;color:#818cf8">X-Factor</h3>
              <p style="font-size:13px;margin-top:6px">{_esc(decon.get("x_factor",""))}</p>
              <div class="sep"></div>
              <h3 style="font-size:14px;color:#22c55e">Lessons for Wiom</h3>
              {"".join(f'<div style="font-size:13px;margin-top:6px">• {_esc(l)}</div>' for l in decon.get("lessons_for_wiom",[]))}''')

            html += f'''<div style="margin-top:16px;display:flex;gap:8px">
              <form method="POST" action="/run/review/{ad_id}" style="display:inline">
                <button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Run Review Now</button>
              </form>
              {_btn("Back to Ads", "/wiom", False)}
            </div>'''
        else:
            html = _card(f'<div style="color:#ef4444">Deconstruct failed: {_esc(msg)}</div><div style="margin-top:12px">{_btn("Back", "/wiom")}</div>')
    except Exception as e:
        html = _card(f'<div style="color:#ef4444">Error: {_esc(str(e))}</div><div style="margin-top:12px">{_btn("Back", "/wiom")}</div>')

    return _page("Deconstruction", html, "wiom")


@app.route("/run/review/<ad_id>", methods=["POST"])
def run_review_action(ad_id):
    """Run the review agent (Groq LLM) for a Wiom ad."""
    try:
        from llm import run_review
        scorecard, msg = run_review(ad_id)
        if scorecard:
            html = f'''<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">{_esc(msg)}</div>'''
            # Show scorecard summary
            dims = ""
            for dn, dd in scorecard.get("dimensions", {}).items():
                dims += _bar_row(_dim_label(dn), dd["score"])

            ba_html = ""
            ba = scorecard.get("brief_alignment")
            if ba:
                ba_html = '<div class="sep"></div>'
                ba_html += f'<h3>Brief Alignment: {ba["overall_brief_score"]}/100</h3>'
                for bk in ["audience_match", "message_delivery", "tone_match", "usp_clarity", "desired_action_driven"]:
                    ba_html += _bar_row(_dim_label(bk), ba[bk])

            strengths = "".join(f'<div style="font-size:13px;color:#22c55e;margin-top:4px">+ {_esc(s)}</div>' for s in scorecard.get("strengths", []))
            gaps = "".join(f'<div style="font-size:13px;color:#f59e0b;margin-top:4px">- {_esc(g["description"])}</div>' for g in scorecard.get("priority_gaps", []))

            html += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center">
              <h3>{_esc(ad_id)} -- Scorecard v{scorecard.get("version",1)}</h3>
              {_gauge(scorecard.get("overall_score", 0))}
            </div>
            <div style="margin-top:16px">{dims}</div>
            {ba_html}
            <div class="sep"></div>
            <h3 style="font-size:14px">Strengths</h3>{strengths}
            <div class="sep"></div>
            <h3 style="font-size:14px">Priority Gaps</h3>{gaps}
            <div class="sep"></div>
            <div style="display:flex;gap:8px">
              <form method="POST" action="/run/suggest/{ad_id}" style="display:inline">
                <button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Generate Suggestions</button>
              </form>
              {_btn("Back to Dashboard", "/")}
            </div>''')
        else:
            html = _card(f'<div style="color:#ef4444">Review failed: {_esc(msg)}</div><div style="margin-top:12px">{_btn("Back", "/")}</div>')
    except Exception as e:
        html = _card(f'<div style="color:#ef4444">Error: {_esc(str(e))}</div><div style="margin-top:12px">{_btn("Back", "/")}</div>')

    return _page("Review Result", html, "wiom")


@app.route("/run/suggest/<ad_id>", methods=["POST"])
def run_suggest_action(ad_id):
    """Run the suggest agent (Groq LLM) for a scored Wiom ad."""
    try:
        from llm import run_suggest
        suggestions, msg = run_suggest(ad_id)
        if suggestions:
            html = f'''<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">{_esc(msg)}</div>'''

            items = ""
            for s in suggestions.get("suggestions", []):
                pc = "red" if s["priority"] == "high" else "amber" if s["priority"] == "medium" else "green"
                items += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                  <strong>{_esc(_dim_label(s.get("dimension","")))}</strong>
                  {_chip(s["priority"], pc)} {_chip(s.get("affects_metric",""), "blue")}
                </div>
                <p style="font-size:13px;margin-top:8px"><strong>Current:</strong> {_esc(s.get("current",""))}</p>
                <p style="font-size:13px;margin-top:4px"><strong>Pattern says:</strong> {_esc(s.get("pattern_says",""))}</p>
                <p style="font-size:13px;margin-top:4px;color:#818cf8"><strong>Suggested:</strong> {_esc(s.get("suggested_change",""))}</p>
                <p style="font-size:12px;color:#8b91a8;margin-top:4px"><em>Why: {_esc(s.get("why_it_works",""))}</em></p>
                <p style="font-size:12px;color:#8b91a8;margin-top:4px">Ref: {_esc(s.get("reference_ad_id",""))} -- {_esc(s.get("reference_note",""))}</p>
                ''', "padding:16px;margin-bottom:12px")

            keeps = "".join(f'<div style="font-size:13px;color:#22c55e;margin-top:4px">+ {_esc(k)}</div>' for k in suggestions.get("keep", []))
            coherence = _esc(suggestions.get("coherence_check", ""))

            html += f'<h2>Suggestions for {_esc(ad_id)}</h2>{items}'
            if keeps:
                html += _card(f'<h3 style="color:#22c55e">Keep These</h3>{keeps}')
            html += _card(f'<h3>Coherence Check</h3><p style="font-size:13px">{coherence}</p>')
            html += f'<div style="margin-top:16px">{_btn("Back to Dashboard", "/")}</div>'
        else:
            html = _card(f'<div style="color:#ef4444">Suggest failed: {_esc(msg)}</div><div style="margin-top:12px">{_btn("Back", "/")}</div>')
    except Exception as e:
        html = _card(f'<div style="color:#ef4444">Error: {_esc(str(e))}</div><div style="margin-top:12px">{_btn("Back", "/")}</div>')

    return _page("Suggestions", html, "wiom")


@app.route("/run/optimize/<ad_id>", methods=["POST"])
def run_optimize_action(ad_id):
    """Run the optimize agent (Groq LLM) for a live campaign."""
    try:
        from llm import run_optimize
        optimization, msg = run_optimize(ad_id)
        if optimization:
            html = f'''<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">{_esc(msg)}</div>'''

            # Performance summary
            ps = optimization.get("performance_summary", {})
            html += _card(f'''<h3>Performance Summary</h3>
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:12px">
                {_stat(ps.get("days_live",0), "Days Live")}
                {_stat(f'{ps.get("total_impressions",0):,}', "Impressions")}
                {_chip(ps.get("trend","?"), "green" if ps.get("trend")=="improving" else "amber" if ps.get("trend")=="stable" else "red")}
                {_chip(f'Accuracy: {ps.get("prediction_accuracy","?")}', "blue")}
              </div>''')

            # Fatigue
            fa = optimization.get("fatigue_assessment", {})
            fc = "green" if fa.get("status") == "no_fatigue" else "amber" if fa.get("status") in ["early_signs", "fatiguing"] else "red"
            html += _card(f'<h3>Fatigue Assessment</h3>{_chip(fa.get("status","?").replace("_"," ").title(), fc)} <span style="font-size:13px;color:#8b91a8;margin-left:8px">{_esc(fa.get("evidence",""))}</span>')

            # Scorecard comparison
            sc_comp = optimization.get("scorecard_comparison", {})
            comp_rows = ""
            for dim, check in sc_comp.items():
                if isinstance(check, dict):
                    vc = "green" if check.get("verdict") == "confirmed" else "amber" if check.get("verdict") == "partially_confirmed" else "red" if check.get("verdict") == "contradicted" else "blue"
                    comp_rows += f'<tr><td>{_dim_label(dim)}</td><td>{check.get("scorecard_score","?")}/5</td><td>{_esc(check.get("actual_signal",""))}</td><td>{_chip(check.get("verdict","?"), vc)}</td></tr>'
            if comp_rows:
                html += _card(f'<h3>Scorecard vs Reality</h3><table><tr><th>Dimension</th><th>Score</th><th>Actual Signal</th><th>Verdict</th></tr>{comp_rows}</table>')

            # Recommendations
            recs = ""
            for r in optimization.get("recommendations", []):
                pc = "red" if r["priority"] == "immediate" else "amber" if r["priority"] == "this_week" else "green"
                recs += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                  {_chip(r["type"], "blue")} {_chip(r["priority"], pc)}
                  {_chip("Needs Approval", "amber") if r.get("requires_human_approval") else ""}
                </div>
                <p style="font-size:13px;margin-top:8px"><strong>{_esc(r.get("action",""))}</strong></p>
                <p style="font-size:12px;color:#8b91a8;margin-top:4px">{_esc(r.get("rationale",""))}</p>''', "padding:16px;margin-bottom:8px")
            html += f'<h3>Recommendations</h3>{recs}'
            html += f'<div style="margin-top:16px">{_btn("Back to Dashboard", "/")}</div>'
        else:
            html = _card(f'<div style="color:#ef4444">Optimize failed: {_esc(msg)}</div><div style="margin-top:12px">{_btn("Back", "/")}</div>')
    except Exception as e:
        html = _card(f'<div style="color:#ef4444">Error: {_esc(str(e))}</div><div style="margin-top:12px">{_btn("Back", "/")}</div>')

    return _page("Optimization", html, "performance")


# ---------------------------------------------------------------------------
# Meta API Pull Routes
# ---------------------------------------------------------------------------

@app.route("/meta/campaigns")
def meta_campaigns():
    """List Meta ad campaigns."""
    try:
        from meta_pull import list_campaigns
        campaigns = list_campaigns()
        rows = "".join(f'''<tr>
          <td><code>{c["id"]}</code></td>
          <td>{_esc(c.get("name",""))}</td>
          <td>{_chip(c.get("status",""), "green" if c.get("status")=="ACTIVE" else "amber")}</td>
          <td>{_esc(c.get("objective",""))}</td>
        </tr>''' for c in campaigns)
        html = f'''<h2>Meta Campaigns</h2>
        <p style="color:#8b91a8;margin-bottom:16px">Campaigns from your Meta ad account. Copy the campaign ID to link it to a CUE ad.</p>
        <table><tr><th>Campaign ID</th><th>Name</th><th>Status</th><th>Objective</th></tr>{rows}</table>
        <div style="margin-top:16px">{_btn("Back", "/performance", False)}</div>'''
    except EnvironmentError as e:
        html = _card(f'''<h3>Meta API Not Configured</h3>
        <p style="color:#ef4444;margin-top:8px">{_esc(str(e))}</p>
        <p style="color:#8b91a8;margin-top:12px">Add these keys to <code>C:\\credentials\\.env</code>:</p>
        <pre style="background:#242836;padding:12px;border-radius:6px;margin-top:8px;font-size:12px">META_ACCESS_TOKEN=your_token_here
META_AD_ACCOUNT_ID=act_XXXXX</pre>''')
    except Exception as e:
        html = _card(f'<div style="color:#ef4444">Error: {_esc(str(e))}</div>')
    return _page("Meta Campaigns", html, "performance")


@app.route("/meta/pull", methods=["GET", "POST"])
def meta_pull_page():
    """Pull performance data from Meta API."""
    wiom_ids = sorted([f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")])
    opts = "".join(f'<option value="{w}">{w}</option>' for w in wiom_ids)

    if request.method == "POST":
        ad_id = request.form["ad_id"]
        meta_ad_id = request.form["meta_ad_id"]
        date_preset = request.form.get("date_preset", "last_7d")
        try:
            from meta_pull import pull_and_save
            ctx = load_campaign_context(ad_id)
            results = pull_and_save(ad_id, meta_ad_id, context_id=ctx["context_id"] if ctx else "none", date_preset=date_preset)
            success = sum(1 for ok, _ in results if ok)
            html = f'''<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">
              Pulled {success}/{len(results)} daily snapshots from Meta for {ad_id}
            </div>'''
            for ok, msg in results:
                color = "#22c55e" if ok else "#ef4444"
                html += f'<div style="font-size:12px;color:{color};margin-bottom:4px">{"OK" if ok else "FAIL"}: {_esc(msg)}</div>'
            html += f'<div style="margin-top:16px">{_btn("View Performance", f"/performance?ad_id={ad_id}")} {_btn("Pull More", "/meta/pull", False)}</div>'
            return _page("Meta Pull Results", html, "performance")
        except EnvironmentError as e:
            html = _card(f'<div style="color:#ef4444">{_esc(str(e))}</div>')
            return _page("Meta Pull Error", html, "performance")
        except Exception as e:
            html = _card(f'<div style="color:#ef4444">Error: {_esc(str(e))}</div>')
            return _page("Meta Pull Error", html, "performance")

    # Pre-fill from query params (when clicking "Pull" from mapping page)
    prefill_ad = request.args.get("ad_id", "")
    prefill_meta = request.args.get("meta_ad_id", "")

    # Re-render opts with pre-selection
    opts = "".join(f'<option value="{w}" {"selected" if w == prefill_ad else ""}>{w}</option>' for w in wiom_ids)

    html = f'''<h2>Pull from Meta Ads</h2>
    <p style="color:#8b91a8;margin-bottom:24px">Auto-fetch performance data from Meta Marketing API. Read-only, safe per ads-api-safety.md.</p>
    <form method="POST" action="/meta/pull">
    {_card(f"""<h3>Link Meta Ad to CUE Ad</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">CUE Ad ID</label>
        <select name="ad_id" required>{opts}</select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Meta Ad ID</label>
        <input type="text" name="meta_ad_id" required placeholder="e.g., 23851234567890" value="{_esc(prefill_meta)}">
        <p style="font-size:11px;color:#8b91a8;margin-top:4px">Find this in Meta Ads Manager > Ad level > ID column</p>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Date Range</label>
        <select name="date_preset">
          <option value="last_7d">Last 7 days</option>
          <option value="last_14d">Last 14 days</option>
          <option value="last_30d">Last 30 days</option>
          <option value="this_month">This month</option>
          <option value="last_month">Last month</option>
        </select>
      </div>
    </div>""")}
    <div style="display:flex;gap:12px">
      <button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Pull Performance Data</button>
      {_btn("Browse Campaigns", "/meta/campaigns", False)}
      {_btn("Cancel", "/performance", False)}
    </div>
    </form>'''
    return _page("Pull from Meta", html, "performance")


# ---------------------------------------------------------------------------
# Ad Management: Archive / Delete
# ---------------------------------------------------------------------------

@app.route("/wiom/<ad_id>/archive", methods=["POST"])
def wiom_archive(ad_id):
    """Toggle archived status on a Wiom ad. Archived ads are hidden from main view."""
    meta_path = WIOM_DIR / f"{ad_id}.json"
    if not meta_path.exists():
        return redirect("/wiom")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta["archived"] = not meta.get("archived", False)
    meta["archived_at"] = datetime.now().isoformat() if meta["archived"] else None
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    action = "Archived" if meta["archived"] else "Unarchived"
    return redirect(f"/wiom?toast={action}+{ad_id}")


@app.route("/wiom/<ad_id>/delete", methods=["POST"])
def wiom_delete(ad_id):
    """Delete a Wiom ad and all associated data (scorecard, suggestions, decon, frames)."""
    import shutil
    # Safety: only delete wiom_ IDs
    if not ad_id.startswith("wiom_"):
        return redirect("/wiom")

    # Delete metadata + deconstruction
    for suffix in ["", "_decon"]:
        p = WIOM_DIR / f"{ad_id}{suffix}.json"
        if p.exists():
            p.unlink()

    # Delete frames directory
    frames_dir = ROOT / "wiom-ads" / "frames" / ad_id
    if frames_dir.exists():
        shutil.rmtree(frames_dir, ignore_errors=True)

    # Delete scorecard, suggestions
    for d, suf in [(SCORECARDS_DIR, "_scorecard"), (SUGGESTIONS_DIR, "_suggestions")]:
        p = d / f"{ad_id}{suf}.json"
        if p.exists():
            p.unlink()

    # Delete optimizations
    for p in OPTIMIZATIONS_DIR.glob(f"{ad_id}_opt_*.json"):
        p.unlink()

    # Delete contexts
    for p in CONTEXTS_DIR.glob(f"{ad_id}_ctx*.json"):
        p.unlink()

    # Delete performance snapshots
    for p in PERFORMANCE_DIR.glob(f"{ad_id}_perf_*.json"):
        p.unlink()

    # Delete history
    hist_dir = HISTORY_DIR / ad_id
    if hist_dir.exists():
        shutil.rmtree(hist_dir, ignore_errors=True)

    return redirect(f"/wiom?toast={ad_id}+deleted&toast_type=warn")


# ---------------------------------------------------------------------------
# Video Upload + Auto-Deconstruct
# ---------------------------------------------------------------------------

@app.route("/wiom/upload", methods=["GET", "POST"])
def wiom_upload():
    """Upload a video file to create a new Wiom ad."""
    if request.method == "POST":
        file = request.files.get("video")
        if not file or not file.filename:
            return _page("Upload Error", _card('<div style="color:#ef4444">No file selected.</div>'), "upload")

        # Save upload
        safe_name = file.filename.replace(" ", "_")
        upload_path = UPLOADS_DIR / safe_name
        file.save(str(upload_path))

        campaign = request.form.get("campaign", "").strip()
        description = request.form.get("description", "").strip()
        language = request.form.get("language", "Hindi")
        platform = request.form.get("platform", "Meta")
        tags_raw = request.form.get("tags", "")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        try:
            from video_ingest import create_wiom_ad
            ad_id, metadata, frames, msg = create_wiom_ad(
                str(upload_path), "Wiom", campaign, description,
                language=language, tags=tags, platform=platform,
            )
            if ad_id:
                html = f'''<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">{_esc(msg)}</div>'''
                html += _card(f'''<h3>{_esc(ad_id)}: {_esc(campaign)}</h3>
                  <p style="font-size:13px;color:#8b91a8">{_esc(description)}</p>
                  <div style="margin-top:12px">{_chip(platform, "blue")} {_chip(language, "blue")} {_chip(f"{metadata.get('duration_seconds',0)}s", "amber")}</div>
                  <div style="margin-top:12px;font-size:12px;color:#8b91a8">{len(frames)} frames extracted</div>''')
                html += f'''<div style="margin-top:16px;display:flex;gap:8px">
                  {_btn("Set Context", f"/context/new?ad_id={ad_id}")}
                  {_btn("Upload Another", "/wiom/upload", False)}
                  {_btn("View All Ads", "/wiom", False)}
                </div>'''
                return _page("Upload Complete", html, "upload")
            else:
                return _page("Upload Error", _card(f'<div style="color:#ef4444">{_esc(msg)}</div>'), "upload")
        except Exception as e:
            return _page("Upload Error", _card(f'<div style="color:#ef4444">Error: {_esc(str(e))}</div>'), "upload")

    html = '''<h2>Upload Wiom Ad</h2>
    <p style="color:#8b91a8;margin-bottom:24px">Upload a video file to create a new ad entry. Frames will be extracted automatically using ffmpeg.</p>
    <form method="POST" action="/wiom/upload" enctype="multipart/form-data">'''

    html += _card(f'''<h3>Video File</h3>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Video File (MP4, MOV, AVI)</label>
      <input type="file" name="video" accept="video/*" required style="padding:8px">
    </div>''')

    html += _card(f'''<h3>Ad Details</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Campaign Name *</label>
        <input type="text" name="campaign" required placeholder="e.g., GAON 2.0">
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Language</label>
        <select name="language">
          <option value="Hindi">Hindi</option>
          <option value="English">English</option>
          <option value="Tamil">Tamil</option>
          <option value="Telugu">Telugu</option>
          <option value="Marathi">Marathi</option>
          <option value="Bengali">Bengali</option>
          <option value="Multilingual">Multilingual</option>
        </select>
      </div>
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Description *</label>
      <textarea name="description" required placeholder="Describe the ad -- setting, narrative, key message, style"></textarea>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Platform</label>
        <select name="platform">
          <option value="Meta">Meta</option>
          <option value="YouTube">YouTube</option>
          <option value="Instagram">Instagram</option>
          <option value="Multi-platform">Multi-platform</option>
        </select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Tags (comma-separated)</label>
        <input type="text" name="tags" placeholder="e.g., family, hindi, narrative, tier-2-3">
      </div>
    </div>''')

    html += '''<button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Upload & Extract Frames</button>
    </form>'''

    return _page("Upload Ad", html, "upload")


# ---------------------------------------------------------------------------
# Campaign ID Mapping
# ---------------------------------------------------------------------------

@app.route("/campaign/map", methods=["GET", "POST"])
def campaign_map():
    """Map CUE ad IDs to Meta/YouTube campaign IDs."""
    wiom_ids = sorted([f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")])

    if request.method == "POST":
        ad_id = request.form["ad_id"]
        platform = request.form.get("platform", "meta")
        data = {
            "ad_id": ad_id,
            "platform": platform,
            "meta_ad_id": request.form.get("meta_ad_id", "").strip() or None,
            "meta_campaign_id": request.form.get("meta_campaign_id", "").strip() or None,
            "meta_adset_id": request.form.get("meta_adset_id", "").strip() or None,
            "youtube_video_id": request.form.get("youtube_video_id", "").strip() or None,
            "created_at": datetime.now().isoformat(),
            "notes": request.form.get("notes", "").strip() or None,
        }
        ok, msg = save_campaign_mapping(data)

        html = f'''<div style="padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px;background:#22c55e18;border:1px solid #22c55e40;color:#22c55e">{_esc(msg)}</div>'''
        if platform == "meta" and data.get("meta_ad_id"):
            html += f'''<div style="margin-top:12px">{_btn("Pull Performance Now", f"/meta/pull?ad_id={ad_id}&meta_ad_id={data['meta_ad_id']}")} {_btn("Map Another", "/campaign/map", False)}</div>'''
        else:
            html += f'<div style="margin-top:12px">{_btn("Map Another", "/campaign/map", False)} {_btn("Back", "/wiom", False)}</div>'
        return _page("Mapping Saved", html, "mapping")

    opts = "".join(f'<option value="{w}">{_esc(_ad_name(w))} ({w})</option>' for w in wiom_ids)

    html = '''<h2>Campaign ID Mapping</h2>
    <p style="color:#8b91a8;margin-bottom:24px">Link CUE ads to Meta or YouTube campaign IDs. Once mapped, you can auto-pull performance data.</p>
    <form method="POST" action="/campaign/map">'''

    html += _card(f'''<h3>Map Ad to Platform</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">CUE Ad</label>
        <select name="ad_id" required>{opts}</select>
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Platform</label>
        <select name="platform"><option value="meta">Meta</option><option value="youtube">YouTube</option></select>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Meta Ad ID</label>
        <input type="text" name="meta_ad_id" placeholder="e.g., 23851234567890">
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Meta Campaign ID</label>
        <input type="text" name="meta_campaign_id" placeholder="e.g., 23851234567890">
      </div>
      <div style="margin-bottom:16px">
        <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Meta Ad Set ID</label>
        <input type="text" name="meta_adset_id" placeholder="Optional">
      </div>
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">YouTube Video ID (if YouTube)</label>
      <input type="text" name="youtube_video_id" placeholder="e.g., dQw4w9WgXcQ">
    </div>
    <div style="margin-bottom:16px">
      <label style="display:block;font-size:12px;color:#8b91a8;margin-bottom:6px;text-transform:uppercase">Notes</label>
      <input type="text" name="notes" placeholder="e.g., Main ad variant, A/B test version B">
    </div>''')

    html += '''<button type="submit" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Save Mapping</button>
    </form>'''

    # Show existing mappings
    mappings = load_all_mappings()
    if mappings:
        rows = ""
        for m in mappings:
            pid = m.get("meta_ad_id") or m.get("youtube_video_id") or "-"
            rows += f'''<tr>
              <td>{_esc(_ad_name(m["ad_id"]))}</td>
              <td>{_chip(m["platform"], "blue")}</td>
              <td><code>{_esc(pid)}</code></td>
              <td>{_esc(m.get("notes","") or "")}</td>
              <td>{_btn("Pull", f"/meta/pull?ad_id={m['ad_id']}&meta_ad_id={m.get('meta_ad_id','')}", True, True) if m.get("meta_ad_id") else ""}</td>
            </tr>'''
        html += f'<h3 style="margin-top:32px">Existing Mappings</h3><table><tr><th>Ad</th><th>Platform</th><th>Platform ID</th><th>Notes</th><th>Action</th></tr>{rows}</table>'

    return _page("Campaign Mapping", html, "mapping")


# ---------------------------------------------------------------------------
# Version Comparison
# ---------------------------------------------------------------------------

@app.route("/compare")
@app.route("/compare/<ad_id>")
def compare_versions(ad_id=None):
    """Side-by-side comparison of scorecard versions."""
    wiom_ids = sorted([f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")])

    if not ad_id:
        # Show ad picker
        html = '<h2>Compare Versions</h2><p style="color:#8b91a8;margin-bottom:24px">Select an ad to compare scorecard versions side-by-side.</p>'
        for wid in wiom_ids:
            sc_count = len(load_history(wid, "scorecards"))
            if sc_count == 0 and (SCORECARDS_DIR / f"{wid}_scorecard.json").exists():
                sc_count = 1
            if sc_count > 0:
                html += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center">
                  <div><h3 style="margin-bottom:4px">{_esc(_ad_name(wid))}</h3><span style="font-size:12px;color:#8b91a8">{sc_count} scorecard version{"s" if sc_count != 1 else ""}</span></div>
                  {_btn("Compare", f"/compare/{wid}", sc_count >= 2, True)}
                </div>''', "padding:16px;margin-bottom:8px")
        if not any(len(load_history(w, "scorecards")) > 0 for w in wiom_ids):
            html += _card('<div style="text-align:center;padding:48px;color:#8b91a8">No scorecards yet. Run a review first.</div>')
        return _page("Compare", html, "compare")

    # Show side-by-side comparison
    scorecards = load_history(ad_id, "scorecards")
    # Fall back to current scorecard if no versioned history exists
    if not scorecards:
        sc_path = SCORECARDS_DIR / f"{ad_id}_scorecard.json"
        if sc_path.exists():
            with open(sc_path, "r", encoding="utf-8") as f:
                scorecards = [json.load(f)]
    if len(scorecards) < 1:
        return _page("Compare", _card(f'<div style="color:#8b91a8">No scorecards for {ad_id}. Run a review first.</div><div style="margin-top:12px"><form method="POST" action="/run/review/{ad_id}" style="display:inline"><button type="submit" style="padding:8px 16px;border-radius:6px;font-size:13px;cursor:pointer;border:none;background:#6366f1;color:white">Run Review</button></form></div>'), "compare")

    html = f'<h2>Version Comparison: {_esc(_ad_name(ad_id))}</h2>'

    # Score trend chart
    if len(scorecards) >= 2:
        trend_points = []
        max_score = max(sc.get("overall_score", 0) for sc in scorecards)
        for i, sc in enumerate(scorecards):
            score = sc.get("overall_score", 0)
            x_pct = (i / max(len(scorecards) - 1, 1)) * 100
            y_pct = 100 - (score / max(max_score * 1.1, 1)) * 100
            trend_points.append(f"{x_pct}%,{y_pct}%")

        dots = ""
        for i, sc in enumerate(scorecards):
            score = sc.get("overall_score", 0)
            x_pct = (i / max(len(scorecards) - 1, 1)) * 100
            y_pct = 100 - (score / max(max_score * 1.1, 1)) * 100
            dots += f'<div style="position:absolute;left:{x_pct}%;top:{y_pct}%;transform:translate(-50%,-50%);width:10px;height:10px;background:#6366f1;border-radius:50%;z-index:2" title="v{sc.get("version",i+1)}: {score}/100"></div>'
            dots += f'<div style="position:absolute;left:{x_pct}%;top:calc({y_pct}% + 14px);transform:translateX(-50%);font-size:10px;color:#8b91a8;z-index:2">v{sc.get("version",i+1)}: {score}</div>'

        html += _card(f'''<h3>Score Trend</h3>
          <div style="position:relative;height:120px;margin:24px 0 32px">{dots}</div>''')

    # Side-by-side cards (show last 2 or all)
    display_scs = scorecards[-2:] if len(scorecards) >= 2 else scorecards
    cols = len(display_scs)
    html += f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:16px">'

    for sc in display_scs:
        version = sc.get("version", "?")
        score = sc.get("overall_score", 0)
        objective = sc.get("campaign_objective", "default")

        dims_html = ""
        for dn, dd in sc.get("dimensions", {}).items():
            dims_html += _bar_row(_dim_label(dn), dd["score"])

        ba_html = ""
        ba = sc.get("brief_alignment")
        if ba:
            ba_html = f'<div class="sep"></div><div style="font-size:13px">Brief: <strong>{ba["overall_brief_score"]}/100</strong></div>'

        strengths = "".join(f'<div style="font-size:11px;color:#22c55e">+ {_esc(s)}</div>' for s in sc.get("strengths", [])[:3])
        gaps = "".join(f'<div style="font-size:11px;color:#f59e0b">- {_esc(g["description"][:80])}</div>' for g in sc.get("priority_gaps", [])[:3])

        html += _card(f'''{_gauge(score)}
          <div style="text-align:center;margin-bottom:12px">
            <div style="font-size:14px;font-weight:600">v{version}</div>
            <div style="font-size:11px;color:#8b91a8">{_esc(objective)}</div>
            {_chip(f"Context: {sc.get('context_id','none')}", "green") if sc.get('context_id') else ""}
          </div>
          {dims_html}
          {ba_html}
          <div class="sep"></div>
          {strengths}{gaps}''', "padding:16px")

    html += '</div>'

    # Dimension-by-dimension diff (if 2+ versions)
    if len(scorecards) >= 2:
        prev = scorecards[-2]
        curr = scorecards[-1]
        html += '<h3 style="margin-top:24px">Dimension Changes (Latest vs Previous)</h3>'
        diff_rows = ""
        for dim in ["hook", "retention", "ctr_drivers", "cta_conversion", "brand_coherence"]:
            prev_score = prev.get("dimensions", {}).get(dim, {}).get("score", 0)
            curr_score = curr.get("dimensions", {}).get(dim, {}).get("score", 0)
            delta = curr_score - prev_score
            arrow = "+" if delta > 0 else ""
            dc = "#22c55e" if delta > 0 else "#ef4444" if delta < 0 else "#8b91a8"
            diff_rows += f'<tr><td>{_dim_label(dim)}</td><td>{prev_score}/5</td><td>{curr_score}/5</td><td style="color:{dc};font-weight:700">{arrow}{delta}</td></tr>'

        prev_total = prev.get("overall_score", 0)
        curr_total = curr.get("overall_score", 0)
        total_delta = curr_total - prev_total
        ta = "+" if total_delta > 0 else ""
        tc = "#22c55e" if total_delta > 0 else "#ef4444" if total_delta < 0 else "#8b91a8"
        diff_rows += f'<tr style="border-top:2px solid #2d3148"><td><strong>Overall</strong></td><td><strong>{prev_total}</strong></td><td><strong>{curr_total}</strong></td><td style="color:{tc};font-weight:700"><strong>{ta}{total_delta}</strong></td></tr>'

        html += _card(f'<table><tr><th>Dimension</th><th>Previous</th><th>Current</th><th>Change</th></tr>{diff_rows}</table>')

    html += f'<div style="margin-top:16px">{_btn("Back to Ads", "/wiom")} {_btn("View Full History", f"/history?ad_id={ad_id}", False)}</div>'

    return _page("Compare", html, "compare")


# ---------------------------------------------------------------------------
# Batch Operations
# ---------------------------------------------------------------------------

@app.route("/batch/review", methods=["GET", "POST"])
def batch_review():
    """Run review on multiple ads at once."""
    wiom_ids = sorted([f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")])

    if request.method == "POST":
        selected = request.form.getlist("ad_ids")
        if not selected:
            return _page("Batch Review", _card('<div style="color:#ef4444">No ads selected.</div>'), "wiom")

        from llm import run_review, run_suggest
        action = request.form.get("action", "review")

        results_html = '<h2>Batch Results</h2>'
        for ad_id in selected:
            try:
                if action == "review":
                    result, msg = run_review(ad_id)
                elif action == "suggest":
                    result, msg = run_suggest(ad_id)
                else:
                    result, msg = None, f"Unknown action: {action}"

                if result:
                    score = result.get("overall_score", "?")
                    results_html += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center">
                      <div><strong>{_esc(_ad_name(ad_id))}</strong> <span style="color:#8b91a8;font-size:12px">{ad_id}</span></div>
                      <div>{_gauge(score) if action == "review" else _chip(f"{len(result.get('suggestions',[]))} suggestions", "green")}</div>
                    </div>
                    <div style="font-size:12px;color:#22c55e;margin-top:4px">{_esc(msg)}</div>''', "padding:16px;margin-bottom:8px")
                else:
                    results_html += _card(f'<div style="display:flex;justify-content:space-between"><strong>{_esc(ad_id)}</strong> <span style="color:#ef4444;font-size:12px">{_esc(msg)}</span></div>', "padding:16px;margin-bottom:8px")
            except Exception as e:
                results_html += _card(f'<div><strong>{_esc(ad_id)}</strong> <span style="color:#ef4444;font-size:12px">Error: {_esc(str(e))}</span></div>', "padding:16px;margin-bottom:8px")

        results_html += f'<div style="margin-top:16px">{_btn("Back to Ads", "/wiom")}</div>'
        return _page("Batch Results", results_html, "wiom")

    # GET: show multi-select form
    html = '<h2>Batch Operations</h2><p style="color:#8b91a8;margin-bottom:24px">Select multiple ads to review or generate suggestions in one go.</p>'
    html += '<form method="POST" action="/batch/review">'

    checkboxes = ""
    for wid in wiom_ids:
        sc_path = SCORECARDS_DIR / f"{wid}_scorecard.json"
        has_score = sc_path.exists()
        score_text = ""
        if has_score:
            with open(sc_path, "r", encoding="utf-8") as f:
                sc = json.load(f)
            score_text = f' — Score: {sc.get("overall_score", "?")}/100'

        checkboxes += f'''<label style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:#1a1d27;border:1px solid #2d3148;border-radius:8px;margin-bottom:8px;cursor:pointer">
          <input type="checkbox" name="ad_ids" value="{wid}" style="width:18px;height:18px;accent-color:#6366f1">
          <div>
            <div style="font-size:14px;font-weight:500">{_esc(_ad_name(wid))}</div>
            <div style="font-size:12px;color:#8b91a8">{wid}{score_text}</div>
          </div>
        </label>'''

    html += _card(f'<h3>Select Ads</h3>{checkboxes}')

    html += '''<div style="display:flex;gap:12px;margin-top:16px">
      <button type="submit" name="action" value="review" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#6366f1;color:white">Run Review on Selected</button>
      <button type="submit" name="action" value="suggest" style="padding:10px 20px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer;border:none;background:#818cf8;color:white">Run Suggest on Selected</button>
    </div></form>'''

    return _page("Batch Operations", html, "wiom")


# ---------------------------------------------------------------------------
# Batch Pull (auto-pull all mapped ads)
# ---------------------------------------------------------------------------

@app.route("/batch/pull", methods=["POST"])
def batch_pull():
    """Pull performance data for all mapped ads from Meta."""
    mappings = load_all_mappings()
    meta_mappings = [m for m in mappings if m.get("platform") == "meta" and m.get("meta_ad_id")]

    if not meta_mappings:
        return _page("Batch Pull", _card('<div style="color:#ef4444">No Meta campaign mappings found. Map ads first.</div>'), "performance")

    from meta_pull import pull_and_save

    results_html = '<h2>Batch Pull Results</h2>'
    date_preset = request.form.get("date_preset", "last_7d")

    for m in meta_mappings:
        ad_id = m["ad_id"]
        meta_ad_id = m["meta_ad_id"]
        try:
            ctx = load_campaign_context(ad_id)
            ctx_id = ctx["context_id"] if ctx else "none"
            results = pull_and_save(ad_id, meta_ad_id, context_id=ctx_id, date_preset=date_preset)
            success = sum(1 for ok, _ in results if ok)
            results_html += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center">
              <strong>{_esc(_ad_name(ad_id))}</strong>
              <span style="color:#22c55e">{success}/{len(results)} snapshots pulled</span>
            </div>''', "padding:16px;margin-bottom:8px")
        except Exception as e:
            results_html += _card(f'<div style="display:flex;justify-content:space-between"><strong>{_esc(ad_id)}</strong> <span style="color:#ef4444">{_esc(str(e)[:100])}</span></div>', "padding:16px;margin-bottom:8px")

    results_html += f'<div style="margin-top:16px">{_btn("View Performance", "/performance")} {_btn("Back", "/wiom", False)}</div>'
    return _page("Batch Pull", results_html, "performance")


# ---------------------------------------------------------------------------
# Update Meta pull route to support pre-filled params from mapping
# ---------------------------------------------------------------------------

# (the existing /meta/pull route already handles this via form fields)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route("/api/state")
def api_state():
    return jsonify(get_state())

@app.route("/api/weights/<objective>")
def api_weights(objective):
    return jsonify({"objective": objective, "weights": get_weight_profile(objective), "priority_patterns": get_priority_patterns(objective)})

@app.route("/api/history/<ad_id>")
def api_history(ad_id):
    return jsonify({"scorecards": load_history(ad_id, "scorecards"), "suggestions": load_history(ad_id, "suggestions"), "optimizations": load_history(ad_id, "optimizations")})


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5100))
    is_local = port == 5100
    if is_local:
        import webbrowser
        webbrowser.open(f"http://localhost:{port}")
    print(f"\n  CUE Web App starting at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
