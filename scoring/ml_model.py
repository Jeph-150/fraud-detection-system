from pathlib import Path

import joblib

from scoring.ml_features import build_features
from shared.schemas import TransactionIn

MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"

_model = joblib.load(MODEL_PATH) if MODEL_PATH.exists() else None


def _fallback_score(transaction: TransactionIn) -> float:
    return min(transaction.amount / 10000.0, 1.0)


def predict(transaction: TransactionIn) -> float:
    # The model is trained on typed transactions with balances; without a type there is nothing to score on.
    if _model is None or transaction.type is None:
        return _fallback_score(transaction)
    features = build_features(
        transaction.type,
        transaction.amount,
        transaction.oldbalance_org,
        transaction.newbalance_org,
        transaction.oldbalance_dest,
        transaction.newbalance_dest,
    )
    return float(_model.predict_proba(features)[0][1])
