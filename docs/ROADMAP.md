# CUE — Implementation Roadmap

**Objective:** Learn what makes the best video ads cut through clutter, then review Wiom's ads against those standards — scorecard + actionable suggestions.

**Two-phase approach:**
- **Phase 1:** Study best-in-class → extract patterns (what works + what doesn't)
- **Phase 2:** Score Wiom's ads against those patterns → suggestions for improvement

**First-Principles Approach:** Each step validates assumptions before investing in the next.

---

## Logical Chain (all must hold true)

```
[A] Best-in-class ads share identifiable, decomposable patterns
    ↓ (if false, "great creative" is idiosyncratic and can't be studied)
[B] Those patterns are learnable and repeatable
    ↓ (if false, AI extracts noise, not signal)
[C] We can access enough best-in-class creatives to extract meaningful patterns
    ↓ (if false, nothing to learn from)
[D] Wiom's ads can be meaningfully scored against these patterns
    ↓ (if false, the benchmark doesn't apply to our context)
[E] Pattern-based suggestions lead to measurable improvement
    ↓ (if false, the exercise is academic)
[F] The team acts on the scorecards and suggestions
    ↓ (if false, shelfware)
```

---

## PHASE 1: LEARN FROM THE BEST

---

### Step 0: Source the Best (Weeks 1-2) — Agent S (Scout)

**Goal:** Build a curated library of 50-100 best-in-class video ads focused on cutting through clutter.

#### 0.1 Define "Best-in-Class" Criteria
- [ ] Primary verticals: ISP/broadband, telecom, consumer internet/apps in India
- [ ] Adjacent verticals (for pattern diversity): fintech, D2C, ed-tech — Indian brands
- [ ] Global exemplars: standout ads from any vertical with exceptional hook, retention, or CTA execution
- [ ] "Best" = cuts through clutter: high video completion + high CTR + strong CTA performance
- [ ] Awards/recognition as proxy where performance data isn't available

#### 0.2 Source Channels
- [ ] **Meta Ad Library** (free, public) — search by advertiser, keyword, region (India). Top competitors: Jio, Airtel, Vi, ACT Fibernet, Excitel, etc.
- [ ] **YouTube Ads Transparency Center** — active/recent video ads by advertiser
- [ ] **WARC Creative Database** — award-winning campaigns with effectiveness data
- [ ] **Cannes Lions / D&AD / Effies India archives** — highest-craft video work
- [ ] **Think with Google India** — case studies with performance benchmarks
- [ ] **Foreplay / Swipe File / AdSpy** (if budget allows) — curated high-performing ad libraries
- [ ] **Team knowledge** — "Which competitor or brand ads made you stop scrolling?"

#### 0.3 Initial Curation
- [ ] Collect 50-100 video ads across sources
- [ ] For each: URL/reference, advertiser, platform, format, duration, language, date
- [ ] Tier: "exceptional" / "strong" / "reference" (LLM suggests, human confirms)
- [ ] Store in `library/metadata/` as structured JSON
- [ ] Also curate 20-30 "mediocre" ads from same verticals (for anti-pattern analysis)

**Decision Gate:** 50+ quality exemplars across 3+ verticals? Proceed. Too thin? Expand categories.

---

### Step 1: Build Deconstruction Framework (Weeks 2-4) — Agent D (Deconstruct)

**Goal:** Structured taxonomy so every ad — best-in-class AND Wiom's — can be broken down the same way.

#### 1.1 Creative Taxonomy (30-50 features)

**Hook (first 3 seconds)**
- Type: question, shocking stat, problem statement, visual surprise, testimonial, product demo, curiosity gap, controversy, relatable moment
- Face in first frame: Y/N
- Text overlay in first frame: Y/N
- Brand visible in first 3s: Y/N
- Audio hook: music hit, voiceover, sound effect, silence, dialogue
- Language of hook: Hindi / English / Hinglish / regional / visual only

**Narrative Structure**
- Arc type: problem→solution, before→after, testimonial/story, demo/walkthrough, listicle, comparison, day-in-life, UGC-style, montage, single-scene
- Tension/payoff: build-up or front-loaded?
- Number of distinct scenes/cuts

**Pacing & Retention**
- Duration: 6s / 15s / 30s / 60s+
- Cuts per 15s (visual pace)
- Pace changes: where do transitions/energy shifts happen?
- Pattern interrupts: moments designed to re-grab attention

**Audio**
- Music: trending audio, original score, no music, sound effects only
- Voiceover: Y/N, tone (authority, conversational, energetic, emotional)
- Language: Hindi / English / Hinglish / code-switching / regional
- Music-visual sync: cuts synced to beats?

**Visual Craft**
- Talent: actor, real user/UGC, influencer, no talent, animation
- Production quality: high-production, mid, lo-fi/UGC-style
- Text overlay density: none / minimal / heavy
- Color/mood: bright, muted, dark, brand-colored
- Product visibility: always visible, reveal moment, absent until CTA

**CTA**
- Type: download app, visit site, book now, learn more, shop, sign up
- Timing: early (first 25%), mid (25-60%), late (60%+), multiple
- Visual treatment: text overlay, button mock-up, voiceover only, combined
- Urgency element: limited time, social proof, scarcity, none

**Brand Integration**
- Logo: always present, bookend only, end card only, embedded naturally
- Brand mention: when first named (seconds)?
- Brand voice consistency: feels like the brand or generic?

**Emotional/Cultural Layer**
- Primary emotion: humor, aspiration, fear/urgency, relatability, pride, warmth
- Cultural specificity: festival, family, regional identity, urban/rural, youth culture
- Hinglish level: pure Hindi / pure English / light mix / heavy code-switching

Document in `docs/creative-taxonomy.md`

#### 1.2 Deconstruction Prompt Engineering
- [ ] Build LLM prompt (Gemini 2.0 for video, Groq for text) that:
  - Takes a video ad as input
  - Outputs complete taxonomy breakdown
  - Explains *why* each element likely works (not just *what*)
  - Identifies the "1-2 things that make this ad cut through" — the X-factor
- [ ] Test on 10 ads, refine until breakdowns are accurate and useful
- [ ] Cultural nuance, Hinglish, Indian context — human spot-check required

#### 1.3 Validation
- [ ] Deconstruct 10 ads, have marketing team review
- [ ] "Does this breakdown capture what actually makes this ad good?"
- [ ] If not → revise taxonomy and prompts before proceeding

---

### Step 2: Extract Patterns (Weeks 4-7) — Agent P (Pattern)

**Goal:** Find the repeatable patterns across top performers. This becomes the benchmark.

#### 2.1 Full Library Deconstruction
- [ ] Run every curated ad through the deconstruction pipeline
- [ ] Human spot-check: minimum 20% (especially Indian/multilingual ads)
- [ ] Store breakdowns in `library/metadata/`
- [ ] Each ad: taxonomy tags + "what makes this one cut through" narrative

#### 2.2 Pattern Extraction — Cutting Through Clutter (Leading Metrics)
- [ ] Cluster by shared features. Look for:
  - **Hook patterns**: Dominant hook types in "exceptional" tier?
  - **Retention patterns**: Where do top ads place pace changes? How prevent mid-video drop-off?
  - **CTR drivers**: What separates "watched AND clicked" from just "watched"?
  - **Format-specific patterns**: Reels vs YouTube pre-roll differences?
  - **Duration sweet spots**: Optimal length by vertical/platform?

- [ ] For each pattern, document:
  - **The pattern**: e.g., "Top ISP ads use problem→solution with problem in first 2 seconds"
  - **Evidence**: "Found in 8/12 exceptional-tier telecom ads"
  - **Why it works**: "Immediate relevance — viewer's frustration reflected, urgency to see solution"
  - **Confidence**: Strong (70%+ of top ads) / Moderate (50-70%) / Emerging

#### 2.3 Pattern Extraction — Conversion Drivers (Lagging Metrics)
- [ ] What drives "watched and clicked" → "actually downloaded/booked"?
  - CTA clarity and timing
  - Value proposition specificity
  - Friction reducers (free trial, no sign-up, instant access)
  - Social proof elements
  - Post-click experience hints
- [ ] These patterns often differ from video completion drivers

#### 2.4 Anti-Patterns
- [ ] Deconstruct the 20-30 "mediocre" ads from Step 0
- [ ] What's systematically different vs exceptional tier?
- [ ] Common pitfalls: brand-first openings, slow hooks, no pattern interrupt, generic CTA, overcrowded visuals, mismatched audio-visual energy

#### 2.5 Creative Playbook v1
- [ ] Output: `docs/creative-playbook.md`
- [ ] **This is the benchmark** — the standard Wiom's ads will be measured against
- [ ] Organized by:
  - What drives video completion
  - What drives CTR
  - What drives app downloads / bookings
- [ ] Each pattern: description, evidence, why it works, confidence, examples
- [ ] Anti-patterns: "don't do this" with evidence
- [ ] Platform-specific notes (Meta vs YouTube)
- [ ] India-specific: Hindi/Hinglish, cultural context, regional variation
- [ ] Scoring rubric: how to rate an ad against each pattern (1-5 scale or pass/partial/fail)

---

## PHASE 2: EVALUATE OURS

---

### Step 3: Review Wiom's Ads (Weeks 7-10) — Agent R (Review) + Agent X (Suggest)

**Goal:** Take Wiom's actual ads, score them against the best-in-class patterns, and generate specific improvement suggestions.

#### 3.1 Wiom Ad Ingestion
- [ ] Collect Wiom's current and recent video ads
- [ ] Sources: Meta Ads Manager exports, YouTube channel, internal creative library
- [ ] For each: video file/URL, campaign objective, platform, format, audience, language, performance data if available
- [ ] Store in `wiom-ads/metadata/`

#### 3.2 Deconstruct Wiom's Ads (Same Taxonomy)
- [ ] Run each Wiom ad through the exact same deconstruction pipeline used for best-in-class
- [ ] Critical: same taxonomy, same prompt, same rigor
- [ ] This creates an apples-to-apples comparison

#### 3.3 Scorecard Generation (Agent R)
- [ ] For each Wiom ad, score against every pattern in the playbook:

  **Scorecard format:**
  ```
  AD: [Wiom ad name/ID]
  PLATFORM: Meta / YouTube    FORMAT: Reel / In-Feed / Pre-Roll
  OVERALL SCORE: [X/100]

  HOOK (Weight: 30%)
  ├── Pattern match: [which best-in-class pattern it aligns with, if any]
  ├── Score: [1-5]
  ├── Gap: "Hook is brand-first (logo at 0s). Best-in-class: problem statement first, brand after 3s"
  └── Reference: [specific best-in-class ad that does this well]

  RETENTION (Weight: 25%)
  ├── Pattern match: ...
  ├── Score: [1-5]
  ├── Gap: "No pace change after 8s. Top ads add a visual interrupt at 8-10s"
  └── Reference: ...

  CTR DRIVERS (Weight: 20%)
  ├── ...

  CTA / CONVERSION (Weight: 15%)
  ├── ...

  BRAND COHERENCE (Weight: 10%)
  ├── ...

  ANTI-PATTERNS TRIGGERED: [list any anti-patterns this ad matches]
  ```

- [ ] Score weights adjustable based on campaign objective (completion-focused vs download-focused)
- [ ] Dual lens: performance patterns + brand/cultural coherence
- [ ] Store in `output/scorecards/`

#### 3.4 Improvement Suggestions (Agent X)
- [ ] For each gap identified in the scorecard, generate a specific suggestion:

  **Suggestion format:**
  ```
  ELEMENT: Hook
  CURRENT: Brand logo animation for 2s, then product features
  PATTERN SAYS: Top-performing ISP ads open with a relatable problem in first 2s
  (Evidence: 9/12 exceptional-tier ads, confidence: Strong)
  SUGGESTION: Replace opening with a "buffering frustration" moment — show
  someone's video call freezing mid-conversation. Cut to solution at 3s.
  WHY IT WORKS: Immediate emotional recognition. Viewer thinks "that's me."
  Creates urgency for the solution (your product).
  REFERENCE ADS: [Jio Fiber "No More Buffering" — see 0:00-0:03], [Airtel "Lag-Free" — hook pattern]
  EXPECTED IMPACT: Hook Rate improvement from ~25th to ~65th percentile based on pattern data
  CONFIDENCE: High (pattern validated across 9/12 top ads in vertical)
  ```

- [ ] Suggestions are constraint-based: must respect Wiom's brand voice, audience, cultural context
- [ ] Prioritized: highest-impact gaps first (biggest score gaps × pattern confidence)
- [ ] Each suggestion includes a reference ad from the library as visual inspiration
- [ ] Store in `output/suggestions/`

#### 3.5 Summary Report
- [ ] Aggregate scorecard: "Across N Wiom ads, the systematic gaps are..."
  - "Hook: 70% of our ads open brand-first vs 15% of best-in-class"
  - "CTA timing: our average is at 82% of video vs best-in-class at 55%"
  - "Pacing: 0/N ads have a pattern interrupt vs 80% of top performers"
- [ ] Top 3 highest-leverage improvements (would move the most ads the furthest)
- [ ] Store in `output/summary-report.md`

#### 3.6 Human Review Gate
- [ ] Creative team reviews scorecards and suggestions
- [ ] Accept / reject / modify each suggestion
- [ ] Track: which suggestions get adopted? This feeds future pattern confidence

---

## PHASE 3 (FUTURE): CREATE NEW

---

### Step 4: Pattern-Informed Briefs — Agent B (Brief)

**Only after Phase 2 proves the patterns hold for Wiom's context.**

#### 4.1 Creative Brief Generator
- [ ] Input: campaign objective, platform, format, audience, language
- [ ] Output: brief informed by validated patterns + Wiom-specific scorecard learnings
- [ ] Every recommendation traceable to a pattern AND validated by Wiom's own scorecard data
- [ ] Reference reel: 3-5 best-in-class ads that exemplify the brief's direction

#### 4.2 A/B Validation
- [ ] Test pattern-informed new creatives vs team's usual approach
- [ ] Same audience, budget, time window
- [ ] Measure: video completion, CTR, app downloads, bookings
- [ ] Feed results back → upgrade/downgrade patterns

#### 4.3 Library Refresh
- [ ] Monthly: add 10-20 new ads to library
- [ ] Re-run pattern extraction for emerging trends
- [ ] Update scorecards as patterns evolve

---

## Key Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Best-in-class ads don't share decomposable patterns | Low-Medium | Premise fails | Step 1.3 validation with team |
| Patterns don't transfer to Wiom's context | Medium | Scorecards are irrelevant | Step 3 reveals this — if Wiom's best ads also violate the patterns, the patterns don't apply |
| AI misreads cultural/Hinglish nuance | High | Inaccurate breakdowns | Human spot-check mandatory |
| Scorecard becomes a checkbox exercise | Medium | Misses the "magic" | Always include X-factor, not just feature counting |
| Frankenstein suggestions | High if ungated | Incoherent creatives | Dual lens + human veto |
| Survivorship bias — only studying winners | Medium | Miss what NOT to do | Anti-pattern analysis (Step 2.4) |
| Team doesn't act on suggestions | Medium | Shelfware | Start with 1-2 highest-leverage suggestions per ad, not everything at once |

---

## Metrics of Success

### Phase 1 (Steps 0-2, ~7 weeks)
- 50-100 best-in-class ads curated + deconstructed
- 20-30 mediocre ads deconstructed for anti-patterns
- Creative taxonomy validated with team
- Pattern library v1: 10-15 patterns with evidence + confidence levels
- Anti-pattern list: 5-10 common pitfalls
- Scoring rubric ready for Phase 2

### Phase 2 (Step 3, ~3 weeks)
- Every current Wiom ad scored against the playbook
- Per-ad scorecards with specific gaps identified
- Per-ad improvement suggestions with reference ads
- Aggregate report: "Here are Wiom's systematic creative gaps"
- Top 3 highest-leverage improvements identified
- Creative team engagement: suggestions being discussed and adopted

### Phase 3 (Step 4, future)
- A/B validated: pattern-informed creatives outperform
  - Video completion: +15-25% vs baseline
  - CTR: +20-30% vs baseline
  - App downloads/bookings: +10-20% vs baseline
- Pattern library evolving from observation → validated for Wiom

---

## What This Is and Isn't

**IS:**
- A structured way to learn from the best and apply those learnings to our own ads
- A scorecard system that tells you exactly where each ad falls short and what to do about it
- Pattern-backed — every suggestion traces to "the best ads do X because Y"

**IS NOT:**
- An audit of historical performance (we don't need our own data to start)
- A template factory (patterns inform, they don't dictate)
- An auto-generator (output is intelligence, not finished ads)
- Optimizing for CAC (focus on completion, CTR, downloads, bookings first)
- A replacement for creative judgment (scorecards inform decisions, humans make them)
