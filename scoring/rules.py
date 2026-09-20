from typing import List, Tuple

from shared.schemas import AccountFeatures, TransactionIn

LARGE_AMOUNT_THRESHOLD = 5000.0
HIGH_RISK_MERCHANTS = {"unknown", "crypto-exchange"}
VELOCITY_BURST_1H = 5
MIN_HISTORY_FOR_BASELINE = 5
SPIKE_Z_SCORE = 3.0
NEW_MERCHANT_LARGE_AMOUNT = 1000.0

# PaySim fraud only occurs in these transaction types.
RISKY_TYPES = {"TRANSFER", "CASH_OUT"}
# Generic rules are weak signals: they add reasons and raise the score but must not flag on
# their own, so their total is capped below pipeline.FLAG_THRESHOLD.
GENERIC_RULES_CAP = 0.5
# Measured on PaySim TRANSFER/CASH_OUT rows: emptying the account catches 97.5% of fraud but
# only 0.7% of hits are fraud; an untouched destination balance is 70% fraud. Each alone stays
# below the flag threshold, and together they reach it.
ACCOUNT_EMPTIED_WEIGHT = 0.35
DEST_UNTOUCHED_WEIGHT = 0.35


def evaluate_rules(
    transaction: TransactionIn, features: AccountFeatures
) -> Tuple[float, List[str]]:
    generic_score, reasons = _generic_rules(transaction, features)
    paysim_score, paysim_reasons = _paysim_rules(transaction)
    # Take the stronger rule group rather than summing: adding a capped generic score to one weak
    # PaySim rule would cross the flag threshold and flag many legitimate transactions.
    return max(min(generic_score, GENERIC_RULES_CAP), paysim_score), reasons + paysim_reasons


def _paysim_rules(transaction: TransactionIn) -> Tuple[float, List[str]]:
    if transaction.type not in RISKY_TYPES:
        return 0.0, []

    score = 0.0
    reasons: List[str] = []
    old, new = transaction.oldbalance_org, transaction.newbalance_org
    if old is not None and new is not None and old > 0 and new == 0 and transaction.amount >= old:
        score += ACCOUNT_EMPTIED_WEIGHT
        reasons.append("account_emptied")

    if transaction.oldbalance_dest == 0 and transaction.newbalance_dest == 0:
        score += DEST_UNTOUCHED_WEIGHT
        reasons.append("dest_balance_untouched")

    return score, reasons


def _generic_rules(
    transaction: TransactionIn, features: AccountFeatures
) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    if transaction.amount >= LARGE_AMOUNT_THRESHOLD:
        score += 0.4
        reasons.append("large_amount")

    if transaction.merchant and transaction.merchant.lower() in HIGH_RISK_MERCHANTS:
        score += 0.3
        reasons.append("high_risk_merchant")

    if features.txn_count_1h >= VELOCITY_BURST_1H:
        score += 0.3
        reasons.append("velocity_burst")

    if features.prior_count >= MIN_HISTORY_FOR_BASELINE:
        std = max(features.prior_std_amount, 1.0)
        if transaction.amount > features.prior_mean_amount + SPIKE_Z_SCORE * std:
            score += 0.3
            reasons.append("amount_spike")

    if (
        features.prior_count > 0
        and transaction.merchant
        and not features.merchant_seen_before
        and transaction.amount >= NEW_MERCHANT_LARGE_AMOUNT
    ):
        score += 0.2
        reasons.append("new_merchant_large_amount")

    return score, reasons
