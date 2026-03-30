---
name: cue-run
description: "Start or resume the CUE pipeline. Use this skill when the user wants to: begin the process, run the pipeline, start scouting, check pipeline status, see what step they're on, or says anything like 'start', 'run mpw', 'where was I', 'what's next', 'begin', 'kick off marketing prompt wars'."
---

# CUE Orchestrator -- Run the Pipeline

You guide the user through the CUE pipeline step by step. Check current state and tell them exactly what to do next.

## Step 1: Check Current State

Run `python src/harness.py status` to get pipeline state, or read these files:

1. `library/metadata/_index.json` -- How many ads are in the library?
2. `docs/creative-playbook.md` -- Does the playbook exist?
3. `wiom-ads/metadata/` -- Are there Wiom ads loaded?
4. `wiom-ads/contexts/` -- Any campaign contexts set up?
5. `output/scorecards/` -- Any scorecards generated?
6. `output/suggestions/` -- Any suggestions generated?
7. `output/performance/` -- Any performance data?
8. `output/optimizations/` -- Any optimization reports?
9. `output/dashboard.html` -- Does a dashboard exist?

## Step 2: Determine Next Action

Based on the state, guide the user:

### State: Empty library (no _index.json or < 5 ads)
**Tell the user:**
> **Phase 1: Build the Library**
>
> You need at least 10-15 best-in-class video ads before patterns become meaningful.
>
> Run `/cue-scout` to begin.

### State: Library has 5-15 ads, not all deconstructed
**Tell the user:**
> **Phase 2: Deconstruct**
>
> Library has [N] ads. [X] deconstructed, [Y] remaining.
>
> Run `/cue-deconstruct` to break down the remaining [Y] ads.

### State: All ads deconstructed, no playbook
**Tell the user:**
> **Phase 3: Extract Patterns**
>
> All [N] ads deconstructed. Time to find what the best ones have in common.
>
> Run `/cue-pattern` to generate the Creative Playbook.

### State: Playbook exists, no Wiom ads loaded
**Tell the user:**
> **Phase 4: Load Wiom's Ads**
>
> The Creative Playbook is ready. Now share Wiom's ads to score.
>
> Share video files or descriptions, and I'll add them to `wiom-ads/`.

### State: Wiom ads loaded, no context set
**Tell the user:**
> **Phase 4.5: Set Campaign Context** (recommended)
>
> [N] Wiom ads loaded. Before scoring, set up campaign context for a more targeted review.
>
> Run `/cue-context {ad_id}` to provide:
> - Campaign objective (awareness/clicks/downloads/conversions)
> - Creative brief (target audience, key message, tone, USP)
> - Targeting details (platform, placements, audience, budget)
>
> Or skip to `/cue-review` for a default-weight review.

### State: Wiom ads loaded (with or without context), no scorecards
**Tell the user:**
> **Phase 5: Score & Review**
>
> [N] Wiom ads ready for review.
>
> Run `/cue-review` to generate scorecards.

### State: Scorecards exist, no suggestions
**Tell the user:**
> **Phase 6: Get Suggestions**
>
> Scorecards are done. Time for improvement recommendations.
>
> Run `/cue-suggest` to generate suggestions.

### State: Suggestions exist, campaign is live with performance data
**Tell the user:**
> **Phase 7: Optimize**
>
> Campaign is live with [N] performance snapshots.
>
> Run `/cue-optimize` to compare scorecard predictions to actual performance and get targeting recommendations.

### State: Everything complete
**Tell the user:**
> **Pipeline Complete**
>
> Library: [N] ads | Playbook: [N] patterns | Scorecards: [N] | Suggestions: [N] | Optimizations: [N]
>
> What's next:
> - `/cue-context {ad_id}` -- set up a new campaign context and re-score
> - `/cue-review` -- score new Wiom ads
> - `/cue-optimize` -- paste live performance data for optimization recommendations
> - `/cue-scout` -- add more ads to strengthen the pattern library
> - `/cue-dashboard` -- refresh the dashboard

## Display Format

Always show the pipeline status bar (run `python src/harness.py status`):

```
Scout [#####] -> Deconstruct [#####] -> Pattern [#####] -> Review [#####] -> Suggest [#####] -> Optimize [.....]
   13 ads          13/13            OK           1/1           1/1            0/-
```
