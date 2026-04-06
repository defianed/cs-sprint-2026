# Earned Ask — Claude Setup Guide

**Your job here**: get the user running this workflow and understanding when and why it matters.

---

## What this workflow does

Analyses recent customer context to decide if this is the right moment to ask for a review — and if yes, drafts the email the CSM should send. Not a template. An actual, situation-specific draft.

The core question it answers: **has this customer genuinely earned the ask?**

**Input:** account name, milestone achieved, interaction summary, sentiment summary (all in `sample_data/` by default).

**Output:**
- `should_ask` — true/false with reasoning
- `reason` — why now is (or isn't) the right moment
- `subject_line` — ready to use
- `email_body` — personalised draft for the CSM to review and send
- `csm_notes` — context for the CSM

---

## Minimum required config

Ask the user for:
1. **Account name** → write to `config.yaml: account_name`
2. **LLM API key** (Anthropic or OpenAI) → write to `.env`

Optional:
3. **Slack token** — to send the draft to Slack for CSM review

---

## `config.yaml` fields for this workflow

```yaml
account_name: "Acme Corp"          # Customer account
csm_name: "Maria Santos"           # CSM name for draft personalisation
llm_provider: manual               # manual | anthropic | openai
review_platform: G2                # G2 | Capterra | Trustpilot | AppSumo
slack_channel: "#cs-team"          # Where to send the draft for CSM review
```

---

## Sample output

See `examples/sample_output.md`.

When `should_ask: true`, the output includes a ready-to-send email draft:
```
Subject: Quick favour — would mean a lot

Hi [Champion Name],

Just wanted to say — watching your team hit go-live ahead of schedule was one of 
those moments that reminds me why I love this work.

If you've got 2 minutes, would you mind leaving us a review on G2?
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
| `should_ask: false` unexpectedly | Check `sample_data/notes.json` — the notes may not contain enough positive signals |
| Email draft is generic | Add more specific milestone detail to `sample_data/notes.json` |
| Slack not sending | Check `SLACK_BOT_TOKEN` in `.env` and `slack_channel` in `config.yaml` |

---

## What success looks like

`python3 local.py` outputs a JSON object with `should_ask`, `reason`, `subject_line`, `email_body`, and `csm_notes`. If `should_ask` is true, the email draft is ready for the CSM to personalise and send.
