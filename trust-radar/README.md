# Trust Radar

Analyses win-back and escalation call transcripts to determine: genuine loss of trust, or commercial negotiation pressure?

Gives the CSM a defensible read before they respond.

## Three ways to run

| Mode | Command | Requires |
|---|---|---|
| Instant demo | `python3 test.py` | Nothing |
| Local real run | `python3 local.py` | API key in `.env` |
| Cloud deploy | `modal deploy execution/main.py` | Modal account |

## Quickstart

```bash
# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: See it work immediately (sample data, no API key needed)
python3 test.py

# Step 3: Set up your API key
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY (or OPENAI_API_KEY)

# Step 4: Run with real AI locally
python3 local.py
```

## What it does

Classifies calls into one of four verdicts:
- `GENUINE_LOSS_OF_TRUST` — repair trust before anything commercial
- `NEGOTIATING` — using frustration as leverage; hold the line or make a targeted concession
- `MIXED` — both signals present; nuanced response needed
- `UNCLEAR` — insufficient signal; listen more before acting

## What you get

```json
{
  "classification": "NEGOTIATING",
  "confidence": 0.79,
  "reasoning": "...",
  "evidence_snippets": [{"timestamp": "...", "text": "...", "signal_type": "..."}],
  "response_strategy": "Specific and actionable",
  "urgency_score": 8,
  "recommended_actions": ["..."]
}
```

## Customising the input

Edit `.env` or set environment variables:
```
ACCOUNT_NAME=Acme Corp
TRANSCRIPT_TEXT=[08:45] Sarah: You've missed three commitments...
```

## Environment variables

See `.env.example`. Only `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) and `SLACK_BOT_TOKEN` are required.

Live CRM (Salesforce, HubSpot), transcript (Gong, Fireflies, Zoom), and support integrations (Zendesk, Intercom) are optional.

**Note on Salesforce:** Live Salesforce integration may require custom field mapping for your org schema.

**Updated env var names:**
- `HUBSPOT_PRIVATE_APP_TOKEN` (not `HUBSPOT_API_KEY`)
- `ZOOM_OAUTH_TOKEN` (not `ZOOM_JWT_TOKEN`)
