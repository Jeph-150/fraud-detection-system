"""Train the fraud classifier on the PaySim CSV and save it to scoring/model.pkl.

Splits by time (`step`) rather than randomly so the reported metrics come from data
that is strictly later than anything the model trained on.

Usage: python scripts/train_model.py [--data data/raw/paysim.csv] [--output scoring/model.pkl]
"""

import argparse
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, confusion_matrix, precision_score, recall_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scoring.ml_features import build_features  # noqa: E402

TRAIN_MAX_STEP = 600  # PaySim spans steps 1-743 (one step = one simulated hour)


def to_features(df: pd.DataFrame):
    return build_features(
        df["type"].to_numpy(),
        df["amount"].to_numpy(),
        df["oldbalanceOrg"].to_numpy(),
        df["newbalanceOrig"].to_numpy(),
        df["oldbalanceDest"].to_numpy(),
        df["newbalanceDest"].to_numpy(),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=str(ROOT / "data" / "raw" / "paysim.csv"))
    parser.add_argument("--output", default=str(ROOT / "scoring" / "model.pkl"))
    args = parser.parse_args()

    df = pd.read_csv(args.data)
    train, test = df[df["step"] <= TRAIN_MAX_STEP], df[df["step"] > TRAIN_MAX_STEP]
    print(f"train: {len(train):,} rows ({int(train['isFraud'].sum()):,} fraud)")
    print(f"test:  {len(test):,} rows ({int(test['isFraud'].sum()):,} fraud)")

    model = HistGradientBoostingClassifier(class_weight="balanced", random_state=42)
    model.fit(to_features(train), train["isFraud"])

    proba = model.predict_proba(to_features(test))[:, 1]
    y_true = test["isFraud"].to_numpy()
    print(f"\nPR-AUC on held-out later steps: {average_precision_score(y_true, proba):.4f}")
    for threshold in (0.5, 0.8, 0.95):
        pred = proba >= threshold
        tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()
        print(
            f"threshold {threshold}: precision={precision_score(y_true, pred):.3f} "
            f"recall={recall_score(y_true, pred):.3f}  caught={tp} missed={fn} false_alarms={fp}"
        )

    joblib.dump(model, args.output)
    print(f"\nSaved model to {args.output}")


if __name__ == "__main__":
    main()
