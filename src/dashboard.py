"""
CUE Dashboard Generator — Produces standalone HTML from pipeline data.
Deterministic: same data in = same HTML out. No LLM involved.
"""

import json
import sys
from pathlib import Path

# Import harness for data export
sys.path.insert(0, str(Path(__file__).parent))
from harness import export_dashboard_data, ROOT

OUTPUT = ROOT / "output" / "dashboard.html"


def generate_dashboard():
    data = export_dashboard_data()
    html = _build_html(data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generated: {OUTPUT}")
    return str(OUTPUT)


def _build_html(data: dict) -> str:
    state = data["state"]
    index = data["index"]
    deconstructions = data["deconstructions"]
    playbook = data["playbook"]
    scorecards = data["scorecards"]
    suggestions = data["suggestions"]

    data_json = json.dumps(data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CUE — Dashboard</title>
<style>
{_css()}
</style>
</head>
<body>
<nav id="sidebar">
  <div class="logo">CUE</div>
  <div class="nav-label">Pipeline</div>
  <a href="#pipeline" class="nav-link active">Status</a>
  <a href="#library" class="nav-link">Library ({state['library']['total_ads']})</a>
  <a href="#playbook" class="nav-link">Playbook</a>
  <a href="#scorecards" class="nav-link">Scorecards ({state['scorecards']['total']})</a>
  <a href="#suggestions" class="nav-link">Suggestions ({state['suggestions']['total']})</a>
  <div class="nav-footer">
    <small>Updated: {state['last_updated'][:16]}</small>
  </div>
</nav>
<main>
  <section id="pipeline">
    <h1>Pipeline Status</h1>
    {_pipeline_section(state)}
  </section>
  <section id="library">
    <h1>Best-in-Class Library</h1>
    {_library_section(index, deconstructions)}
  </section>
  <section id="playbook">
    <h1>Creative Playbook</h1>
    {_playbook_section(playbook)}
  </section>
  <section id="scorecards">
    <h1>Wiom Scorecards</h1>
    {_scorecards_section(scorecards)}
  </section>
  <section id="suggestions">
    <h1>Improvement Suggestions</h1>
    {_suggestions_section(suggestions)}
  </section>
</main>
<script>
const DATA = {data_json};
{_js()}
</script>
</body>
</html>"""


def _pipeline_section(state):
    lib = state["library"]
    phases = [
        ("Scout", lib["total_ads"], 15, state["current_phase"] == "scout"),
        ("Deconstruct", lib["deconstructed"], max(lib["total_ads"], 1), state["current_phase"] == "deconstruct"),
        ("Pattern", 1 if state["playbook_exists"] else 0, 1, state["current_phase"] == "pattern"),
        ("Review", state["scorecards"]["total"], max(state["wiom_ads"]["total"], 1), state["current_phase"] == "review"),
        ("Suggest", state["suggestions"]["total"], max(state["scorecards"]["total"], 1), state["current_phase"] == "suggest"),
    ]

    html = '<div class="pipeline-bar">'
    for name, filled, cap, is_current in phases:
        pct = min(round(filled / cap * 100), 100) if cap > 0 else 0
        status = "complete" if pct == 100 else ("active" if is_current else "pending")
        label = f"{filled}/{cap}" if cap > 1 else ("Done" if pct == 100 else "—")
        html += f'''
        <div class="phase {status}">
          <div class="phase-bar-bg"><div class="phase-bar-fill" style="width:{pct}%"></div></div>
          <div class="phase-name">{name}</div>
          <div class="phase-count">{label}</div>
        </div>'''
        if name != "Suggest":
            html += '<div class="phase-arrow">→</div>'
    html += '</div>'

    # Tier breakdown
    tiers = lib.get("by_tier", {})
    html += '<div class="tier-summary">'
    for t, color in [("exceptional", "#16A34A"), ("strong", "#2563EB"), ("reference", "#D97706"), ("unrated", "#94A3B8")]:
        count = tiers.get(t, 0)
        html += f'<span class="tier-badge" style="background:{color}">{t.title()}: {count}</span>'
    html += '</div>'
    return html


def _library_section(index, deconstructions):
    if not index:
        return '<div class="empty-state">No ads in library yet. Run <code>/cue-scout</code> to start.</div>'

    html = '<div class="filter-bar"><input type="text" id="lib-search" placeholder="Filter by advertiser, vertical, tag..." onkeyup="filterLibrary()"></div>'
    html += '<div class="card-grid" id="library-grid">'
    for ad in index:
        tier = ad.get("tier") or "unrated"
        tier_color = {"exceptional": "#16A34A", "strong": "#2563EB", "reference": "#D97706", "unrated": "#94A3B8"}[tier]
        decon = deconstructions.get(ad["id"])
        decon_badge = '<span class="badge green">Deconstructed</span>' if ad.get("deconstructed") else '<span class="badge grey">Pending</span>'

        xfactor = ""
        if decon:
            xfactor = f'<div class="xfactor"><strong>X-Factor:</strong> {_esc(decon.get("x_factor", "")[:200])}</div>'

        html += f'''
        <div class="card" data-search="{_esc(ad.get('advertiser',''))} {_esc(ad.get('vertical',''))} {_esc(ad.get('description',''))}">
          <div class="card-header">
            <span class="advertiser">{_esc(ad.get('advertiser',''))}</span>
            <span class="tier-dot" style="background:{tier_color}" title="{tier}">{tier[0].upper()}</span>
          </div>
          <div class="card-meta">{_esc(ad.get('platform',''))} · {_esc(ad.get('vertical',''))} {decon_badge}</div>
          <div class="card-desc">{_esc(ad.get('description','')[:120])}</div>
          {xfactor}
          <div class="card-url"><a href="{_esc(ad.get('url',''))}" target="_blank">View Ad →</a></div>
        </div>'''
    html += '</div>'
    return html


def _playbook_section(playbook):
    if not playbook:
        return '<div class="empty-state">Playbook not generated yet. Run <code>/cue-pattern</code> after deconstructing ads.</div>'

    html = '<div class="card-grid">'
    patterns = playbook.get("patterns", [])
    for p in patterns:
        conf = p.get("confidence", "unknown")
        conf_color = {"strong": "#16A34A", "moderate": "#D97706", "emerging": "#94A3B8"}.get(conf, "#94A3B8")
        html += f'''
        <div class="card pattern-card">
          <div class="card-header">
            <span class="pattern-name">{_esc(p.get('name',''))}</span>
            <span class="conf-badge" style="background:{conf_color}">{conf}</span>
          </div>
          <div class="card-desc">{_esc(p.get('description',''))}</div>
          <div class="card-meta">Frequency: {p.get('frequency','')} | Metric: {_esc(p.get('primary_metric',''))}</div>
        </div>'''
    html += '</div>'

    # Anti-patterns
    anti = playbook.get("anti_patterns", [])
    if anti:
        html += '<h2>Anti-Patterns</h2><div class="card-grid">'
        for a in anti:
            html += f'''
            <div class="card anti-card">
              <div class="card-header"><span class="pattern-name">{_esc(a.get('name',''))}</span></div>
              <div class="card-desc">{_esc(a.get('description',''))}</div>
            </div>'''
        html += '</div>'
    return html


def _scorecards_section(scorecards):
    if not scorecards:
        return '<div class="empty-state">No scorecards yet. Load Wiom ads and run <code>/cue-review</code>.</div>'

    html = ''
    for ad_id, sc in scorecards.items():
        score = sc.get("overall_score", 0)
        score_color = "#DC2626" if score < 40 else ("#D97706" if score < 70 else "#16A34A")

        html += f'''
        <div class="scorecard">
          <div class="score-header">
            <div class="score-gauge">
              <svg viewBox="0 0 120 120" width="120" height="120">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#E2E8F0" stroke-width="10"/>
                <circle cx="60" cy="60" r="50" fill="none" stroke="{score_color}" stroke-width="10"
                  stroke-dasharray="{score * 3.14} 314" stroke-linecap="round" transform="rotate(-90 60 60)"/>
                <text x="60" y="65" text-anchor="middle" font-size="28" font-weight="700" fill="{score_color}">{score}</text>
              </svg>
            </div>
            <div class="score-info">
              <h3>{_esc(ad_id)}</h3>
              <div class="score-label">Overall Score / 100</div>
            </div>
          </div>
          <div class="dimension-bars">'''

        dims = sc.get("dimensions", {})
        dim_labels = {"hook": "Hook", "retention": "Retention", "ctr_drivers": "CTR Drivers", "cta_conversion": "CTA/Conv", "brand_coherence": "Brand"}
        weights = sc.get("weight_profile", {})
        for key, label in dim_labels.items():
            d = dims.get(key, {})
            s_val = d.get("score", 0)
            w = weights.get(key, 0)
            bar_pct = s_val * 20
            bar_color = "#DC2626" if s_val < 2 else ("#D97706" if s_val <= 3 else "#16A34A")
            html += f'''
            <div class="dim-row">
              <span class="dim-label">{label} <small>({int(w*100)}%)</small></span>
              <div class="dim-bar-bg"><div class="dim-bar-fill" style="width:{bar_pct}%;background:{bar_color}"></div></div>
              <span class="dim-score">{s_val}/5</span>
            </div>'''

        html += '</div>'

        # Strengths
        strengths = sc.get("strengths", [])
        if strengths:
            html += '<div class="strengths"><strong>Strengths:</strong> ' + "; ".join(_esc(s) for s in strengths) + '</div>'

        # Priority gaps
        gaps = sc.get("priority_gaps", [])
        if gaps:
            html += '<div class="gaps"><strong>Priority Gaps:</strong><ol>'
            for g in gaps:
                html += f'<li><strong>{_esc(g.get("dimension",""))}</strong>: {_esc(g.get("description",""))}</li>'
            html += '</ol></div>'

        html += '</div>'
    return html


def _suggestions_section(suggestions):
    if not suggestions:
        return '<div class="empty-state">No suggestions yet. Run <code>/cue-suggest</code> after scorecards.</div>'

    html = ''
    for ad_id, sg in suggestions.items():
        html += f'<div class="suggestion-set"><h3>{_esc(ad_id)} — Score: {sg.get("overall_score",0)}/100</h3>'

        for i, s in enumerate(sg.get("suggestions", []), 1):
            pri = s.get("priority", "medium")
            pri_color = {"high": "#DC2626", "medium": "#D97706", "low": "#2563EB"}[pri]
            html += f'''
            <div class="suggestion-card">
              <div class="sug-header">
                <span class="sug-num">#{i}</span>
                <span class="sug-dim">{_esc(s.get('dimension',''))}</span>
                <span class="pri-badge" style="background:{pri_color}">{pri}</span>
                <span class="metric-badge">{_esc(s.get('affects_metric',''))}</span>
              </div>
              <div class="sug-body">
                <div class="sug-current"><strong>Current:</strong> {_esc(s.get('current',''))}</div>
                <div class="sug-change"><strong>Suggested:</strong> {_esc(s.get('suggested_change',''))}</div>
                <div class="sug-why"><strong>Why:</strong> {_esc(s.get('why_it_works',''))}</div>
                <div class="sug-ref"><strong>Reference:</strong> {_esc(s.get('reference_ad_id',''))} — {_esc(s.get('reference_note',''))}</div>
              </div>
            </div>'''

        # Keep section
        keep = sg.get("keep", [])
        if keep:
            html += '<div class="keep-section"><strong>Keep (don\'t change):</strong><ul>'
            for k in keep:
                html += f'<li>{_esc(k)}</li>'
            html += '</ul></div>'

        html += '</div>'
    return html


def _esc(s):
    """HTML escape."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _css():
    return """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Inter', -apple-system, 'Segoe UI', system-ui, sans-serif; background: #F8FAFC; color: #1E293B; display: flex; min-height: 100vh; }

/* Sidebar */
#sidebar { width: 220px; background: #1E293B; color: #CBD5E1; padding: 24px 16px; position: fixed; height: 100vh; overflow-y: auto; }
.logo { font-size: 24px; font-weight: 800; color: #fff; margin-bottom: 32px; letter-spacing: 2px; }
.nav-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #64748B; margin: 16px 0 8px; }
.nav-link { display: block; padding: 8px 12px; color: #94A3B8; text-decoration: none; border-radius: 6px; margin-bottom: 2px; font-size: 14px; }
.nav-link:hover, .nav-link.active { background: #334155; color: #fff; }
.nav-footer { position: absolute; bottom: 16px; font-size: 11px; color: #475569; }

/* Main */
main { margin-left: 220px; padding: 40px; width: calc(100% - 220px); max-width: 1200px; }
section { margin-bottom: 48px; }
h1 { font-size: 24px; font-weight: 700; margin-bottom: 24px; color: #0F172A; }
h2 { font-size: 18px; font-weight: 600; margin: 24px 0 16px; color: #334155; }

/* Pipeline */
.pipeline-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
.phase { text-align: center; flex: 1; min-width: 100px; }
.phase-bar-bg { height: 8px; background: #E2E8F0; border-radius: 4px; overflow: hidden; }
.phase-bar-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
.phase.complete .phase-bar-fill { background: #16A34A; }
.phase.active .phase-bar-fill { background: #2563EB; }
.phase.pending .phase-bar-fill { background: #94A3B8; }
.phase-name { font-size: 13px; font-weight: 600; margin-top: 6px; }
.phase-count { font-size: 11px; color: #64748B; }
.phase-arrow { color: #94A3B8; font-size: 18px; align-self: center; }
.tier-summary { display: flex; gap: 8px; margin-top: 12px; }
.tier-badge { color: #fff; font-size: 12px; padding: 3px 10px; border-radius: 12px; font-weight: 500; }

/* Cards */
.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.card { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.advertiser { font-weight: 700; font-size: 16px; }
.tier-dot { width: 24px; height: 24px; border-radius: 50%; color: #fff; font-size: 12px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.card-meta { font-size: 12px; color: #64748B; margin-bottom: 8px; }
.card-desc { font-size: 14px; line-height: 1.5; color: #334155; margin-bottom: 8px; }
.card-url a { font-size: 13px; color: #2563EB; text-decoration: none; }
.card-url a:hover { text-decoration: underline; }
.xfactor { font-size: 13px; color: #475569; background: #F0FDF4; padding: 8px 12px; border-radius: 6px; margin: 8px 0; border-left: 3px solid #16A34A; }
.badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 500; }
.badge.green { background: #DCFCE7; color: #166534; }
.badge.grey { background: #F1F5F9; color: #475569; }

/* Pattern cards */
.pattern-card { border-left: 3px solid #2563EB; }
.anti-card { border-left: 3px solid #DC2626; background: #FEF2F2; }
.pattern-name { font-weight: 700; font-size: 15px; }
.conf-badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; color: #fff; }

/* Scorecards */
.scorecard { background: #fff; border-radius: 10px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; margin-bottom: 24px; }
.score-header { display: flex; align-items: center; gap: 24px; margin-bottom: 20px; }
.score-info h3 { font-size: 18px; font-weight: 700; }
.score-label { font-size: 13px; color: #64748B; }
.dimension-bars { margin-bottom: 16px; }
.dim-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.dim-label { width: 140px; font-size: 13px; font-weight: 500; }
.dim-label small { color: #94A3B8; }
.dim-bar-bg { flex: 1; height: 10px; background: #E2E8F0; border-radius: 5px; overflow: hidden; }
.dim-bar-fill { height: 100%; border-radius: 5px; transition: width 0.3s; }
.dim-score { font-size: 13px; font-weight: 600; width: 30px; text-align: right; }
.strengths { font-size: 14px; color: #166534; background: #F0FDF4; padding: 12px; border-radius: 6px; margin: 12px 0; }
.gaps { font-size: 14px; margin-top: 12px; }
.gaps ol { margin-left: 20px; margin-top: 4px; }
.gaps li { margin-bottom: 4px; }

/* Suggestions */
.suggestion-set { margin-bottom: 32px; }
.suggestion-set h3 { font-size: 18px; font-weight: 700; margin-bottom: 16px; }
.suggestion-card { background: #fff; border-radius: 10px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; margin-bottom: 12px; }
.sug-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.sug-num { font-weight: 800; font-size: 16px; color: #2563EB; }
.sug-dim { font-weight: 600; font-size: 14px; }
.pri-badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; color: #fff; }
.metric-badge { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: #E0E7FF; color: #3730A3; }
.sug-body > div { margin-bottom: 8px; font-size: 14px; line-height: 1.5; }
.sug-change { background: #EFF6FF; padding: 10px 12px; border-radius: 6px; border-left: 3px solid #2563EB; }
.sug-ref { font-size: 13px; color: #64748B; }
.keep-section { background: #F0FDF4; padding: 12px; border-radius: 6px; margin-top: 12px; font-size: 14px; }
.keep-section ul { margin-left: 20px; margin-top: 4px; }

/* Empty */
.empty-state { background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 10px; padding: 40px; text-align: center; color: #64748B; font-size: 15px; }
.empty-state code { background: #E2E8F0; padding: 2px 6px; border-radius: 4px; font-size: 13px; }

/* Filter */
.filter-bar { margin-bottom: 16px; }
.filter-bar input { width: 100%; padding: 10px 14px; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 14px; outline: none; }
.filter-bar input:focus { border-color: #2563EB; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }

@media print {
  #sidebar { display: none; }
  main { margin-left: 0; padding: 20px; }
  .card, .scorecard, .suggestion-card { break-inside: avoid; box-shadow: none; border: 1px solid #ccc; }
}
"""


def _js():
    return """
// Filter library cards
function filterLibrary() {
  const q = document.getElementById('lib-search').value.toLowerCase();
  document.querySelectorAll('#library-grid .card').forEach(card => {
    const text = card.getAttribute('data-search').toLowerCase();
    card.style.display = text.includes(q) ? '' : 'none';
  });
}

// Smooth scroll for nav
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(link.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth' });
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    link.classList.add('active');
  });
});

// Highlight active section on scroll
const sections = document.querySelectorAll('section');
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      const link = document.querySelector('.nav-link[href=\"#' + entry.target.id + '\"]');
      if (link) link.classList.add('active');
    }
  });
}, { threshold: 0.3 });
sections.forEach(s => observer.observe(s));
"""


if __name__ == "__main__":
    path = generate_dashboard()
    # Auto-open in browser on Windows
    import subprocess
    subprocess.run(["cmd.exe", "/c", "start", "", path], check=False)
