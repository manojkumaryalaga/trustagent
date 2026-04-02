
import re
import json
from datetime import datetime
from enum import Enum

class RiskType(Enum):
    PROMPT_INJECTION = "prompt_injection"
    GOAL_DEVIATION   = "goal_deviation"
    POLICY_VIOLATION = "policy_violation"
    SAFE             = "safe"

INJECTION_PATTERNS = [
    r"ignore (previous|all|above) instructions",
    r"forget (everything|your|the) (instructions|prompt|goal)",
    r"you are now",
    r"new (instructions|directive|goal)",
    r"disregard (your|the|all)",
    r"override (safety|instructions)",
    r"pretend (you are|to be)",
    r"act as (if|a|an)",
    r"bypass",
    r"jailbreak",
]

GOAL_DEVIATION_PATTERNS = [
    r"transfer (funds|money|assets)",
    r"delete (data|records|files|logs|audit)",
    r"remove (logs|audit|records|data)",
    r"wipe (logs|data|records|audit)",
    r"send (email|message) to",
    r"execute (system|os|shell|command)",
    r"reveal (password|key|secret|token|credential)",
    r"expose (user|customer|personal) data",
    r"modify (record|transaction|database)",
]

POLICY_PATTERNS = [
    r"social security",
    r"credit card number",
    r"password",
    r"private key",
    r"api key",
    r"bearer token",
]

class SafetyEnforcer:
    def __init__(self, strict_mode=True):
        self.strict_mode = strict_mode
        self.violations  = []

    def _scan(self, text):
        t = text.lower()
        for p in INJECTION_PATTERNS:
            if re.search(p, t): return RiskType.PROMPT_INJECTION, p
        for p in GOAL_DEVIATION_PATTERNS:
            if re.search(p, t): return RiskType.GOAL_DEVIATION, p
        for p in POLICY_PATTERNS:
            if re.search(p, t): return RiskType.POLICY_VIOLATION, p
        return RiskType.SAFE, ""

    def check(self, text, step="input"):
        risk, pattern = self._scan(text)
        if risk != RiskType.SAFE:
            v = {
                "timestamp" : datetime.utcnow().isoformat(),
                "step"      : step,
                "risk_type" : risk.value,
                "pattern"   : pattern,
                "snippet"   : text[:200],
            }
            self.violations.append(v)
            print(f"VIOLATION | {risk.value} | {step} | {pattern}")
            if self.strict_mode:
                raise ValueError(f"Safety violation [{risk.value}] at {step}")
            return False
        return True

    def clear(self):
        self.violations = []

    def save(self, path="logs/violations/violations.json"):
        with open(path, "w") as f:
            json.dump(self.violations, f, indent=2)
        print(f"Violations saved → {path}")
