
import pandas as pd
from config import CONFIG

def load_data():
    raw = pd.read_csv(CONFIG["data_path"])

    cols = ["TransactionID", "TransactionAmt", "ProductCD",
            "card4", "card6", "P_emaildomain", "isFraud"]
    df = raw[cols].dropna(subset=["TransactionID", "TransactionAmt", "isFraud"])
    df = df.fillna("unknown").reset_index(drop=True)
    df["TransactionID"] = df["TransactionID"].astype(int)

    print(f"Loaded {df.shape[0]} transactions | Fraud rate: {df.isFraud.mean()*100:.1f}%")
    return df

def balance_sample(df):
    fraud = df[df.isFraud == 1]
    legit = df[df.isFraud == 0]
    n     = min(CONFIG["sample_size"] // 2, len(fraud), len(legit))

    sample = pd.concat([
        fraud.sample(n, random_state=CONFIG["random_seed"]),
        legit.sample(n,  random_state=CONFIG["random_seed"]),
    ]).sample(frac=1, random_state=CONFIG["random_seed"]).reset_index(drop=True)

    print(f"Balanced sample: {len(sample)} | Fraud: {sample.isFraud.sum()} | Legit: {(sample.isFraud==0).sum()}")
    return sample

def compute_stats(df):
    stats = {
        "fraud_amt_mean" : df[df.isFraud==1]["TransactionAmt"].mean(),
        "fraud_amt_std"  : df[df.isFraud==1]["TransactionAmt"].std(),
        "fraud_amt_p95"  : df[df.isFraud==1]["TransactionAmt"].quantile(0.95),
        "legit_amt_mean" : df[df.isFraud==0]["TransactionAmt"].mean(),
        "legit_amt_std"  : df[df.isFraud==0]["TransactionAmt"].std(),
        "domain_rates"   : (
            df.groupby("P_emaildomain")["isFraud"]
            .agg(["mean", "count"])
            .rename(columns={"mean": "rate", "count": "n"})
            .to_dict("index")
        ),
        "product_rates"  : df.groupby("ProductCD")["isFraud"].mean().to_dict(),
    }
    print(f"Stats: fraud_avg=${stats['fraud_amt_mean']:.2f} legit_avg=${stats['legit_amt_mean']:.2f}")
    return stats
