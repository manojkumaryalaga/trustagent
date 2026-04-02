
from datetime import datetime

class EscalationRouter:
    def __init__(self, threshold=0.75):
        self.threshold   = threshold
        self.escalations = []

    def route(self, record):
        conf     = record.get("confidence_pct", 0.5)
        decision = record.get("agent_decision", "UNCERTAIN")
        tid      = record.get("transaction_id", "?")

        needs_human = conf < self.threshold or decision == "UNCERTAIN"

        routing = {
            "transaction_id" : tid,
            "decision"       : decision,
            "confidence_pct" : conf,
            "escalated"      : needs_human,
            "reason"         : (
                f"Confidence {conf*100:.0f}% below threshold"
                if conf < self.threshold else
                "Agent returned UNCERTAIN"
                if decision == "UNCERTAIN" else
                "Auto-approved"
            ),
            "timestamp" : datetime.utcnow().isoformat(),
        }

        if needs_human:
            self.escalations.append(routing)
            print(f"ESCALATE | {tid} | {conf*100:.0f}% | {routing['reason']}")
        else:
            print(f"AUTO     | {tid} | {decision} | {conf*100:.0f}%")

        return routing
