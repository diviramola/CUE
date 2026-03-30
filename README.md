# CUE — Creative Understanding & Execution

A web tool for scoring ad creatives against industry best practices and optimizing live campaigns.

Built for the Wiom marketing team.

---

## What it does

- **Upload** a video ad → auto-extracts frames
- **Review** → scores the ad across 5 dimensions (Hook, Retention, CTR Drivers, CTA, Brand) against a playbook of best-in-class Indian ISP/telecom ads
- **Suggest** → generates specific, actionable improvements
- **Optimize** → pulls live Meta performance data and recommends targeting/creative changes
- **Compare** → side-by-side scorecard versions to track improvement over iterations

---

## Setup (5 min)

### Requirements
- Python 3.11+
- ffmpeg ([Windows](https://ffmpeg.org/download.html) · Mac: `brew install ffmpeg`)

### Install

```bash
git clone https://github.com/diviramola/CUE.git
cd CUE
pip install -r requirements.txt
```

### Add your API key

Create a file called `.env` in the CUE folder:

```
GROQ_API_KEY=your_key_here
```

Get a free key at **[console.groq.com](https://console.groq.com)** — takes 1 minute, no credit card needed.

### Run

```bash
python src/webapp.py
```

Opens at **http://localhost:5100**

---

## How to use it

1. **Upload an ad** → Ads & Scorecards → Upload Ad (or use an existing Wiom ad)
2. **Set context** (optional but recommended) → New Context → pick objective, fill in brief
3. **Click Review** on any ad → runs full pipeline automatically (deconstruct → score → suggest)
4. **Add performance data** → Performance → enter metrics or pull from Meta API
5. **Click Optimize** → compares scorecard predictions to real data, recommends actions

---

## Meta API (optional)

To pull performance data automatically from Meta Ads Manager, add to your `.env`:

```
META_ACCESS_TOKEN=your_token
META_AD_ACCOUNT_ID=act_XXXXXXXX
```

Then use **Campaign Mapping** to link your CUE ads to Meta ad IDs.

---

## Questions

Contact Divi (divi.ramola@wiom.in)
