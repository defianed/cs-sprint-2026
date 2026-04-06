# Webinar Demo Script

## Before the webinar
1. Run `setup.py` on your machine — have `.env` and Slack configured
2. Open terminal in the repo root
3. Have this file open in another window for reference

---

## Your demo commands (run these live)

### Demo 1 — Churn Risk (Meridian Software — the struggling account)
```bash
cd churn-risk-summarizer
DEMO_ACCOUNT=../demo/account.json DEMO_TICKETS=../demo/tickets.json python3 local.py
```
**What to say:** "Meridian Software — 42 health score, 11 of 25 seats active, renewal in 98 days, competitor mentioned twice. Let's see what the agent surfaces."

---

### Demo 2 — Expansion Signal (Brightline Health — the happy account)
```bash
cd expansion-signal-detector
DEMO_TRANSCRIPT=../demo/expansion_transcript.json python3 local.py
```
**What to say:** "Different account entirely. Strong health, team is growing, CSM just had a great call. Does the AI spot the expansion opportunity — and does it tell you how to ask?"

---

### Demo 3 — Earned Ask (after a milestone)
```bash
cd earned-ask
DEMO_ACCOUNT=../demo/account.json DEMO_TRANSCRIPT=../demo/expansion_transcript.json python3 local.py
```
**What to say:** "The hardest moment in CS — knowing when to ask for something. Referral, case study, expansion. The agent reads the relationship and tells you if the moment is right."

---

## Talk track

**Opening:**
"Every CSM on your team is making these decisions manually. Reading notes, scanning transcripts, gut-checking health scores. It works — until you have 15 accounts and a renewal due Friday. These workflows don't replace that judgment. They surface what your team would have missed."

**After Demo 1:**
"That Slack message just appeared in my #cs-alerts channel. My CSM didn't have to do anything. They just got told: Meridian is at risk, here's why, here's what to do. That's the whole point."

**After Demo 2:**
"Same tool, different account, completely different output. It's not a template — it read the call and made a judgment. Marcus Webb is ready to be asked. The workflow tells you that and gives you the language to do it."

**The close:**
"You leave today with all 5 of these. Clone the repo, run setup.py, you're running them on your own accounts in under 30 minutes. The one that saves you the most time — that's your starting point. The Program is where we go deeper."

---

## If something breaks live
- Kill it, laugh it off: "This is why we're all here — this is what it looks like to build with AI. Let me show you the output instead."
- Open `demo/sample_output.md` in the relevant workflow folder — it has a pre-written realistic output you can show
- Move to the next demo

---

## Audience command (what to tell them to run)
```bash
git clone https://github.com/defianed/cs-webinar.git
cd cs-webinar
pip install -r requirements.txt
python3 setup.py
```
After setup: `python3 churn-risk-summarizer/local.py`
