# Trust Radar — Claude Setup Guide

**Your job here**: get the user running this workflow and understanding why the classification matters.

---

## What this workflow does

Reads a win-back or escalation call transcript and classifies the situation: is the customer showing genuine loss of trust, or are they applying commercial negotiation pressure? These require completely different CSM responses.

Getting this wrong is expensive. Treating a negotiating customer like a burned one gives away unnecessary concessions. Treating a genuinely burned customer commercially ends the relationship.

**Input:** customer name, call transcript (all in `sample_data/` by default).

**Output:**
- `classification` — one of: `GENUINE_LOSS_OF_TRUST` | `NEGOTIATING` | `MIXED` | `UNCLEAR`
- `confidence` — 0.0–1.0 score
- `reasoning` — why the model classified it this way
- `evidence_snippets` — exact quotes from the transcript with signal type
- `response_strategy` — specific, actionable advice for the CSM
- `urgency_score` — 1–10
- `recommended_actions` — concrete next steps

---

## Minimum required config

Ask the user for:
1. **Account/customer name** → write to `config.yaml: account_name`
2. **LLM API key** (Anthropic or OpenAI) → write to `.env`

---

## `config.yaml` fields for this workflow

```yaml
account_name: "Acme Corp"          # Customer in the call
csm_name: "Chris Park"             # CSM on the call
llm_provider: manual               # manual | anthropic | openai
transcript_provider: manual        # manual | gong | fireflies | zoom
slack_channel: "#cs-escalations"   # Where to send the alert
min_confidence: 0.6                # Only alert if confidence >= this value
```

---

## Understanding the verdicts

| Verdict | What it means | CSM response |
|---|---|---|
| `GENUINE_LOSS_OF_TRUST` | Real relationship damage | Lead with empathy, don't go commercial |
| `NEGOTIATING` | Using frustration as leverage | Hold the line or make a targeted concession |
| `MIXED` | Both signals present | Nuanced approach — acknowledge and explore |
| `UNCLEAR` | Not enough signal | Listen more before acting |

---

## Sample output

See `examples/sample_output.md`.

```
Classification: NEGOTIATING (confidence: 0.79)

Reasoning: The frustration is real, but the language pattern is classic negotiation.
The conditional offer at 11:04 is the tell...

Evidence:
[10:02] "We're actively evaluating Salesforce and HubSpot right now." [leverage]
[11:04] "If you can get the API live this week, I'll hold off the evaluation." [conditional opening]

Response Strategy: Don't get defensive. Go away from this call and confirm the API date
with engineering today. Come back within 24 hours with: (1) confirmed GA date in writing...
```

---

## Running the workflow

```bash
python3 test.py    # Always works, sample data
python3 local.py   # Real AI run with your transcript
```

---

## Common issues and fixes

| Problem | Fix |
|---|---|
| Classification is `UNCLEAR` | The transcript needs more explicit signal phrases |
| `HUBSPOT_API_KEY` error | Update your `.env` to use `HUBSPOT_PRIVATE_APP_TOKEN` instead |
| `ZOOM_JWT_TOKEN` error | Update your `.env` to use `ZOOM_OAUTH_TOKEN` instead |
| Confidence is low | Provide a longer or more complete transcript in `sample_data/notes.json` |
| Slack not alerting | Check `min_confidence` in `config.yaml` — it may be set higher than the score |

---

## What success looks like

`python3 local.py` outputs a classification with confidence score, evidence snippets from the transcript, and a specific response strategy. If Slack is configured, an alert is sent with the verdict and top recommended actions.
