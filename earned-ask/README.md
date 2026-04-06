# Earned Ask

Detects whether a customer has genuinely earned a review request, then drafts the email for your CSM to send.

Never ask for a review at the wrong moment again.

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

Analyses interaction context, milestone evidence, and sentiment signals to decide whether this is the right moment to ask for a review. If yes, drafts the email for the CSM to approve and send.

## What you get

```json
{
  "should_ask": true,
  "reason": "Why now is the right moment",
  "subject_line": "Quick favour — would mean a lot",
  "email_body": "Ready-to-send draft...",
  "csm_notes": "Context for the CSM"
}
```

## Customising the input

Edit `.env` or set environment variables:
```
ACCOUNT_NAME=Acme Corp
MILESTONE_ACHIEVED=Went live ahead of schedule
INTERACTION_SUMMARY=Champion offered to recommend us to peers
SENTIMENT_SUMMARY=NPS 9, tickets resolved same-day
```

## Note

The CSM always reviews and approves before sending. This workflow drafts the email — it does not send it.

## Environment variables

See `.env.example`. Only `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`) is required.
