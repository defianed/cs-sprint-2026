# test.py — zero setup required. If API key found, calls real LLM with sample_data/.
# Otherwise prints labelled mock output and exits 0.
# Run: python3 test.py
import os, json, sys
LIVE_MODE = "--live" in sys.argv
from pathlib import Path

try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Load .env from repo root (one level up from workflow dir)
    _root = Path(__file__).parent.parent
    load_dotenv(_root / ".env")
    load_dotenv()  # fallback: local .env
except ImportError:
    pass

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
    "rationale": "Acme Corp is organically growing into expansion: they're near plan limits, API usage is accelerating, and their VP Sales proactively raised expansion pricing. The only friction is budget timing and getting the CFO the ROI story she needs — both are solvable in 3-4 weeks."
}


def load_sample_data() -> dict:
    data = {}
    for filename in ["account.json", "transcript.json"]:
        path = WORKFLOW_DIR / "sample_data" / filename
        if path.exists():
            key = filename.replace(".json", "")
            data[key] = json.loads(path.read_text())
    return data


def has_api_key() -> bool:
    ak = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    ok = (os.getenv("OPENAI_API_KEY") or "").strip()
    # Validate OpenAI key format — skip revoked/invalid keys
    return bool(ak) or (bool(ok) and ok.startswith("sk-"))


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
    raw = call_llm(prompt)
    for marker in ["```json", "```"]:
        if marker in raw:
            raw = raw.split(marker)[1].split("```")[0]
            break
    try:
        return json.loads(raw.strip())
    except Exception:
        return {"expansion_ready": False, "confidence": 0.0, "rationale": "Parse error.", "buying_signals": [], "blockers": [], "recommended_timing": "unknown", "next_steps": []}


def main():
    data = load_sample_data()
    account_name = data.get("account", {}).get("name", "Acme Corp")
    print(f"Expansion Signal Detector — {account_name}\n")

    if LIVE_MODE and has_api_key():
        print(f"[LIVE] API key found — calling {get_provider()} with sample data...\n")
        result = detect_expansion_signals(data)
    else:
        print("[MOCK] No API key — showing sample output.")
        print("       Set ANTHROPIC_API_KEY or OPENAI_API_KEY to call live LLM.\n")
        result = MOCK_OUTPUT

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
