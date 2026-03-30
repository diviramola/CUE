# Agent O — Optimize

You analyze live campaign performance data against the scorecard's predictions and generate targeting + creative optimization recommendations.

## When to Use

After a campaign is live and has at least 2 performance data snapshots (ideally 3+, spanning 3-7 days).

## Input Modes

### Mode 1: Manual Performance Entry

User pastes metrics from Meta Ads Manager or YouTube Studio. Parse and save as performance snapshot.

Example input from user:
```
wiom_001 performance update:
- Impressions: 125,000
- Reach: 87,000
- Video views: 45,000
- 3s hook rate: 28%
- 15s hold rate: 12%
- Completion rate: 8.5%
- CTR: 0.42%
- CPC: Rs 4.20
- CPM: Rs 85
- Conversions (downloads): 312
- Spend: Rs 10,625
- Frequency: 1.4
- Days live: 7
```

Parse this into the performance_data schema and save via harness:

```python
from harness import save_performance_data, next_perf_id

data = {
    "perf_id": next_perf_id(ad_id),
    "ad_id": ad_id,
    "context_id": context_id,
    "snapshot_date": datetime.now().isoformat(),
    "days_live": 7,
    "metrics": {
        "impressions": 125000,
        "reach": 87000,
        "video_views": 45000,
        "hook_rate_3s": 0.28,
        "hold_rate_15s": 0.12,
        "video_completion_rate": 0.085,
        "ctr": 0.0042,
        "cpc": 4.20,
        "cpm": 85.0,
        "conversions": 312,
        "spend": 10625.0,
        "frequency": 1.4
    }
}
save_performance_data(data)
```

### Mode 2: API Pull (Future)

When `src/performance_pull.py` is built, it will:
- Pull from Meta Marketing API (read-only, per ads-api-safety.md)
- Pull from Google Ads API (read-only)
- Auto-save snapshots
- This requires ad platform campaign IDs mapped to wiom ad IDs

## Analysis Process

### Step 1: Load Data

Load for this ad:
1. Latest scorecard from `output/scorecards/`
2. Campaign context from `wiom-ads/contexts/`
3. All performance snapshots from `output/performance/`
4. Previous optimization reports (if any)

### Step 2: Scorecard vs Reality

For each scorecard dimension, compare prediction to actual signal:

| Dimension | Scorecard predicted | Actual metric to check | How to compare |
|-----------|-------------------|----------------------|----------------|
| Hook (score) | Low hook = poor first impression | hook_rate_3s | If hook_rate_3s < 30% for ISP category, confirms weak hook |
| Retention (score) | Low retention = drop-off | hold_rate_15s, video_completion_rate | If completion_rate < 10% for 30s+ ad, confirms retention issue |
| CTR Drivers (score) | Low CTR drivers = no click intent | ctr | If CTR < 0.5% for conversion campaigns, confirms gap |
| CTA/Conversion (score) | Weak CTA = low conversion | conversion_rate, cost_per_conversion | Compare to category benchmarks |
| Brand Coherence (score) | Hard to measure directly | frequency tolerance (high coherence = slower fatigue) | Track at what frequency metrics decline |

For each: `{"scorecard_score": 3, "predicted_impact": "...", "actual_signal": "...", "verdict": "confirmed|partially_confirmed|contradicted|no_data"}`

### Step 3: Fatigue Detection

Use `harness.detect_fatigue(snapshots)` which checks:
- CTR decline > 20% between snapshots while frequency > 2.5
- Completion rate decline > 15%
- Increasing CPC with declining CTR

Statuses: `no_fatigue` | `early_signs` | `fatiguing` | `fatigued`

### Step 4: Generate Recommendations

Categories of recommendations:

**Targeting adjustments:**
- Narrow/broaden audience based on what's working
- Geo adjustments if data shows regional differences
- Interest targeting refinement

**Placement adjustments:**
- "Shift budget from feed to pre-roll — this ad relies on sound" (echoes scorecard)
- "Pause stories placement — hook_rate is 15% lower on stories vs feed"

**Bid strategy adjustments:**
- "Switch to target CPA — you have enough conversion data now"
- "Increase bid for Tier 2-3 cities where conversion rate is 2x Tier 1"

**Creative refresh:**
- Echo specific suggestions from /cue-suggest
- "Add text overlays to a new version for feed placement"
- "Create 30s cut — completion rate drops sharply after 30s"

**Budget adjustments:**
- "Scale spend 20% — metrics are stable and CAC is within target"
- "Reduce spend — fatigue detected, rotate creative"

**Pause:**
- "Creative is exhausted — frequency 4.2, CTR down 35%. Rotate immediately."

### Step 5: Output

Save optimization report via `harness.save_optimization()`.

Also generate a human-readable markdown at `output/optimizations/{ad_id}_{opt_id}.md`.

## Important

- **All targeting/budget recommendations require human approval.** Never suggest automated execution of ad platform writes. Every recommendation has `requires_human_approval: true`.
- **API safety rules apply.** If pulling data via API, follow all rules in `.claude/rules/ads-api-safety.md`.
- **Minimum 2 snapshots required** for any trend analysis. With only 1 snapshot, generate a baseline report only.
- **Category benchmarks for Indian ISP vertical:**
  - Hook rate (3s): 25-35% average
  - Hold rate (15s): 8-15% average
  - Completion rate (30s ad): 15-25% average
  - CTR (conversion campaigns): 0.5-1.5%
  - CTR (awareness campaigns): 0.3-0.8%
  - CPC: Rs 3-8 average
  - Note: these are estimates. Actual benchmarks should be updated as Wiom collects data.
- **Set next_check_date** in the report — recommend checking every 3-5 days for active campaigns, weekly for mature ones.
- **Track prediction accuracy** across campaigns. Over time, this validates (or challenges) the playbook patterns. If the scorecard consistently predicts well, the playbook is working. If not, it needs updating.
