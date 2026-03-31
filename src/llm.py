"""
CUE LLM — Groq API integration for running pipeline actions from the web app.

Uses Llama 3.3 70B via Groq free tier.
All credentials from C:\\credentials\\.env.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Load from local credentials file if it exists (dev), otherwise use env vars (Railway)
_local_env = Path(r"C:\credentials\.env")
if _local_env.exists():
    load_dotenv(_local_env)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MODEL = "llama-3.3-70b-versatile"

# Paths for loading data
import sys
sys.path.insert(0, str(Path(__file__).parent))
from harness import (
    ROOT, LIBRARY_DIR, WIOM_DIR, PLAYBOOK_JSON, PLAYBOOK_MD,
    SCORECARDS_DIR, SUGGESTIONS_DIR, CONTEXTS_DIR,
    get_weight_profile, get_priority_patterns, adjust_pattern_relevance,
    calculate_overall_score, load_campaign_context, load_history,
    save_scorecard, save_suggestion, save_deconstruction,
    load_performance_history, detect_fatigue,
    save_optimization, next_opt_id,
)


def _check_credentials():
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "Missing GROQ_API_KEY in C:\\credentials\\.env. "
            "Get a free key at console.groq.com and add it."
        )


def _call_groq(system_prompt, user_prompt, temperature=0.3, max_tokens=4000):
    """Call Groq API and return the text response."""
    _check_credentials()
    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _load_playbook_summary():
    """Load playbook patterns and anti-patterns for prompts."""
    if PLAYBOOK_JSON.exists():
        with open(PLAYBOOK_JSON, "r", encoding="utf-8") as f:
            pb = json.load(f)
        patterns = "\n".join(
            f"- {p['id']} {p['name']}: {p['description']} (confidence: {p['confidence']})"
            for p in pb.get("patterns", [])
        )
        anti = "\n".join(
            f"- {a['id']} {a['name']}: {a['description']} (severity: {a['severity']})"
            for a in pb.get("anti_patterns", [])
        )
        return patterns, anti, pb
    return "", "", {}


def _load_ad_deconstruction(ad_id):
    """Load deconstruction for a Wiom ad or library ad."""
    for dir in [WIOM_DIR, LIBRARY_DIR]:
        path = dir / f"{ad_id}_decon.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    return None


def _load_ad_metadata(ad_id):
    """Load metadata for a Wiom ad."""
    path = WIOM_DIR / f"{ad_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _extract_json(text):
    """Extract JSON from LLM response that may contain markdown fences."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())


# ---------------------------------------------------------------------------
# Run Deconstruct
# ---------------------------------------------------------------------------

def run_deconstruct(ad_id):
    """Deconstruct a Wiom ad using Groq LLM. Returns (decon_dict, message)."""
    meta = _load_ad_metadata(ad_id)
    if not meta:
        return None, f"No metadata found for {ad_id}. Add metadata first."

    # List frame files if available
    frames_dir = WIOM_DIR.parent / "frames" / ad_id
    frame_files = sorted(frames_dir.glob("*.jpg")) if frames_dir.exists() else []
    frames_text = f"{len(frame_files)} frames extracted at: {frames_dir}" if frame_files else "No frames extracted."

    # Load a few example deconstructions for format reference
    examples = []
    for f in sorted(LIBRARY_DIR.glob("*_decon.json"))[:2]:
        with open(f, "r", encoding="utf-8") as fh:
            examples.append(json.load(fh))
    ex_text = "\n".join(f"EXAMPLE ({e['ad_id']}): hook.type={e['hook']['type']}, narrative.arc_type={e['narrative']['arc_type']}, emotional.primary_emotion={e['emotional']['primary_emotion']}" for e in examples)

    system_prompt = f"""You are CUE Agent D — a creative deconstruction expert for Indian video ads.

Analyze the provided Wiom ad metadata and deconstruct it using the 9-dimension taxonomy below.
Base your analysis on the description, transcript, tags, and any frame information provided.

EXAMPLES FOR REFERENCE:
{ex_text}

IMPORTANT ENUM VALUES — you MUST use exactly these values:

hook.type: question | shocking_stat | problem_statement | visual_surprise | testimonial | product_demo | curiosity_gap | controversy | relatable_moment
hook.audio_hook: music_hit | voiceover | sound_effect | silence | dialogue
narrative.arc_type: problem_solution | before_after | testimonial | demo | listicle | comparison | day_in_life | ugc_style | montage | single_scene
narrative.tension_payoff: buildup | front_loaded
pacing.duration_bucket: 6s | 15s | 30s | 60s+
audio.music_type: trending | original_score | no_music | sound_effects_only
audio.voiceover_tone: authority | conversational | energetic | emotional (or null)
visual.talent_type: actor | real_user_ugc | influencer | no_talent | animation
visual.production_quality: high | mid | lo_fi_ugc
visual.text_overlay_density: none | minimal | heavy
visual.color_mood: bright | muted | dark | brand_colored
visual.product_visibility: always_visible | reveal_moment | absent_until_cta
cta.type: download_app | visit_site | book_now | learn_more | shop | sign_up | other
cta.timing: early | mid | late | multiple
cta.visual_treatment: text_overlay | button_mockup | voiceover_only | combined
cta.urgency_element: limited_time | social_proof | scarcity | none
brand.logo_presence: always_visible | bookend | end_card_only | embedded_naturally
emotional.primary_emotion: humor | aspiration | fear_urgency | relatability | pride | warmth
emotional.hinglish_level: pure_hindi | pure_english | light_mix | heavy_code_switching

Output ONLY valid JSON (no markdown, no explanation):
{{
  "ad_id": "{ad_id}",
  "hook": {{
    "type": "<enum>",
    "face_first_frame": <bool>,
    "text_overlay_first_frame": <bool>,
    "brand_visible_3s": <bool>,
    "audio_hook": "<enum>",
    "language": "<string>",
    "effectiveness_note": "<30+ char analysis of why this hook works or doesn't>"
  }},
  "narrative": {{
    "arc_type": "<enum>",
    "tension_payoff": "<enum>",
    "num_scenes": <int>,
    "effectiveness_note": "<30+ char analysis>"
  }},
  "pacing": {{
    "duration_bucket": "<enum>",
    "cuts_per_15s": <number>,
    "pace_changes": ["<timestamp: description>"],
    "pattern_interrupts": ["<description>"],
    "retention_note": "<30+ char analysis>"
  }},
  "audio": {{
    "music_type": "<enum>",
    "voiceover": <bool>,
    "voiceover_tone": "<enum or null>",
    "language": "<string>",
    "music_visual_sync": <bool>,
    "audio_note": "<30+ char analysis>"
  }},
  "visual": {{
    "talent_type": "<enum>",
    "production_quality": "<enum>",
    "text_overlay_density": "<enum>",
    "color_mood": "<enum>",
    "product_visibility": "<enum>",
    "visual_note": "<30+ char analysis>"
  }},
  "cta": {{
    "type": "<enum>",
    "timing": "<enum>",
    "visual_treatment": "<enum>",
    "urgency_element": "<enum>",
    "cta_note": "<30+ char analysis>"
  }},
  "brand": {{
    "logo_presence": "<enum>",
    "brand_first_named_seconds": <number>,
    "brand_voice_consistent": <bool>,
    "brand_note": "<30+ char analysis>"
  }},
  "emotional": {{
    "primary_emotion": "<enum>",
    "cultural_specificity": ["<cultural element>"],
    "hinglish_level": "<enum>",
    "cultural_note": "<30+ char analysis>"
  }},
  "x_factor": "<50+ char unique creative insight — what makes this ad distinctive>",
  "lessons_for_wiom": ["<20+ char lesson 1>", "<20+ char lesson 2>", "<20+ char lesson 3>"]
}}"""

    # Extract transcript explicitly so the LLM doesn't miss it buried in metadata JSON
    transcript_text = meta.get("transcript", "")
    transcript_lang = meta.get("language", "")
    transcript_section = (
        f"\nAUDIO TRANSCRIPT ({transcript_lang}):\n{transcript_text}"
        if transcript_text else
        "\nAUDIO TRANSCRIPT: Not available — infer from description and tags."
    )

    user_prompt = f"""Deconstruct this Wiom ad:

AD METADATA:
{json.dumps(meta, indent=2, ensure_ascii=False)}

FRAMES: {frames_text}
{transcript_section}

Use the transcript to determine:
- hook.audio_hook and audio.voiceover (is there voiceover? what language?)
- emotional.hinglish_level (what mix of Hindi/English is in the dialogue?)
- narrative.arc_type (what story structure does the dialogue follow?)
- brand.brand_first_named_seconds (when is "Wiom" first mentioned in the transcript?)

Be specific and honest — note weaknesses as well as strengths in the effectiveness notes.
Lessons for Wiom should be actionable creative insights."""

    try:
        raw = _call_groq(system_prompt, user_prompt, temperature=0.2, max_tokens=3000)
        decon = _extract_json(raw)
        decon["ad_id"] = ad_id  # Ensure correct ID

        ok, msg = save_deconstruction(decon)
        if not ok:
            return None, f"Saved JSON but schema validation failed: {msg}\nRaw: {raw[:300]}"
        return decon, msg
    except json.JSONDecodeError as e:
        return None, f"LLM returned invalid JSON: {e}. Raw: {raw[:400]}"
    except Exception as e:
        return None, f"Error: {str(e)}"


# ---------------------------------------------------------------------------
# Run Review
# ---------------------------------------------------------------------------

def run_review(ad_id):
    """Run the full review pipeline for a Wiom ad. Returns (scorecard_dict, message)."""
    # Load all inputs
    meta = _load_ad_metadata(ad_id)
    decon = _load_ad_deconstruction(ad_id)
    if not decon:
        return None, f"No deconstruction found for {ad_id}. Run /cue-deconstruct first."

    patterns_text, anti_text, pb = _load_playbook_summary()
    if not patterns_text:
        return None, "No playbook found. Run /cue-pattern first."

    # Load campaign context
    ctx = load_campaign_context(ad_id)
    if ctx:
        objective_type = ctx["objective"]["type"]
        weights = get_weight_profile(objective_type)
        priority = get_priority_patterns(objective_type)
        context_id = ctx["context_id"]
    else:
        objective_type = "default"
        weights = get_weight_profile("default")
        priority = get_priority_patterns("default")
        context_id = None

    # Check if brief exists
    has_brief = ctx and ctx.get("brief") is not None
    brief_text = ""
    if has_brief:
        b = ctx["brief"]
        brief_text = f"""
CREATIVE BRIEF:
- Target Audience: {b['target_audience']}
- Key Message: {b['key_message']}
- Tone: {b['tone']}
- USP: {b['usp']}
- Desired Action: {b['desired_action']}
- Constraints: {', '.join(b.get('constraints', []))}
"""

    # Placement context
    placement_text = ""
    if ctx and ctx.get("targeting") and ctx["targeting"].get("placements"):
        adjusted = adjust_pattern_relevance(priority, ctx["targeting"]["placements"])
        placement_text = f"\nPlacement-adjusted pattern relevance: {json.dumps(adjusted)}"

    # Version
    existing = load_history(ad_id, "scorecards")
    version = len(existing) + 1

    # Load reference library deconstructions for comparison
    ref_ads = []
    for f in sorted(LIBRARY_DIR.glob("*_decon.json"))[:5]:
        with open(f, "r", encoding="utf-8") as fh:
            ref_ads.append(json.load(fh))
    ref_text = "\n".join(f"- {r.get('ad_id','?')}: hook={r.get('hook',{}).get('type','?')}, narrative={r.get('narrative_arc',{}).get('structure','?')}" for r in ref_ads)

    system_prompt = f"""You are CUE Agent R — a creative scoring expert for Indian ISP/telecom video ads.

Your job: Score this Wiom ad against the Creative Playbook patterns. Produce a scorecard JSON.

CAMPAIGN OBJECTIVE: {objective_type}
WEIGHT PROFILE: {json.dumps(weights)}
PRIORITY PATTERNS (evaluate these first): {json.dumps(priority)}
{placement_text}
{brief_text}

PLAYBOOK PATTERNS:
{patterns_text}

ANTI-PATTERNS:
{anti_text}

REFERENCE LIBRARY ADS:
{ref_text}

SCORING RUBRIC (1-5 per dimension):
5 = Matches top best-in-class pattern exactly
4 = Strong pattern match, minor improvements possible
3 = Decent but average, no top pattern match
2 = Weak, partially matches an anti-pattern
1 = Matches an anti-pattern, actively hurts the ad

Output ONLY valid JSON matching this structure (no markdown, no explanation):
{{
  "ad_id": "{ad_id}",
  "context_id": {json.dumps(context_id)},
  "version": {version},
  "date_reviewed": "{datetime.now().strftime('%Y-%m-%d')}",
  "campaign_objective": "{objective_type}",
  "weight_profile": {json.dumps(weights)},
  "dimensions": {{
    "hook": {{"score": <1-5>, "what_ad_does": "<specific description>", "pattern_match": "<pattern ID and name>", "gap": "<specific gap>", "reference_ad_id": "<ad_XXX or null>"}},
    "retention": {{...same...}},
    "ctr_drivers": {{...same...}},
    "cta_conversion": {{...same...}},
    "brand_coherence": {{...same...}}
  }},
  {"brief_alignment" if has_brief else "// no brief"}: {{"audience_match": <1-5>, "audience_match_note": "...", "message_delivery": <1-5>, "message_delivery_note": "...", "tone_match": <1-5>, "tone_match_note": "...", "usp_clarity": <1-5>, "usp_clarity_note": "...", "desired_action_driven": <1-5>, "desired_action_driven_note": "...", "overall_brief_score": <0-100>}},
  "overall_score": <calculated>,
  "anti_patterns_triggered": [{{"name": "...", "description": "..."}}],
  "strengths": ["...", "..."],
  "priority_gaps": [{{"dimension": "...", "impact_score": <number>, "description": "..."}}]
}}"""

    user_prompt = f"""Score this Wiom ad:

AD METADATA:
{json.dumps(meta, indent=2, ensure_ascii=False) if meta else "No metadata available"}

AD DECONSTRUCTION:
{json.dumps(decon, indent=2, ensure_ascii=False)}

Calculate overall_score using weights: sum(dimension_score * weight * 20) for each dimension.
{f"Also score brief alignment across all 5 sub-dimensions." if has_brief else "No brief provided — skip brief_alignment (set to null)."}

Be honest but constructive. Frame gaps as opportunities. Always note strengths first."""

    try:
        raw = _call_groq(system_prompt, user_prompt, temperature=0.2, max_tokens=3000)
        scorecard = _extract_json(raw)

        # Recalculate overall score deterministically
        dim_scores = {d: scorecard["dimensions"][d]["score"] for d in weights}
        scorecard["overall_score"] = calculate_overall_score(dim_scores, weights)

        # Ensure required fields
        if not has_brief:
            scorecard["brief_alignment"] = None
        scorecard["context_id"] = context_id
        scorecard["version"] = version

        ok, msg = save_scorecard(scorecard)
        return scorecard, msg
    except json.JSONDecodeError as e:
        return None, f"LLM returned invalid JSON: {e}. Raw response: {raw[:500]}"
    except Exception as e:
        return None, f"Error: {str(e)}"


# ---------------------------------------------------------------------------
# Run Suggest
# ---------------------------------------------------------------------------

def run_suggest(ad_id):
    """Generate improvement suggestions for a scored Wiom ad. Returns (suggestions_dict, message)."""
    # Load scorecard
    sc_path = SCORECARDS_DIR / f"{ad_id}_scorecard.json"
    if not sc_path.exists():
        return None, f"No scorecard for {ad_id}. Run review first."
    with open(sc_path, "r", encoding="utf-8") as f:
        scorecard = json.load(f)

    decon = _load_ad_deconstruction(ad_id)
    patterns_text, anti_text, pb = _load_playbook_summary()
    ctx = load_campaign_context(ad_id)

    # Load reference deconstructions
    ref_ads = {}
    for f in LIBRARY_DIR.glob("*_decon.json"):
        aid = f.stem.replace("_decon", "")
        with open(f, "r", encoding="utf-8") as fh:
            ref_ads[aid] = json.load(fh)

    brief_text = ""
    if ctx and ctx.get("brief"):
        b = ctx["brief"]
        brief_text = f"""
CREATIVE BRIEF:
- Target Audience: {b['target_audience']}
- Key Message: {b['key_message']}
- Tone: {b['tone']}
- USP: {b['usp']}
- Desired Action: {b['desired_action']}

If the ad doesn't align with the brief, include brief_alignment_suggestions."""

    targeting_text = ""
    if ctx and ctx.get("targeting"):
        t = ctx["targeting"]
        targeting_text = f"\nTARGETING: Platform={t.get('platform','?')}, Placements={t.get('placements',[])}, Tier={t.get('audience',{}).get('tier','?')}"

    existing = load_history(ad_id, "suggestions")
    version = len(existing) + 1
    context_id = ctx["context_id"] if ctx else None

    system_prompt = f"""You are CUE Agent X — a creative improvement advisor for Indian ISP/telecom video ads.

Given a scorecard showing gaps, generate specific, actionable suggestions. Each suggestion must be concrete enough for a creative team to act on.

PLAYBOOK PATTERNS:
{patterns_text}

REFERENCE ADS AVAILABLE: {', '.join(list(ref_ads.keys())[:10])}
{brief_text}
{targeting_text}

Output ONLY valid JSON:
{{
  "ad_id": "{ad_id}",
  "context_id": {json.dumps(context_id)},
  "version": {version},
  "overall_score": {scorecard['overall_score']},
  "suggestions": [
    {{
      "dimension": "<hook|retention|ctr_drivers|cta_conversion|brand_coherence>",
      "priority": "<high|medium|low>",
      "affects_metric": "<video_completion|ctr|downloads|bookings>",
      "current": "<what the ad does now, 20+ chars>",
      "pattern_says": "<what best-in-class do, 20+ chars>",
      "suggested_change": "<specific actionable recommendation, 30+ chars>",
      "why_it_works": "<mechanism, 20+ chars>",
      "reference_ad_id": "<ad_XXX>",
      "reference_note": "<what to study, 10+ chars>",
      "impact_confidence": "<high|medium|low>"
    }}
  ],
  {f'"brief_alignment_suggestions": [...],' if brief_text else '"brief_alignment_suggestions": null,'}
  "keep": ["<elements to preserve>"],
  "coherence_check": "<do these suggestions work together? 20+ chars>",
  "next_step": "<recommended next action, 10+ chars>"
}}

Max 5 suggestions, prioritized by impact. Respect creative judgment — frame as insights, not mandates."""

    user_prompt = f"""Generate suggestions for:

SCORECARD:
{json.dumps(scorecard, indent=2, ensure_ascii=False)}

AD DECONSTRUCTION:
{json.dumps(decon, indent=2, ensure_ascii=False) if decon else "Not available"}

Focus on the priority_gaps. Max 5 suggestions, highest impact first."""

    try:
        raw = _call_groq(system_prompt, user_prompt, temperature=0.3, max_tokens=3000)
        suggestions = _extract_json(raw)
        suggestions["ad_id"] = ad_id
        suggestions["context_id"] = context_id
        suggestions["version"] = version
        suggestions["overall_score"] = scorecard["overall_score"]

        ok, msg = save_suggestion(suggestions)
        return suggestions, msg
    except json.JSONDecodeError as e:
        return None, f"LLM returned invalid JSON: {e}"
    except Exception as e:
        return None, f"Error: {str(e)}"


# ---------------------------------------------------------------------------
# Run Optimize
# ---------------------------------------------------------------------------

def run_optimize(ad_id):
    """Compare scorecard predictions to live performance and generate optimization recs."""
    # Load scorecard
    sc_path = SCORECARDS_DIR / f"{ad_id}_scorecard.json"
    if not sc_path.exists():
        return None, f"No scorecard for {ad_id}. Run review first."
    with open(sc_path, "r", encoding="utf-8") as f:
        scorecard = json.load(f)

    # Load performance snapshots
    snapshots = load_performance_history(ad_id)
    if len(snapshots) < 1:
        return None, f"No performance data for {ad_id}. Add snapshots first."

    ctx = load_campaign_context(ad_id)
    context_id = ctx["context_id"] if ctx else "none"
    fatigue = detect_fatigue(snapshots)
    opt_id = next_opt_id(ad_id)

    system_prompt = f"""You are CUE Agent O — a campaign optimization advisor for Indian ISP/telecom video ads.

Compare scorecard predictions to actual performance data. Identify what's confirmed vs contradicted.
Generate targeting, placement, bid, and creative recommendations.

IMPORTANT: Every recommendation with type targeting, placement, bid_strategy, budget, or pause MUST have requires_human_approval: true.

Output ONLY valid JSON:
{{
  "opt_id": "{opt_id}",
  "ad_id": "{ad_id}",
  "context_id": "{context_id}",
  "generated_at": "{datetime.now().isoformat()}",
  "performance_summary": {{
    "days_live": <int>,
    "total_impressions": <int>,
    "trend": "<improving|stable|declining|insufficient_data>",
    "scorecard_predicted_weaknesses": ["..."],
    "actual_weaknesses": ["..."],
    "prediction_accuracy": "<high|medium|low|insufficient_data>"
  }},
  "scorecard_comparison": {{
    "hook": {{"scorecard_score": <int>, "predicted_impact": "...", "actual_signal": "...", "verdict": "<confirmed|partially_confirmed|contradicted|no_data>"}},
    "retention": {{...}},
    "ctr_drivers": {{...}},
    "cta_conversion": {{...}},
    "brand_coherence": {{...}}
  }},
  "fatigue_assessment": {json.dumps(fatigue)},
  "recommendations": [
    {{
      "type": "<targeting|placement|bid_strategy|creative_refresh|budget|pause>",
      "priority": "<immediate|this_week|next_cycle>",
      "action": "<specific action, 20+ chars>",
      "rationale": "<why this will help, 20+ chars>",
      "requires_human_approval": true
    }}
  ],
  "next_check_date": "{(datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')}"
}}"""

    user_prompt = f"""Analyze this campaign:

SCORECARD:
{json.dumps(scorecard, indent=2, ensure_ascii=False)}

PERFORMANCE SNAPSHOTS ({len(snapshots)} total):
{json.dumps(snapshots, indent=2, ensure_ascii=False)}

FATIGUE DETECTION:
{json.dumps(fatigue, indent=2)}

Compare each scorecard dimension's prediction to actual metrics. Generate max 5 recommendations."""

    try:
        raw = _call_groq(system_prompt, user_prompt, temperature=0.2, max_tokens=3000)
        optimization = _extract_json(raw)

        # Ensure fatigue assessment from our deterministic detector
        optimization["fatigue_assessment"] = fatigue
        optimization["opt_id"] = opt_id
        optimization["ad_id"] = ad_id
        optimization["context_id"] = context_id
        optimization["generated_at"] = datetime.now().isoformat()

        ok, msg = save_optimization(optimization)
        return optimization, msg
    except json.JSONDecodeError as e:
        return None, f"LLM returned invalid JSON: {e}"
    except Exception as e:
        return None, f"Error: {str(e)}"
