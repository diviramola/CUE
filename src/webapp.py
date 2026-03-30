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
    return f'''<div style="width:100px;height:100px;border-radius:50%;margin:0 auto 8px;
      background:conic-gradient(#6366f1 {score*3.6}deg,#242836 0);
      display:flex;align-items:center;justify-content:center;position:relative">
      <div style="width:76px;height:76px;border-radius:50%;background:#1a1d27;position:absolute"></div>
      <span style="position:relative;z-index:1;font-size:20px;font-weight:700">{score}</span>
    </div>'''


def _card(content, extra_style=""):
    return f'<div style="background:#1a1d27;border:1px solid #2d3148;border-radius:10px;padding:24px;margin-bottom:20px;{extra_style}">{content}</div>'


def _stat(num, label):
    return _card(f'<div style="text-align:center;padding:16px"><div style="font-size:28px;font-weight:700;color:#818cf8">{num}</div><div style="font-size:11px;color:#8b91a8;text-transform:uppercase;letter-spacing:1px;margin-top:4px">{label}</div></div>', "padding:8px;margin-bottom:12px")


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
</style>
</head><body>
<div style="display:flex;min-height:100vh">
  <nav style="width:240px;background:#1a1d27;border-right:1px solid #2d3148;padding:24px 16px;position:fixed;top:0;left:0;bottom:0;overflow-y:auto">
    <h1 style="font-size:18px;font-weight:700;color:#818cf8;margin-bottom:4px">CUE</h1>
    <div style="font-size:11px;color:#8b91a8;margin-bottom:24px;text-transform:uppercase;letter-spacing:1px">Creative Understanding Experiment</div>
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#8b91a8;margin-bottom:8px">Pipeline</div>
    {nav_html}
  </nav>
  <main style="margin-left:240px;padding:32px 40px;flex:1;max-width:1100px">
    {content}
  </main>
</div>
</body></html>'''


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    state = get_state()
    pb = get_progress_bar()

    stats = '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-top:24px">'
    stats += _stat(state["library"]["total_ads"], "Library Ads")
    stats += _stat(state["wiom_ads"]["total"], "Wiom Ads")
    stats += _stat(state["contexts"]["total"], "Contexts")
    stats += _stat(state["scorecards"]["total"], "Scorecards")
    stats += _stat(state["performance"]["total"], "Perf Snapshots")
    stats += '</div>'

    html = f'<h2>Pipeline Status</h2>'
    html += f'<div style="font-family:monospace;font-size:12px;color:#8b91a8;white-space:pre;line-height:1.6;padding:12px;background:#242836;border-radius:6px">{_esc(pb)}</div>'
    html += stats

    # Scorecards
    scorecards = {}
    for f in SCORECARDS_DIR.glob("*_scorecard.json"):
        ad_id = f.stem.replace("_scorecard", "")
        with open(f, "r", encoding="utf-8") as fh:
            scorecards[ad_id] = json.load(fh)

    if scorecards:
        html += '<h2 style="margin-top:32px">Latest Scorecards</h2>'
        for ad_id, sc in scorecards.items():
            dims = ""
            for dn, dd in sc.get("dimensions", {}).items():
                dims += _bar_row(_dim_label(dn), dd["score"])

            chips = _chip(_format_label(sc.get("campaign_objective", "default")), "blue")
            if sc.get("context_id"):
                chips += _chip(f"Context: {sc['context_id']}", "green")
            if sc.get("version"):
                chips += _chip(f"v{sc['version']}", "amber")

            brief_html = ""
            ba = sc.get("brief_alignment")
            if ba:
                brief_html = '<div class="sep"></div>'
                brief_html += f'<h3>Brief Alignment: {ba["overall_brief_score"]}/100</h3>'
                for bk in ["audience_match", "message_delivery", "tone_match", "usp_clarity", "desired_action_driven"]:
                    brief_html += _bar_row(_dim_label(bk), ba[bk])

            buttons = f'''<div style="display:flex;gap:8px">
              {_btn("Set Context & Re-Score", f"/context/new?ad_id={ad_id}", False, True)}
              {_btn("Add Performance Data", f"/performance?ad_id={ad_id}", False, True)}
              {_btn("View History", f"/history?ad_id={ad_id}", False, True)}
            </div>'''

            inner = f'''<div style="display:flex;justify-content:space-between;align-items:center">
              <div><h3 style="margin-bottom:4px">{_esc(_ad_name(ad_id))}</h3><div style="font-size:11px;color:#8b91a8;margin-bottom:4px">{ad_id}</div>{chips}</div>
              {_gauge(sc.get("overall_score", 0))}
            </div>
            <div style="margin-top:16px">{dims}</div>
            {brief_html}
            <div class="sep"></div>{buttons}'''
            html += _card(inner)

    # Suggestions
    suggestions = {}
    for f in SUGGESTIONS_DIR.glob("*_suggestions.json"):
        ad_id = f.stem.replace("_suggestions", "")
        with open(f, "r", encoding="utf-8") as fh:
            suggestions[ad_id] = json.load(fh)

    if suggestions:
        html += '<h2 style="margin-top:32px">Latest Suggestions</h2>'
        for ad_id, sug in suggestions.items():
            items = ""
            for s in sug.get("suggestions", []):
                pc = "red" if s["priority"] == "high" else "amber" if s["priority"] == "medium" else "green"
                change_text = _esc(s.get("suggested_change", ""))
                items += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center">
                  <span><strong>{_esc(_dim_label(s.get("dimension","")))}</strong>: {change_text}</span>
                  {_chip(s["priority"], pc)}
                </div>''', "background:#242836;padding:16px;margin-bottom:8px;margin-top:8px")

            keeps = ""
            for k in sug.get("keep", [])[:3]:
                keeps += f'<div style="font-size:12px;color:#8b91a8;margin-top:4px">- {_esc(k)}</div>'
            if keeps:
                keeps = f'<div style="margin-top:12px"><strong style="font-size:12px;color:#22c55e">KEEP:</strong>{keeps}</div>'

            html += _card(f'<h3>{_esc(_ad_name(ad_id))} -- {len(sug.get("suggestions",[]))} suggestions</h3>{items}{keeps}')

    return _page("Dashboard", html, "home")


@app.route("/library")
def library():
    index = load_index()
    rows = ""
    for ad in index:
        tc = "green" if ad.get("tier") == "exceptional" else "amber" if ad.get("tier") == "strong" else "blue"
        rows += f'''<tr>
          <td><strong>{_esc(ad["id"])}</strong></td>
          <td>{_esc(ad.get("advertiser",""))}</td>
          <td>{_esc(ad.get("platform",""))}</td>
          <td>{_esc(ad.get("vertical",""))}</td>
          <td>{_chip(ad.get("tier","unrated"), tc)}</td>
          <td>{"Yes" if ad.get("deconstructed") else "No"}</td>
        </tr>'''

    verticals = len(set(ad.get("vertical", "") for ad in index))
    html = f'''<h2>Best-in-Class Ad Library</h2>
    <p style="color:#8b91a8;margin-bottom:16px">{len(index)} ads across {verticals} verticals</p>
    <table><tr><th>ID</th><th>Advertiser</th><th>Platform</th><th>Vertical</th><th>Tier</th><th>Deconstructed</th></tr>{rows}</table>'''
    return _page("Ad Library", html, "library")


@app.route("/playbook")
def playbook():
    if not PLAYBOOK_JSON.exists():
        html = _card('<div style="text-align:center;padding:48px;color:#8b91a8"><h3 style="color:#e4e7f0;margin-bottom:8px">No playbook yet</h3><p>Run /cue-pattern to generate the Creative Playbook.</p></div>')
        return _page("Playbook", html, "playbook")

    with open(PLAYBOOK_JSON, "r", encoding="utf-8") as f:
        pb = json.load(f)

    html = f'<h2>Creative Playbook</h2>'
    html += f'<p style="color:#8b91a8;margin-bottom:24px">{pb.get("library_size",0)} ads analyzed | {len(pb.get("patterns",[]))} patterns | {len(pb.get("anti_patterns",[]))} anti-patterns</p>'

    html += '<h3>Patterns</h3>'
    for p in pb.get("patterns", []):
        cc = "green" if p.get("confidence") == "strong" else "amber" if p.get("confidence") == "moderate" else "blue"
        html += _card(f'''<div style="display:flex;justify-content:space-between;align-items:center">
          <div>{_chip(p["id"], "blue")} <strong>{_esc(p["name"])}</strong></div>
          {_chip(f'{p.get("confidence","")} ({p.get("frequency","")})', cc)}
        </div>
        <p style="font-size:13px;color:#8b91a8;margin-top:6px">{_esc(p.get("description",""))}</p>
        <p style="font-size:12px;color:#8b91a8;margin-top:4px"><em>Mechanism: {_esc(p.get("mechanism",""))}</em></p>''', "padding:16px;margin-bottom:12px")

    html += '<h3 style="margin-top:24px">Anti-Patterns</h3>'
    for ap in pb.get("anti_patterns", []):
        sc = "red" if ap.get("severity") == "high" else "amber"
        html += _card(f'''<div style="display:flex;justify-content:space-between">
          <div>{_chip(ap["id"], "red")} <strong>{_esc(ap["name"])}</strong></div>
          {_chip(ap.get("severity",""), sc)}
        </div>
        <p style="font-size:13px;color:#8b91a8;margin-top:6px">{_esc(ap.get("description",""))}</p>''', "padding:16px;margin-bottom:12px;border-left:3px solid #ef4444")

    rubric = pb.get("scoring_rubric", {}).get("dimensions", {})
    if rubric:
        html += '<h3 style="margin-top:24px">Scoring Rubric</h3><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">'
        for dn, dd in rubric.items():
            scores_html = ""
            for sk, sv in dd.get("scores", {}).items():
                scores_html += f'<div style="font-size:12px;margin-bottom:4px"><strong>{sk}:</strong> {_esc(sv)}</div>'
            html += _card(f'<h3>{_dim_label(dn)} ({int(dd.get("weight",0)*100)}%)</h3>{scores_html}', "padding:16px;margin-bottom:12px")
        html += '</div>'

    return _page("Playbook", html, "playbook")


@app.route("/wiom")
def wiom():
    wiom_ids = sorted([f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")])

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

    html = f'<h2>Wiom Ads & Scorecards</h2><div style="display:flex;gap:12px;margin-bottom:20px">{_btn("+ Upload Ad", "/wiom/upload")} {_btn("Batch Review/Suggest", "/batch/review", False)} {_btn("Campaign Mapping", "/campaign/map", False)}</div>'
    for wid in wiom_ids:
        meta_path = WIOM_DIR / f"{wid}.json"
        meta = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as fh:
                meta = json.load(fh)

        desc = f'<p style="font-size:13px;color:#8b91a8">{_esc(meta.get("description",""))}</p>'
        tags = "".join(_chip(t, "blue") for t in meta.get("tags", []))

        score_html = ""
        if wid in scorecards:
            sc = scorecards[wid]
            ba_text = ""
            ba = sc.get("brief_alignment")
            if ba:
                ba_text = f'<div style="font-size:13px">Brief Alignment: <strong>{ba["overall_brief_score"]}/100</strong></div>'
            score_html = f'''<div style="margin-top:16px;display:flex;align-items:center;gap:24px">
              {_gauge(sc.get("overall_score", 0))}
              <div>
                <div style="font-size:13px">Pattern Score: <strong>{sc.get("overall_score",0)}/100</strong></div>
                {ba_text}
                <div style="font-size:12px;color:#8b91a8">Objective: {sc.get("campaign_objective","default")}</div>
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

        buttons = f'''<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
          {review_btn} {optimize_btn}
          {_btn("+ Context", f"/context/new?ad_id={wid}", False, True)}
          {_btn("+ Performance", f"/performance?ad_id={wid}", False, True)}
          {_btn("Pull from Meta", "/meta/pull", False, True)}
          {_btn("History", f"/history?ad_id={wid}", False, True)}
        </div>'''

        decon_badge = _chip("Deconstructed", "green") if has_decon else _chip("Not Deconstructed", "amber")
        ad_title = _ad_name(wid)
        html += _card(f'<h3>{_esc(ad_title)}</h3><div style="font-size:11px;color:#8b91a8;margin-bottom:8px">{wid} &nbsp;{decon_badge}</div>{desc}<div style="margin-top:8px">{tags}</div>{score_html}{ctx_html}{buttons}')

    if not wiom_ids:
        html += _card('<div style="text-align:center;padding:48px;color:#8b91a8"><h3 style="color:#e4e7f0;margin-bottom:8px">No Wiom ads loaded</h3><p>Share a video file in Claude Code to add your first Wiom ad.</p></div>')

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
    return redirect(f"/performance?ad_id={ad_id}")


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
        except Exception as e:
            steps.append(("Deconstruct", False, str(e)))
            # Can't proceed without decon
            return _render_pipeline_result(ad_id, steps, None, None)

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

    # Steps summary
    steps_html = '<div style="display:flex;gap:8px;margin-bottom:24px;align-items:center">'
    for i, (name, ok, msg) in enumerate(steps):
        c = "#22c55e" if ok else "#ef4444"
        icon = "✓" if ok else "✗"
        steps_html += f'<div style="padding:6px 14px;border-radius:20px;font-size:12px;font-weight:500;background:{c}22;color:{c};border:1px solid {c}44">{icon} {name}</div>'
        if i < len(steps) - 1:
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
