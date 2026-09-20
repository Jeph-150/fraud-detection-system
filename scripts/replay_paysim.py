"""Replay PaySim transactions, in time order, through a running ingestion service and score the result.

By default replays only steps after the model's training cutoff, so the summary reflects data the
model has never seen. Requires the ingestion and scoring services to be running.

Usage: python scripts/replay_paysim.py [--limit 5000] [--from-step 601] [--url http://localhost:8000]
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.train_model import TRAIN_MAX_STEP  # noqa: E402


def to_payload(index: int, row) -> dict:
    return {
        "id": f"ps-{index}",  # PaySim has no id column; the CSV row index is stable across runs
        "account_id": row.nameOrig,
        "amount": row.amount,
        "merchant": row.nameDest if row.nameDest.startswith("M") else None,
        "type": row.type,
        "step": int(row.step),
        "oldbalance_org": row.oldbalanceOrg,
        "newbalance_org": row.newbalanceOrig,
        "oldbalance_dest": row.oldbalanceDest,
        "newbalance_dest": row.newbalanceDest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "data" / "raw" / "paysim.csv"))
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--from-step", type=int, default=TRAIN_MAX_STEP + 1)
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    df = df[df["step"] >= args.from_step].sort_values("step", kind="stable").head(args.limit)

    tp = fp = fn = tn = rejected = rejected_fraud = errors = 0
    latencies_ms = []
    with httpx.Client(base_url=args.url, timeout=10.0) as client:
        for row in df.itertuples():
            start = time.perf_counter()
            response = client.post("/transactions", json=to_payload(row.Index, row))
            latencies_ms.append((time.perf_counter() - start) * 1000)

            if response.status_code == 422:
                rejected += 1
                rejected_fraud += int(row.isFraud)
            elif response.status_code != 201:
                errors += 1
            else:
                flagged = response.json()["is_flagged"]
                if row.isFraud:
                    tp, fn = tp + flagged, fn + (not flagged)
                else:
                    fp, tn = fp + flagged, tn + (not flagged)

    scored = tp + fp + fn + tn
    latencies_ms.sort()
    print(f"replayed {len(df):,} rows from step {args.from_step}+ ({int(df['isFraud'].sum())} fraud)")
    print(f"scored:   {scored:,}   rejected by API (422): {rejected} ({rejected_fraud} were fraud)   errors: {errors}")
    print(f"caught:   {tp} / {tp + fn} fraud   missed: {fn}   false alarms: {fp}")
    if latencies_ms:
        p95 = latencies_ms[min(int(len(latencies_ms) * 0.95), len(latencies_ms) - 1)]
        print(f"latency:  mean {statistics.mean(latencies_ms):.1f} ms   p95 {p95:.1f} ms")


if __name__ == "__main__":
    main()
