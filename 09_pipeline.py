
import time
from tqdm import tqdm
from openai import OpenAI
from config import CONFIG
from react_agent import run_agent
from safety_enforcer import SafetyEnforcer
from audit_logger import AuditLogger
from escalation_router import EscalationRouter

class TrustAgentPipeline:
    """
    Full TrustAgent pipeline:
    Safety Enforcer → ReAct Agent → Audit Logger → Escalation Router
    """
    def __init__(self, client, df, STATS):
        self.client   = client
        self.df       = df
        self.STATS    = STATS
        self.enforcer = SafetyEnforcer(strict_mode=CONFIG["strict_mode"])
        self.logger   = AuditLogger()
        self.router   = EscalationRouter(CONFIG["confidence_threshold"])
        self.results  = []

    def investigate(self, transaction_id, true_label):
        tid   = str(transaction_id)
        query = f"Investigate transaction {tid} for fraud risk."

        self.enforcer.clear()
        start = time.time()

        try:
            self.enforcer.check(query, step="user_input")
        except ValueError as e:
            return {"transaction_id": tid, "status": "blocked", "error": str(e)}

        try:
            result = run_agent(self.client, self.df, self.STATS, tid)
            status = "completed"
        except Exception as e:
            result = {"output": f"ERROR: {e}", "intermediate_steps": []}
            status = "error"

        duration      = time.time() - start
        record        = self.logger.log(
                            tid, query, result,
                            list(self.enforcer.violations),
                            true_label, duration)
        record["status"]  = status
        record["routing"] = self.router.route(record)
        self.results.append(record)
        return record

    def run_batch(self, transactions, max_cases=10):
        subset = transactions.head(max_cases)
        print(f"\nTrustAgent — {len(subset)} investigations")
        print("=" * 50)
        for _, row in tqdm(subset.iterrows(), total=len(subset)):
            self.investigate(row["TransactionID"], int(row["isFraud"]))
            time.sleep(1)
        self.logger.save_session()
        return self.results
