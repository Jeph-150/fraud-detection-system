from scoring.ml_model import predict
from scoring.rules import evaluate_rules
from shared.schemas import AccountFeatures, ScoreResult, TransactionIn

FLAG_THRESHOLD = 0.6


def score_transaction(transaction: TransactionIn, features: AccountFeatures) -> ScoreResult:
    rule_score, reasons = evaluate_rules(transaction, features)
    ml_score = predict(transaction)
    # Either detector being confident is enough to flag; averaging would let a sure model be diluted by quiet rules.
    combined_score = max(rule_score, ml_score)

    if ml_score >= 0.6:
        reasons.append("ml_high_risk")

    return ScoreResult(
        score=combined_score,
        is_flagged=combined_score >= FLAG_THRESHOLD,
        reasons=reasons,
    )
