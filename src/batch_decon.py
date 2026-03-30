"""Batch deconstruct all 13 ads. Text-based analysis from descriptions."""
import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from harness import save_deconstruction

null = None

deconstructions = [
    # ─── ad_001: Airtel Xstream Fiber ─────────────────────────────────────
    {
        "ad_id": "ad_001",
        "hook": {
            "type": "visual_surprise",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": True,
            "audio_hook": "music_hit",
            "language": "Hindi",
            "effectiveness_note": "Characters from popular shows literally bursting onto screen creates instant recognition and curiosity. Viewers think 'that's my show' which stops the scroll. Leverages parasocial attachment to fictional characters."
        },
        "narrative": {
            "arc_type": "montage",
            "tension_payoff": "front_loaded",
            "num_scenes": 8,
            "effectiveness_note": "Montage of entertainment characters creates a 'greatest hits' feeling. No single narrative to follow means low cognitive load. Each scene is self-contained — if you miss one, the next still works. Keeps viewers watching to see which show appears next."
        },
        "pacing": {
            "duration_bucket": "30s",
            "cuts_per_15s": 6,
            "pace_changes": ["0-3s: high energy opener", "15s: brief product shot slows pace", "25s: energy ramps for finale"],
            "pattern_interrupts": ["Each new character entrance acts as a mini pattern interrupt"],
            "retention_note": "Risk of drop-off at mid-point when product messaging kicks in. The character parade format prevents this by promising 'what show is next?' curiosity throughout."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": True,
            "voiceover_tone": "energetic",
            "language": "Hindi",
            "music_visual_sync": True,
            "audio_note": "Catchy original soundtrack synced to character entrances. Music carries the energy between scenes. Multi-lingual versions (9 languages) mean the audio layer was designed as the primary retention tool — it works regardless of language comprehension."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "high",
            "text_overlay_density": "minimal",
            "color_mood": "bright",
            "product_visibility": "reveal_moment",
            "visual_note": "High production value matches the entertainment promise. Bright, saturated colors signal 'premium entertainment experience.' Product (fiber connection) is abstract so they visualize it through the content it enables — smart choice for an infrastructure product."
        },
        "cta": {
            "type": "visit_site",
            "timing": "late",
            "visual_treatment": "combined",
            "urgency_element": "none",
            "cta_note": "CTA is 'get Xstream Fiber' at the end. Feels like a natural conclusion — after showing all this entertainment, the ask is simply 'want access to all of this?' The entertainment montage itself is the argument. CTA does not feel forced but lacks urgency."
        },
        "brand": {
            "logo_presence": "bookend",
            "brand_first_named_seconds": 3,
            "brand_voice_consistent": True,
            "brand_note": "Airtel brand appears early and at end. The entertainment focus IS the brand voice for Xstream Fiber specifically. Brand enhances rather than interrupts because the characters validate the entertainment promise."
        },
        "emotional": {
            "primary_emotion": "aspiration",
            "cultural_specificity": ["family", "urban/rural"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Entertainment as aspiration is deeply rooted in Indian culture — the living room TV is the center of family life. Multi-lingual versions signal 'this is for everyone, not just metros.' Regional language versions with local show characters would resonate strongly in Tier 2-3."
        },
        "x_factor": "The 9-language localization is not just translation — it implies different entertainment content per region, which makes the ad itself feel personalized. Most ISP ads show speed tests or buffering wheels. This one never mentions speed once. It sells the dream (entertainment) not the pipe (broadband). That reframe is the creative breakthrough.",
        "lessons_for_wiom": [
            "Sell the dream, not the pipe: Wiom could show what reliable internet ENABLES (kids acing online classes, family movie nights, parents video-calling grandparents) rather than speeds and plans.",
            "Regional language versions with locally relevant content are not optional for Tier 2-3 India — Airtel did 9 languages, Wiom should plan for at least 3-4 from day one.",
            "Entertainment montage format works for broadband because the product is invisible — you can only show what it delivers, not the product itself."
        ]
    },

    # ─── ad_002: Lahori Zeera ────────────────────────────────────────────
    {
        "ad_id": "ad_002",
        "hook": {
            "type": "visual_surprise",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": False,
            "audio_hook": "music_hit",
            "language": "Hindi",
            "effectiveness_note": "Opens with someone doing something physically extreme — immediately bizarre and unexpected. The brain cannot ignore incongruity. You HAVE to watch for 2 more seconds to understand what is happening. Classic curiosity gap via visual absurdity."
        },
        "narrative": {
            "arc_type": "montage",
            "tension_payoff": "front_loaded",
            "num_scenes": 6,
            "effectiveness_note": "Each scene escalates the absurdity — running becomes wrestling becomes swimming. Escalation ladder keeps raising stakes. The viewer thinks 'it can't get more ridiculous' and then it does. Each scene is a mini punchline that resets the curiosity for the next."
        },
        "pacing": {
            "duration_bucket": "30s",
            "cuts_per_15s": 8,
            "pace_changes": ["0-5s: immediate high energy", "10-20s: rapid escalation", "25-30s: product reveal + brand"],
            "pattern_interrupts": ["Every new extreme scenario is a pattern interrupt — you never know what absurd activity comes next"],
            "retention_note": "Extremely fast cuts prevent drop-off. No single scene lasts long enough to lose interest. The escalation structure creates a 'what next?' loop. Risk: some viewers may tune out if the humor does not land — exaggeration comedy is polarizing."
        },
        "audio": {
            "music_type": "trending",
            "voiceover": False,
            "voiceover_tone": null,
            "language": "Hindi",
            "music_visual_sync": True,
            "audio_note": "Upbeat music drives the energy. No voiceover means the visual comedy carries the message entirely — this works well for sound-off environments (Instagram/Facebook feed). Music syncs with action cuts for satisfying rhythm."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "mid",
            "text_overlay_density": "minimal",
            "color_mood": "bright",
            "product_visibility": "reveal_moment",
            "visual_note": "Deliberately mid-production — the slightly rough quality makes the exaggeration funnier. High-polish would make it feel like a car ad trying too hard. The lo-fi energy matches the D2C brand personality. Designed to work sound-off: the visual comedy is self-explanatory."
        },
        "cta": {
            "type": "shop",
            "timing": "late",
            "visual_treatment": "text_overlay",
            "urgency_element": "none",
            "cta_note": "Brand and product reveal at the end. The CTA is implicit — the entire ad makes you curious about the drink. No hard sell, which fits the humor-first strategy. Risk: viewers may enjoy the comedy but not connect it to the product."
        },
        "brand": {
            "logo_presence": "end_card_only",
            "brand_first_named_seconds": 25,
            "brand_voice_consistent": True,
            "brand_note": "Brand reveal delayed until the end. This is bold for a challenger brand — they bet that the humor is memorable enough that the punchline (product) lands. For an established brand this would be risky, but for Lahori Zeera trying to break through clutter, the entertainment-first approach is correct."
        },
        "emotional": {
            "primary_emotion": "humor",
            "cultural_specificity": ["youth_culture", "urban/rural"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Exaggeration humor is universal but the physical comedy style is very Bollywood-influenced — slapstick with a wink. Appeals across class and geography. The drink itself is a mass-market product, so the humor needs to be broad, not niche. It delivers."
        },
        "x_factor": "The escalation structure is deceptively simple but incredibly effective for retention. Each scene is funnier than the last, creating a dopamine ladder. You cannot stop watching because your brain predicts the next hit. This is the same mechanic that makes TikTok addictive, compressed into a 30-second ad. The restraint of saving brand reveal until the end shows confidence in the creative.",
        "lessons_for_wiom": [
            "Escalation ladders work for retention: Wiom could show increasingly ridiculous scenarios of life WITHOUT good internet (video call freezing at worse and worse moments) — each funnier than the last, building to the punchline.",
            "Sound-off friendly design is critical for Meta/Instagram: if the humor works visually without audio, you capture the 85 percent who scroll with sound off.",
            "Mid-production quality can be an asset for D2C/challenger brands — it signals authenticity and relatability versus the polished corporate feel of Jio/Airtel ads."
        ]
    },

    # ─── ad_003: WD-40 ──────────────────────────────────────────────────
    {
        "ad_id": "ad_003",
        "hook": {
            "type": "problem_statement",
            "face_first_frame": False,
            "text_overlay_first_frame": False,
            "brand_visible_3s": True,
            "audio_hook": "sound_effect",
            "language": "Hindi",
            "effectiveness_note": "In 6 seconds there is no scroll to stop — these are non-skippable bumpers. The hook IS the ad. Opens with a familiar household problem (squeaky hinge, stuck bolt) that triggers instant recognition. The sound effect of the problem (squeak, grind) is the audio hook."
        },
        "narrative": {
            "arc_type": "problem_solution",
            "tension_payoff": "front_loaded",
            "num_scenes": 3,
            "effectiveness_note": "Problem (1s) -> Product (2s) -> Payoff with humor (3s). Three-act structure compressed to 6 seconds. Works because the problem is universally understood — no setup needed. The humor in the payoff is the retention reward."
        },
        "pacing": {
            "duration_bucket": "6s",
            "cuts_per_15s": 12,
            "pace_changes": ["No pace changes possible in 6s — it is one continuous energy burst"],
            "pattern_interrupts": ["The punchline at 4-5s is the only interrupt needed"],
            "retention_note": "At 6 seconds, retention is near 100 percent because these run as non-skippable pre-roll. The challenge is memorability, not retention. The humor punchline solves this — you remember the joke, which means you remember the product."
        },
        "audio": {
            "music_type": "sound_effects_only",
            "voiceover": False,
            "voiceover_tone": null,
            "language": "Hindi",
            "music_visual_sync": True,
            "audio_note": "Sound effects carry the entire narrative: squeak -> spray -> satisfying result sound. No music, no voiceover. The sounds ARE the story. This is brilliant for a utility product — the sound of the problem and solution is more persuasive than any words."
        },
        "visual": {
            "talent_type": "no_talent",
            "production_quality": "mid",
            "text_overlay_density": "minimal",
            "color_mood": "bright",
            "product_visibility": "always_visible",
            "visual_note": "Close-up product shots dominate. No talent needed — the product IS the protagonist. Simple visual language: problem object -> product -> fixed object. Designed for immediate comprehension. Works perfectly sound-off because the visual narrative is complete."
        },
        "cta": {
            "type": "shop",
            "timing": "late",
            "visual_treatment": "text_overlay",
            "urgency_element": "none",
            "cta_note": "Product IS the CTA — showing it working is the entire pitch. End card with brand. No explicit call to action needed because the ad creates an 'I should get that' impulse through demonstrated utility."
        },
        "brand": {
            "logo_presence": "always_visible",
            "brand_first_named_seconds": 0,
            "brand_voice_consistent": True,
            "brand_note": "WD-40 can is visible throughout — the distinctive blue and yellow is instantly recognizable. Brand IS the product IS the solution. No separation between brand message and utility demonstration."
        },
        "emotional": {
            "primary_emotion": "humor",
            "cultural_specificity": ["universal"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Household problems are universal. A squeaky door is the same frustration in Mumbai and Memphis. The humor transcends culture. However, the specific use-cases chosen likely reflect Indian household scenarios to feel locally relevant."
        },
        "x_factor": "The series format is the genius. Eight ads means eight different use-cases, each one a potential moment of recognition for a different viewer. Together they position WD-40 as the universal fixer. The 6-second constraint forced the creative team to find the absolute essence of problem-solution storytelling. Nothing is wasted. Every frame earns its place. This is what advertising under constraint looks like at its best.",
        "lessons_for_wiom": [
            "6-second bumper series could work brilliantly for Wiom: 8 different buffering/slow-internet problems, each solved in 6 seconds. Family video call freezing, cricket stream buffering, kids homework not loading, mom recipe video stuck — one problem per bumper, build the series.",
            "Sound design as narrative: the SOUND of buffering (that spinning wheel silence) versus the SOUND of fast internet (instant video play, crisp audio) could be Wiom's version of WD-40's squeak-to-fix audio storytelling.",
            "Product-as-protagonist works when the product solves a tangible problem. Wiom router/app as the hero object appearing to fix each scenario."
        ]
    },

    # ─── ad_004: Zomato Diwali ───────────────────────────────────────────
    {
        "ad_id": "ad_004",
        "hook": {
            "type": "relatable_moment",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": False,
            "audio_hook": "dialogue",
            "language": "Hinglish",
            "effectiveness_note": "Opens with a recognizable Diwali meme/moment that millions of Indians have shared. Instant cultural recognition creates an in-group feeling: 'they get us.' Piyush Mishra's face is itself a hook — he signals dry wit and intelligence, setting expectations for satirical tone."
        },
        "narrative": {
            "arc_type": "single_scene",
            "tension_payoff": "buildup",
            "num_scenes": 4,
            "effectiveness_note": "Single-scene format with dialogue-driven humor. The build-up is in the escalating satire — each line gets sharper. Viewers stay for Piyush Mishra's delivery as much as the message. The narrative rewards patience, which is unusual for a 60s digital ad."
        },
        "pacing": {
            "duration_bucket": "60s+",
            "cuts_per_15s": 3,
            "pace_changes": ["0-10s: scene setting", "10-40s: satirical build", "40-55s: payoff and pivot to brand", "55-60s: CTA"],
            "pattern_interrupts": ["20s: unexpected satirical twist", "40s: brand reveal pivot"],
            "retention_note": "60 seconds is long for digital. Drop-off risk at 15-20s for viewers who do not connect with the satirical tone. Piyush Mishra's screen presence and delivery are the retention engine — you watch HIM, and the brand message comes along for the ride."
        },
        "audio": {
            "music_type": "no_music",
            "voiceover": False,
            "voiceover_tone": null,
            "language": "Hinglish",
            "music_visual_sync": False,
            "audio_note": "Dialogue-only format. No music means full focus on the words and delivery. This is a deliberate choice — Piyush Mishra's voice IS the audio production. His cadence, pauses, and intonation carry more emotion than any soundtrack. Silence between lines creates tension."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "high",
            "text_overlay_density": "none",
            "color_mood": "bright",
            "product_visibility": "absent_until_cta",
            "visual_note": "Festive Diwali setting with warm lighting. High production quality but not flashy — the visual restraint lets Mishra's performance shine. No text overlays means this is designed for sound-ON viewing. Would lose most of its impact sound-off."
        },
        "cta": {
            "type": "download_app",
            "timing": "late",
            "visual_treatment": "combined",
            "urgency_element": "limited_time",
            "cta_note": "Diwali-specific CTA with festive offers. Feels earned because the entire ad has been a Diwali cultural moment. The festival creates natural urgency without the ad needing to manufacture it. 'Order on Zomato this Diwali' connects the cultural moment to the action."
        },
        "brand": {
            "logo_presence": "end_card_only",
            "brand_first_named_seconds": 45,
            "brand_voice_consistent": True,
            "brand_note": "Zomato delays brand reveal until 45 seconds. Bold for a 60s ad. Works because Zomato has built a distinctive brand voice (witty, irreverent, culturally plugged in) that audiences recognize even before the logo appears. The satire IS Zomato's brand."
        },
        "emotional": {
            "primary_emotion": "humor",
            "cultural_specificity": ["festival"],
            "hinglish_level": "heavy_code_switching",
            "cultural_note": "Diwali meme-jacking is high-risk high-reward. Get it right and you own the cultural conversation. Get it wrong and you are cringe. Zomato gets it right because they parody WITH the culture, not AT it. Heavy Hinglish code-switching signals urban millennial/GenZ — Zomato's core audience."
        },
        "x_factor": "Zomato has built a brand voice so distinctive that their ads work as entertainment FIRST, advertising second. The audience actively seeks out and shares Zomato ads — they have achieved the holy grail of ads that people WANT to watch. The casting of Piyush Mishra is inspired: he brings instant credibility to satirical content and elevates what could be a generic festive ad into a cultural commentary.",
        "lessons_for_wiom": [
            "Cultural moment-jacking requires a distinctive brand voice FIRST. Wiom needs to develop a voice (witty? warm? rebellious?) before trying to ride cultural moments, otherwise it feels like any-brand-Diwali-ad.",
            "Celebrity casting should match brand tone, not just fame. Piyush Mishra works for Zomato's satire. Wiom should ask 'who embodies our voice?' not 'who is the most famous person we can afford?'",
            "Long-form (60s) can work on digital IF the talent and writing are strong enough. But it requires sound-on viewing, which limits reach. Consider a 15s cut-down for feed plus the full 60s as a targeted view."
        ]
    },

    # ─── ad_005: Urban Company Native RO ─────────────────────────────────
    {
        "ad_id": "ad_005",
        "hook": {
            "type": "relatable_moment",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": False,
            "audio_hook": "dialogue",
            "language": "Hindi",
            "effectiveness_note": "Opens with a service professional (relatable if you have ever had an RO serviced) speaking in authentic working-class dialogue. The humor comes from the unexpected eloquence/absurdity of a mundane service interaction. Stops the scroll because it looks like real life, not an ad."
        },
        "narrative": {
            "arc_type": "demo",
            "tension_payoff": "buildup",
            "num_scenes": 5,
            "effectiveness_note": "Product demo disguised as comedy sketch. The USP (Native RO features) is delivered through funny dialogue, not a feature list. Viewers absorb product information without feeling sold to. The 1980s Bollywood aesthetic makes it memorable — it is not just a demo, it is a demo in a distinctive world."
        },
        "pacing": {
            "duration_bucket": "30s",
            "cuts_per_15s": 4,
            "pace_changes": ["0-5s: establishes scenario", "5-20s: comedic build with product info", "20-30s: retro musical payoff"],
            "pattern_interrupts": ["15s: retro Bollywood music drop is a sharp tonal shift that re-grabs attention"],
            "retention_note": "The retro aesthetic is itself a pattern interrupt — viewers think 'wait, is this an 80s movie?' The tonal contrast between mundane service scenario and Bollywood musical treatment keeps the brain engaged through incongruity."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": True,
            "voiceover_tone": "conversational",
            "language": "Hindi",
            "music_visual_sync": True,
            "audio_note": "Retro Bollywood score is the signature audio element. It transforms a product demo into entertainment. The music style signals nostalgia and warmth while making the product features feel important and dramatic. Brilliant tonal mismatch that works."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "mid",
            "text_overlay_density": "minimal",
            "color_mood": "bright",
            "product_visibility": "always_visible",
            "visual_note": "Retro color grading gives a warm, amber tone reminiscent of 80s Bollywood. This visual distinctiveness means you immediately know it is an Urban Company ad even before the logo appears. The product (RO purifier) is visible throughout but never feels like a product shot because the comedic scene gives it context."
        },
        "cta": {
            "type": "download_app",
            "timing": "late",
            "visual_treatment": "combined",
            "urgency_element": "none",
            "cta_note": "CTA to download Urban Company app at the end. Feels natural because the ad demonstrated a service you would book through the app. The entire ad is an answer to 'why should I use Urban Company for RO service?' — CTA is just the how."
        },
        "brand": {
            "logo_presence": "end_card_only",
            "brand_first_named_seconds": 25,
            "brand_voice_consistent": True,
            "brand_note": "Brand reveal late but the retro aesthetic IS the brand identity for this campaign. Distinctive enough that repeat viewers recognize it instantly. Urban Company is building a visual language that transcends the logo."
        },
        "emotional": {
            "primary_emotion": "humor",
            "cultural_specificity": ["urban/rural"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "The service professional as comedic talent is culturally specific to India where home services (plumber, electrician, RO technician) are frequent household interactions. Every Indian household recognizes this scenario. The humor is affectionate, not mocking — important distinction."
        },
        "x_factor": "The retro Bollywood aesthetic turns a forgettable product demo into appointment viewing. It is a distinctive visual and tonal world that no competitor can replicate without looking like a copycat. This is brand moat through creative execution. The product information lands BECAUSE it is wrapped in entertainment, not despite it. The viewer remembers both the joke AND the feature — that is the rarest outcome in advertising.",
        "lessons_for_wiom": [
            "Distinctive aesthetic as brand moat: Wiom could develop a visual world (retro? animated? documentary?) that makes every ad instantly recognizable even before the logo appears. Consistency across campaigns builds cumulative recognition.",
            "Demo disguised as entertainment: instead of listing broadband speeds, show a technician installing Wiom fiber while having a funny conversation that naturally reveals product benefits. The human interaction carries the information.",
            "Home service scenarios are perfect for home internet brands. The installer, the family, the living room — these are Wiom's natural territories. Own them creatively."
        ]
    },

    # ─── ad_006: HDFC Mutual Fund ────────────────────────────────────────
    {
        "ad_id": "ad_006",
        "hook": {
            "type": "relatable_moment",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": False,
            "audio_hook": "voiceover",
            "language": "Hindi",
            "effectiveness_note": "Opens with a daily-life scenario everyone recognizes (like saving a seat, or buying extra when something is cheap). The mundane familiarity disarms the viewer — it does not feel like a finance ad. The hook works by making you nod before you realize you are being taught."
        },
        "narrative": {
            "arc_type": "comparison",
            "tension_payoff": "buildup",
            "num_scenes": 5,
            "effectiveness_note": "Parallel structure: everyday scenario THEN investment concept. This A-to-B mapping is the core mechanic. Each pair of scenes builds the argument that investing is not exotic — you already do it instinctively. The build-up across multiple analogies creates cumulative persuasion."
        },
        "pacing": {
            "duration_bucket": "30s",
            "cuts_per_15s": 4,
            "pace_changes": ["0-10s: first analogy, slow setup", "10-30s: rapid analogy series", "30-40s: brand payoff"],
            "pattern_interrupts": ["Each new analogy is a mini-reset that re-engages attention"],
            "retention_note": "The analogy format creates a game-like experience: viewer tries to guess the investment concept before it is revealed. This predictive engagement is a strong retention mechanism. Low drop-off risk because each analogy is self-contained and interesting on its own."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": True,
            "voiceover_tone": "conversational",
            "language": "Hindi",
            "music_visual_sync": False,
            "audio_note": "Warm, conversational voiceover in Hindi. Not authoritative or preachy — feels like a wise friend explaining something. The tone deliberately avoids the typical finance ad gravitas. Light background score stays out of the way. The voice does all the work."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "mid",
            "text_overlay_density": "minimal",
            "color_mood": "bright",
            "product_visibility": "absent_until_cta",
            "visual_note": "Everyday Indian settings: vegetable market, kitchen, neighborhood. Deliberately ordinary to reinforce the message that investing is ordinary. No suits, no offices, no graphs. The visual strategy is to DE-financialize finance. This is revolutionary for the category."
        },
        "cta": {
            "type": "learn_more",
            "timing": "late",
            "visual_treatment": "combined",
            "urgency_element": "none",
            "cta_note": "Soft CTA. The ad's goal is perception shift (investing is not scary) not immediate conversion. Appropriate for the category — mutual fund purchases are considered decisions. The lack of urgency is intentional and correct."
        },
        "brand": {
            "logo_presence": "end_card_only",
            "brand_first_named_seconds": 35,
            "brand_voice_consistent": True,
            "brand_note": "HDFC MF brand appears only at the end. The ad builds trust through the relatable content first, then attaches the brand. For a financial brand, this trust-first approach is more effective than leading with the brand name."
        },
        "emotional": {
            "primary_emotion": "relatability",
            "cultural_specificity": ["urban/rural"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Uses specifically Indian middle-class daily-life scenarios. The analogies are drawn from sabzi mandi, chai stalls, and household habits — unmistakably Indian. This grounds abstract financial concepts in the physical reality of Indian middle-class life. The cultural specificity IS the strategy."
        },
        "x_factor": "The reframe is everything. Every mutual fund ad in India either uses jargon-heavy explanations or celebrity endorsements. This ad does neither. It says 'you are already an investor — you just do not know it.' That single insight transforms the entire communication. It does not teach DOWN to the audience; it reveals intelligence the audience already has. This is respectful, empowering advertising, and it is devastatingly effective for a category plagued by intimidation.",
        "lessons_for_wiom": [
            "Reframe the commodity: instead of selling broadband, show that families are already using internet for everything that matters (kids learning, parents working, family connecting) — they just need RELIABLE internet. The need already exists; Wiom just fulfills it.",
            "Analogy-based storytelling makes complex or boring products accessible. Wiom could compare broadband reliability to something every family understands: 'you would not accept electricity that cuts out 5 times a day, so why accept internet that does?'",
            "Respect the audience's intelligence. Do not explain what broadband is. Assume they know. Show them why Wiom's version is different — through scenarios, not specs."
        ]
    },

    # ─── ad_007: Cadbury Dairy Milk New Neighbour ────────────────────────
    {
        "ad_id": "ad_007",
        "hook": {
            "type": "curiosity_gap",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": False,
            "audio_hook": "dialogue",
            "language": "Hindi",
            "effectiveness_note": "Opens with a woman mid-conversation, clearly about to tell a story. The viewer's brain automatically wants to hear the story — narrative curiosity is one of the strongest psychological hooks. The setup implies a social situation (new neighbor) everyone can relate to."
        },
        "narrative": {
            "arc_type": "single_scene",
            "tension_payoff": "buildup",
            "num_scenes": 3,
            "effectiveness_note": "Single narrative thread with a slow burn to an emotional twist. The woman's internal conflict (how to include a non-local speaker) creates genuine tension. The payoff is emotional, not comedic. Viewers stay because they are invested in the human problem, not waiting for a product."
        },
        "pacing": {
            "duration_bucket": "60s+",
            "cuts_per_15s": 2,
            "pace_changes": ["0-15s: scenario setup, relaxed", "15-40s: internal deliberation builds", "40-55s: emotional resolution", "55-60s: brand moment"],
            "pattern_interrupts": ["30s: the moment she makes her decision creates a subtle but powerful narrative gear shift"],
            "retention_note": "Slow pace is a DELIBERATE choice — it builds emotional investment. Fast cuts would destroy the intimacy. Drop-off risk at 15s for impatient viewers, but those who stay past 20s will watch to the end because they are now emotionally committed to the character."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": False,
            "voiceover_tone": null,
            "language": "Hindi",
            "music_visual_sync": False,
            "audio_note": "Subtle background score that swells at the emotional moment. Dialogue-driven but unlike Zomato's dialogue (witty), this is warm and naturalistic. The music stays invisible until the payoff moment where it amplifies the emotion. Restraint in the audio makes the swell hit harder."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "high",
            "text_overlay_density": "none",
            "color_mood": "bright",
            "product_visibility": "absent_until_cta",
            "visual_note": "Warm, intimate cinematography. Close-ups on faces during dialogue create connection. The visual language is more 'indie film' than 'ad' — deliberate choice to earn emotional credibility. Cadbury product appears only in the last moments, almost incidentally."
        },
        "cta": {
            "type": "other",
            "timing": "late",
            "visual_treatment": "voiceover_only",
            "urgency_element": "none",
            "cta_note": "No explicit CTA. The ad is pure brand building — Cadbury equals warmth, inclusion, human connection. The Cadbury bar appearing in the final scene is the gentlest possible product integration. This is a premium brand strategy: build love, not clicks."
        },
        "brand": {
            "logo_presence": "end_card_only",
            "brand_first_named_seconds": 55,
            "brand_voice_consistent": True,
            "brand_note": "Cadbury delays brand appearance to 55 seconds in a 60 second ad. Only possible because decades of consistent brand voice have made Cadbury's emotional territory (warmth, sharing, connection) immediately recognizable. The audience feels 'this is a Cadbury ad' long before the logo appears."
        },
        "emotional": {
            "primary_emotion": "warmth",
            "cultural_specificity": ["family", "regional_identity"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Language as inclusion/exclusion is deeply resonant in India where language divides are real and emotional. Moving to a new city where no one speaks your language is a lived experience for millions. The ad touches this nerve gently and offers Cadbury as a universal bridge. The cultural insight is profound."
        },
        "x_factor": "The power of this ad is restraint. In a world of 6-second bumpers and jump cuts, Cadbury bets on slow, quiet, emotionally honest storytelling. The twist is not a plot twist — it is an empathy twist. The woman does not just translate her story; she REIMAGINES it to include someone different. That act of creative empathy is the most human thing an ad has depicted in years. And it makes Cadbury feel like a brand that understands humanity, not just sells chocolate.",
        "lessons_for_wiom": [
            "Connectivity as inclusion: Wiom literally connects people. A story about internet enabling a family to stay connected across languages/regions/distances would be authentic and powerful. Not 'fast internet' but 'internet that keeps your family together.'",
            "Restraint can be more powerful than spectacle. One quiet, true story about a family whose lives changed because of reliable internet would outperform ten flashy speed-test ads. But it requires confidence and craft.",
            "Language diversity is Wiom's territory to own. In multi-lingual India, showing how internet bridges language gaps (translate, video call grandparents who speak a different language, kids learning in their mother tongue) is uniquely relevant."
        ]
    },

    # ─── ad_008: Colgate Night Brushing ──────────────────────────────────
    {
        "ad_id": "ad_008",
        "hook": {
            "type": "visual_surprise",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": True,
            "audio_hook": "dialogue",
            "language": "Hindi",
            "effectiveness_note": "Opens with Colgate apparently selling food — a toothpaste brand selling biryani or chaat. The incongruity is immediate and irresistible. Viewers MUST watch to resolve the confusion: 'why is Colgate selling food?' The cognitive dissonance is the hook."
        },
        "narrative": {
            "arc_type": "problem_solution",
            "tension_payoff": "front_loaded",
            "num_scenes": 4,
            "effectiveness_note": "The inversion structure carries the narrative: brand does opposite of what you expect, which makes the actual message (brush at night) land harder. The structure is: surprise (Colgate sells food) -> explanation (because you need to brush after eating) -> product. The logic chain is clear and satisfying."
        },
        "pacing": {
            "duration_bucket": "30s",
            "cuts_per_15s": 5,
            "pace_changes": ["0-5s: surprise hook", "5-15s: escalating food scenarios", "15-25s: reveal and message", "25-30s: product and CTA"],
            "pattern_interrupts": ["5s: first food item reveal", "15s: message pivot from food to brushing"],
            "retention_note": "The surprise hook creates a question that must be answered. Viewers stay to understand WHY Colgate is selling food. Once the reveal happens at 15s, the payoff is satisfying enough that viewers watch through the product message. Low drop-off because the curiosity gap is tight."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": True,
            "voiceover_tone": "conversational",
            "language": "Hindi",
            "music_visual_sync": False,
            "audio_note": "Playful tone in voiceover matches the inversions visual surprise. The voiceover sells food with genuine enthusiasm which makes the eventual pivot funnier. Light, bouncy music supports the playful tone without dominating."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "high",
            "text_overlay_density": "minimal",
            "color_mood": "bright",
            "product_visibility": "reveal_moment",
            "visual_note": "Food is shot beautifully (food-ad quality) which deepens the inversion joke — this LOOKS like a food ad. The visual craft serves the misdirection. When the Colgate tube appears, the contrast with the food imagery is stark and memorable."
        },
        "cta": {
            "type": "other",
            "timing": "late",
            "visual_treatment": "combined",
            "urgency_element": "none",
            "cta_note": "CTA is behavioral (brush at night) not commercial (buy Colgate). This is a long-term category-building strategy. If people brush at night, they buy more toothpaste. The CTA serves Colgate's business without being transactional."
        },
        "brand": {
            "logo_presence": "bookend",
            "brand_first_named_seconds": 2,
            "brand_voice_consistent": True,
            "brand_note": "Colgate visible from the start — critical for the inversion to work. You NEED to know it is Colgate selling food for the surprise to land. Brand presence enhances the creative rather than interrupting it. One of the rare cases where early brand reveal makes the ad better."
        },
        "emotional": {
            "primary_emotion": "humor",
            "cultural_specificity": ["family", "urban/rural"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Night eating (late dinner, midnight snacking) is universal in Indian households. The food items shown (biryani, chaat) are culturally specific and appetizing. The ad taps into the guilty pleasure of eating late, which is relatable across class and region."
        },
        "x_factor": "The inversion mechanic is what makes this exceptional. A toothpaste brand selling food is such a clean, simple concept that it feels obvious in hindsight — the hallmark of a great idea. It makes the 'brush at night' message unforgettable because it is wrapped in a memorable joke. The brand benefits from early reveal (unusual) because the brand-doing-unexpected-thing IS the joke.",
        "lessons_for_wiom": [
            "Inversion as creative technique: what is the OPPOSITE of what an ISP would advertise? An ISP promoting 'disconnect time' or 'go outside' could be a powerful inversion that ultimately reinforces why you need reliable internet (so you can disconnect on YOUR terms, not because it dropped).",
            "Early brand reveal works when the brand is part of the surprise. If Wiom did something unexpected (ISP selling board games, ISP promoting outdoor activities), the brand visibility is essential to the joke.",
            "Behavior change messaging (brush at night / check your internet speed) can build category while building brand. Wiom could promote 'test your internet speed' as a behavior that ultimately drives switching."
        ]
    },

    # ─── ad_009: Sony LIV Do Not Apply ───────────────────────────────────
    {
        "ad_id": "ad_009",
        "hook": {
            "type": "controversy",
            "face_first_frame": False,
            "text_overlay_first_frame": True,
            "brand_visible_3s": True,
            "audio_hook": "voiceover",
            "language": "Hindi",
            "effectiveness_note": "Title card saying 'Do Not Apply' for a registration ad. The contradiction is impossible to ignore. Reverse psychology triggers reactance — when told NOT to do something, people want to do it more. The hook works on a deep psychological level that bypasses rational evaluation."
        },
        "narrative": {
            "arc_type": "single_scene",
            "tension_payoff": "buildup",
            "num_scenes": 5,
            "effectiveness_note": "Builds a satirical argument for why you should NOT apply to Shark Tank. Each reason is actually a disguised argument for WHY you should (e.g., 'do not apply because you will have to work hard' = 'Shark Tank rewards hard work'). The double-meaning structure rewards attentive viewers."
        },
        "pacing": {
            "duration_bucket": "30s",
            "cuts_per_15s": 4,
            "pace_changes": ["0-5s: provocative title card", "5-25s: escalating satirical reasons", "25-35s: reveal and CTA", "35-45s: registration details"],
            "pattern_interrupts": ["Each new satirical reason re-engages because the viewer is enjoying the cleverness of the double-meaning"],
            "retention_note": "The viewer stays because they are decoding the double-meaning in real time. It is intellectually engaging — you are solving a puzzle, not passively watching. People who get the satire feel smart, which creates positive brand association."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": True,
            "voiceover_tone": "authority",
            "language": "Hindi",
            "music_visual_sync": False,
            "audio_note": "Authoritative voiceover delivers the 'do not apply' message with deadpan seriousness. The contrast between serious delivery and satirical content is the comedy engine. If the voiceover winked, it would undermine the whole concept. The straight delivery is essential."
        },
        "visual": {
            "talent_type": "no_talent",
            "production_quality": "mid",
            "text_overlay_density": "heavy",
            "color_mood": "dark",
            "product_visibility": "always_visible",
            "visual_note": "Bold typography dominates — the text IS the visual. Heavy text overlay works here because the words ARE the content. Dark, serious visual tone reinforces the fake-warning aesthetic. This is designed to work sound-off because the text carries the full message."
        },
        "cta": {
            "type": "sign_up",
            "timing": "late",
            "visual_treatment": "combined",
            "urgency_element": "limited_time",
            "cta_note": "Registration deadline creates natural urgency. The entire reverse-psychology setup makes the CTA (apply now) feel like a rebellion — you are defying the ad's instructions. This transforms a mundane registration CTA into an act of agency. Brilliant."
        },
        "brand": {
            "logo_presence": "bookend",
            "brand_first_named_seconds": 2,
            "brand_voice_consistent": True,
            "brand_note": "Sony LIV and Shark Tank branding upfront — necessary because the reverse psychology only works if you know WHO is telling you not to apply. Brand presence is essential to the mechanic, not a compromise."
        },
        "emotional": {
            "primary_emotion": "humor",
            "cultural_specificity": ["youth_culture"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "References employment debates and startup culture in India. Taps into the aspirational energy of Indian youth who dream of building businesses. The 'do not apply' framing implicitly says 'only the brave should apply' which flatters the target audience."
        },
        "x_factor": "Reverse psychology is an underused mechanic in Indian advertising. This ad proves it works spectacularly. The concept is so simple it fits in three words ('Do Not Apply') yet generates layers of satirical meaning. The ad makes the VIEWER do the work of persuading themselves — the most powerful form of marketing. You are not told to apply; you DECIDE to apply despite being told not to. That is agency, not advertising.",
        "lessons_for_wiom": [
            "Reverse psychology for ISP: 'Do Not Switch to Wiom' campaign listing reasons not to switch that are actually reasons TO switch. 'Do not switch because you will get addicted to video calls that actually work.' Bold, memorable, shareable.",
            "Text-heavy sound-off design is underused in Indian digital ads. For Meta feed placement, a bold-text reverse-psychology ad would stop thumbs because it looks different from every other video ad.",
            "Making the viewer persuade themselves is more powerful than persuading them. Wiom could pose challenges: 'Think your internet is fast enough? Run this test.' Let the experience do the selling."
        ]
    },

    # ─── ad_010: Adani Group ─────────────────────────────────────────────
    {
        "ad_id": "ad_010",
        "hook": {
            "type": "curiosity_gap",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": False,
            "audio_hook": "dialogue",
            "language": "Hindi",
            "effectiveness_note": "Opens with the cryptic catchphrase 'Pehle pankha aayega, phir bijli aayegi' (first the fan will come, then the electricity). This makes NO logical sense — fans need electricity, not the other way around. The logical impossibility creates an irresistible curiosity gap. You MUST watch to understand."
        },
        "narrative": {
            "arc_type": "problem_solution",
            "tension_payoff": "buildup",
            "num_scenes": 6,
            "effectiveness_note": "Mystery narrative structure: the catchphrase is repeated in different contexts, each time deepening the mystery. The viewer is solving a puzzle: what does this phrase mean? The reveal (Adani's rural electrification) recontextualizes everything. The delayed gratification makes the payoff more powerful."
        },
        "pacing": {
            "duration_bucket": "60s+",
            "cuts_per_15s": 3,
            "pace_changes": ["0-10s: mysterious opening", "10-40s: repeated catchphrase in different scenarios builds intrigue", "40-50s: reveal", "50-60s: brand and emotional payoff"],
            "pattern_interrupts": ["Each repetition of the catchphrase in a new context is a mini-mystery that re-engages the viewer"],
            "retention_note": "Mystery structure is one of the strongest retention mechanics. The unanswered question (what does the catchphrase mean?) creates an open loop the brain NEEDS to close. Drop-off is low because leaving early means never getting the answer."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": True,
            "voiceover_tone": "emotional",
            "language": "Hindi",
            "music_visual_sync": False,
            "audio_note": "Score builds gradually from mysterious to emotional as the reveal approaches. The catchphrase becomes almost musical through repetition — it lodges in memory. The voiceover shifts from enigmatic to warm at the reveal, mirroring the narrative arc."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "high",
            "text_overlay_density": "none",
            "color_mood": "muted",
            "product_visibility": "absent_until_cta",
            "visual_note": "Rural Indian settings — villages without electricity. Muted tones convey pre-electrification reality. When electricity arrives, the visual palette shifts to warm, brighter tones. The color shift IS the payoff, experienced visually even before the narration explains it."
        },
        "cta": {
            "type": "other",
            "timing": "late",
            "visual_treatment": "voiceover_only",
            "urgency_element": "none",
            "cta_note": "No commercial CTA. This is corporate brand building — 'Adani brings electricity to those who need it.' The ad asks nothing of the viewer except a changed perception. For an infrastructure conglomerate with reputation challenges, this is the right strategy."
        },
        "brand": {
            "logo_presence": "end_card_only",
            "brand_first_named_seconds": 50,
            "brand_voice_consistent": True,
            "brand_note": "Brand reveal at 50 seconds is the most delayed in the library. The mystery would be destroyed by early brand reveal. When Adani's name finally appears, it carries the weight of the entire narrative. The delay is essential to the mechanic."
        },
        "emotional": {
            "primary_emotion": "pride",
            "cultural_specificity": ["urban/rural"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Rural electrification touches a deep nerve in India where millions still lack reliable power. The catchphrase structure has an oral-tradition quality, like a folk saying, which gives it cultural weight. The pride emotion (look what India is building) is powerful for infrastructure brands."
        },
        "x_factor": "The catchphrase is the ad. 'Pehle pankha aayega, phir bijli aayegi' is memorable, quotable, and works as both mystery and revelation. Before the reveal it is nonsensical and intriguing. After the reveal it is poetic and moving (fans are delivered to villages BEFORE the electricity grid reaches them — the fan arriving first symbolizes the promise of progress). A single phrase that works on two levels simultaneously is rare and valuable creative craft.",
        "lessons_for_wiom": [
            "Catchphrase as narrative device: Wiom could build a campaign around a seemingly paradoxical phrase about connectivity that resolves into a meaningful truth. 'Pehle connection aayega, phir internet aayegi' — first the human connection, then the internet connection.",
            "Mystery structure for infrastructure brands: broadband installation is inherently boring. But wrapped in a mystery narrative, the reveal of 'what Wiom actually does for a family' could be genuinely moving. Show the BEFORE (disconnected life) as a mystery that the AFTER (connected life) solves.",
            "Rural/Tier-3 India as protagonist, not afterthought. Most ISP ads show urban apartments. Showing a small-town family getting reliable internet for the first time would be emotionally powerful and differentiate Wiom from metro-focused Jio/Airtel."
        ]
    },

    # ─── ad_011: Meesho ──────────────────────────────────────────────────
    {
        "ad_id": "ad_011",
        "hook": {
            "type": "visual_surprise",
            "face_first_frame": True,
            "text_overlay_first_frame": True,
            "brand_visible_3s": True,
            "audio_hook": "dialogue",
            "language": "Hindi",
            "effectiveness_note": "Kapil Sharma's face is an instant hook for the Tier 2-3 audience — he is India's most recognized comedy face in non-metro India. The 'Aise Kaise?' (How is this possible?) tagline in text immediately signals deals/offers. For the target audience, celebrity plus deals equals mandatory viewing."
        },
        "narrative": {
            "arc_type": "demo",
            "tension_payoff": "front_loaded",
            "num_scenes": 5,
            "effectiveness_note": "Series of scenarios where families discover prices so low they cannot believe it. Each scenario is a mini-demo of a product category (fashion, kidswear, home). The 'Aise Kaise?' reaction is the throughline. Works because it mirrors the real user experience of discovering Meesho's prices."
        },
        "pacing": {
            "duration_bucket": "30s",
            "cuts_per_15s": 6,
            "pace_changes": ["0-5s: celebrity hook", "5-20s: rapid product showcases", "20-30s: brand and sale details"],
            "pattern_interrupts": ["Each new product category with its shock-price reveal re-grabs attention"],
            "retention_note": "Fast-paced deal montage keeps energy high. The 'Aise Kaise?' reaction after each reveal is a satisfying micro-payoff. Risk: at 30s of rapid-fire deals, it could feel like a QVC infomercial. The celebrity presence and humor prevent this."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": True,
            "voiceover_tone": "energetic",
            "language": "Hindi",
            "music_visual_sync": True,
            "audio_note": "Upbeat, festive music matching the sale energy. Kapil's voice and comic timing carry the humor. The 'Aise Kaise?' catchphrase is repeated with different intonations — surprise, disbelief, excitement. Music is functional: it creates urgency and festive energy."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "mid",
            "text_overlay_density": "heavy",
            "color_mood": "bright",
            "product_visibility": "always_visible",
            "visual_note": "Bright, festive colors. Heavy price text overlays because the PRICE is the content — this is a sale ad, and the price must be readable. Products prominently displayed in every frame. Visual design is functional over artistic — clarity beats creativity for this audience and objective."
        },
        "cta": {
            "type": "download_app",
            "timing": "multiple",
            "visual_treatment": "combined",
            "urgency_element": "limited_time",
            "cta_note": "Multiple CTAs: sale dates, app download, specific offers. For a sale campaign, multiple CTAs work because the urgency is real and time-bound. The festive context (Diwali shopping) means the audience is already in buying mode — the CTA is pushing an open door."
        },
        "brand": {
            "logo_presence": "always_visible",
            "brand_first_named_seconds": 2,
            "brand_voice_consistent": True,
            "brand_note": "Meesho brand prominent throughout. For a value/sale campaign, brand visibility is essential — you need to remember WHERE to get these deals. The orange brand color is woven into the festive visual palette. Celebrity and brand are co-equal in visibility."
        },
        "emotional": {
            "primary_emotion": "aspiration",
            "cultural_specificity": ["festival", "family"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Festive shopping is a ritual for Indian families. The ad shows families (parents and kids together) discovering deals — this is the real Diwali shopping experience for lower-middle-class households. The emotional core is 'I can afford nice things for my family this festival.' That is deeply aspirational for the target segment."
        },
        "x_factor": "Meesho understands its audience better than almost any Indian brand. The ad does not try to be clever or award-winning. It is functionally perfect for lower-middle-class families in Tier 2-3 cities: celebrity they love, prices that shock them, products they want, a festival they are shopping for. The 'Aise Kaise?' catchphrase turns price into entertainment. The 100 percent Day 1 order increase proves this is not just good creative — it is effective creative. That distinction matters.",
        "lessons_for_wiom": [
            "For Tier 2-3 families, celebrity plus value is the proven formula. Wiom should consider a relatable celebrity (not Bollywood A-list but TV-famous like Kapil) paired with a clear value proposition (price per month, what you get).",
            "Heavy text overlays work for deal-oriented content targeting lower-middle-class audiences. When the price IS the hook, make it huge and unmissable. Wiom plan prices displayed prominently would work for this segment.",
            "Festive timing is not optional for this audience. Diwali, Dussehra, Eid, Onam — families make purchase decisions around festivals. Wiom launch or promotional campaigns should align with festive windows."
        ]
    },

    # ─── ad_012: Surf Excel ──────────────────────────────────────────────
    {
        "ad_id": "ad_012",
        "hook": {
            "type": "relatable_moment",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": False,
            "audio_hook": "dialogue",
            "language": "Hindi",
            "effectiveness_note": "Opens with a kid doing something messy — every parent instantly relates. The immediate thought is 'my kid does this too.' The hook is not the stain; it is the parental recognition. The viewer is hooked because they see their own family."
        },
        "narrative": {
            "arc_type": "problem_solution",
            "tension_payoff": "buildup",
            "num_scenes": 5,
            "effectiveness_note": "The narrative subverts the expected problem-solution: the 'problem' (stain) is reframed as a 'badge' (the kid did something good). The 'solution' is not the detergent but the parent's realization. This double-layer narrative is why the campaign has endured for 15 plus years. The detergent is secondary to the parenting story."
        },
        "pacing": {
            "duration_bucket": "30s",
            "cuts_per_15s": 3,
            "pace_changes": ["0-10s: kid gets stained doing something sweet/brave", "10-25s: parent discovers and initially reacts", "25-35s: parent understands, emotional payoff", "35-45s: product and tagline"],
            "pattern_interrupts": ["15s: parent's initial worried reaction creates a moment of tension — will they scold the kid?"],
            "retention_note": "The parental tension (will they be angry or proud?) is a natural retention mechanism. Every parent recognizes this fork in the road. The emotional resolution (pride, not anger) is deeply satisfying and keeps people watching through the product message."
        },
        "audio": {
            "music_type": "original_score",
            "voiceover": True,
            "voiceover_tone": "emotional",
            "language": "Hindi",
            "music_visual_sync": False,
            "audio_note": "Gentle, emotional score that swells at the realization moment. The voiceover delivers 'Daag Acche Hain' as a tagline-turned-philosophy. The audio layer is warm and reassuring — it sounds like being hugged. For parents, this audio tone hits directly in the heart."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "high",
            "text_overlay_density": "none",
            "color_mood": "bright",
            "product_visibility": "reveal_moment",
            "visual_note": "Bright, warm colors. Real-looking middle-class homes, school uniforms, playgrounds. The visual world is aspirational but achievable — the home is nice but not rich. The kid looks like every kid. The visual strategy is 'your family, slightly idealized.' Product appears only after the emotional payoff."
        },
        "cta": {
            "type": "other",
            "timing": "late",
            "visual_treatment": "voiceover_only",
            "urgency_element": "none",
            "cta_note": "No hard CTA. 'Daag Acche Hain' is both the tagline and the call to action — it reframes stains from negative to positive, which is the only persuasion needed. If you believe stains are okay, you need a detergent that handles them. Implicit logic, no explicit ask."
        },
        "brand": {
            "logo_presence": "end_card_only",
            "brand_first_named_seconds": 35,
            "brand_voice_consistent": True,
            "brand_note": "Surf Excel has earned the right to delay brand reveal through 15 plus years of consistent 'Daag Acche Hain' campaigns. The emotional territory is so thoroughly owned that the tagline IS the brand. No other detergent can run this ad."
        },
        "emotional": {
            "primary_emotion": "warmth",
            "cultural_specificity": ["family"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Indian parenting culture puts enormous emphasis on clean clothes (especially school uniforms). A stained shirt is genuinely anxiety-inducing for Indian parents. The ad directly addresses this anxiety and offers a reframe: your kid's stained clothes prove they are brave and kind. This is therapeutic advertising."
        },
        "x_factor": "Daag Acche Hain is possibly the greatest Indian advertising idea of the 21st century. It did what no detergent ad had done: it made the stain the HERO. Every competitor says 'our detergent removes stains better.' Surf Excel says 'stains are good — and we will clean them after.' That repositioning of the entire category conversation is a masterclass in strategic creativity. The insight (parents feel guilty when kids get stained, but the stain often means the kid did something wonderful) is true, universal, and endlessly extensible.",
        "lessons_for_wiom": [
            "Reframe the negative: every ISP competes on 'fewer outages, faster speed.' What if Wiom reframed? 'Your kid spent 3 hours on a video call with grandma. That is 3 hours of love, powered by Wiom.' The usage (bandwidth) becomes the badge, just as the stain became the badge.",
            "Commodity-to-emotion transformation is the ultimate brand strategy. Broadband is a commodity. Wiom's creative must attach emotional meaning to the product beyond specs. What does reliable internet MEAN for a family? That is the creative territory.",
            "Family-as-protagonist with kids at the center is the most effective format for household products in India. Wiom should build campaigns around what kids DO with internet (learn, create, connect with family) not what the internet IS (fast, reliable)."
        ]
    },

    # ─── ad_013: Tata Tea Jaago Re ───────────────────────────────────────
    {
        "ad_id": "ad_013",
        "hook": {
            "type": "controversy",
            "face_first_frame": True,
            "text_overlay_first_frame": False,
            "brand_visible_3s": False,
            "audio_hook": "dialogue",
            "language": "Hindi",
            "effectiveness_note": "Opens with a parent and child in a mild argument about patriotism — a politically charged topic that immediately creates tension. Controversy hooks work because they trigger emotional engagement before rational evaluation. The family setting makes it feel intimate rather than preachy."
        },
        "narrative": {
            "arc_type": "single_scene",
            "tension_payoff": "buildup",
            "num_scenes": 3,
            "effectiveness_note": "Single living-room conversation that builds from disagreement to understanding. The generational tension is the engine: parents believe patriotism means one thing, kids believe it means another. Neither is wrong. The narrative does not resolve the debate — it reframes it. Viewers stay because they are choosing sides."
        },
        "pacing": {
            "duration_bucket": "60s+",
            "cuts_per_15s": 2,
            "pace_changes": ["0-15s: scene setting and positions established", "15-40s: debate escalates with emotional stakes", "40-55s: emotional resolution/reframe", "55-60s: brand moment"],
            "pattern_interrupts": ["25s: one character says something unexpectedly vulnerable that shifts the debate from intellectual to emotional"],
            "retention_note": "Debate format is inherently high-retention because the viewer is actively processing arguments and forming opinions. You cannot passively watch a debate — your brain engages. The family context adds emotional stakes to the intellectual content."
        },
        "audio": {
            "music_type": "no_music",
            "voiceover": False,
            "voiceover_tone": null,
            "language": "Hindi",
            "music_visual_sync": False,
            "audio_note": "No music during the conversation — just dialogue in a living room. This is a bold choice that creates intimacy and realism. The absence of music makes every word land harder. A score would signal 'this is an ad' — the silence says 'this is real.' Music only enters at the brand moment."
        },
        "visual": {
            "talent_type": "actor",
            "production_quality": "high",
            "text_overlay_density": "none",
            "color_mood": "muted",
            "product_visibility": "absent_until_cta",
            "visual_note": "Middle-class living room set. Muted, natural lighting — no advertising gloss. The visual restraint matches the conversational tone. Close-ups on faces during dialogue mirror the emotional intimacy. The living room IS the visual strategy: this is where India's conversations happen."
        },
        "cta": {
            "type": "other",
            "timing": "late",
            "visual_treatment": "voiceover_only",
            "urgency_element": "none",
            "cta_note": "No commercial CTA. 'Jaago Re' (wake up) is the call to action — a call to think, not to buy. The tea appears in the scene naturally (family having chai during discussion). The product is incidental to the conversation it enables. Brand building through cultural relevance."
        },
        "brand": {
            "logo_presence": "end_card_only",
            "brand_first_named_seconds": 55,
            "brand_voice_consistent": True,
            "brand_note": "Tata Tea's 'Jaago Re' platform has run for over 15 years, establishing the brand as a catalyst for social conversations. The brand delayed until the end works because the debate format IS the Jaago Re brand. The chai in the scene is a subtle visual brand presence throughout."
        },
        "emotional": {
            "primary_emotion": "pride",
            "cultural_specificity": ["family"],
            "hinglish_level": "pure_hindi",
            "cultural_note": "Generational debates about India are a living-room staple. Every Indian family has had a version of this conversation. The ad captures a REAL dynamic rather than inventing one. The patriotism topic during Republic Day or Independence Day timing is culturally precise. The debate format respects the audience by not giving easy answers."
        },
        "x_factor": "This ad turns a brand into a conversation starter. Most ads try to end conversations (buy this, done). Tata Tea starts them. The 'Jaago Re' platform is brilliant because it positions tea as the fuel for meaningful family discussions. The ad works because it does not preach — both sides of the generational debate are presented with empathy. The viewer leaves thinking about patriotism and family, not about tea. But the association (Tata Tea equals thoughtful conversations) is permanently planted.",
        "lessons_for_wiom": [
            "Internet as conversation enabler: Wiom could position itself as what POWERS the family conversations that matter. Not just 'fast internet' but 'the connection behind every connection.' A family debating something important over a video call with grandparents — powered by Wiom.",
            "Living room as brand territory: for a home internet provider, the living room is the natural stage. Showing real family dynamics (generational debates, kids teaching parents tech, family movie night disagreements) in the living room where the Wiom router sits quietly in the background.",
            "Debate format drives shareability: people shared this ad because they wanted to continue the debate. Wiom could create debate-format content ('Is unlimited data a right or a privilege?') that people share to express their position."
        ]
    }
]

# Save all through harness
for d in deconstructions:
    ok, msg = save_deconstruction(d)
    print(f"{'OK' if ok else 'FAIL'} | {msg}")
