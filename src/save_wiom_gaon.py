"""Save Wiom GAON ad metadata, scorecard, and suggestions."""
import sys
import json
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from harness import WIOM_DIR, save_scorecard, save_suggestion, _update_state

null = None

# ─── 1. Wiom Ad Metadata ────────────────────────────────────────────────────
wiom_meta = {
    "id": "wiom_001",
    "advertiser": "Wiom",
    "campaign": "GAON",
    "platform": "YouTube",
    "format": "TVC",
    "duration_seconds": 49,
    "language": "Hindi",
    "source": "manual",
    "date_found": "2026-03-28",
    "date_published": "2026-03",
    "vertical": "ISP/broadband",
    "region": "India",
    "production": "TVF (The Viral Fever)",
    "description": "Small-town family preparing to leave their village home, cancelling services one by one — lights, newspaper, milk, internet. An auto-rickshaw driver overhears 'ghar ka net' and asks about it. The young woman explains Wiom's pay-for-what-you-use model using the auto-meter as analogy. Authentic Tier 2-3 India setting with family of 4-5.",
    "tags": ["family", "small-town", "hindi", "narrative", "auto-rickshaw", "pay-per-use", "tier-2-3", "dialogue-driven"],
    "transcript_summary": "Family cancels utilities before leaving home. Auto driver asks about 'ghar ka net'. Daughter explains: 'jitna use karo, utne paise bharo' (pay for what you use). Driver relates it to his auto meter. End: Wiom tagline.",
    "frames_path": "wiom-ads/frames/gaon_01.jpg through gaon_11.jpg"
}

meta_file = WIOM_DIR / "wiom_001.json"
with open(meta_file, "w", encoding="utf-8") as f:
    json.dump(wiom_meta, f, indent=2, ensure_ascii=False)
print(f"OK | Wiom metadata saved to {meta_file}")

# ─── 2. Scorecard ───────────────────────────────────────────────────────────
scorecard = {
    "ad_id": "wiom_001",
    "date_reviewed": "2026-03-28",
    "campaign_objective": "default",
    "weight_profile": {
        "hook": 0.30,
        "retention": 0.25,
        "ctr_drivers": 0.20,
        "cta_conversion": 0.15,
        "brand_coherence": 0.10
    },
    "dimensions": {
        "hook": {
            "score": 3,
            "what_ad_does": "Opens with a production title card (OFFLINE SEC), then cuts to a young woman smiling at her phone in a small-town setting. The family scene develops gradually — mother talking animatedly near an auto-rickshaw. No immediate curiosity gap or pattern interrupt in the first 3 seconds.",
            "pattern_match": "Partially matches C1 (no brand-first opening — brand only appears in end card). Does NOT match C2 (no curiosity engine — no open question or escalating tension in the opener). The title card is a dead first 3 seconds for feed viewing.",
            "gap": "The hook lacks a scroll-stopping moment. No relatable problem statement, no visual surprise, no curiosity gap. The viewer has to invest 10+ seconds before anything intriguing happens (the mother's animated conversation). For feed platforms, this means losing 60-70% of viewers before the story even starts.",
            "reference_ad_id": "ad_010"
        },
        "retention": {
            "score": 3,
            "what_ad_does": "49-second narrative with a dialogue-driven through-line. Family cancels services → auto-rickshaw ride → driver asks about internet → product concept explained via meter analogy. The auto driver's entry at ~35s (71% mark) is the closest thing to a pattern interrupt.",
            "pattern_match": "Partially matches C2 (the 'what is ghar ka net?' question from the driver creates a mild open loop). Does NOT match C3 (49s is in the dead zone — too long for feed, not long enough for deep emotional narrative like ad_007 Cadbury or ad_010 Adani at 60s). Pattern interrupt at 71% is too late for C4 (should be 40-60%).",
            "gap": "The pace is conversational throughout — no tonal shift, no energy change, no escalation. Viewers who stay past the hook encounter pleasant but undifferentiated dialogue scenes. The auto driver's curiosity is the strongest retention element but arrives too late. The 49s duration doesn't justify itself the way a 60s emotional narrative does.",
            "reference_ad_id": "ad_007"
        },
        "ctr_drivers": {
            "score": 2,
            "what_ad_does": "Entirely dialogue-driven with no text overlays until the end card. No visual CTA elements. The story does logically lead to the product (matches K1 partially — the meter analogy is narrative-connected). Zero sound-off survivability — without audio, this is just people talking near an auto-rickshaw.",
            "pattern_match": "Partially matches K1 (the CTA/tagline feels like a narrative conclusion, not an appended ask). Completely fails K2 (sound-off survivability). On Meta where 85% of videos are watched without sound, this ad communicates nothing. No text overlays, no visual storytelling that works silent.",
            "gap": "Critical gap for Meta/Instagram placement. The ad was designed for TV/YouTube (sound-on contexts) but Wiom needs feed performance. Adding bold Hindi text overlays at key moments (the question, the meter analogy, the tagline) would make this work across all platforms without hurting the narrative.",
            "reference_ad_id": "ad_002"
        },
        "cta_conversion": {
            "score": 2,
            "what_ad_does": "End card shows tagline 'Wiom — Pure ghar ka net, jitna use karo, bass utna bharo' over a wide shot of the street. No download prompt, no app mention, no QR code, no specific action requested. The tagline is memorable and narrative-connected but is a brand sign-off, not a call to action.",
            "pattern_match": "The tagline is narrative-earned (the whole ad builds to this concept), which aligns with K1. But there is literally no CTA — no 'Download Wiom', no 'Try free for 7 days', no 'Switch now'. The best-in-class ads all have specific, actionable CTAs. This has a slogan.",
            "gap": "The ad does all the work of building desire and understanding but fails to convert that into action. Adding a specific CTA ('Download Wiom — first month free' or 'Try Wiom free — jitna use karo') that extends the narrative metaphor would dramatically improve conversion potential. Urgency element completely absent.",
            "reference_ad_id": "ad_009"
        },
        "brand_coherence": {
            "score": 4,
            "what_ad_does": "Brand appears only in the end card — delayed reveal that avoids ad-skip instinct. The setting (small-town India, auto-rickshaw, family of 4-5, school-uniform kid) perfectly mirrors Wiom's Tier 2-3 target. The auto-meter analogy is culturally resonant and distinctive. Pure Hindi in authentic small-town register. TVF production quality is high but grounded.",
            "pattern_match": "Strong match with the cultural authenticity standard. The auto-meter analogy is a brand asset — it explains a complex concept (metered broadband) through something every Indian understands. Casting and setting feel real, not aspirational-urban. This is exactly the cultural register the playbook emphasizes (anti-pattern X5 avoided completely).",
            "gap": "Minor gap: the brand voice is established here but may not be consistent across other Wiom ads. The end card is text-only — a brief logo animation or audio sting would build brand recall across a campaign. The ad doesn't quite have a 'distinctive aesthetic' that's instantly recognizable as Wiom.",
            "reference_ad_id": null
        }
    },
    "overall_score": 55,
    "anti_patterns_triggered": [
        {
            "name": "X3 — Flat Energy (partial)",
            "description": "The ad maintains a consistent conversational tone throughout. No dramatic pace change, no energy shift, no tonal surprise. The auto driver's entry provides mild interest but not a true pattern interrupt. The energy is pleasant but never spikes."
        },
        {
            "name": "X4 — No CTA (worse than generic)",
            "description": "The ad has no call to action at all. Not even a generic 'Learn More'. The tagline is strong but a tagline is not a CTA. There is no prompt for the viewer to do anything after watching."
        }
    ],
    "strengths": [
        "Perfect cultural register for Tier 2-3 India — authentic setting, casting, and Hindi dialect that Wiom's audience will recognize as their own world",
        "The auto-meter analogy is a brilliant commodity-to-emotion reframe (D1) — it makes 'metered broadband' instantly understandable through something every Indian knows",
        "Family as protagonist (D2) with 4-5 members matches the exact household Wiom targets",
        "No brand-first opening (avoids X1) — Wiom appears only at the end, letting the story do the work",
        "TVF production quality gives the ad credibility without feeling corporate or inauthentic"
    ],
    "priority_gaps": [
        {
            "dimension": "ctr_drivers",
            "impact_score": 9,
            "description": "Zero sound-off survivability. On Meta (85% sound-off viewing), this ad communicates nothing. Adding text overlays at 3-4 key moments would make the ad work across all platforms."
        },
        {
            "dimension": "cta_conversion",
            "impact_score": 8,
            "description": "No call to action exists. The ad builds understanding and desire but gives the viewer nowhere to go. A specific, narrative-connected CTA (app download, free trial) would convert completers into action-takers."
        },
        {
            "dimension": "hook",
            "impact_score": 7,
            "description": "The first 3-5 seconds (title card + woman on phone) don't create enough curiosity or relatability to stop the scroll. For feed placement, the hook needs to be dramatically stronger."
        },
        {
            "dimension": "retention",
            "impact_score": 5,
            "description": "49s duration is in the dead zone — neither tight enough for feed (30s) nor earned for long-form (60s). Consider a 30s cut for feed that preserves the auto-meter analogy as the core."
        }
    ]
}

ok, msg = save_scorecard(scorecard)
print(f"{'OK' if ok else 'FAIL'} | {msg}")

# ─── 3. Suggestions ────────────────────────────────────────────────────────
suggestions = {
    "ad_id": "wiom_001",
    "overall_score": 55,
    "suggestions": [
        {
            "dimension": "ctr_drivers",
            "priority": "high",
            "affects_metric": "ctr",
            "current": "The ad is 100% dialogue-driven with no text overlays, captions, or visual storytelling that works without sound. On Meta feed (85% sound-off), the viewer sees people talking near an auto-rickshaw with no context.",
            "pattern_says": "Pattern K2 (Sound-Off Survivability): Ads designed to communicate their core message visually without audio, via visual comedy or bold text overlays, significantly outperform on Meta. 4 of 13 top ads are explicitly sound-off ready.",
            "suggested_change": "Add 3-4 bold Hindi text overlays at key narrative beats: (1) 'Bijli band, akhbaar band, doodh band...' at the cancellation montage, (2) 'Ghar ka net bhi band?' when the driver asks, (3) 'Jitna use karo, utna bharo' at the punchline, (4) Wiom CTA at the end. Use large, high-contrast text that's readable on a phone screen. This preserves the narrative while making it work sound-off.",
            "why_it_works": "Text overlays create a parallel visual narrative that communicates the story's essence without audio. The viewer understands problem (cancelling services), curiosity (what about internet?), and solution (pay-per-use) even on mute.",
            "reference_ad_id": "ad_002",
            "reference_note": "Lahori Zeera uses exaggerated visual storytelling that works entirely without sound — the humor is visual, not verbal. While GAON's dialogue is its strength, text overlays can bridge the sound-off gap.",
            "impact_confidence": "high"
        },
        {
            "dimension": "cta_conversion",
            "priority": "high",
            "affects_metric": "downloads",
            "current": "The ad ends with a tagline ('Wiom — Pure ghar ka net, jitna use karo, bass utna bharo') but no actual call to action. No app download prompt, no website, no QR code, no free trial offer. The viewer has no next step.",
            "pattern_says": "Pattern K1 (Earned CTA): The CTA should feel like the natural conclusion of the narrative, not an appended ask. 12 of 13 top ads place a late CTA that connects to the story. But it must be a CTA, not just a tagline.",
            "suggested_change": "After the tagline, add a 3-second end card: 'Download Wiom — Pehla mahina free' (First month free) with app store badges and a QR code. The 'free trial' extends the meter metaphor — try before you pay, just like an auto ride. Keep the tagline as the emotional close, then add the action prompt as the functional close.",
            "why_it_works": "The ad successfully builds understanding of Wiom's value proposition. A free trial CTA capitalizes on that understanding while the viewer's interest is at its peak. The meter metaphor makes 'try free' feel natural, not salesy.",
            "reference_ad_id": "ad_009",
            "reference_note": "Sony LIV's 'Do Not Apply' ad uses reverse psychology but still ends with a clear CTA (register now). The boldness of the creative earns the CTA. GAON's narrative earns it too — just needs to actually ask.",
            "impact_confidence": "high"
        },
        {
            "dimension": "hook",
            "priority": "high",
            "affects_metric": "video_completion",
            "current": "Opens with a production title card ('OFFLINE SEC 23.03.26') followed by a young woman on her phone. The first interesting visual (mother talking animatedly) arrives at ~10 seconds. For feed platforms, this is 7 seconds too late.",
            "pattern_says": "Pattern C1 (Open with Recognition, Not Brand) + C2 (Curiosity Engine): Open with a moment the viewer recognizes — relatable problem, visual surprise, or curiosity gap. Create an unanswered question in the first 2-3 seconds that the viewer must resolve by watching.",
            "suggested_change": "Re-edit to open with the mother's animated dialogue about cancelling services — 'Bijli band karo, akhbaar band karo, doodh band karo... aur haan, net bhi band karo!' The rapid-fire cancellations create curiosity (why is everything being cancelled?) and the 'net band karo' is the hook that sets up the rest. Cut the title card entirely for feed versions.",
            "why_it_works": "The cancellation montage creates immediate curiosity (why is this family shutting everything down?) and the 'net bhi band karo' raises the specific question the ad answers. It filters for the target audience (families, Tier 2-3, household decisions) within 3 seconds.",
            "reference_ad_id": "ad_010",
            "reference_note": "Adani's 'Pehle Pankha Aayega' opens with a mysterious catchphrase that creates instant curiosity. GAON has a similarly curiosity-worthy moment (cancelling everything including internet) — it just needs to be moved to the front.",
            "impact_confidence": "medium"
        },
        {
            "dimension": "retention",
            "priority": "medium",
            "affects_metric": "video_completion",
            "current": "49 seconds with consistent conversational pacing throughout. No tonal shift, no energy spike, no dramatic reveal. The auto driver enters at ~35s (71% mark) but doesn't create a dramatic change in energy. The pace is pleasant but flat.",
            "pattern_says": "Pattern C4 (Pattern Interrupt at Midpoint): Place a tonal shift, surprise, or energy change at 40-60% of the ad's duration. 11 of 13 top ads have documented pace changes. Pattern C3 suggests 30s is the feed sweet spot; 49s needs exceptional retention mechanics to justify.",
            "suggested_change": "Create a 30-second feed cut that compresses the narrative: (0-5s) cancellation montage hook, (5-15s) auto-rickshaw ride + driver's curiosity, (15-22s) meter analogy explanation with energy shift (driver's 'aha' moment as pattern interrupt), (22-27s) family reaction + warmth beat, (27-30s) Wiom tagline + CTA. The 30s version should also have a clear energy spike at the 15s mark when the driver 'gets it'.",
            "why_it_works": "A 30s cut forces tighter storytelling and hits the duration sweet spot for feed. The driver's realization becomes the pattern interrupt at exactly 50% (15s mark). The shorter format also reduces the risk of mid-roll drop-off that 49s invites.",
            "reference_ad_id": "ad_003",
            "reference_note": "WD-40 tells complete problem-solution-payoff stories in 6 seconds. GAON has enough narrative material for 30s — the auto-meter analogy is the core insight and needs only 10-15 seconds to land.",
            "impact_confidence": "medium"
        },
        {
            "dimension": "brand_coherence",
            "priority": "low",
            "affects_metric": "downloads",
            "current": "Wiom appears only in the text-only end card. No logo animation, no audio sting, no recurring visual motif. While the delayed brand reveal is correct strategy, the brand needs to be more memorable when it does appear.",
            "pattern_says": "Top ads use brand as enhancement, not interruption. The brand moment should be distinctive enough to build recall across a campaign. Best ads have intentional, crafted brand reveals — not just text on screen.",
            "suggested_change": "Design a 3-second Wiom brand moment for the end card: the auto-meter visual metaphor as a branded animation (meter ticking = data being used), accompanied by a short audio signature. Use this consistently across all GAON campaign ads. The meter-as-logo concept reinforces the USP visually every time Wiom appears.",
            "why_it_works": "A distinctive brand moment that extends the ad's core metaphor (the meter) creates recall beyond a single viewing. When the viewer sees the meter animation on a second ad, they instantly recall the concept. This builds brand equity across the campaign.",
            "reference_ad_id": "ad_012",
            "reference_note": "Surf Excel's 'Daag Acche Hain' has built a brand identity so strong that the tagline itself is a cultural artifact. GAON's meter analogy has similar potential if it's visually codified as a brand element.",
            "impact_confidence": "low"
        }
    ],
    "keep": [
        "The auto-meter analogy — this is Wiom's single most powerful creative asset. It makes metered broadband instantly understandable. Never lose this.",
        "Authentic Tier 2-3 setting and casting — the small-town street, auto-rickshaw, school uniform kid, blue saree mother. This is real India, not aspirational India. The target audience sees themselves.",
        "Pure Hindi dialogue in authentic small-town register — not Hinglish, not urban. This is exactly right for the target audience.",
        "TVF production quality — high craft that doesn't feel corporate. The grounded, warm aesthetic matches the brand positioning.",
        "Family as protagonists with 4-5 members — the exact household making broadband decisions in Tier 2-3 India."
    ],
    "coherence_check": "The suggestions focus on packaging (hook, sound-off, CTA, duration) rather than substance. The ad's core — the auto-meter analogy, the family setting, the cultural register — is strong and must not change. The risk is that adding text overlays could make it feel cluttered or that a 30s cut could lose the warmth of the longer narrative. Recommendation: create the 30s feed cut AND keep the 49s version for YouTube pre-roll where sound-on and longer attention are the norm. Test both.",
    "next_step": "Create a 30-second feed-optimized cut of GAON with: (1) re-ordered hook starting with cancellation montage, (2) 3-4 bold Hindi text overlays for sound-off viewing, (3) specific CTA end card with app download + free trial offer. Test against the original 49s on YouTube to validate whether the playbook patterns hold."
}

ok, msg = save_suggestion(suggestions)
print(f"{'OK' if ok else 'FAIL'} | {msg}")

# Update pipeline state
state = _update_state()
print(f"\nPipeline phase: {state['current_phase']}")
print(f"Wiom ads: {state['wiom_ads']['total']}")
print(f"Scorecards: {state['scorecards']['total']}")
print(f"Suggestions: {state['suggestions']['total']}")
