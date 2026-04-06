"""
DemoStackClient — wraps the cs-demo-stack lab API at https://lab.extensibleagents.com

Auth: X-API-Key header. Key from env var DEMO_STACK_API_KEY.

MCP endpoints use JSON-RPC 2.0 over HTTP POST (streamable HTTP transport).
REST endpoints for billing use standard GET requests.
"""

import os
import json
from datetime import date, datetime
from typing import Optional
import requests

BASE_URL = "https://lab.extensibleagents.com"

# Fixed company UUIDs
COMPANY_IDS = {
    "acme corp":    "00000001-0000-0000-0000-000000000000",
    "bluewave":     "00000002-0000-0000-0000-000000000000",
    "corelogic":    "00000003-0000-0000-0000-000000000000",
    "driftnet":     "00000004-0000-0000-0000-000000000000",
    "elevatehr":    "00000005-0000-0000-0000-000000000000",
    "forgepath":    "00000006-0000-0000-0000-000000000000",
    "grayfield":    "00000007-0000-0000-0000-000000000000",
    "horizonai":    "00000008-0000-0000-0000-000000000000",
    "ironclad":     "00000009-0000-0000-0000-000000000000",
    "juniper co":   "0000000a-0000-0000-0000-000000000000",
}


def company_id_for(name: str) -> Optional[str]:
    """Resolve a company name to its fixed UUID, case-insensitive."""
    return COMPANY_IDS.get(name.lower().strip())


class DemoStackClient:
    """
    Client for the cs-demo-stack lab API.

    Usage:
        client = DemoStackClient(api_key="sk-...")
        # or rely on DEMO_STACK_API_KEY env var:
        client = DemoStackClient()
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("DEMO_STACK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "api_key is required. Pass it directly or set DEMO_STACK_API_KEY."
            )
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        self._mcp_id = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _next_id(self) -> int:
        self._mcp_id += 1
        return self._mcp_id

    def _mcp_call(self, endpoint: str, tool: str, arguments: dict) -> dict:
        """
        Send a JSON-RPC 2.0 tools/call request to an MCP endpoint and return
        the parsed result. Raises on HTTP errors or JSON-RPC error responses.
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
            "id": self._next_id(),
        }
        resp = self.session.post(f"{BASE_URL}{endpoint}", json=payload)
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            raise RuntimeError(
                f"MCP error from {endpoint}/{tool}: {body['error']}"
            )
        # MCP result may be wrapped: {"result": {"content": [{"type":"text","text":"..."}]}}
        result = body.get("result", {})
        # Unwrap text content if present
        content = result.get("content")
        if content and isinstance(content, list):
            text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
            if text_parts:
                raw = "".join(text_parts)
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"text": raw}
        return result

    def _get(self, path: str) -> dict | list:
        """Simple authenticated GET for REST endpoints."""
        resp = self.session.get(f"{BASE_URL}{path}")
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Health (no auth)
    # ------------------------------------------------------------------

    def health(self) -> dict:
        resp = requests.get(f"{BASE_URL}/health")
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # CRM  (/crm/mcp)
    # ------------------------------------------------------------------

    def get_company(self, company_id: str) -> dict:
        return self._mcp_call("/crm/mcp", "get_company", {"company_id": company_id})

    def list_companies(self) -> list:
        result = self._mcp_call("/crm/mcp", "list_companies", {})
        return result if isinstance(result, list) else result.get("companies", [])

    def get_contacts(self, company_id: str) -> list:
        result = self._mcp_call("/crm/mcp", "get_contacts", {"company_id": company_id})
        return result if isinstance(result, list) else result.get("contacts", [])

    def get_deals(self, company_id: str) -> list:
        result = self._mcp_call("/crm/mcp", "get_deals", {"company_id": company_id})
        return result if isinstance(result, list) else result.get("deals", [])

    def get_activities(self, company_id: str, limit: int = 10) -> list:
        result = self._mcp_call(
            "/crm/mcp", "get_activities",
            {"company_id": company_id, "limit": limit}
        )
        return result if isinstance(result, list) else result.get("activities", [])

    # ------------------------------------------------------------------
    # Calls  (/calls/mcp)
    # ------------------------------------------------------------------

    def list_recordings(self, company_id: str) -> list:
        result = self._mcp_call(
            "/calls/mcp", "list_recordings", {"company_id": company_id}
        )
        return result if isinstance(result, list) else result.get("recordings", [])

    def get_transcript(self, recording_id: str) -> str:
        result = self._mcp_call(
            "/calls/mcp", "get_transcript", {"recording_id": recording_id}
        )
        if isinstance(result, str):
            return result
        return result.get("transcript", result.get("text", ""))

    # ------------------------------------------------------------------
    # Helpdesk  (/helpdesk/mcp)
    # ------------------------------------------------------------------

    def list_tickets(self, company_id: str, status: str = None) -> list:
        args = {"company_id": company_id}
        if status:
            args["status"] = status
        result = self._mcp_call("/helpdesk/mcp", "list_tickets", args)
        return result if isinstance(result, list) else result.get("tickets", [])

    def get_ticket(self, ticket_id: str) -> dict:
        return self._mcp_call("/helpdesk/mcp", "get_ticket", {"ticket_id": ticket_id})

    # ------------------------------------------------------------------
    # CS Platform  (/cs/mcp)
    # ------------------------------------------------------------------

    def get_health_score(self, company_id: str) -> dict:
        return self._mcp_call("/cs/mcp", "get_health_score", {"company_id": company_id})

    def get_nps_history(self, company_id: str) -> list:
        result = self._mcp_call(
            "/cs/mcp", "get_nps_history", {"company_id": company_id}
        )
        return result if isinstance(result, list) else result.get("nps_history", [])

    # ------------------------------------------------------------------
    # Billing  (REST)
    # ------------------------------------------------------------------

    def get_subscription(self, company_id: str) -> dict:
        return self._get(f"/billing/subscriptions/{company_id}")

    def get_invoices(self, company_id: str) -> list:
        result = self._get(f"/billing/invoices/{company_id}")
        return result if isinstance(result, list) else result.get("invoices", [])

    # ------------------------------------------------------------------
    # Usage  (/usage/mcp)
    # ------------------------------------------------------------------

    def get_usage_history(self, company_id: str, months: int = 6) -> list:
        result = self._mcp_call(
            "/usage/mcp", "get_usage_history",
            {"company_id": company_id, "months": months}
        )
        return result if isinstance(result, list) else result.get("usage_history", [])

    def get_seat_utilization(self, company_id: str) -> dict:
        return self._mcp_call(
            "/usage/mcp", "get_seat_utilization", {"company_id": company_id}
        )

    def get_feature_adoption(self, company_id: str) -> dict:
        return self._mcp_call(
            "/usage/mcp", "get_feature_adoption", {"company_id": company_id}
        )

    # ------------------------------------------------------------------
    # Composite  — drop-in replacement for load_sample_data()
    # ------------------------------------------------------------------

    def get_account_context(self, company_id: str) -> dict:
        """
        Assemble the same dict shape that load_sample_data() returns in each
        workflow's local.py, so workflow logic can treat live data identically
        to sample data.

        Returns:
        {
            "account":    dict,   # company metadata + health + billing + usage
            "transcript": dict,   # latest call (call_date, call_type, participants,
                                  #              duration_minutes, transcript)
            "tickets":    list,   # support tickets
            "notes":      dict,   # activity / engagement summary
        }
        """
        # Fetch all sources in parallel-ish order (sequential for simplicity;
        # callers can parallelise externally if latency matters)
        company    = self._safe(self.get_company, company_id) or {}
        health     = self._safe(self.get_health_score, company_id) or {}
        sub        = self._safe(self.get_subscription, company_id) or {}
        seats      = self._safe(self.get_seat_utilization, company_id) or {}
        nps_hist   = self._safe(self.get_nps_history, company_id) or []
        activities = self._safe(self.get_activities, company_id, limit=20) or []
        tickets    = self._safe(self.list_tickets, company_id) or []
        recordings = self._safe(self.list_recordings, company_id) or []

        # --- account dict ---
        # NPS: latest and previous from history
        nps_current  = nps_hist[0].get("score")  if len(nps_hist) > 0 else health.get("nps")
        nps_previous = nps_hist[1].get("score")  if len(nps_hist) > 1 else None

        # Days to renewal
        contract_end = sub.get("contract_end_date") or sub.get("renewal_date") or company.get("contract_end_date")
        days_to_renewal = _days_until(contract_end)

        account = {
            # identity
            "name":              company.get("name", ""),
            "tier":              company.get("tier") or sub.get("tier", ""),
            "csm_name":          company.get("csm_name") or company.get("csm") or "",
            "champion":          company.get("champion", ""),
            "economic_buyer":    company.get("economic_buyer", ""),
            "industry":          company.get("industry", ""),
            "company_size":      company.get("company_size") or company.get("employee_count"),
            # financials
            "arr":               sub.get("arr") or sub.get("mrr", 0) * 12 or company.get("arr", 0),
            "contract_end_date": contract_end,
            "days_to_renewal":   days_to_renewal,
            "payment_terms":     sub.get("payment_terms", ""),
            "current_plan":      sub.get("plan") or sub.get("plan_name", ""),
            # health
            "health_score":      health.get("score") or health.get("health_score"),
            "health_trend":      health.get("trend") or health.get("health_trend", ""),
            "nps":               nps_current,
            "nps_previous":      nps_previous,
            # seats / usage
            "seats_total":       seats.get("total") or seats.get("seats_total") or sub.get("seats_total"),
            "seats_active":      seats.get("active") or seats.get("seats_active"),
            # support
            "open_support_tickets": sum(1 for t in tickets if t.get("status") == "open"),
        }
        # Merge any extra fields the API returns on company directly
        for k, v in company.items():
            if k not in account:
                account[k] = v

        # --- transcript dict (latest recording) ---
        transcript = {}
        if recordings:
            latest = recordings[0]
            recording_id = latest.get("id") or latest.get("recording_id")
            raw_transcript = self._safe(self.get_transcript, recording_id) or ""
            transcript = {
                "call_date":        latest.get("date") or latest.get("call_date", ""),
                "call_type":        latest.get("call_type") or latest.get("type", ""),
                "participants":     latest.get("participants", []),
                "duration_minutes": latest.get("duration_minutes") or latest.get("duration"),
                "transcript":       raw_transcript,
            }

        # --- notes dict (synthesised from activities) ---
        activity_texts = [
            a.get("notes") or a.get("description") or a.get("body") or ""
            for a in activities
            if a.get("notes") or a.get("description") or a.get("body")
        ]
        last_interaction = ""
        if activities:
            last_interaction = (
                activities[0].get("date")
                or activities[0].get("created_at")
                or activities[0].get("activity_date", "")
            )
        notes = {
            "recent_activity":    "\n".join(activity_texts[:5]),
            "engagement_summary": "\n".join(activity_texts),
            "support_summary":    _summarise_tickets(tickets),
            "csm_notes":          "\n".join(
                a.get("csm_notes", "") for a in activities if a.get("csm_notes")
            ),
            "last_interaction":   last_interaction,
        }

        return {
            "account":    account,
            "transcript": transcript,
            "tickets":    tickets,
            "notes":      notes,
        }

    # ------------------------------------------------------------------
    # Internal utility
    # ------------------------------------------------------------------

    @staticmethod
    def _safe(fn, *args, **kwargs):
        """Call fn, return None on any exception (logs to stderr)."""
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            import sys
            print(f"[demo_stack] warning: {fn.__name__} failed: {exc}", file=sys.stderr)
            return None


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _days_until(date_str: Optional[str]) -> Optional[int]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            target = datetime.strptime(date_str, fmt).date()
            return (target - date.today()).days
        except ValueError:
            continue
    return None


def _summarise_tickets(tickets: list) -> str:
    if not tickets:
        return "No support tickets."
    open_tickets = [t for t in tickets if t.get("status") == "open"]
    closed_count = len(tickets) - len(open_tickets)
    lines = [f"{len(open_tickets)} open ticket(s), {closed_count} closed."]
    for t in open_tickets[:5]:
        lines.append(f"  [{t.get('priority','?').upper()}] {t.get('title','')}")
    return "\n".join(lines)
