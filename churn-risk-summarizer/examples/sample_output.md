# Churn Risk Summarizer — Sample Output

**Account:** Acme Corp | **CSM:** Sarah Johnson | **ARR:** $84K | **Health:** 47/100

---

## Slack Message (sent to CSM)

```
🔴 Churn Risk Alert — Acme Corp

📊 Urgency: HIGH

Summary: Acme Corp started strong but has gone quiet. Login drop, ghost users, a
stalled support ticket, and two missed check-ins — all in the same 30-day window.

Risk Story:
The 14-day Salesforce sync ticket is the most urgent issue — not because it's
technically severe, but because Dana (COO) is personally tracking it. When an
executive starts watching a support ticket, it's no longer just a support problem.
It becomes the reason they leave.

Tom and Alicia haven't logged in since February. Marcus mentioned them as intended
power users. If they've reverted to spreadsheets, that's adoption regression — and
it will show up in the renewal conversation.

Primary Risks:
• 14-day open Salesforce sync ticket — COO tracking it personally
• Login frequency down 40% — Tom and Alicia inactive since February
• Missed last 2 monthly check-ins — no meaningful contact in 60 days
• NPS dropped from 8 to 6 — directional signal, not a crisis yet

Stabilizers:
• Core workflow still in use by 61 of 100 seats
• Renewal is 189 days away — time to course-correct
• COO confirmed no competitor evaluation underway yet
• Both stakeholders engaged in QBR and gave specific conditions to improve

Next Call Focus:
• Lead with the Salesforce ticket — give a WRITTEN resolution date before end of day
• Schedule separate 30-min call with Tom and Alicia — listening only, no sales
• Propose fixed monthly check-ins with standing agenda starting April
• Ask directly: "What would move your renewal confidence from a 6 to an 8?"

Recommended action: Resolve Salesforce ticket + re-engage ghost users this week.
CSM: Sarah Johnson
```

---

## Analysis JSON

```json
{
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
    "COO confirmed no competitor evaluation underway yet",
    "Both Marcus and Dana engaged in QBR and gave specific recovery conditions"
  ],
  "next_call_focus": [
    "Lead with the Salesforce ticket — give a written resolution date before end of day",
    "Schedule separate 30-min call with Tom and Alicia — listening only, no sales",
    "Propose monthly check-ins with fixed agenda starting April",
    "Ask directly what would move their renewal confidence from 6 to 8"
  ],
  "urgency": "high"
}
```
