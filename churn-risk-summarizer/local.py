#!/usr/bin/env python3
"""
Churn Risk Summarizer — local runner (no Modal required)
Run: python3 local.py

Modes:
  No API key  — loads sample_data/, prints mock output
  With API key — loads sample_data/, calls real LLM

Config: edit config.yaml (no secrets there)
Secrets: copy .env.example to .env and add your API key
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
    "summary": "Acme Corp is showing early-to-mid churn indicators: login drop, ghost users, a stalled support ticket, and two missed check-ins.",
    "risk_story": "Acme Corp started strong but has gone quiet. Two users — Tom and Alicia — haven't logged in since February. The Salesforce sync ticket has been open 14 days with no resolution date, and their COO scored renewal confidence at 6/10 in today's QBR. The open ticket is the most urgent issue: at this stage, an unresolved support problem becomes the reason they leave.",
    "primary_risks": [
        "14-day open Salesforce sync ticket — COO is tracking it personally",
        "Login frequency down 40% — 2 ghost users since February",
        "Missed last 2 monthly check-ins — two-month communication gap",
        "NPS dropped from 8 to 6 in latest survey"
    ],
    "stabilizers": [
        "Core workflow still in use by 61 of 100 seats",
        "Renewal is 189 days away — time to course-correct",
        "COO confirmed no competitor evaluation underway yet"
    ],
    "next_call_focus": [
        "Lead with the Salesforce ticket — give a written resolution date before end of day",
        "Schedule separate 30-min call with ghost users Tom and Alicia — listening only",
        "Propose fixed monthly check-in cadence starting April",
        "Ask directly what would move their renewal confidence from 6 to 8"
    ],
    "urgency": "high"
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


def build_risk_story(data: dict) -> dict:
    prompt = f"""Return JSON only.
Create a plain-language churn risk story from the account context below.
Do not output a numeric health score only — explain the situation as a narrative.

Context:
{json.dumps(data, indent=2)}

Return keys: summary, risk_story, primary_risks (list), stabilizers (list), next_call_focus (list), urgency."""
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
        return {"summary": raw[:300], "risk_story": raw[:300], "primary_risks": [], "stabilizers": [], "next_call_focus": [], "urgency": "unknown"}


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
    print("  Churn Risk Summarizer")
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
    # Override account name from config
    if "account" in data:
        data["account"]["name"] = account_name

    if has_api_key():
        print(f"\n[LIVE] Calling {get_provider()} with sample data...\n")
        result = build_risk_story(data)
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
