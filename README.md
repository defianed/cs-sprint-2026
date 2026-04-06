# CS Agentic Workflow Templates

5 agentic CS workflows you can clone, run today, and adapt to your stack.

Built for the [ExtensibleAgents](https://extensibleagents.com) webinar. No developer needed.

---

## ⚡ Quick Start — Sprint Participants (you have an API key)

```bash
git clone https://github.com/defianed/cs-sprint-2026
cd cs-sprint-2026
pip install -r requirements.txt
python3 setup.py
```

When setup asks *"Demo data or your own tools?"* — choose **Demo data** and paste your `sprint-XXXXXX-XXXXXX` key.

Done. All 5 workflows run immediately against 10 realistic dummy companies — CRM, calls, tickets, billing, usage. No Salesforce, Gong, or Zendesk needed.

**To switch which company you're analysing:** edit `account_name` in the workflow's `config.yaml`.

---

## ⚡ Quickest way to start (without a sprint key)

**Open this repo in [Claude Code](https://claude.ai/code) and say:**

> set me up

Claude will ask you which workflow to try, install dependencies, write your `.env` and `config.yaml`, and run the demo — all in one conversation.

---

## The 5 Workflows

| Workflow | What it does | Sample output |
|---|---|---|
| **Churn Risk Summarizer** | Turns recent account activity into a plain-language risk narrative | [→ example](churn-risk-summarizer/examples/sample_output.md) |
| **Earned Ask** | Decides when to ask for a G2 review, drafts the email | [→ example](earned-ask/examples/sample_output.md) |
| **Expansion Signal Detector** | Spots upsell signals in call notes and transcripts | [→ example](expansion-signal-detector/examples/sample_output.md) |
| **Invisible Handoff** | Turns a Closed Won deal into a CSM handoff brief | [→ example](invisible-handoff/examples/sample_output.md) |
| **Trust Radar** | Reads win-back calls: genuine loss of trust, or negotiating? | [→ example](trust-radar/examples/sample_output.md) |

---

## Three ways to run

| Mode | Command | Requires |
|---|---|---|
| **Demo** | `python3 test.py` | Nothing |
| **Local** | `python3 local.py` | API key in `.env` |
| **Cloud** | `modal deploy execution/main.py` | Modal account |

Start with `test.py`. Then move to `local.py`. Only use Modal when you're ready for cloud deployment.

---

## Manual path (if not using Claude Code)

```bash
# Step 1: Clone and install
git clone https://github.com/defianed/cs-webinar
cd cs-webinar
pip install -r requirements.txt

# Step 2: See the demo
cd trust-radar   # or any workflow
python3 test.py  # no setup required, shows sample output

# Step 3: See the example output before running anything
cat examples/sample_output.md

# Step 4: Set up your API key
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY (or OPENAI_API_KEY)

# Step 5: Edit config.yaml for your account
# Set account_name, csm_name, and provider preferences

# Step 6: Run with real AI
python3 local.py

# Step 7 (optional): Deploy to the cloud
pip install modal && modal setup
modal deploy execution/main.py
```

---

## What you need

- Python 3.9+
- An [Anthropic](https://claude.ai/settings) or [OpenAI](https://platform.openai.com) API key
- (Optional) Slack bot token for notifications
- (Optional) Modal account for cloud deployment

**Cost per run:** approximately $0.02–0.05 with Claude or GPT-4o.

---

## How it works

Each workflow has:
- `test.py` — always works, shows sample output with no setup
- `local.py` — full workflow logic locally, reads from `config.yaml`
- `config.yaml` — non-secret settings (account name, CSM, provider choices)
- `.env` — secrets only (API keys, Slack tokens)
- `sample_data/` — realistic fixtures for manual mode
- `examples/sample_output.md` — what the workflow produces
- `execution/main.py` — Modal deploy target for cloud use

Providers default to `manual` mode — no CRM, Gong, or Zendesk accounts required to get started.

---

Built with [Claude](https://anthropic.com) by [ExtensibleAgents](https://extensibleagents.com)
