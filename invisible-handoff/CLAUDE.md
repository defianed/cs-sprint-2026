# Invisible Handoff — Claude Setup Guide

**Your job here**: get the user running this workflow and understanding the problem it solves.

---

## What this workflow does

When a deal closes (Closed Won), the CSM shouldn't go into their first customer call blind. This workflow pulls sales context and produces a structured CSM handoff brief — so the customer never has to repeat goals, objections, or commitments they already discussed with sales.

The customer should never feel the gap between sales and CS. That's the invisible handoff.

**Input:** account name, deal value, transcript summary, sales rep notes (all in `sample_data/` by default).

**Output:**
- `account_overview` — one paragraph on who this customer is
- `customer_goals` — what the customer said they want to achieve
- `pain_points` — what was frustrating them before
- `commitments_made` — what Sales promised
- `objections_handled` — objections raised and how they were addressed
- `key_stakeholders` — who's who with roles
- `urgency_timeline` — hard deadlines and first-call timing
- `watchouts` — risks the CSM should be aware of
- `suggested_first_call_agenda` — step-by-step agenda

---

## Minimum required config

Ask the user for:
1. **Account name** → write to `config.yaml: account_name`
2. **LLM API key** (Anthropic or OpenAI) → write to `.env`

---

## `config.yaml` fields for this workflow

```yaml
account_name: "Acme Corp"          # Closed Won customer
csm_name: "Taylor Reyes"           # CSM receiving the handoff
llm_provider: manual               # manual | anthropic | openai
crm_provider: manual               # manual | salesforce | hubspot
transcript_provider: manual        # manual | gong | fireflies
slack_channel: "#cs-handoffs"      # Where to send the brief
```

---

## Sample output

See `examples/sample_output.md`.

The Slack message looks like:
```
🤝 New Handoff Brief: Acme Corp
CSM: Taylor Reyes | Deal: $48K ACV

Key watchouts:
⚠️ CTO is skeptical — he's been burned before. Don't overpromise.
⚠️ James in DevOps wasn't in the demo — get him in the kickoff.
⚠️ API GA date is tight. Confirm with product before first call.

📝 Full brief: [Notion link]
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
| Brief is too generic | Add more specific transcript detail to `sample_data/notes.json` |
| Notion link missing | `NOTION_API_KEY` and `NOTION_PARENT_PAGE_ID` not set in `.env` — brief outputs to Slack only |
| No CSM assigned | Set `csm_name` in `config.yaml` |

---

## What success looks like

`python3 local.py` outputs a structured JSON handoff brief and (if Slack token is set) sends a Slack DM to the CSM with the top 3 watchouts and a link to the full brief.
