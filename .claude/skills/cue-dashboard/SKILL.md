---
name: cue-dashboard
description: "Generate or refresh the CUE HTML dashboard. Use this skill when the user wants to: see results, view the dashboard, generate a report, see the output, view scorecards, see the playbook summary, or says anything like 'show me the dashboard', 'generate report', 'show output', 'open dashboard', 'view results', 'how does it look'."
---

# CUE Dashboard Generator

Generate a single-page HTML dashboard at `output/dashboard.html` that elegantly displays the full CUE pipeline output.

## Data Sources

Read all available data from:
- `library/metadata/_index.json` — ad library
- `library/metadata/*_decon.json` — deconstructions
- `docs/creative-playbook.json` — patterns + scoring rubric
- `wiom-ads/metadata/` — Wiom ad metadata + deconstructions
- `output/scorecards/*.json` — scorecards
- `output/suggestions/*.json` — suggestions

## Dashboard Sections

Build the HTML with these sections. Only show sections that have data.

### 1. Pipeline Status Header
A visual progress bar across the top showing which phases are complete:
- Scout → Deconstruct → Pattern → Review → Suggest
- Color: green (complete), amber (in progress), grey (not started)
- Show counts: "15 ads", "15/15 deconstructed", "8 patterns", "3 scorecards", "3 suggestion sets"

### 2. Best-in-Class Library (from Scout + Deconstruct)
Card grid showing each ad in the library:
- Card shows: advertiser, platform, format, duration, tier badge (color-coded)
- Click to expand: full deconstruction summary, X-factor, tags
- Filter by: tier, vertical, platform
- Sort by: date added, tier

### 3. Creative Playbook Summary (from Pattern)
Visual summary of the extracted patterns:
- Each pattern as a card: name, confidence level (badge), frequency, key finding
- Separate section for anti-patterns (red-tinted cards)
- The scoring rubric as a clean table

### 4. Wiom Scorecards (from Review)
For each scored Wiom ad:
- **Score dial**: large circular gauge showing 0-100 score
- **Dimension bars**: horizontal bar chart for each dimension (Hook, Retention, CTR, CTA, Brand) showing score out of 5, colored by performance (red < 2, amber 2-3, green > 3)
- **Anti-patterns triggered**: red flags
- **Priority gaps**: ranked list
- If multiple ads: aggregate view showing average scores + systematic gaps

### 5. Improvement Suggestions (from Suggest)
For each ad with suggestions:
- Priority-ordered cards
- Each card: suggestion title, priority badge, affected metric, the specific change, reference ad link
- "What to Keep" section highlighted in green
- Coherence check note

### 6. Aggregate Insights (if multiple Wiom ads scored)
- Radar chart comparing Wiom's average scores to best-in-class benchmarks across all dimensions
- "Systematic Gaps" — issues that appear across ALL Wiom ads
- "Systematic Strengths" — what Wiom consistently does well

## Design Requirements

**Style: Clean, modern, data-rich but not cluttered.**

- Use a dark sidebar with light content area
- Font: system font stack (Inter if available, else -apple-system, Segoe UI, etc.)
- Colors:
  - Primary: #2563EB (blue)
  - Success: #16A34A (green)
  - Warning: #D97706 (amber)
  - Danger: #DC2626 (red)
  - Background: #F8FAFC
  - Sidebar: #1E293B
  - Cards: white with subtle shadow
- Score gauges: SVG circles with animated fill
- Responsive: works on desktop and tablet
- All data embedded in the HTML (no external JS dependencies) — use inline `<script>` with vanilla JS
- CSS embedded in `<style>` block
- Collapsible sections with smooth transitions
- Print-friendly: include `@media print` styles

**Interactivity (vanilla JS only):**
- Filter/sort the library cards
- Expand/collapse deconstruction details
- Tab switching between Wiom ads in scorecard section
- Smooth scroll navigation from sidebar links

## Build Process

**DO NOT generate HTML manually. Run the Python dashboard generator:**

```bash
cd "C:\Users\divir\claude code\cue"
python src/dashboard.py
```

This is deterministic — same data always produces same HTML. The script:
1. Reads all JSON via `harness.export_dashboard_data()`
2. Builds HTML from templates in `dashboard.py`
3. Saves to `output/dashboard.html`
4. Opens in browser automatically

If the dashboard template needs changes (new sections, visual updates), edit `src/dashboard.py` — never hand-write HTML.

## Empty States

If a section has no data, show an elegant empty state:
- Grey card with icon and message
- Example: "No ads in library yet. Run /cue-scout to start building your library."
- Include the pipeline status so the user knows what step to do next

## Important
- The dashboard must work as a standalone HTML file — no server, no dependencies
- All styling and scripting inline
- Must look professional enough to share with the creative team
- Regenerate the entire file each time (don't try to patch)
- Always open in browser after generating
