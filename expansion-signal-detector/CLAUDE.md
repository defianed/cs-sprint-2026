# Expansion Signal Detector — Claude Setup Guide

**Your job here**: get the user running this workflow and understanding how it surfaces upsell opportunities.

---

## What this workflow does

Analyses call transcripts and post-call notes for signals that a customer is ready to expand — either adding seats, expanding to new teams, or moving to a higher plan. Tells the CSM whether to start the expansion conversation and when.

**Input:** account name, transcript snippets, post-call notes, usage summary (all in `sample_data/` by default).

**Output:**
- `expansion_ready` — true/false
- `confidence` — 0.0–1.0 score
- `buying_signals` — specific quotes and signals from the transcript
- `blockers` — what might delay or prevent expansion
- `recommended_timing` — when to have the conversation
- `next_steps` — concrete actions for the CSM

---

## Minimum required config

Ask the user for:
1. **Account name** → write to `config.yaml: account_name`
2. **LLM API key** (Anthropic or OpenAI) → write to `.env`

---

## `config.yaml` fields for this workflow

```yaml
account_name: "ScaleUp Ltd"        # Customer account
csm_name: "Jordan Lee"             # CSM name
llm_provider: manual               # manual | anthropic | openai
transcript_provider: manual        # manual | gong | fireflies | zoom
slack_channel: "#expansion-alerts" # Where to send expansion signals
confidence_threshold: 0.7          # Only alert if confidence >= this value
```

---

## Sample output

See `examples/sample_output.md`.

When `expansion_ready: true`:
```
Expansion Ready: YES (confidence: 0.82)

Buying signals:
- "We're rolling this out to the sales team next quarter"
- At 95 of 100 seat capacity — approaching plan limits
- Champion asked about pricing for 20 more seats

Recommended timing: Approach in 3-4 weeks after integration fix
```

---

## Running the workflow

```bash
python3 test.py    # Always works, sample data
python3 local.py   # Real AI run with your context
```

---

## Common issues and fixes

| Problem | Fix |
|---|---|
| `expansion_ready: false` but user thinks it should be true | Add more specific expansion signal phrases to `sample_data/notes.json` |
| Confidence is low | The transcript needs more explicit signals — add specific quotes |
| Alert not sent | Check `confidence_threshold` in `config.yaml` — may be set too high |

---

## What success looks like

`python3 local.py` outputs a JSON object with `expansion_ready`, `confidence`, `buying_signals`, `blockers`, `recommended_timing`, and `next_steps`. If `expansion_ready` is true and confidence meets threshold, a Slack alert is sent.
