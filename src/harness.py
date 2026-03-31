"""
CUE Harness — Deterministic backbone for CUE pipeline.
Handles: schema validation, state tracking, index management, file I/O,
         weight engine, pattern prioritization, campaign context, versioning.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# jsonschema is the only external dep — install: pip install jsonschema==4.23.0
from jsonschema import validate, ValidationError

# --- Paths ---------------------------------------------------------------
# On Railway, CUE_DATA_DIR points to a persistent volume. Locally, use repo root.
_data_dir = os.environ.get("CUE_DATA_DIR")
if _data_dir:
    ROOT = Path(_data_dir)
else:
    ROOT = Path(__file__).parent.parent
SCHEMAS_DIR = ROOT / "src" / "schemas"
LIBRARY_DIR = ROOT / "library" / "metadata"
WIOM_DIR = ROOT / "wiom-ads" / "metadata"
CONTEXTS_DIR = ROOT / "wiom-ads" / "contexts"
SCORECARDS_DIR = ROOT / "output" / "scorecards"
SUGGESTIONS_DIR = ROOT / "output" / "suggestions"
PERFORMANCE_DIR = ROOT / "output" / "performance"
OPTIMIZATIONS_DIR = ROOT / "output" / "optimizations"
HISTORY_DIR = ROOT / "output" / "history"
PLAYBOOK_JSON = ROOT / "docs" / "creative-playbook.json"
PLAYBOOK_MD = ROOT / "docs" / "creative-playbook.md"
STATE_FILE = ROOT / "pipeline-state.json"
DASHBOARD_FILE = ROOT / "output" / "dashboard.html"
MAPPINGS_DIR = ROOT / "wiom-ads" / "mappings"
UPLOADS_DIR = ROOT / "wiom-ads" / "uploads"
INDEX_FILE = LIBRARY_DIR / "_index.json"

# Ensure dirs exist
for d in [LIBRARY_DIR, WIOM_DIR, CONTEXTS_DIR, SCORECARDS_DIR,
          SUGGESTIONS_DIR, PERFORMANCE_DIR, OPTIMIZATIONS_DIR,
          HISTORY_DIR, MAPPINGS_DIR, UPLOADS_DIR, ROOT / "docs"]:
    d.mkdir(parents=True, exist_ok=True)


# --- Weight Engine -------------------------------------------------------
WEIGHT_PROFILES = {
    "default":      {"hook": 0.30, "retention": 0.25, "ctr_drivers": 0.20, "cta_conversion": 0.15, "brand_coherence": 0.10},
    "awareness":    {"hook": 0.35, "retention": 0.30, "ctr_drivers": 0.15, "cta_conversion": 0.10, "brand_coherence": 0.10},
    "completion":   {"hook": 0.35, "retention": 0.30, "ctr_drivers": 0.15, "cta_conversion": 0.10, "brand_coherence": 0.10},
    "click":        {"hook": 0.25, "retention": 0.15, "ctr_drivers": 0.35, "cta_conversion": 0.15, "brand_coherence": 0.10},
    "traffic":      {"hook": 0.25, "retention": 0.15, "ctr_drivers": 0.35, "cta_conversion": 0.15, "brand_coherence": 0.10},
    "app_download": {"hook": 0.20, "retention": 0.15, "ctr_drivers": 0.20, "cta_conversion": 0.35, "brand_coherence": 0.10},
    "conversion":   {"hook": 0.20, "retention": 0.15, "ctr_drivers": 0.20, "cta_conversion": 0.35, "brand_coherence": 0.10},
    "booking":      {"hook": 0.20, "retention": 0.15, "ctr_drivers": 0.20, "cta_conversion": 0.35, "brand_coherence": 0.10},
}


def get_weight_profile(objective_type: str) -> dict:
    """Return dimension weights for a given campaign objective."""
    return WEIGHT_PROFILES.get(objective_type, WEIGHT_PROFILES["default"])


def get_priority_patterns(objective_type: str) -> list:
    """Return playbook pattern IDs prioritized for this objective."""
    priority_map = {
        "default":      ["C1", "C2", "C4", "K1", "K2", "D1", "D2", "D3", "C3"],
        "awareness":    ["C1", "C2", "C3", "C4", "D1", "D2", "K1", "K2", "D3"],
        "completion":   ["C1", "C2", "C3", "C4", "D1", "D2", "K1", "K2", "D3"],
        "click":        ["K1", "K2", "C1", "C2", "C4", "D1", "C3", "D2", "D3"],
        "traffic":      ["K1", "K2", "C1", "C2", "C4", "D1", "C3", "D2", "D3"],
        "app_download": ["D1", "D2", "D3", "K1", "K2", "C1", "C2", "C4", "C3"],
        "conversion":   ["D1", "D2", "D3", "K1", "K2", "C1", "C2", "C4", "C3"],
        "booking":      ["D1", "D2", "D3", "K1", "K2", "C1", "C2", "C4", "C3"],
    }
    return priority_map.get(objective_type, priority_map["default"])


# Placement-aware pattern relevance modifiers
PLACEMENT_PATTERN_MODIFIERS = {
    "feed":      {"K2": 1.5, "C3": 1.3, "C1": 1.2},
    "stories":   {"K2": 1.5, "C3": 1.5, "C1": 1.3},
    "reels":     {"K2": 1.4, "C3": 1.3, "C1": 1.3},
    "pre_roll":  {"K2": 0.5, "C2": 1.3, "C4": 1.3},
    "mid_roll":  {"K2": 0.5, "C2": 1.3, "C4": 1.3},
    "shorts":    {"K2": 1.2, "C3": 1.5, "C1": 1.3},
    "in_stream": {"K2": 0.5, "C2": 1.3, "C4": 1.3},
    "explore":   {"K2": 1.3, "C1": 1.4, "C3": 1.2},
}


def adjust_pattern_relevance(base_patterns: list, placements: list) -> list:
    """Given priority-ordered patterns and target placements, return
    patterns sorted by relevance with multipliers."""
    pattern_scores = {p: 1.0 for p in base_patterns}
    for placement in placements:
        mods = PLACEMENT_PATTERN_MODIFIERS.get(placement, {})
        for pid, mult in mods.items():
            if pid in pattern_scores:
                pattern_scores[pid] *= mult
    return sorted(pattern_scores.items(), key=lambda x: -x[1])


def calculate_overall_score(dimension_scores: dict, weight_profile: dict) -> float:
    """Calculate weighted overall score from dimension scores and weights.
    dimension_scores: {"hook": 3, "retention": 4, ...} (1-5 scale)
    Returns 0-100 scale."""
    total = sum(
        dimension_scores.get(dim, 3) * weight * 20
        for dim, weight in weight_profile.items()
    )
    return round(total, 1)


# --- Schema Loading ------------------------------------------------------
_schema_cache = {}

def _load_schema(name: str) -> dict:
    if name not in _schema_cache:
        path = SCHEMAS_DIR / f"{name}.json"
        with open(path, "r", encoding="utf-8") as f:
            _schema_cache[name] = json.load(f)
    return _schema_cache[name]


def validate_data(data: dict, schema_name: str) -> tuple:
    """Validate data against a named schema. Returns (ok, error_message)."""
    try:
        schema = _load_schema(schema_name)
        validate(instance=data, schema=schema)
        return True, ""
    except ValidationError as e:
        return False, f"Schema '{schema_name}' validation failed: {e.message} at {list(e.absolute_path)}"


# --- Index Management ----------------------------------------------------
def load_index() -> list:
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_index(index: list):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def next_ad_id() -> str:
    index = load_index()
    if not index:
        return "ad_001"
    max_num = max(int(entry["id"].replace("ad_", "")) for entry in index)
    return f"ad_{max_num + 1:03d}"


def check_duplicate(url: str = None, advertiser: str = None, description: str = None):
    """Returns existing ad_id if duplicate found, else None."""
    index = load_index()
    for entry in index:
        if url and entry.get("url") == url:
            return entry["id"]
        if advertiser and description:
            if (entry.get("advertiser", "").lower() == advertiser.lower() and
                _similarity(entry.get("description", ""), description) > 0.7):
                return entry["id"]
    return None


def _similarity(a: str, b: str) -> float:
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))


# --- Ad CRUD -------------------------------------------------------------
def save_ad(data: dict) -> tuple:
    """Validate and save ad metadata. Returns (ok, message)."""
    ok, err = validate_data(data, "ad_metadata")
    if not ok:
        return False, err
    dup = check_duplicate(url=data.get("url"), advertiser=data.get("advertiser"), description=data.get("description"))
    if dup:
        return False, f"Duplicate detected: matches existing {dup}"
    ad_file = LIBRARY_DIR / f"{data['id']}.json"
    with open(ad_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    index = load_index()
    index_entry = {
        "id": data["id"],
        "advertiser": data["advertiser"],
        "platform": data["platform"],
        "vertical": data["vertical"],
        "tier": data["tier"],
        "deconstructed": data["deconstructed"],
        "url": data.get("url", ""),
        "description": data.get("description", "")[:100]
    }
    index.append(index_entry)
    save_index(index)
    _update_state()
    return True, f"Saved {data['id']} ({data['advertiser']})"


def save_deconstruction(data: dict) -> tuple:
    """Validate and save deconstruction. Mark ad as deconstructed.
    Handles both library ads (ad_XXX) and Wiom ads (wiom_XXX).
    Schema validation is informational — file is always saved if JSON is valid."""
    ok, err = validate_data(data, "deconstruction")
    # Don't block on schema validation — LLM enum mismatches shouldn't kill the pipeline
    validation_note = f" (schema warning: {err})" if not ok else ""
    ad_id = data["ad_id"]
    is_wiom = ad_id.startswith("wiom_")

    # Save decon file to appropriate directory
    save_dir = WIOM_DIR if is_wiom else LIBRARY_DIR
    decon_file = save_dir / f"{ad_id}_decon.json"
    with open(decon_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Mark metadata as deconstructed
    ad_file = save_dir / f"{ad_id}.json"
    if ad_file.exists():
        with open(ad_file, "r", encoding="utf-8") as f:
            ad = json.load(f)
        ad["deconstructed"] = True
        with open(ad_file, "w", encoding="utf-8") as f:
            json.dump(ad, f, indent=2, ensure_ascii=False)

    if not is_wiom:
        index = load_index()
        for entry in index:
            if entry["id"] == ad_id:
                entry["deconstructed"] = True
        save_index(index)

    _update_state()
    return True, f"Deconstruction saved for {ad_id}{validation_note}"


# --- Campaign Context CRUD -----------------------------------------------
def save_campaign_context(data: dict) -> tuple:
    """Validate and save a campaign context. Returns (ok, message)."""
    ok, err = validate_data(data, "campaign_context")
    if not ok:
        return False, err
    ctx_id = data["context_id"]
    ad_id = data["ad_id"]
    out = CONTEXTS_DIR / f"{ad_id}_{ctx_id}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    _update_state()
    return True, f"Context saved: {ctx_id} for {ad_id}"


def load_campaign_context(ad_id: str, context_id: str = None):
    """Load latest context for an ad, or a specific one by context_id."""
    if context_id:
        path = CONTEXTS_DIR / f"{ad_id}_{context_id}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    # Load latest by modification time
    candidates = sorted(
        CONTEXTS_DIR.glob(f"{ad_id}_ctx_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if candidates:
        with open(candidates[0], "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def next_context_id(ad_id: str) -> str:
    existing = list(CONTEXTS_DIR.glob(f"{ad_id}_ctx_*.json"))
    return f"ctx_{len(existing) + 1:03d}"


# --- Versioned Scorecard CRUD --------------------------------------------
def save_scorecard(data: dict) -> tuple:
    ok, err = validate_data(data, "scorecard")
    if not ok:
        return False, err
    ad_id = data["ad_id"]
    version = data.get("version", 1)

    # Save versioned copy to history
    history_dir = HISTORY_DIR / ad_id / "scorecards"
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_file = history_dir / f"v{version:03d}_{ts}.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Save current (latest) to output/scorecards
    out = SCORECARDS_DIR / f"{ad_id}_scorecard.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    _update_state()
    return True, f"Scorecard v{version} saved for {ad_id} -- score: {data['overall_score']}/100"


def save_suggestion(data: dict) -> tuple:
    ok, err = validate_data(data, "suggestion")
    if not ok:
        return False, err
    ad_id = data["ad_id"]
    version = data.get("version", 1)

    # Save versioned copy to history
    history_dir = HISTORY_DIR / ad_id / "suggestions"
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_file = history_dir / f"v{version:03d}_{ts}.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Save current (latest)
    out = SUGGESTIONS_DIR / f"{ad_id}_suggestions.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    _update_state()
    return True, f"Suggestions v{version} saved for {ad_id} -- {len(data['suggestions'])} suggestions"


# --- Performance Data CRUD -----------------------------------------------
def save_performance_data(data: dict) -> tuple:
    ok, err = validate_data(data, "performance_data")
    if not ok:
        return False, err
    out = PERFORMANCE_DIR / f"{data['ad_id']}_{data['perf_id']}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    _update_state()
    return True, f"Performance snapshot saved: {data['perf_id']} for {data['ad_id']}"


def load_performance_history(ad_id: str) -> list:
    """Load all performance snapshots for an ad, sorted chronologically."""
    snapshots = []
    for f in sorted(PERFORMANCE_DIR.glob(f"{ad_id}_perf_*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            snapshots.append(json.load(fh))
    return snapshots


def next_perf_id(ad_id: str) -> str:
    existing = list(PERFORMANCE_DIR.glob(f"{ad_id}_perf_*.json"))
    return f"perf_{len(existing) + 1:03d}"


def detect_fatigue(snapshots: list) -> dict:
    """Analyze performance snapshots for creative fatigue signals.
    Returns {"status": ..., "evidence": ..., "estimated_remaining_days": ...}"""
    if len(snapshots) < 2:
        return {"status": "no_fatigue", "evidence": "Insufficient data (need 2+ snapshots)", "estimated_remaining_days": None}

    latest = snapshots[-1]["metrics"]
    prev = snapshots[-2]["metrics"]

    ctr_current = latest.get("ctr")
    ctr_prev = prev.get("ctr")
    freq_current = latest.get("frequency")

    signals = []

    # CTR decline check
    if ctr_current is not None and ctr_prev is not None and ctr_prev > 0:
        ctr_change = (ctr_current - ctr_prev) / ctr_prev
        if ctr_change < -0.20:
            signals.append(f"CTR dropped {abs(ctr_change)*100:.0f}% ({ctr_prev:.3f} -> {ctr_current:.3f})")
        elif ctr_change < -0.10:
            signals.append(f"CTR declining {abs(ctr_change)*100:.0f}%")

    # Frequency check
    if freq_current is not None and freq_current > 3.0:
        signals.append(f"High frequency: {freq_current:.1f} (threshold: 3.0)")
    elif freq_current is not None and freq_current > 2.5:
        signals.append(f"Frequency approaching threshold: {freq_current:.1f}")

    # Completion rate decline
    vcr_current = latest.get("video_completion_rate")
    vcr_prev = prev.get("video_completion_rate")
    if vcr_current is not None and vcr_prev is not None and vcr_prev > 0:
        vcr_change = (vcr_current - vcr_prev) / vcr_prev
        if vcr_change < -0.15:
            signals.append(f"Completion rate dropped {abs(vcr_change)*100:.0f}%")

    if len(signals) >= 2:
        status = "fatigued" if freq_current and freq_current > 3.0 else "fatiguing"
    elif len(signals) == 1:
        status = "early_signs"
    else:
        status = "no_fatigue"

    return {
        "status": status,
        "evidence": "; ".join(signals) if signals else "No fatigue signals detected",
        "estimated_remaining_days": None
    }


# --- Optimization CRUD ---------------------------------------------------
def save_optimization(data: dict) -> tuple:
    ok, err = validate_data(data, "optimization")
    if not ok:
        return False, err
    ad_id = data["ad_id"]
    opt_id = data["opt_id"]

    # Save versioned copy to history
    history_dir = HISTORY_DIR / ad_id / "optimizations"
    history_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    history_file = history_dir / f"{opt_id}_{ts}.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Save current (latest)
    out = OPTIMIZATIONS_DIR / f"{ad_id}_{opt_id}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    _update_state()
    return True, f"Optimization saved: {opt_id} for {ad_id}"


def next_opt_id(ad_id: str) -> str:
    existing = list(OPTIMIZATIONS_DIR.glob(f"{ad_id}_opt_*.json"))
    return f"opt_{len(existing) + 1:03d}"


# --- Campaign Mapping CRUD ------------------------------------------------
def save_campaign_mapping(data: dict) -> tuple:
    """Save a mapping between CUE ad ID and platform ad/campaign IDs."""
    ad_id = data["ad_id"]
    platform = data["platform"]
    out = MAPPINGS_DIR / f"{ad_id}_{platform}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return True, f"Mapping saved: {ad_id} -> {platform}"


def load_campaign_mapping(ad_id: str, platform: str = "meta"):
    """Load campaign mapping for an ad."""
    path = MAPPINGS_DIR / f"{ad_id}_{platform}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_all_mappings() -> list:
    """Load all campaign mappings."""
    mappings = []
    for f in sorted(MAPPINGS_DIR.glob("*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            mappings.append(json.load(fh))
    return mappings


# --- History Loader -------------------------------------------------------
def load_history(ad_id: str, artifact_type: str = "scorecards") -> list:
    """Load all versioned artifacts for an ad.
    artifact_type: scorecards|suggestions|optimizations"""
    history_dir = HISTORY_DIR / ad_id / artifact_type
    if not history_dir.exists():
        return []
    results = []
    for f in sorted(history_dir.glob("v*.json")):
        with open(f, "r", encoding="utf-8") as fh:
            item = json.load(fh)
            item["_history_file"] = f.name
            results.append(item)
    # Also load optimization files (opt_XXX pattern)
    if artifact_type == "optimizations":
        for f in sorted(history_dir.glob("opt_*.json")):
            with open(f, "r", encoding="utf-8") as fh:
                item = json.load(fh)
                item["_history_file"] = f.name
                if item not in results:
                    results.append(item)
    return results


# --- Pipeline State -------------------------------------------------------
def _update_state():
    """Rebuild pipeline state from files on disk."""
    index = load_index()
    total_ads = len(index)
    deconstructed = sum(1 for e in index if e.get("deconstructed"))
    playbook_exists = PLAYBOOK_JSON.exists()

    wiom_ads = [f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_") and not f.stem.endswith("_decon")]
    scorecards = [f.stem.replace("_scorecard", "") for f in SCORECARDS_DIR.glob("*_scorecard.json")]
    suggestions = [f.stem.replace("_suggestions", "") for f in SUGGESTIONS_DIR.glob("*_suggestions.json")]
    contexts = [f.stem for f in CONTEXTS_DIR.glob("*.json")]
    performance = [f.stem for f in PERFORMANCE_DIR.glob("*_perf_*.json")]
    optimizations = [f.stem for f in OPTIMIZATIONS_DIR.glob("*_opt_*.json")]

    state = {
        "last_updated": datetime.now().isoformat(),
        "library": {
            "total_ads": total_ads,
            "deconstructed": deconstructed,
            "not_deconstructed": total_ads - deconstructed,
            "by_tier": _count_tiers(index)
        },
        "playbook_exists": playbook_exists,
        "wiom_ads": {
            "total": len(wiom_ads),
            "ids": wiom_ads
        },
        "contexts": {
            "total": len(contexts),
            "ids": contexts
        },
        "scorecards": {
            "total": len(scorecards),
            "ids": scorecards
        },
        "suggestions": {
            "total": len(suggestions),
            "ids": suggestions
        },
        "performance": {
            "total": len(performance),
            "ids": performance
        },
        "optimizations": {
            "total": len(optimizations),
            "ids": optimizations
        },
        "current_phase": _determine_phase(total_ads, deconstructed, playbook_exists, len(wiom_ads), len(scorecards), len(suggestions)),
        "dashboard_exists": DASHBOARD_FILE.exists()
    }

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    return state


def _count_tiers(index):
    tiers = {"exceptional": 0, "strong": 0, "reference": 0, "unrated": 0}
    for e in index:
        t = e.get("tier")
        if t in tiers:
            tiers[t] += 1
        else:
            tiers["unrated"] += 1
    return tiers


def _determine_phase(total, decon, playbook, wiom, scores, suggests):
    if total < 5:
        return "scout"
    if decon < total:
        return "deconstruct"
    if not playbook:
        return "pattern"
    if wiom == 0:
        return "load_wiom_ads"
    if scores < wiom:
        return "review"
    if suggests < scores:
        return "suggest"
    return "complete"


def get_state() -> dict:
    return _update_state()


def get_progress_bar() -> str:
    s = get_state()
    lib = s["library"]
    total = lib["total_ads"]
    decon = lib["deconstructed"]
    pb = s["playbook_exists"]
    wiom = s["wiom_ads"]["total"]
    sc = s["scorecards"]["total"]
    su = s["suggestions"]["total"]
    perf = s["performance"]["total"]
    opt = s["optimizations"]["total"]

    def bar(filled, capacity):
        if capacity == 0:
            return "[.....]"
        ratio = min(filled / capacity, 1.0)
        full = round(ratio * 5)
        return "[" + "#" * full + "." * (5 - full) + "]"

    scout_bar = bar(total, 15)
    decon_bar = bar(decon, max(total, 1))
    pattern_bar = bar(1 if pb else 0, 1)
    review_bar = bar(sc, max(wiom, 1))
    suggest_bar = bar(su, max(sc, 1))
    optimize_bar = bar(opt, max(perf, 1)) if perf > 0 else "[.....]"

    line1 = f"Scout {scout_bar} -> Deconstruct {decon_bar} -> Pattern {pattern_bar} -> Review {review_bar} -> Suggest {suggest_bar} -> Optimize {optimize_bar}"
    line2 = f"   {total} ads          {decon}/{total}            {'OK' if pb else '-'}           {sc}/{wiom if wiom else '-'}           {su}/{sc if sc else '-'}            {opt}/{perf if perf else '-'}"
    return f"{line1}\n{line2}"


# --- Dashboard Data Export ------------------------------------------------
def export_dashboard_data() -> dict:
    """Collect all data needed for dashboard rendering."""
    state = get_state()
    index = load_index()

    deconstructions = {}
    for f in LIBRARY_DIR.glob("*_decon.json"):
        ad_id = f.stem.replace("_decon", "")
        with open(f, "r", encoding="utf-8") as fh:
            deconstructions[ad_id] = json.load(fh)

    playbook = None
    if PLAYBOOK_JSON.exists():
        with open(PLAYBOOK_JSON, "r", encoding="utf-8") as f:
            playbook = json.load(f)

    scorecards = {}
    for f in SCORECARDS_DIR.glob("*_scorecard.json"):
        ad_id = f.stem.replace("_scorecard", "")
        with open(f, "r", encoding="utf-8") as fh:
            scorecards[ad_id] = json.load(fh)

    suggestions = {}
    for f in SUGGESTIONS_DIR.glob("*_suggestions.json"):
        ad_id = f.stem.replace("_suggestions", "")
        with open(f, "r", encoding="utf-8") as fh:
            suggestions[ad_id] = json.load(fh)

    contexts = {}
    for f in CONTEXTS_DIR.glob("*.json"):
        with open(f, "r", encoding="utf-8") as fh:
            ctx = json.load(fh)
            contexts[f.stem] = ctx

    performance = {}
    for f in sorted(PERFORMANCE_DIR.glob("*_perf_*.json")):
        ad_id = f.stem.split("_perf_")[0]
        if ad_id not in performance:
            performance[ad_id] = []
        with open(f, "r", encoding="utf-8") as fh:
            performance[ad_id].append(json.load(fh))

    optimizations = {}
    for f in OPTIMIZATIONS_DIR.glob("*_opt_*.json"):
        ad_id = f.stem.split("_opt_")[0]
        with open(f, "r", encoding="utf-8") as fh:
            optimizations[ad_id] = json.load(fh)

    # Load history for each wiom ad
    history = {}
    wiom_ads = [f.stem for f in WIOM_DIR.glob("*.json") if not f.stem.startswith("_")]
    for ad_id in wiom_ads:
        history[ad_id] = {
            "scorecards": load_history(ad_id, "scorecards"),
            "suggestions": load_history(ad_id, "suggestions"),
            "optimizations": load_history(ad_id, "optimizations"),
        }

    return {
        "state": state,
        "index": index,
        "deconstructions": deconstructions,
        "playbook": playbook,
        "scorecards": scorecards,
        "suggestions": suggestions,
        "contexts": contexts,
        "performance": performance,
        "optimizations": optimizations,
        "history": history
    }


# --- CLI ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        print(get_progress_bar())
        print()
        s = get_state()
        print(f"Phase: {s['current_phase']}")
        print(f"Library: {s['library']['total_ads']} ads ({s['library']['deconstructed']} deconstructed)")
        print(f"Playbook: {'exists' if s['playbook_exists'] else 'not yet'}")
        print(f"Wiom ads: {s['wiom_ads']['total']}")
        print(f"Contexts: {s['contexts']['total']}")
        print(f"Scorecards: {s['scorecards']['total']}")
        print(f"Suggestions: {s['suggestions']['total']}")
        print(f"Performance snapshots: {s['performance']['total']}")
        print(f"Optimizations: {s['optimizations']['total']}")

    elif cmd == "validate":
        schema_name = sys.argv[2]
        file_path = sys.argv[3]
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ok, err = validate_data(data, schema_name)
        if ok:
            print(f"OK Valid {schema_name}")
        else:
            print(f"FAIL {err}")
            sys.exit(1)

    elif cmd == "next-id":
        print(next_ad_id())

    elif cmd == "weights":
        objective = sys.argv[2] if len(sys.argv) > 2 else "default"
        profile = get_weight_profile(objective)
        patterns = get_priority_patterns(objective)
        print(f"Objective: {objective}")
        print(f"Weights: {json.dumps(profile, indent=2)}")
        print(f"Priority patterns: {patterns}")

    elif cmd == "history":
        ad_id = sys.argv[2]
        artifact_type = sys.argv[3] if len(sys.argv) > 3 else "scorecards"
        h = load_history(ad_id, artifact_type)
        print(f"{len(h)} {artifact_type} versions for {ad_id}")
        for item in h:
            print(f"  {item.get('_history_file', '?')}: score={item.get('overall_score', '?')}")

    elif cmd == "export-dashboard":
        data = export_dashboard_data()
        print(json.dumps(data, indent=2, ensure_ascii=False))

    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python harness.py [status|validate|next-id|weights|history|export-dashboard]")
        sys.exit(1)
