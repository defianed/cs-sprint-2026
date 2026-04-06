"""
Trust Radar - Agentic Workflow for Analyzing Win-Back/Escalation Calls

Analyzes customer calls to determine trust status:
- GENUINE_LOSS_OF_TRUST
- NEGOTIATING
- MIXED
- UNCLEAR

Modes:
- live: Real-time analysis during calls
- post_call: Analysis after call completion
"""

import os
import json
import time
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Literal, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import modal

# Modal App Configuration
app = modal.App("trust-radar")

# Image with required dependencies
image = modal.Image.debian_slim().pip_install([
    "anthropic>=0.20.0",
    "openai>=1.0.0",
    "slack-sdk>=3.20.0",
    "requests>=2.30.0",
    "pydantic>=2.0.0",
])

# ============================================================================
# CONFIGURATION & ENVIRONMENT
# ============================================================================

class Config:
    """Configuration loaded from environment variables."""
    
    # CRM Provider
    CRM_PROVIDER = os.getenv("CRM_PROVIDER", "salesforce")  # salesforce | hubspot
    SALESFORCE_DOMAIN = os.getenv("SALESFORCE_DOMAIN")
    SALESFORCE_CLIENT_ID = os.getenv("SALESFORCE_CLIENT_ID")
    SALESFORCE_CLIENT_SECRET = os.getenv("SALESFORCE_CLIENT_SECRET")
    SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME")
    SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD")
    HUBSPOT_PRIVATE_APP_TOKEN = os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
    
    # Call Transcript Provider
    CALL_TRANSCRIPT_PROVIDER = os.getenv("CALL_TRANSCRIPT_PROVIDER", "gong")  # gong | fireflies | zoom
    GONG_ACCESS_KEY = os.getenv("GONG_ACCESS_KEY")
    GONG_SECRET_KEY = os.getenv("GONG_SECRET_KEY")
    FIREFLIES_API_KEY = os.getenv("FIREFLIES_API_KEY")
    ZOOM_OAUTH_TOKEN = os.getenv("ZOOM_OAUTH_TOKEN")
    
    # Support Provider
    SUPPORT_PROVIDER = os.getenv("SUPPORT_PROVIDER", "zendesk")  # zendesk | intercom
    ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
    ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
    ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
    INTERCOM_ACCESS_TOKEN = os.getenv("INTERCOM_ACCESS_TOKEN")
    
    # Slack
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    
    # LLM Provider
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # anthropic | openai
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Trust Radar Config
    TRUST_RADAR_MIN_CONFIDENCE = float(os.getenv("TRUST_RADAR_MIN_CONFIDENCE", "0.7"))
    LIVE_POLL_INTERVAL_SECONDS = int(os.getenv("LIVE_POLL_INTERVAL_SECONDS", "30"))
    MAX_CALL_MONITOR_MINUTES = int(os.getenv("MAX_CALL_MONITOR_MINUTES", "120"))
    
    # Event Logging
    EVENT_LOG_PATH = os.getenv("EVENT_LOG_PATH", "/tmp/trust_radar_events.jsonl")


# ============================================================================
# DATA MODELS
# ============================================================================

class TrustClassification(str, Enum):
    """Trust classification categories."""
    GENUINE_LOSS_OF_TRUST = "GENUINE_LOSS_OF_TRUST"
    NEGOTIATING = "NEGOTIATING"
    MIXED = "MIXED"
    UNCLEAR = "UNCLEAR"


class AnalysisMode(str, Enum):
    """Analysis mode."""
    LIVE = "live"
    POST_CALL = "post_call"


@dataclass
class EvidenceSnippet:
    """Evidence snippet for auditability."""
    timestamp: Optional[str]
    speaker: Optional[str]
    text: str
    signal_type: str  # frustration, negotiation, broken_promise, emotional_shift, churn_threat, openness_to_repair
    confidence: float


@dataclass
class TrustAnalysisResult:
    """Result of trust analysis."""
    classification: TrustClassification
    confidence: float
    reasoning: str
    evidence_snippets: list[EvidenceSnippet] = field(default_factory=list)
    response_strategy: str = ""
    urgency_score: int = 5  # 1-10
    recommended_actions: list[str] = field(default_factory=list)


@dataclass
class CRMContext:
    """CRM context for a customer."""
    customer_id: str
    customer_name: str
    account_tier: str = ""
    arr: float = 0.0
    health_score: Optional[int] = None
    recent_health_changes: list[dict] = field(default_factory=list)
    escalation_history: list[dict] = field(default_factory=list)
    last_engagement: Optional[str] = None
    csm_owner: str = ""
    csm_slack_id: str = ""


@dataclass
class SupportNote:
    """Support note/escalation note."""
    note_id: str
    created_at: str
    subject: str
    body: str
    sentiment: Optional[str] = None


@dataclass
class TranscriptChunk:
    """A chunk of transcript data."""
    chunk_id: str
    timestamp: str
    speaker: str
    text: str
    duration_seconds: Optional[int] = None
    
    def fingerprint(self) -> str:
        """Generate fingerprint for deduplication."""
        content = f"{self.timestamp}:{self.speaker}:{self.text[:100]}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class CallTranscript:
    """Complete or partial call transcript."""
    call_id: str
    customer_id: str
    chunks: list[TranscriptChunk] = field(default_factory=list)
    is_complete: bool = False
    call_start_time: Optional[str] = None
    call_end_time: Optional[str] = None
    participants: list[str] = field(default_factory=list)
    
    def get_full_text(self) -> str:
        """Get full transcript text."""
        sorted_chunks = sorted(self.chunks, key=lambda x: x.timestamp)
        return "\n".join([f"[{c.timestamp}] {c.speaker}: {c.text}" for c in sorted_chunks])


@dataclass
class TrustRadarEvent:
    """Structured event log entry."""
    event_id: str
    timestamp: str
    call_id: str
    customer_id: str
    mode: AnalysisMode
    classification: TrustClassification
    confidence: float
    reasoning: str
    evidence_count: int
    csm_notified: bool
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


# ============================================================================
# CRM INTEGRATION
# ============================================================================

class CRMProvider:
    """Base CRM provider interface."""
    
    async def get_customer_context(self, customer_id: str) -> CRMContext:
        raise NotImplementedError
    
    async def get_escalation_history(self, customer_id: str) -> list[dict]:
        raise NotImplementedError


class SalesforceProvider(CRMProvider):
    """Salesforce CRM integration."""
    
    def __init__(self):
        self.domain = Config.SALESFORCE_DOMAIN
        self.client_id = Config.SALESFORCE_CLIENT_ID
        self.client_secret = Config.SALESFORCE_CLIENT_SECRET
        self.username = Config.SALESFORCE_USERNAME
        self.password = Config.SALESFORCE_PASSWORD
        self.access_token = None
    
    async def _get_access_token(self) -> str:
        """Get OAuth access token."""
        import requests
        
        if self.access_token:
            return self.access_token
        
        url = f"https://{self.domain}.my.salesforce.com/services/oauth2/token"
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        }
        
        try:
            resp = requests.post(url, data=data, timeout=30)
            resp.raise_for_status()
            self.access_token = resp.json()["access_token"]
            return self.access_token
        except Exception as e:
            raise Exception(f"Salesforce auth failed: {e}")
    
    async def get_customer_context(self, customer_id: str) -> CRMContext:
        """Fetch customer context from Salesforce."""
        import requests
        
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        # Query Account data
        query = f"""
            SELECT Id, Name, Account_Tier__c, ARR__c, Health_Score__c, 
                   CSM_Owner__r.Name, CSM_Owner__r.Slack_User_ID__c
            FROM Account 
            WHERE Id = '{customer_id}' OR Name LIKE '%{customer_id}%'
            LIMIT 1
        """
        
        try:
            url = f"https://{self.domain}.my.salesforce.com/services/data/v58.0/query"
            resp = requests.get(url, headers=headers, params={"q": query}, timeout=30)
            resp.raise_for_status()
            records = resp.json().get("records", [])
            
            if not records:
                # Return minimal context if not found
                return CRMContext(
                    customer_id=customer_id,
                    customer_name="Unknown",
                    csm_slack_id=""
                )
            
            record = records[0]
            return CRMContext(
                customer_id=record.get("Id", customer_id),
                customer_name=record.get("Name", "Unknown"),
                account_tier=record.get("Account_Tier__c", ""),
                arr=float(record.get("ARR__c", 0) or 0),
                health_score=record.get("Health_Score__c"),
                csm_owner=record.get("CSM_Owner__r", {}).get("Name", ""),
                csm_slack_id=record.get("CSM_Owner__r", {}).get("Slack_User_ID__c", ""),
            )
        except Exception as e:
            # Degraded mode: return minimal context
            return CRMContext(
                customer_id=customer_id,
                customer_name="Unknown (fetch failed)",
                csm_slack_id="",
                escalation_history=[{"error": str(e)}]
            )
    
    async def get_escalation_history(self, customer_id: str) -> list[dict]:
        """Fetch escalation history."""
        import requests
        
        token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        query = f"""
            SELECT Id, Subject, Status, Priority, CreatedDate, Description
            FROM Case 
            WHERE AccountId = '{customer_id}' AND IsEscalated = true
            ORDER BY CreatedDate DESC
            LIMIT 10
        """
        
        try:
            url = f"https://{self.domain}.my.salesforce.com/services/data/v58.0/query"
            resp = requests.get(url, headers=headers, params={"q": query}, timeout=30)
            resp.raise_for_status()
            return resp.json().get("records", [])
        except Exception:
            return []


class HubSpotProvider(CRMProvider):
    """HubSpot CRM integration."""
    
    def __init__(self):
        self.api_key = Config.HUBSPOT_PRIVATE_APP_TOKEN
    
    async def get_customer_context(self, customer_id: str) -> CRMContext:
        """Fetch customer context from HubSpot."""
        import requests
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            # Get company record
            url = f"https://api.hubapi.com/crm/v3/objects/companies/{customer_id}"
            params = {
                "properties": "name,annual_revenue,csm_owner,health_score,tier"
            }
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            props = data.get("properties", {})
            return CRMContext(
                customer_id=customer_id,
                customer_name=props.get("name", "Unknown"),
                account_tier=props.get("tier", ""),
                arr=float(props.get("annual_revenue", 0) or 0),
                csm_owner=props.get("csm_owner", ""),
                csm_slack_id="",  # Would need mapping table
            )
        except Exception as e:
            return CRMContext(
                customer_id=customer_id,
                customer_name="Unknown (fetch failed)",
                csm_slack_id="",
                escalation_history=[{"error": str(e)}]
            )
    
    async def get_escalation_history(self, customer_id: str) -> list[dict]:
        """Fetch escalation history from HubSpot."""
        import requests
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            # Get tickets associated with company
            url = f"https://api.hubapi.com/crm/v3/objects/tickets/search"
            data = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "associations.company",
                        "operator": "EQ",
                        "value": customer_id
                    }, {
                        "propertyName": "hs_pipeline_stage",
                        "operator": "EQ", 
                        "value": "escalated"
                    }]
                }],
                "limit": 10
            }
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json().get("results", [])
        except Exception:
            return []


def get_crm_provider() -> CRMProvider:
    """Factory for CRM provider."""
    if Config.CRM_PROVIDER == "salesforce":
        return SalesforceProvider()
    elif Config.CRM_PROVIDER == "hubspot":
        return HubSpotProvider()
    else:
        raise ValueError(f"Unknown CRM provider: {Config.CRM_PROVIDER}")


# ============================================================================
# TRANSCRIPT PROVIDER INTEGRATION
# ============================================================================

class TranscriptProvider:
    """Base transcript provider interface."""
    
    async def get_transcript(self, call_id: str, partial: bool = False) -> CallTranscript:
        raise NotImplementedError
    
    async def is_call_active(self, call_id: str) -> bool:
        raise NotImplementedError


class GongProvider(TranscriptProvider):
    """Gong call transcript integration."""
    
    def __init__(self):
        self.access_key = Config.GONG_ACCESS_KEY
        self.secret_key = Config.GONG_SECRET_KEY
    
    async def get_transcript(self, call_id: str, partial: bool = False) -> CallTranscript:
        """Fetch transcript from Gong."""
        import requests
        
        auth = (self.access_key, self.secret_key)
        
        try:
            # Get call details
            url = f"https://api.gong.io/v2/calls/{call_id}"
            resp = requests.get(url, auth=auth, timeout=30)
            resp.raise_for_status()
            call_data = resp.json()
            
            # Get transcript
            transcript_url = f"https://api.gong.io/v2/calls/{call_id}/transcript"
            resp = requests.get(transcript_url, auth=auth, timeout=30)
            resp.raise_for_status()
            transcript_data = resp.json()
            
            chunks = []
            for item in transcript_data.get("transcript", []):
                chunk = TranscriptChunk(
                    chunk_id=item.get("id", ""),
                    timestamp=item.get("startTime", ""),
                    speaker=item.get("speakerId", ""),
                    text=item.get("text", ""),
                    duration_seconds=item.get("duration", 0),
                )
                chunks.append(chunk)
            
            return CallTranscript(
                call_id=call_id,
                customer_id=call_data.get("context", {}).get("companyId", ""),
                chunks=chunks,
                is_complete=call_data.get("isFinished", True) and not partial,
                call_start_time=call_data.get("started"),
                call_end_time=call_data.get("ended"),
                participants=[p.get("id") for p in call_data.get("parties", [])],
            )
        except Exception as e:
            raise Exception(f"Gong transcript fetch failed: {e}")
    
    async def is_call_active(self, call_id: str) -> bool:
        """Check if call is still active."""
        import requests
        
        auth = (self.access_key, self.secret_key)
        
        try:
            url = f"https://api.gong.io/v2/calls/{call_id}"
            resp = requests.get(url, auth=auth, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return not data.get("isFinished", True)
        except Exception:
            return False


class FirefliesProvider(TranscriptProvider):
    """Fireflies transcript integration."""
    
    def __init__(self):
        self.api_key = Config.FIREFLIES_API_KEY
    
    async def get_transcript(self, call_id: str, partial: bool = False) -> CallTranscript:
        """Fetch transcript from Fireflies."""
        import requests
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        query = """
            query GetTranscript($transcriptId: String!) {
                transcript(id: $transcriptId) {
                    id
                    title
                    date
                    duration
                    sentences {
                        text
                        speaker_name
                        start_time
                    }
                }
            }
        """
        
        try:
            resp = requests.post(
                "https://api.fireflies.ai/graphql",
                headers=headers,
                json={
                    "query": query,
                    "variables": {"transcriptId": call_id}
                },
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            transcript = data.get("data", {}).get("transcript", {})
            
            chunks = []
            for sent in transcript.get("sentences", []):
                chunk = TranscriptChunk(
                    chunk_id=f"{call_id}_{len(chunks)}",
                    timestamp=str(sent.get("start_time", 0)),
                    speaker=sent.get("speaker_name", "Unknown"),
                    text=sent.get("text", ""),
                )
                chunks.append(chunk)
            
            return CallTranscript(
                call_id=call_id,
                customer_id="",  # Would need to extract from metadata
                chunks=chunks,
                is_complete=True,
                call_start_time=transcript.get("date"),
            )
        except Exception as e:
            raise Exception(f"Fireflies transcript fetch failed: {e}")
    
    async def is_call_active(self, call_id: str) -> bool:
        """Fireflies doesn't support live transcripts."""
        return False


class ZoomProvider(TranscriptProvider):
    """Zoom transcript integration."""
    
    def __init__(self):
        self.jwt_token = Config.ZOOM_OAUTH_TOKEN
    
    async def get_transcript(self, call_id: str, partial: bool = False) -> CallTranscript:
        """Fetch transcript from Zoom."""
        import requests
        
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        
        try:
            # Get recording transcript
            url = f"https://api.zoom.us/v2/meetings/{call_id}/recordings"
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            chunks = []
            for file in data.get("recording_files", []):
                if file.get("file_type") == "TRANSCRIPT":
                    # Download and parse VTT
                    vtt_url = file.get("download_url")
                    vtt_resp = requests.get(vtt_url, headers=headers, timeout=30)
                    chunks = self._parse_vtt(vtt_resp.text)
            
            return CallTranscript(
                call_id=call_id,
                customer_id="",
                chunks=chunks,
                is_complete=True,
            )
        except Exception as e:
            raise Exception(f"Zoom transcript fetch failed: {e}")
    
    def _parse_vtt(self, vtt_content: str) -> list[TranscriptChunk]:
        """Parse WebVTT transcript format."""
        chunks = []
        lines = vtt_content.split("\n")
        current_text = ""
        current_time = ""
        
        for line in lines:
            if " --> " in line:
                current_time = line.split(" --> ")[0]
            elif line.strip() and not line.startswith("WEBVTT"):
                if current_text:
                    chunks.append(TranscriptChunk(
                        chunk_id=f"chunk_{len(chunks)}",
                        timestamp=current_time,
                        speaker="Unknown",
                        text=line.strip(),
                    ))
                    current_text = ""
                else:
                    current_text = line.strip()
        
        return chunks
    
    async def is_call_active(self, call_id: str) -> bool:
        """Zoom doesn't expose live transcript status easily."""
        return False


def get_transcript_provider() -> TranscriptProvider:
    """Factory for transcript provider."""
    if Config.CALL_TRANSCRIPT_PROVIDER == "gong":
        return GongProvider()
    elif Config.CALL_TRANSCRIPT_PROVIDER == "fireflies":
        return FirefliesProvider()
    elif Config.CALL_TRANSCRIPT_PROVIDER == "zoom":
        return ZoomProvider()
    else:
        raise ValueError(f"Unknown transcript provider: {Config.CALL_TRANSCRIPT_PROVIDER}")


# ============================================================================
# SUPPORT PROVIDER INTEGRATION
# ============================================================================

class SupportProvider:
    """Base support provider interface."""
    
    async def get_recent_notes(self, customer_id: str, days: int = 30) -> list[SupportNote]:
        raise NotImplementedError


class ZendeskProvider(SupportProvider):
    """Zendesk support integration."""
    
    def __init__(self):
        self.subdomain = Config.ZENDESK_SUBDOMAIN
        self.email = Config.ZENDESK_EMAIL
        self.api_token = Config.ZENDESK_API_TOKEN
    
    async def get_recent_notes(self, customer_id: str, days: int = 30) -> list[SupportNote]:
        """Fetch recent support tickets and notes."""
        import requests
        
        auth = (f"{self.email}/token", self.api_token)
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        try:
            url = f"https://{self.subdomain}.zendesk.com/api/v2/search.json"
            params = {
                "query": f"organization:{customer_id} created>{since} type:ticket",
                "sort_by": "created_at",
                "sort_order": "desc",
            }
            resp = requests.get(url, auth=auth, params=params, timeout=30)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            
            notes = []
            for ticket in results[:10]:  # Limit to 10 recent tickets
                note = SupportNote(
                    note_id=str(ticket.get("id")),
                    created_at=ticket.get("created_at", ""),
                    subject=ticket.get("subject", ""),
                    body=ticket.get("description", ""),
                )
                notes.append(note)
            
            return notes
        except Exception:
            return []


class IntercomProvider(SupportProvider):
    """Intercom support integration."""
    
    def __init__(self):
        self.access_token = Config.INTERCOM_ACCESS_TOKEN
    
    async def get_recent_notes(self, customer_id: str, days: int = 30) -> list[SupportNote]:
        """Fetch recent conversations."""
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
        }
        
        try:
            url = "https://api.intercom.io/conversations/search"
            data = {
                "query": {
                    "field": "contact_ids",
                    "operator": "~",
                    "value": customer_id
                }
            }
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            conversations = resp.json().get("conversations", [])
            
            notes = []
            for conv in conversations[:10]:
                note = SupportNote(
                    note_id=conv.get("id"),
                    created_at=conv.get("created_at"),
                    subject=conv.get("title", ""),
                    body=conv.get("source", {}).get("body", ""),
                )
                notes.append(note)
            
            return notes
        except Exception:
            return []


def get_support_provider() -> SupportProvider:
    """Factory for support provider."""
    if Config.SUPPORT_PROVIDER == "zendesk":
        return ZendeskProvider()
    elif Config.SUPPORT_PROVIDER == "intercom":
        return IntercomProvider()
    else:
        raise ValueError(f"Unknown support provider: {Config.SUPPORT_PROVIDER}")


# ============================================================================
# LLM ANALYSIS LAYER
# ============================================================================

class LLMClassifier:
    """LLM-based trust classification."""
    
    SYSTEM_PROMPT = """You are an expert customer success analyst specializing in trust signals during win-back and escalation calls.

Your task is to analyze call transcripts and classify the customer's trust status.

CLASSIFICATION CATEGORIES:
1. GENUINE_LOSS_OF_TRUST - Customer expresses deep disappointment, betrayal, or fundamental loss of confidence in the company/product. Signals: explicit statements about broken trust, past failures, "never again" language, emotional investment in leaving.

2. NEGOTIATING - Customer is using dissatisfaction as leverage for better terms. Signals: comparing competitors, asking for discounts immediately, conditional language ("if you can..."), focus on price/concessions rather than relationship repair.

3. MIXED - Customer shows genuine frustration but also openness to repair. Signals: complaints balanced with questions about solutions, expressing disappointment but staying engaged, testing boundaries.

4. UNCLEAR - Insufficient evidence to make a determination. Signals: neutral tone throughout, limited interaction, no explicit trust-related statements.

SIGNALS TO MONITOR:
- Frustration: Raised voice, repeated complaints, "I've told you before"
- Negotiation tactics: Competitive quotes, "what can you offer", trial closing
- Broken promises: References to past commitments not kept, "you said"
- Emotional shifts: Tone changes from warm to cold, sudden formality
- Churn threats: "We're looking at alternatives", "evaluating options"
- Openness to repair: "What would need to change", "How could we", "Tell me more"

OUTPUT FORMAT:
You must respond with a valid JSON object matching this schema:
{
    "classification": "GENUINE_LOSS_OF_TRUST|NEGOTIATING|MIXED|UNCLEAR",
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation of your analysis",
    "evidence_snippets": [
        {
            "timestamp": "HH:MM:SS or null",
            "speaker": "speaker name",
            "text": "exact quote",
            "signal_type": "frustration|negotiation|broken_promise|emotional_shift|churn_threat|openness_to_repair",
            "confidence": 0.0-1.0
        }
    ],
    "response_strategy": "recommended approach for CSM",
    "urgency_score": 1-10,
    "recommended_actions": ["action 1", "action 2"]
}

GUIDELINES:
- Confidence < 0.7 → classify as MIXED or UNCLEAR, never force a high-confidence label
- Include exact quotes as evidence snippets with timestamps when available
- Consider CRM context (health score, escalation history) in your reasoning
- If partial transcript, note uncertainty in reasoning
- Be conservative: when in doubt, prefer MIXED/UNCLEAR over false certainty
- Never invent evidence - only quote from the actual transcript
"""
    
    def __init__(self):
        self.provider = Config.LLM_PROVIDER
        self.anthropic_key = Config.ANTHROPIC_API_KEY
        self.openai_key = Config.OPENAI_API_KEY
    
    async def classify(
        self,
        transcript: CallTranscript,
        crm_context: CRMContext,
        support_notes: list[SupportNote],
        is_partial: bool = False
    ) -> TrustAnalysisResult:
        """Classify trust status using LLM."""
        
        # Build context
        context = self._build_context(crm_context, support_notes, is_partial)
        transcript_text = transcript.get_full_text()
        
        if self.provider == "anthropic":
            return await self._classify_anthropic(context, transcript_text, is_partial)
        else:
            return await self._classify_openai(context, transcript_text, is_partial)
    
    def _build_context(
        self,
        crm_context: CRMContext,
        support_notes: list[SupportNote],
        is_partial: bool
    ) -> str:
        """Build context string for LLM."""
        lines = ["=== CUSTOMER CONTEXT ==="]
        lines.append(f"Customer: {crm_context.customer_name} (ID: {crm_context.customer_id})")
        lines.append(f"Account Tier: {crm_context.account_tier}")
        lines.append(f"ARR: ${crm_context.arr:,.2f}")
        lines.append(f"Health Score: {crm_context.health_score or 'Unknown'}")
        lines.append(f"CSM Owner: {crm_context.csm_owner}")
        
        if crm_context.escalation_history:
            lines.append(f"\nRecent Escalations: {len(crm_context.escalation_history)}")
            for esc in crm_context.escalation_history[:3]:
                lines.append(f"  - {esc.get('Subject', 'N/A')}: {esc.get('Status', 'N/A')}")
        
        if support_notes:
            lines.append(f"\n=== RECENT SUPPORT NOTES ({len(support_notes)} recent) ===")
            for note in support_notes[:5]:
                lines.append(f"[{note.created_at}] {note.subject}")
                body_preview = note.body[:200] + "..." if len(note.body) > 200 else note.body
                lines.append(f"  {body_preview}")
        
        if is_partial:
            lines.append("\n[NOTE: This is a PARTIAL transcript from an ongoing call]")
        
        return "\n".join(lines)
    
    async def _classify_anthropic(
        self,
        context: str,
        transcript_text: str,
        is_partial: bool
    ) -> TrustAnalysisResult:
        """Classify using Anthropic Claude."""
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=self.anthropic_key)
        
        user_message = f"""{context}

=== CALL TRANSCRIPT ===
{transcript_text}

Analyze this call and provide your classification as JSON."""
        
        try:
            resp = await client.messages.create(
                model="claude-opus-4-6",
                max_tokens=4096,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )
            
            content = resp.content[0].text
            return self._parse_llm_response(content)
        except Exception as e:
            # Degraded mode: return unclear with error
            return TrustAnalysisResult(
                classification=TrustClassification.UNCLEAR,
                confidence=0.0,
                reasoning=f"LLM analysis failed: {e}. Manual review required.",
                evidence_snippets=[],
                response_strategy="Manual review recommended due to analysis failure.",
                urgency_score=5,
                recommended_actions=["Review transcript manually", "Contact customer directly"],
            )
    
    async def _classify_openai(
        self,
        context: str,
        transcript_text: str,
        is_partial: bool
    ) -> TrustAnalysisResult:
        """Classify using OpenAI GPT."""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.openai_key)
        
        user_message = f"""{context}

=== CALL TRANSCRIPT ===
{transcript_text}

Analyze this call and provide your classification as JSON."""
        
        try:
            resp = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                max_tokens=4096,
            )
            
            content = resp.choices[0].message.content
            return self._parse_llm_response(content)
        except Exception as e:
            return TrustAnalysisResult(
                classification=TrustClassification.UNCLEAR,
                confidence=0.0,
                reasoning=f"LLM analysis failed: {e}. Manual review required.",
                evidence_snippets=[],
                response_strategy="Manual review recommended due to analysis failure.",
                urgency_score=5,
                recommended_actions=["Review transcript manually", "Contact customer directly"],
            )
    
    def _parse_llm_response(self, content: str) -> TrustAnalysisResult:
        """Parse and validate LLM response."""
        try:
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content.strip())
            
            # Validate confidence threshold
            confidence = float(data.get("confidence", 0))
            classification_str = data.get("classification", "UNCLEAR")
            
            # Enforce low confidence handling
            if confidence < Config.TRUST_RADAR_MIN_CONFIDENCE:
                if classification_str in ["GENUINE_LOSS_OF_TRUST", "NEGOTIATING"]:
                    classification_str = "MIXED"
            
            # Parse evidence snippets
            evidence = []
            for item in data.get("evidence_snippets", []):
                evidence.append(EvidenceSnippet(
                    timestamp=item.get("timestamp"),
                    speaker=item.get("speaker"),
                    text=item.get("text", ""),
                    signal_type=item.get("signal_type", "unknown"),
                    confidence=float(item.get("confidence", 0.5)),
                ))
            
            return TrustAnalysisResult(
                classification=TrustClassification(classification_str),
                confidence=confidence,
                reasoning=data.get("reasoning", ""),
                evidence_snippets=evidence,
                response_strategy=data.get("response_strategy", ""),
                urgency_score=int(data.get("urgency_score", 5)),
                recommended_actions=data.get("recommended_actions", []),
            )
        except Exception as e:
            return TrustAnalysisResult(
                classification=TrustClassification.UNCLEAR,
                confidence=0.0,
                reasoning=f"Failed to parse LLM response: {e}. Raw: {content[:500]}",
                evidence_snippets=[],
                response_strategy="Manual review required - parsing error.",
                urgency_score=5,
                recommended_actions=["Review transcript manually"],
            )


# ============================================================================
# SLACK NOTIFICATION
# ============================================================================

class SlackNotifier:
    """Slack notification handler."""
    
    def __init__(self):
        from slack_sdk.web.async_client import AsyncWebClient
        self.client = AsyncWebClient(token=Config.SLACK_BOT_TOKEN)
    
    async def notify_csm(
        self,
        csm_slack_id: str,
        customer_name: str,
        result: TrustAnalysisResult,
        call_id: str,
        mode: AnalysisMode
    ) -> bool:
        """Send DM to CSM with analysis results."""
        
        if not csm_slack_id:
            # Try to find user by email or name if no slack ID
            return False
        
        # Build message blocks
        classification_emoji = {
            TrustClassification.GENUINE_LOSS_OF_TRUST: "🔴",
            TrustClassification.NEGOTIATING: "🟡",
            TrustClassification.MIXED: "🟠",
            TrustClassification.UNCLEAR: "⚪",
        }
        
        emoji = classification_emoji.get(result.classification, "⚪")
        mode_label = "🔴 LIVE" if mode == AnalysisMode.LIVE else "📼 POST-CALL"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Trust Radar Alert: {result.classification.value}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Customer:*\n{customer_name}"},
                    {"type": "mrkdwn", "text": f"*Call ID:*\n`{call_id}`"},
                    {"type": "mrkdwn", "text": f"*Mode:*\n{mode_label}"},
                    {"type": "mrkdwn", "text": f"*Confidence:*\n{result.confidence:.0%}"},
                    {"type": "mrkdwn", "text": f"*Urgency:*\n{result.urgency_score}/10"},
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reasoning:*\n{result.reasoning[:500]}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommended Strategy:*\n{result.response_strategy}"
                }
            },
        ]
        
        # Add evidence snippets
        if result.evidence_snippets:
            evidence_text = "*Key Evidence:*\n"
            for ev in result.evidence_snippets[:5]:  # Limit to 5
                ts = ev.timestamp or "unknown"
                evidence_text += f"• [{ts}] _{ev.signal_type}_: \"{ev.text[:100]}...\"\n"
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": evidence_text}
            })
        
        # Add recommended actions
        if result.recommended_actions:
            actions_text = "*Recommended Actions:*\n" + "\n".join([f"• {a}" for a in result.recommended_actions])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": actions_text}
            })
        
        try:
            # Open DM channel
            conv = await self.client.conversations_open(users=[csm_slack_id])
            channel_id = conv["channel"]["id"]
            
            # Send message
            await self.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text=f"Trust Radar: {result.classification.value} for {customer_name}"
            )
            return True
        except Exception as e:
            print(f"Slack notification failed: {e}")
            return False


# ============================================================================
# EVENT LOGGING
# ============================================================================

class EventLogger:
    """Structured event logging."""
    
    def __init__(self, log_path: str = None):
        self.log_path = log_path or Config.EVENT_LOG_PATH
    
    def log_event(self, event: TrustRadarEvent):
        """Persist event to log."""
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(asdict(event), default=str) + "\n")
        except Exception as e:
            print(f"Event logging failed: {e}")
    
    def get_events(self, call_id: str = None, customer_id: str = None, limit: int = 100) -> list[TrustRadarEvent]:
        """Query events from log."""
        events = []
        try:
            with open(self.log_path, "r") as f:
                for line in reversed(f.readlines()):
                    if len(events) >= limit:
                        break
                    data = json.loads(line.strip())
                    if call_id and data.get("call_id") != call_id:
                        continue
                    if customer_id and data.get("customer_id") != customer_id:
                        continue
                    events.append(TrustRadarEvent(**data))
        except FileNotFoundError:
            pass
        return events


# ============================================================================
# CALL MONITOR (LIVE MODE)
# ============================================================================

class CallMonitor:
    """Monitors calls in real-time."""
    
    def __init__(self):
        self.seen_chunks: dict[str, set] = defaultdict(set)  # call_id -> set of fingerprints
        self.transcript_provider = get_transcript_provider()
        self.crm_provider = get_crm_provider()
        self.support_provider = get_support_provider()
        self.classifier = LLMClassifier()
        self.slack = SlackNotifier()
        self.logger = EventLogger()
    
    async def monitor_call(
        self,
        call_id: str,
        customer_id: str,
        max_duration_minutes: int = None
    ) -> TrustAnalysisResult:
        """Monitor a call in real-time until completion or timeout."""
        
        max_duration = max_duration_minutes or Config.MAX_CALL_MONITOR_MINUTES
        start_time = time.time()
        poll_interval = Config.LIVE_POLL_INTERVAL_SECONDS
        
        crm_context = await self.crm_provider.get_customer_context(customer_id)
        support_notes = await self.support_provider.get_recent_notes(customer_id)
        
        last_result = None
        analysis_count = 0
        
        while True:
            elapsed_minutes = (time.time() - start_time) / 60
            
            # Check timeout
            if elapsed_minutes > max_duration:
                print(f"Call monitoring timeout for {call_id}")
                break
            
            # Check if call is still active
            is_active = await self.transcript_provider.is_call_active(call_id)
            
            try:
                # Fetch transcript (partial)
                transcript = await self.transcript_provider.get_transcript(call_id, partial=True)
                
                # Deduplicate chunks
                new_chunks = self._deduplicate_chunks(call_id, transcript.chunks)
                if not new_chunks and analysis_count > 0:
                    # No new content, wait and retry
                    await asyncio.sleep(poll_interval)
                    continue
                
                # Create partial transcript with only new chunks
                partial_transcript = CallTranscript(
                    call_id=call_id,
                    customer_id=customer_id,
                    chunks=new_chunks,
                    is_complete=not is_active,
                )
                
                # Analyze
                result = await self.classifier.classify(
                    partial_transcript,
                    crm_context,
                    support_notes,
                    is_partial=True
                )
                last_result = result
                analysis_count += 1
                
                # Log event
                event = TrustRadarEvent(
                    event_id=f"{call_id}_live_{analysis_count}",
                    timestamp=datetime.utcnow().isoformat(),
                    call_id=call_id,
                    customer_id=customer_id,
                    mode=AnalysisMode.LIVE,
                    classification=result.classification,
                    confidence=result.confidence,
                    reasoning=result.reasoning,
                    evidence_count=len(result.evidence_snippets),
                    csm_notified=False,
                    metadata={"chunks_analyzed": len(transcript.chunks), "new_chunks": len(new_chunks)}
                )
                self.logger.log_event(event)
                
                # Notify on significant findings (high confidence genuine loss or negotiating)
                if result.confidence >= Config.TRUST_RADAR_MIN_CONFIDENCE:
                    if result.classification in [TrustClassification.GENUINE_LOSS_OF_TRUST, TrustClassification.NEGOTIATING]:
                        notified = await self.slack.notify_csm(
                            crm_context.csm_slack_id,
                            crm_context.customer_name,
                            result,
                            call_id,
                            AnalysisMode.LIVE
                        )
                        event.csm_notified = notified
                        self.logger.log_event(event)
                
            except Exception as e:
                print(f"Error during live monitoring: {e}")
            
            # Check if call ended
            if not is_active:
                print(f"Call {call_id} has ended")
                break
            
            await asyncio.sleep(poll_interval)
        
        return last_result
    
    def _deduplicate_chunks(self, call_id: str, chunks: list[TranscriptChunk]) -> list[TranscriptChunk]:
        """Filter out already-seen chunks."""
        new_chunks = []
        for chunk in chunks:
            fp = chunk.fingerprint()
            if fp not in self.seen_chunks[call_id]:
                self.seen_chunks[call_id].add(fp)
                new_chunks.append(chunk)
        return new_chunks


# ============================================================================
# MAIN WORKFLOW FUNCTIONS (MODAL)
# ============================================================================

# In-memory state for deduplication (Modal container-local)
_seen_calls: set = set()


@app.function(image=image)
@modal.web_endpoint(method="POST")
async def webhook_analyze(body: dict):
    """
    Webhook endpoint for post-call or live call trigger.
    
    Expected body:
    {
        "call_id": "string",
        "customer_id": "string", 
        "mode": "live" | "post_call",
        "webhook_source": "gong" | "fireflies" | "zoom" | "manual"
    }
    """
    import uuid
    
    call_id = body.get("call_id")
    customer_id = body.get("customer_id")
    mode = body.get("mode", "post_call")
    
    if not call_id or not customer_id:
        return {"error": "Missing call_id or customer_id"}, 400
    
    # Deduplication check
    dedup_key = f"{call_id}_{mode}"
    if dedup_key in _seen_calls:
        return {"status": "already_processed", "call_id": call_id}
    _seen_calls.add(dedup_key)
    
    try:
        if mode == "live":
            # Start live monitoring
            monitor = CallMonitor()
            result = await monitor.monitor_call(call_id, customer_id)
            return {
                "status": "monitoring_complete",
                "call_id": call_id,
                "final_classification": result.classification.value if result else None,
            }
        else:
            # Post-call analysis
            return await _run_post_call_analysis(call_id, customer_id)
    except Exception as e:
        return {"error": str(e), "call_id": call_id}, 500


async def _run_post_call_analysis(call_id: str, customer_id: str) -> dict:
    """Run post-call analysis workflow."""
    import uuid
    
    # Initialize providers
    crm_provider = get_crm_provider()
    support_provider = get_support_provider()
    transcript_provider = get_transcript_provider()
    classifier = LLMClassifier()
    slack = SlackNotifier()
    logger = EventLogger()
    
    # Gather context
    crm_context = await crm_provider.get_customer_context(customer_id)
    support_notes = await support_provider.get_recent_notes(customer_id)
    
    # Fetch transcript
    transcript = await transcript_provider.get_transcript(call_id, partial=False)
    
    # Analyze
    result = await classifier.classify(
        transcript,
        crm_context,
        support_notes,
        is_partial=False
    )
    
    # Notify CSM
    notified = await slack.notify_csm(
        crm_context.csm_slack_id,
        crm_context.customer_name,
        result,
        call_id,
        AnalysisMode.POST_CALL
    )
    
    # Log event
    event = TrustRadarEvent(
        event_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat(),
        call_id=call_id,
        customer_id=customer_id,
        mode=AnalysisMode.POST_CALL,
        classification=result.classification,
        confidence=result.confidence,
        reasoning=result.reasoning,
        evidence_count=len(result.evidence_snippets),
        csm_notified=notified,
    )
    logger.log_event(event)
    
    return {
        "status": "complete",
        "call_id": call_id,
        "classification": result.classification.value,
        "confidence": result.confidence,
        "csm_notified": notified,
    }


@app.function(image=image, schedule=modal.Period(minutes=5))
async def scheduled_poll():
    """
    Scheduled function to poll for new calls needing analysis.
    Can be used as a fallback when webhooks aren't available.
    """
    print("Scheduled poll ran. No polling source configured, so no calls were processed.")
    return {"status": "polling_complete", "calls_processed": 0, "mode": "manual_or_webhook_only"}


@app.function(image=image)
@modal.web_endpoint(method="GET")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "providers": {
            "crm": Config.CRM_PROVIDER,
            "transcript": Config.CALL_TRANSCRIPT_PROVIDER,
            "support": Config.SUPPORT_PROVIDER,
            "llm": Config.LLM_PROVIDER,
        }
    }


@app.function(image=image)
@modal.web_endpoint(method="GET")
async def get_analysis_history(call_id: str = None, customer_id: str = None, limit: int = 50):
    """Query analysis history."""
    logger = EventLogger()
    events = logger.get_events(call_id=call_id, customer_id=customer_id, limit=limit)
    return {
        "events": [asdict(e) for e in events]
    }


# ============================================================================
# LOCAL TESTING
# ============================================================================

if __name__ == "__main__":
    # Local testing entry point
    print("Trust Radar - Modal App")
    print("Deploy with: modal deploy main.py")
    print("\nEnvironment variables required:")
    print("  - CRM_PROVIDER (salesforce/hubspot)")
    print("  - CALL_TRANSCRIPT_PROVIDER (gong/fireflies/zoom)")
    print("  - SUPPORT_PROVIDER (zendesk/intercom)")
    print("  - LLM_PROVIDER (anthropic/openai)")
    print("  - SLACK_BOT_TOKEN")
    print("  - Provider-specific credentials")
