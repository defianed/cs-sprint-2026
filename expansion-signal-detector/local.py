#!/usr/bin/env python3
"""
Expansion Signal Detector — local runner (no Modal required)
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
    "expansion_ready": True,
    "confidence": 0.83,
    "buying_signals": [
        "Ben mentioned rolling platform out to sales team in Q3 (unprompted)",
        "At 95/100 seat capacity — organically approaching plan limits",
        "Champion said 'this has transformed how our RevOps team works'",
        "Proactively asked about pricing for adding seats",
        "API calls up 40% MoM — deep product integration signals stickiness"
    ],
    "blockers": [
        "Budget cycle resets Q3 — CFO Chloe Park is the approver",
        "CFO is ROI-focused — needs data before sign-off",
        "Open CRM integration ticket should be resolved first"
    ],
    "recommended_timing": "Prepare ROI one-pager in 2 weeks, schedule expansion call for late April once Q3 budget opens",
    "next_steps": [
        "Escalate open CRM integration ticket — resolve before expansion conversation",
        "Build ROI one-pager with Hana's time-savings data for CFO audience",
        "Prepare custom Business 150 quote with per-seat comparison",
        "Schedule dedicated expansion call — do not attach to regular check-in",
        "Ask Ben to pre-sell internally to Chloe before formal call"
    ],
    "rationale": "Acme Corp is organically growing into expansion: near plan limits, API usage accelerating, VP Sales proactively raised expansion pricing. Friction is budget timing and CFO ROI story — both solvable in 3-4 weeks."
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


def detect_expansion_signals(data: dict) -> dict:
    prompt = f"""Return JSON only.
Analyse this account context for expansion readiness signals.

Context:
{json.dumps(data, indent=2)}

Return keys: expansion_ready (bool), confidence (0.0-1.0), buying_signals (list), blockers (list), recommended_timing, next_steps (list), rationale."""
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
        return {"expansion_ready": False, "confidence": 0.0, "rationale": "Parse error.", "buying_signals": [], "blockers": [], "recommended_timing": "unknown", "next_steps": []}


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
    for filename in ["account.json", "transcript.json", "notes.json"]:
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
    print("  Expansion Signal Detector")
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
        result = detect_expansion_signals(data)
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
