#!/usr/bin/env python3
"""
Invisible Handoff — local runner (no Modal required)
Run: python3 local.py

Modes:
  No API key  — loads sample_data/, prints mock output
  With API key — loads sample_data/, calls real LLM

Config: edit config.yaml (no secrets there)
Secrets: copy .env.example to .env and add your API key
         Add NOTION_API_KEY and NOTION_PARENT_PAGE_ID to .env to auto-create Notion pages
"""
import os, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Load .env from repo root (one level up from workflow dir)
    _root = Path(__file__).parent.parent
    load_dotenv(_root / ".env")
    load_dotenv()  # fallback: local .env
except ImportError:
    pass

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

WORKFLOW_DIR = Path(__file__).parent

MOCK_OUTPUT = {
    "account_overview": "Acme Corp is a 200-person fintech that closed a $48K ACV deal on 2026-03-20. Sarah Okonkwo (VP Engineering) is the champion. Mike Chen (CTO) is the economic buyer and skeptical — been burned before. James Liu (Senior DevOps) will own the integration but was not in any demos.",
    "customer_goals": [
        "Replace fragmented 3-tool toolchain with single platform by Q3",
        "Reduce time-to-integrate from 3 weeks to under 5 days",
        "Hit Q3 product launch deadline (August 1) with API layer in place"
    ],
    "pain_points": [
        "Previous vendors had good uptime but terrible support SLAs",
        "Engineering team is stretched — migration overhead is costly",
        "CTO skeptical of vendor commitments after being burned before"
    ],
    "commitments_made": [
        "API GA by May 15 — confirmed with product team",
        "Marcus (senior onboarding engineer, ex-Stripe) assigned for 30 days",
        "Custom migration guide for Node.js + Postgres stack",
        "SOC 2 Type II report and pen test results sent with contract",
        "Milestone payments: 50% kickoff, 50% at API GA",
        "30-day contract extension if API slips past May 15"
    ],
    "objections_handled": [
        "Security: SOC 2 Type II certified + pen test provided",
        "Migration risk: Marcus has Node.js migration experience at Stripe",
        "Reliability: milestone payments tied to delivery not time",
        "Competitors: differentiated vs DataBridge and NovaSuite"
    ],
    "key_stakeholders": [
        {"name": "Sarah Okonkwo", "title": "VP Engineering", "role": "Champion — drove evaluation, day-to-day contact, highly bought-in"},
        {"name": "Mike Chen", "title": "CTO", "role": "Economic buyer — skeptical, wants written record of all commitments"},
        {"name": "James Liu", "title": "Senior DevOps", "role": "Will own integration — NOT in demos, get him into kickoff ASAP"}
    ],
    "urgency_timeline": "Q3 launch is August 1 (hard). API GA is May 15. First CSM call within 24 hours of deal close (March 20). Kickoff with James before April.",
    "watchouts": [
        "Mike's skepticism is real — do not hedge or over-promise",
        "API GA (May 15) is tight — reconfirm with product before first call",
        "James was not in demos — he will have concerns, get him on kickoff ASAP",
        "Mike asked for written record of all commitments — send deal summary today"
    ],
    "suggested_first_call_agenda": [
        "Introduce yourself, confirm you've read Jake's deal summary",
        "Introduce Marcus — confirm his 30-day exclusive availability",
        "Confirm API GA date (May 15) on the call, ask Mike to confirm he has it in writing",
        "Get James added to kickoff — ask Sarah to facilitate",
        "Walk through migration guide outline with James",
        "Set weekly sync cadence through Q3 launch"
    ]
}


def load_config() -> dict:
    config_path = WORKFLOW_DIR / "config.yaml"
    if _YAML_AVAILABLE and config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def has_api_key() -> bool:
    return bool((os.getenv("ANTHROPIC_API_KEY") or "").strip()) or bool((os.getenv("OPENAI_API_KEY") or "").strip())


def get_provider() -> str:
    if (os.getenv("ANTHROPIC_API_KEY") or "").strip():
        return "anthropic"
    if (os.getenv("OPENAI_API_KEY") or "").strip():
        return "openai"
    return "anthropic"


def call_llm(prompt: str) -> str:
    provider = get_provider()
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        return resp.choices[0].message.content
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6"),
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def build_brief(data: dict) -> dict:
    prompt = f"""Return JSON only.
Create a CSM handoff brief from the sales context below.

Context:
{json.dumps(data, indent=2)}

Return keys: account_overview, customer_goals (list), pain_points (list), commitments_made (list), objections_handled (list), key_stakeholders (list of objects with name/title/role), urgency_timeline, watchouts (list), suggested_first_call_agenda (list)."""
    try:
        raw = call_llm(prompt)
    except Exception as e:
        print(f"Warning: LLM call failed: {e}")
        return None
    for marker in ["```json", "```"]:
        if marker in raw:
            raw = raw.split(marker)[1].split("```")[0]
            break
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"account_overview": "Parse error", "raw": raw[:500]}


def load_demo_stack_data(account_name: str = "Acme Corp") -> dict:
    api_key = os.getenv("DEMO_STACK_API_KEY", "").strip()
    if not api_key:
        raise ValueError("DEMO_STACK_API_KEY not set in .env")
    from demo_stack.client import DemoStackClient
    client = DemoStackClient(api_key)
    companies = client.list_companies()
    company = next(
        (c for c in companies if c.get("name", "").lower() == account_name.lower()),
        companies[0] if companies else {"id": "00000001-0000-0000-0000-000000000000"}
    )
    return client.get_account_context(company["id"])


def load_sample_data() -> dict:
    data = {}
    for filename in ["account.json", "transcript.json", "tickets.json", "notes.json"]:
        path = WORKFLOW_DIR / "sample_data" / filename
        if path.exists():
            key = filename.replace(".json", "")
            try:
                data[key] = json.loads(path.read_text())
            except Exception:
                pass
    return data


def main():
    config = load_config()
    account_name = config.get("account_name", "Acme Corp")
    csm_name = config.get("csm_name", "Sarah Johnson")

    print("=" * 60)
    print("  Invisible Handoff")
    print("=" * 60)
    print(f"  Account : {account_name}")
    print(f"  CSM     : {csm_name}")

    data_source = config.get("data_source", "sample")
    if data_source == "demo_stack":
        print(f"\n[DEMO STACK] Loading live data for {account_name}...")
        try:
            data = load_demo_stack_data(account_name)
            print(f"[DEMO STACK] Loaded: {data.get('account', {}).get('name', account_name)}\n")
        except Exception as e:
            print(f"[DEMO STACK] Failed: {e}")
            print("[DEMO STACK] Falling back to sample data.\n")
            data = load_sample_data()
    else:
        data = load_sample_data()
    if "account" in data:
        data["account"]["name"] = account_name

    if has_api_key():
        print(f"\n[LIVE] Calling {get_provider()} with sample data...\n")
        result = build_brief(data)
        if result is None:
            print("LLM call failed — falling back to mock output.\n")
            result = MOCK_OUTPUT
    else:
        print("\n[MOCK] No API key found — showing sample output.")
        print("       Add ANTHROPIC_API_KEY or OPENAI_API_KEY to .env to use live LLM.\n")
        result = MOCK_OUTPUT

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
