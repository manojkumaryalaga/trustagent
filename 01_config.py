
import os
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

for d in ["logs/audit", "logs/violations", "results/plots"]:
    Path(d).mkdir(parents=True, exist_ok=True)

CONFIG = {
    "model"                : "gpt-4o-mini",
    "temperature"          : 0,
    "max_iterations"       : 8,
    "strict_mode"          : True,
    "confidence_threshold" : 0.75,
    "data_path"            : "data/train_transaction.csv",
    "sample_size"          : 500,
    "random_seed"          : 42,
}
