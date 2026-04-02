
import re
import json
from datetime import datetime
from pathlib import Path

class AuditLogger:
    def __init__(self, log_dir="logs/audit"):
        self.log_dir     = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.session_log = []

    def log(self, transaction_id, query, result,
            violations, true_label, duration_sec):
        output     = result.get("output", "")
        steps      = result.get("intermediate_steps", [])
        decision   = self._parse_decision(output)
        confidence = self._parse_confidence(output)

        record = {
            "timestamp"      : datetime.utcnow().isoformat(),
            "transaction_id" : transaction_id,
            "true_label"     : "FRAUD" if true_label==1 else "LEGITIMATE",
            "agent_decision" : decision,
            "confidence_pct" : confidence,
            "correct"        : self._is_correct(decision, true_label),
            "num_tool_calls" : len(steps),
            "tools_used"     : [s["tool"] for s in steps],
            "violation_count": len(violations),
            "violations"     : violations,
            "duration_sec"   : round(duration_sec, 2),
            "full_output"    : output,
        }

        with open(self.log_dir / f"{transaction_id}.json", "w") as f:
            json.dump(record, f, indent=2)

        self.session_log.append(record)
        return record

    def _parse_decision(self, output):
        u = output.upper()
        if "DECISION: FRAUD"      in u: return "FRAUD"
        if "DECISION: LEGITIMATE" in u: return "LEGITIMATE"
        if "DECISION: UNCERTAIN"  in u: return "UNCERTAIN"
        if "FRAUD" in u and "LEGITIMATE" not in u: return "FRAUD"
        if "LEGITIMATE" in u: return "LEGITIMATE"
        return "UNCERTAIN"

    def _parse_confidence(self, output):
        m = re.search(r"CONFIDENCE[:\s]+(\d+)%", output, re.IGNORECASE)
        return float(m.group(1)) / 100 if m else 0.5

    def _is_correct(self, decision, true_label):
        if decision == "FRAUD"      and true_label == 1: return True
        if decision == "LEGITIMATE" and true_label == 0: return True
        return False

    def save_session(self, path="logs/audit/session_summary.json"):
        with open(path, "w") as f:
            json.dump(self.session_log, f, indent=2)
        print(f"Session saved → {path} ({len(self.session_log)} records)")
