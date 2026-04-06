# Churn Risk Summarizer — Claude Setup Guide

**Your job here**: get the user running this workflow and understanding what it produces.

---

## What this workflow does

Analyses recent account activity, support friction, and engagement changes to produce a plain-language churn risk narrative. Not a health score — an actual story the CSM can use in their next call.

**Input:** account name, recent activity summary, support summary, engagement summary (all in `sample_data/` by default).

**Output:**
- `risk_story` — 2-3 sentence narrative explaining what's happening
- `primary_risks` — bulleted list of specific risk signals
- `stabilizers` — what's working in the account's favour
- `next_call_focus` — 3 specific things for the CSM to address

---

## Minimum required config

Ask the user for:
1. **Account name** (default: "TechFlow Inc") → write to `config.yaml: account_name`
2. **LLM API key** (Anthropic or OpenAI) → write to `.env: ANTHROPIC_API_KEY` or `OPENAI_API_KEY`

That's it for a working run. Everything else is optional.

---

## `config.yaml` fields for this workflow

```yaml
account_name: "TechFlow Inc"       # Edit to match the real customer
csm_name: "Alex Chen"              # CSM's name for output context
llm_provider: manual               # manual | anthropic | openai
crm_provider: manual               # manual | salesforce | hubspot
support_provider: manual           # manual | zendesk | intercom
urgency_threshold: high            # high | medium | low — minimum urgency for Slack alert
slack_channel: "#cs-alerts"        # Slack channel for notifications
```

---

## Sample output

See `examples/sample_output.md` for a full example Slack message and JSON output.

Quick preview — the workflow produces output like:
```
Risk Story: TechFlow started strong but has gone quiet over the past 30 days.
Two users who were previously active have stopped logging in entirely...

Primary Risks:
- 40% login drop over 30 days
- Integration ticket open 12 days
- Skipped 2 monthly check-ins

Next Call Focus:
- Lead with the support ticket — give a specific timeline
- Ask about the 2 inactive users
```

---

## Running the workflow

```bash
# Step 1: Demo with sample data (always works)
python3 test.py

# Step 2: Real run with your own data
python3 local.py
```

---

## Common issues and fixes

| Problem | Fix |
|---|---|
| `OPENAI_API_KEY` present but revoked | Set `llm_provider: manual` in `config.yaml` or provide a valid Anthropic key |
| Output is empty | Check `sample_data/account.json` and `sample_data/notes.json` exist |
| Slack message not sending | Check `SLACK_BOT_TOKEN` in `.env` and `slack_channel` in `config.yaml` |
| Parse error in output | The LLM returned malformed JSON — retry or check the model setting in `.env` |

---

## What success looks like

`python3 local.py` runs without errors and prints a JSON object with `risk_story`, `primary_risks`, `stabilizers`, `next_call_focus`, and `urgency`. If Slack token is set, a notification is sent to the configured channel.
