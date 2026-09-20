"""Feature construction shared by training (scripts/train_model.py) and inference (scoring/ml_model.py)."""

import numpy as np

TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
FEATURE_NAMES = (
    [f"type_{t}" for t in TYPES]
    + ["amount", "oldbalance_org", "newbalance_org", "oldbalance_dest", "newbalance_dest"]
    + ["error_balance_org", "error_balance_dest", "org_emptied"]
)


def build_features(type_, amount, oldbalance_org, newbalance_org, oldbalance_dest, newbalance_dest):
    """Accepts scalars or equal-length array-likes; returns an (n, len(FEATURE_NAMES)) matrix.

    Missing balances (None/NaN) are treated as 0, matching how the fields are optional at the API.
    """
    type_ = np.atleast_1d(np.asarray(type_, dtype=object))
    amount, oo, no, od, nd = (
        np.nan_to_num(np.atleast_1d(np.asarray(v, dtype=float)))
        for v in (amount, oldbalance_org, newbalance_org, oldbalance_dest, newbalance_dest)
    )
    one_hot = np.stack([(type_ == t).astype(float) for t in TYPES], axis=1)
    error_org = no + amount - oo
    error_dest = od + amount - nd
    emptied = ((no == 0) & (oo > 0)).astype(float)
    numeric = np.stack([amount, oo, no, od, nd, error_org, error_dest, emptied], axis=1)
    return np.hstack([one_hot, numeric])
