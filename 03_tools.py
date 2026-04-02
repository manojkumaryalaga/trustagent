
import json

# Tool functions — called by the ReAct agent
# df and STATS are passed in at runtime from data_loader

def lookup_transaction(df, transaction_id: str) -> str:
    """Look up a transaction by ID and return its full details."""
    try:
        row = df[df["TransactionID"] == int(transaction_id)]
    except ValueError:
        return f"Invalid transaction ID: {transaction_id}"
    if row.empty:
        return f"Transaction {transaction_id} not found."
    r = row.iloc[0]
    return (f"TransactionID: {r.TransactionID} | "
            f"Amount: ${r.TransactionAmt:.2f} | "
            f"Product: {r.ProductCD} | "
            f"Card: {r.card4} {r.card6} | "
            f"Email: {r.P_emaildomain} | "
            f"Label: {'FRAUD' if r.isFraud==1 else 'LEGITIMATE'} | "
            f"[Use Amount={r.TransactionAmt:.2f} and ProductCode={r.ProductCD} for other tools]")

def check_amount_risk(STATS, amount: str) -> str:
    """Check if a transaction amount is statistically high risk."""
    try:
        amt = float(amount)
    except ValueError:
        return f"Invalid amount: {amount}"
    risk = "HIGH" if amt > STATS["fraud_amt_mean"] * 0.8 else "LOW"
    return (f"Amount: ${amt:.2f} | "
            f"Fraud avg: ${STATS['fraud_amt_mean']:.2f} | "
            f"Fraud p95: ${STATS['fraud_amt_p95']:.2f} | "
            f"Legit avg: ${STATS['legit_amt_mean']:.2f} | "
            f"Risk: {risk}")

def check_email_domain_risk(STATS, email_domain: str) -> str:
    """Check historical fraud rate for a given email domain."""
    info = STATS["domain_rates"].get(str(email_domain))
    if not info:
        return f"No data for domain: {email_domain} — treat as UNKNOWN"
    fraud_rate = info["rate"] * 100
    risk = "HIGH" if fraud_rate > 10 else "MEDIUM" if fraud_rate > 5 else "LOW"
    return (f"Domain: {email_domain} | "
            f"Transactions: {info['n']} | "
            f"Fraud rate: {fraud_rate:.1f}% | "
            f"Risk: {risk}")

def get_similar_fraud_cases(df, STATS, amount: str, product_code: str) -> str:
    """Find historical fraud cases similar by amount and product code."""
    try:
        amt = float(amount)
    except ValueError:
        return f"Invalid amount: {amount}"
    similar = df[
        (df.isFraud == 1) &
        (df.ProductCD == product_code) &
        (df.TransactionAmt.between(amt * 0.7, amt * 1.3))
    ]
    if len(similar) == 0:
        return f"No similar fraud cases for Product={product_code} Amount~${amt:.2f}"
    return (f"Similar fraud cases: {len(similar)} | "
            f"Product: {product_code} | "
            f"Avg fraud amount: ${similar.TransactionAmt.mean():.2f} | "
            f"Product fraud rate: {STATS['product_rates'].get(product_code,0)*100:.1f}% | "
            f"Risk signal: ELEVATED")


def get_tools_schema():
    return [
        {"type": "function", "function": {
            "name": "lookup_transaction",
            "description": "Look up a transaction by ID and return full details.",
            "parameters": {"type": "object",
                "properties": {"transaction_id": {"type": "string"}},
                "required": ["transaction_id"]}}},
        {"type": "function", "function": {
            "name": "check_amount_risk",
            "description": "Check if transaction amount is statistically high risk.",
            "parameters": {"type": "object",
                "properties": {"amount": {"type": "string"}},
                "required": ["amount"]}}},
        {"type": "function", "function": {
            "name": "check_email_domain_risk",
            "description": "Check historical fraud rate for an email domain.",
            "parameters": {"type": "object",
                "properties": {"email_domain": {"type": "string"}},
                "required": ["email_domain"]}}},
        {"type": "function", "function": {
            "name": "get_similar_fraud_cases",
            "description": "Find historical fraud cases by amount and product code.",
            "parameters": {"type": "object",
                "properties": {
                    "amount"       : {"type": "string"},
                    "product_code" : {"type": "string"}},
                "required": ["amount", "product_code"]}}},
    ]
