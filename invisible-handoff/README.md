# Invisible Handoff

Turns a Closed Won deal into a structured CSM handoff brief — so the customer never has to repeat themselves.

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

Takes sales call notes and context, then generates a structured handoff brief covering: what the customer cares about, what was promised, key stakeholders, watchouts, and a suggested first-call agenda.

## What you get

```json
{
  "account_overview": "...",
  "customer_goals": ["..."],
  "pain_points": ["..."],
  "commitments_made": ["..."],
  "objections_handled": ["..."],
  "key_stakeholders": [{"name": "...", "title": "...", "role": "..."}],
  "urgency_timeline": "...",
  "watchouts": ["..."],
  "suggested_first_call_agenda": ["..."]
}
```

## Customising the input

Edit `.env` or set environment variables:
```
ACCOUNT_NAME=Acme Corp
DEAL_VALUE=$48,000 ACV
TRANSCRIPT_SUMMARY=Closed Won. Final call confirmed API GA...
SALES_REP_NOTES=Champion is Sarah VP Eng. Q3 launch is hard deadline...
```

## Note on live integrations

CRM and transcript integrations (Salesforce, HubSpot, Gong, Fireflies) are available as configurable adapters in `execution/main.py`. The local path (`local.py`) works without them.

## Environment variables

See `.env.example`. Only `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) is required for the local path.
