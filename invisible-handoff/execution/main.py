"""Invisible Handoff — beginner-friendly CS handoff workflow.
Deploy with: modal deploy execution/main.py
"""

import json
import os
from datetime import datetime
from typing import Any

import modal

app = modal.App("invisible-handoff")
image = modal.Image.debian_slim().pip_install(
    "anthropic>=0.20.0",
    "openai>=1.0.0",
    "requests>=2.30.0",
    "slack-sdk>=3.20.0",
)


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def build_input_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a clean handoff context from provided payload fields.

    This workflow is intentionally beginner-friendly: it works from the text you
    provide (transcript snippets, sales notes, deal context) without requiring
    live CRM or call-transcript integrations.
    """
    return {
        "account_id": payload.get("account_id", ""),
        "opportunity_id": payload.get("opportunity_id", ""),
        "account_name": payload.get("account_name", ""),
        "customer_segment": payload.get("customer_segment", ""),
        "acv": payload.get("acv", ""),
        "close_notes": payload.get("close_notes", ""),
        "sales_summary": payload.get("sales_summary", ""),
        "implementation_context": payload.get("implementation_context", ""),
    }


def get_transcript_text(payload: dict[str, Any]) -> str:
    transcript_text = payload.get("transcript_text", "")
    if transcript_text:
        return transcript_text

    fallback_parts = [
        payload.get("sales_summary", ""),
        payload.get("close_notes", ""),
        payload.get("implementation_context", ""),
    ]
    combined = "\n\n".join(part.strip() for part in fallback_parts if part and part.strip())
    return combined


def call_llm(prompt: str) -> str:
    provider = _env("LLM_PROVIDER", "anthropic")
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=_env("OPENAI_API_KEY"))
        resp = client.responses.create(model=_env("OPENAI_MODEL", "gpt-4.1-mini"), input=prompt)
        return resp.output_text
    import anthropic
    client = anthropic.Anthropic(api_key=_env("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=_env("ANTHROPIC_MODEL", "claude-opus-4-6"),
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def build_brief(input_context: dict[str, Any], transcript: str, payload: dict[str, Any]) -> dict[str, Any]:
    prompt = f"""Create a JSON CSM handoff brief.

INPUT CONTEXT:
{json.dumps(input_context, indent=2)}

PAYLOAD CONTEXT:
{json.dumps(payload, indent=2)}

SALES TRANSCRIPT / NOTES:
{transcript[:9000]}

Return JSON with keys:
account_overview, customer_goals, pain_points, commitments_made, objections_handled,
stakeholder_map, communication_style, onboarding_risks, first_call_agenda, top_3_watchouts, brief_summary.
Return valid JSON only.
"""
    raw = call_llm(prompt)
    try:
        return json.loads(raw)
    except Exception:
        return {
            "account_overview": "",
            "customer_goals": [],
            "pain_points": [],
            "commitments_made": [],
            "objections_handled": [],
            "stakeholder_map": [],
            "communication_style": "",
            "onboarding_risks": [],
            "first_call_agenda": [],
            "top_3_watchouts": [],
            "brief_summary": raw,
        }


def post_to_notion(title: str, brief: dict[str, Any]) -> str:
    if not _env("NOTION_API_KEY") or not _env("NOTION_PARENT_PAGE_ID"):
        return ""
    import requests
    headers = {
        "Authorization": f"Bearer {_env('NOTION_API_KEY')}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    body = {
        "parent": {"page_id": _env("NOTION_PARENT_PAGE_ID")},
        "properties": {"title": {"title": [{"text": {"content": title[:200]}}]}},
        "children": [{
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": json.dumps(brief, indent=2)[:1900]}}]},
        }],
    }
    resp = requests.post("https://api.notion.com/v1/pages", headers=headers, json=body, timeout=30)
    data = resp.json()
    return data.get("url", "")


def slack_notify(csm_slack_user_id: str, account_name: str, brief: dict[str, Any], notion_url: str) -> None:
    token = _env("SLACK_BOT_TOKEN")
    if not token or not csm_slack_user_id:
        return
    from slack_sdk import WebClient
    client = WebClient(token=token)
    channel = client.conversations_open(users=[csm_slack_user_id])["channel"]["id"]
    watchouts = "\n".join(f"• {x}" for x in brief.get("top_3_watchouts", [])[:3]) or "• None captured"
    text = (
        f"*Invisible Handoff: {account_name}*\n\n"
        f"{brief.get('brief_summary', '')}\n\n"
        f"*Top watchouts*\n{watchouts}\n\n"
        f"{notion_url if notion_url else 'No Notion URL generated.'}"
    )
    client.chat_postMessage(channel=channel, text=text)


@app.function(image=image, secrets=[modal.Secret.from_name("invisible-handoff-secrets")])
@modal.fastapi_endpoint(method="POST")
def webhook(data: dict[str, Any]) -> dict[str, Any]:
    input_context = build_input_context(data)
    transcript = get_transcript_text(data)
    brief = build_brief(input_context, transcript, data)
    account_name = data.get("account_name") or data.get("account_id") or "Unknown Account"
    title = f"{account_name} — Invisible Handoff Brief — {datetime.utcnow().date().isoformat()}"
    notion_url = post_to_notion(title, brief)
    slack_notify(data.get("csm_slack_user_id", ""), account_name, brief, notion_url)
    result = {
        "status": "ok",
        "workflow": "invisible-handoff",
        "account_name": account_name,
        "notion_url": notion_url,
        "processed_at": datetime.utcnow().isoformat(),
        "brief": brief,
    }
    print(json.dumps(result))
    return result


@app.local_entrypoint()
def main():
    sample = webhook.local({
        "account_id": _env("ACCOUNT_ID"),
        "opportunity_id": _env("OPPORTUNITY_ID"),
        "account_name": _env("ACCOUNT_NAME"),
        "csm_slack_user_id": _env("CSM_SLACK_USER_ID"),
        "transcript_text": _env("TRANSCRIPT_TEXT"),
        "sales_summary": _env("SALES_SUMMARY"),
        "close_notes": _env("CLOSE_NOTES"),
        "implementation_context": _env("IMPLEMENTATION_CONTEXT"),
    })
    print(json.dumps(sample, indent=2))
