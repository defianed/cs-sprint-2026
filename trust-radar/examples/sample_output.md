# Trust Radar — Sample Output

**Account:** Acme Corp | **CSM:** Sarah Johnson | **ARR:** $72K | **Urgency:** 8/10

---

## Slack Message (sent to CSM + escalation lead)

```
🔍 Trust Radar Analysis — Acme Corp
Classification: NEGOTIATING (82% confidence)

This is NOT a genuine loss of trust — it's leverage.

Here's the tell: at 03:18, Sarah Mitchell said "If you can get the API live by
March 28 and give me written commitments on the next two milestones, I'll hold
off the evaluation."

That's not someone exiting. That's someone telling you exactly what she needs
to stay. The competitor mentions (Salesforce, HubSpot) are leverage, not a
resignation letter. She even added: "I'll hold off calling DataBridge until I
see it." She's giving you a path.

Urgency Score: 8/10

The path is narrow and time-bound. Use it.

Recommended actions:
1. Deliver CTO written commitment letter to Sarah Mitchell by 5pm TODAY
2. Confirm API GA date (March 28) with engineering before sending anything
3. Set up weekly PM sync — invite Sarah to the first one this week
4. Do NOT offer financial concessions — she hasn't asked for them
5. Follow up within 24 hours — do not let this go cold

CSM: Sarah Johnson
```

---

## Analysis JSON

```json
{
  "classification": "NEGOTIATING",
  "confidence": 0.82,
  "reasoning": "Sarah Mitchell's frustration is real — three missed API commitments caused 40 hours of manual work. But the language is classic negotiation, not relationship exit. The conditional offer at 03:18 is the tell: 'If you can get the API live by March 28 and give me written commitments on the next two milestones, I'll hold off the evaluation.' Someone who has genuinely lost trust doesn't give you a specific, actionable bar to clear. They leave quietly. She's giving you a very precise path.",
  "evidence_snippets": [
    {
      "timestamp": "00:12",
      "speaker": "Sarah Mitchell",
      "text": "You've missed three commitments in a row. The API was supposed to be live in January. It's March.",
      "signal_type": "genuine_frustration",
      "confidence": 0.93
    },
    {
      "timestamp": "01:35",
      "speaker": "Sarah Mitchell",
      "text": "We are actively evaluating Salesforce and HubSpot right now. Just so you're aware.",
      "signal_type": "negotiation_leverage",
      "confidence": 0.87
    },
    {
      "timestamp": "03:18",
      "speaker": "Sarah Mitchell",
      "text": "If you can get the API live by March 28 and give me written commitments on the next two milestones, I'll hold off the evaluation.",
      "signal_type": "conditional_opening",
      "confidence": 0.91
    },
    {
      "timestamp": "04:08",
      "speaker": "Sarah Mitchell",
      "text": "Okay. I'll hold off calling DataBridge until I see it.",
      "signal_type": "door_left_open",
      "confidence": 0.88
    }
  ],
  "response_strategy": "Do not get defensive. Do not hedge. Confirm API date with engineering today and deliver CTO written commitment by 5pm. Come back within 24 hours with: (1) written API GA date — March 28, no ranges, (2) written commitments on next two milestones with specific dates, (3) PM added to weekly sync.",
  "urgency_score": 8,
  "recommended_actions": [
    "Deliver CTO written commitment letter to Sarah Mitchell by 5pm today",
    "Confirm API GA date (March 28) with engineering before sending anything",
    "Set up weekly PM sync — invite Sarah to the first one this week",
    "Do not offer financial concessions — she has not asked for them",
    "Follow up within 24 hours — do not let this go cold"
  ]
}
```
