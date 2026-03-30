# CUE

## Project Overview
Three-phase creative intelligence system:
- **Phase 1 (Learn):** Study best-in-class video ads that cut through clutter -- break down what makes them work, extract repeatable patterns
- **Phase 2 (Evaluate):** Review Wiom's own ads against those best-in-class patterns -- scorecard each ad, surface gaps, suggest specific improvements
- **Phase 3 (Optimize):** Once campaigns are live, compare scorecard predictions to actual performance and suggest targeting/creative adjustments

## Optimization Targets
**Leading metrics:** Video completion rate, CTR, Hook Rate, Hold Rate
**Lagging metrics:** App downloads, bookings (conversions)
**NOT optimizing for CAC in initial phase.**

## Pipeline (7 Agents)

### Phase 1: Learn from the Best
1. **Agent S (Scout)** -- Find + curate best-in-class ads from external sources
2. **Agent D (Deconstruct)** -- Break each ad down by taxonomy + explain WHY each element works
3. **Agent P (Pattern)** -- Extract repeatable patterns + anti-patterns --> Creative Playbook

### Phase 2: Evaluate Ours
4. **Agent C (Context)** -- Set up campaign context: objective, creative brief, targeting
5. **Agent R (Review)** -- Score Wiom's ads against patterns with context-aware weights --> Scorecard
6. **Agent X (Suggest)** -- Generate specific improvement recommendations

### Phase 3: Optimize Live
7. **Agent O (Optimize)** -- Compare predictions to actuals, suggest targeting adjustments, detect creative fatigue

### Future
8. **Agent B (Brief)** -- Generate pattern-informed creative briefs for new ads

## Campaign Context System

Reviews are now customizable via campaign context:
- **Objective** (required): awareness / completion / click / traffic / app_download / conversion / booking
  - Drives scoring weight distribution (e.g., app_download: CTA/Conversion gets 35% weight)
  - Drives which playbook patterns are prioritized
- **Creative Brief** (optional): target audience, key message, tone, USP, desired action
  - Enables "Brief Alignment" scoring (separate from pattern score)
  - Shows whether the ad delivers on what it promised
- **Targeting** (optional): platform, placements, audience, budget tier
  - Adjusts pattern relevance (e.g., sound-off survivability critical for Meta feed, irrelevant for YouTube pre-roll)

## Weight Engine

Scoring weights shift based on campaign objective:

| Objective | Hook | Retention | CTR Drivers | CTA/Conv | Brand |
|-----------|------|-----------|-------------|----------|-------|
| Default | 30% | 25% | 20% | 15% | 10% |
| Awareness/Completion | 35% | 30% | 15% | 10% | 10% |
| Click/Traffic | 25% | 15% | 35% | 15% | 10% |
| Download/Conversion/Booking | 20% | 15% | 20% | 35% | 10% |

## History & Versioning

All scorecards, suggestions, and optimizations are versioned:
- **Latest** always in `output/scorecards/`, `output/suggestions/`, `output/optimizations/`
- **All versions** archived in `output/history/{ad_id}/{type}/v{NNN}_{timestamp}.json`
- Dashboard shows score trends across versions
- Each version links to the campaign context that produced it

## First-Principles Constraints
1. **Study before judging** -- Build the pattern library before reviewing our own ads
2. **Patterns, not templates** -- Extract principles (why it works), not just formats
3. **Dual lens** -- Every review assesses both performance patterns AND brief alignment
4. **Human creative judgment leads** -- Scorecards inform decisions, they don't make them
5. **Frankenstein prevention** -- "Add all winning elements" destroys what made each one work
6. **Indian market context** -- Multilingual, cultural nuance, festival seasonality require human judgment
7. **Objective drives weights** -- A completion ad is scored differently from a conversion ad

## API Safety
All API interactions MUST follow `.claude/rules/ads-api-safety.md`. Primary use: Meta Ad Library reads (public), performance data pulls for validation.

## Credentials
All API keys loaded from `C:\credentials\.env` per global security rules.

## Tech Stack
- **Web UI:** Flask app at localhost:5100 -- full pipeline control from browser
- **LLM layer:** Groq (free tier, Llama 3.3 70B) via `src/llm.py`
- **Video analysis:** Gemini 2.0 for visual/audio breakdown, ffmpeg for frame extraction
- **Performance data:** Auto-pull from Meta Marketing API via `src/meta_pull.py` (read-only)
- **Ad sources:** Meta Ad Library, YouTube Ads Transparency, WARC, Cannes Lions, Think with Google India
- **Storage:** Local JSON with schema validation, versioned history

## Getting Started

**Web UI (primary):** `python src/webapp.py` -- opens browser at localhost:5100
- Set campaign context via forms
- Run Review / Suggest / Optimize with buttons
- Pull performance data from Meta API or enter manually
- View history, playbook, ad library

**CLI (alternative):** Slash commands in Claude Code

| Command | Agent | What it does |
|---------|-------|-------------|
| `/cue-run` | Orchestrator | Check pipeline status, tells you what to do next |
| `/cue-scout` | S -- Scout | Find + curate best-in-class ads into the library |
| `/cue-deconstruct` | D -- Deconstruct | Break down ads by taxonomy, explain WHY things work |
| `/cue-pattern` | P -- Pattern | Extract repeatable patterns --> Creative Playbook |
| `/cue-context` | C -- Context | Set campaign objective, brief, targeting for a Wiom ad |
| `/cue-review` | R -- Review | Score Wiom's ads vs Playbook --> Scorecard (0-100) |
| `/cue-suggest` | X -- Suggest | Specific improvement recs with reference examples |
| `/cue-optimize` | O -- Optimize | Compare predictions to actuals, suggest targeting changes |
| `/cue-dashboard` | Dashboard | Generate HTML dashboard --> opens in browser |

## Required Credentials (C:\credentials\.env)

```
GROQ_API_KEY=...              # Required for Review/Suggest/Optimize
META_ACCESS_TOKEN=...          # Required for Meta API pull
META_AD_ACCOUNT_ID=act_...     # Required for Meta API pull
```

## Project Structure
```
cue/
├── CLAUDE.md                    # This file
├── .claude/
│   ├── rules/
│   │   └── ads-api-safety.md   # API rate limit + safety rules
│   └── skills/
│       ├── cue-run/            # Orchestrator
│       ├── cue-scout/          # Agent S
│       ├── cue-deconstruct/    # Agent D
│       ├── cue-pattern/        # Agent P
│       ├── cue-context/        # Agent C (NEW)
│       ├── cue-review/         # Agent R
│       ├── cue-suggest/        # Agent X
│       ├── cue-optimize/       # Agent O (NEW)
│       └── cue-dashboard/      # HTML report generator
├── src/
│   ├── harness.py              # Core: validation, weights, state, versioning
│   ├── webapp.py               # Flask web UI (python src/webapp.py)
│   ├── llm.py                  # Groq LLM integration for review/suggest/optimize
│   ├── meta_pull.py            # Meta Marketing API performance data pull
│   ├── dashboard.py            # Standalone HTML dashboard generator
│   └── schemas/
│       ├── ad_metadata.json
│       ├── deconstruction.json
│       ├── campaign_context.json   # NEW
│       ├── scorecard.json          # UPDATED: context, version, brief alignment
│       ├── suggestion.json         # UPDATED: context, version, brief suggestions
│       ├── performance_data.json   # NEW
│       └── optimization.json       # NEW
├── docs/
│   ├── ROADMAP.md
│   ├── creative-playbook.md
│   └── creative-playbook.json
├── library/
│   └── metadata/               # Best-in-class ad library
│       ├── _index.json
│       ├── {ad_id}.json
│       └── {ad_id}_decon.json
├── wiom-ads/
│   ├── metadata/               # Wiom ad metadata
│   ├── contexts/               # Campaign contexts (NEW)
│   └── frames/                 # Extracted video frames
├── output/
│   ├── dashboard.html
│   ├── scorecards/             # Latest scorecards
│   ├── suggestions/            # Latest suggestions
│   ├── performance/            # Performance snapshots (NEW)
│   ├── optimizations/          # Optimization reports (NEW)
│   └── history/                # Versioned archive (NEW)
│       └── {ad_id}/
│           ├── scorecards/     # v001_*.json, v002_*.json, ...
│           ├── suggestions/
│           └── optimizations/
```
