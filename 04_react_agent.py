
import json
from openai import OpenAI
from config import CONFIG
from tools import (lookup_transaction, check_amount_risk,
                   check_email_domain_risk, get_similar_fraud_cases,
                   get_tools_schema)

SYSTEM_PROMPT = """You are TrustAgent, a trustworthy AI fraud investigation agent.

Investigate transactions step by step using your tools.
Use ALL 4 tools before making a decision.
Cite specific tool results in your final answer.

End your response with EXACTLY this format:
DECISION: [FRAUD / LEGITIMATE / UNCERTAIN]
CONFIDENCE: [0-100]%
REASONING: <cite each tool result that supports this decision>
"""

def run_agent(client, df, STATS, transaction_id: str) -> dict:
    tid      = str(transaction_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": (
            f"Investigate transaction {tid}. "
            f"Use lookup_transaction, check_amount_risk, "
            f"check_email_domain_risk, and get_similar_fraud_cases. "
            f"Then give DECISION, CONFIDENCE, REASONING."
        )}
    ]

    tool_functions = {
        "lookup_transaction"      : lambda **k: lookup_transaction(df, **k),
        "check_amount_risk"       : lambda **k: check_amount_risk(STATS, **k),
        "check_email_domain_risk" : lambda **k: check_email_domain_risk(STATS, **k),
        "get_similar_fraud_cases" : lambda **k: get_similar_fraud_cases(df, STATS, **k),
    }

    steps      = []
    iterations = 0
    final_msg  = None

    while iterations < CONFIG["max_iterations"]:
        iterations += 1
        response = client.chat.completions.create(
            model       = CONFIG["model"],
            messages    = messages,
            tools       = get_tools_schema(),
            tool_choice = "auto",
            temperature = CONFIG["temperature"],
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            final_msg = msg
            break

        messages.append(msg)

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            result  = tool_functions.get(fn_name, lambda **k: "unknown tool")(**fn_args)

            steps.append({"tool": fn_name, "input": fn_args, "output": result})
            messages.append({
                "role"         : "tool",
                "tool_call_id" : tc.id,
                "content"      : str(result),
            })

    output = final_msg.content if final_msg and final_msg.content else ""
    return {
        "output"             : output,
        "intermediate_steps" : steps,
        "num_iterations"     : iterations,
    }
