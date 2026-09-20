import statistics
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from shared.models import Transaction
from shared.schemas import AccountFeatures, TransactionIn

HISTORY_LIMIT = 200


def compute_features(db: Session, transaction: TransactionIn) -> AccountFeatures:
    history = (
        db.query(Transaction)
        .filter(Transaction.account_id == transaction.account_id)
        .order_by(Transaction.created_at.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    if not history:
        return AccountFeatures()

    amounts = [t.amount for t in history]
    txn_count_1h, txn_count_24h = _recent_counts(history, transaction)

    return AccountFeatures(
        txn_count_1h=txn_count_1h,
        txn_count_24h=txn_count_24h,
        prior_count=len(history),
        prior_mean_amount=statistics.fmean(amounts),
        prior_std_amount=statistics.pstdev(amounts),
        merchant_seen_before=transaction.merchant is not None
        and any(t.merchant == transaction.merchant for t in history),
    )


def _recent_counts(history, transaction: TransactionIn):
    # Replayed datasets carry their own clock (PaySim `step` = one simulated hour); wall-clock
    # time would make every replayed transaction look like it happened seconds ago.
    if transaction.step is not None:
        steps = [t.step for t in history if t.step is not None]
        return (
            sum(1 for s in steps if s == transaction.step),
            sum(1 for s in steps if transaction.step - 24 < s <= transaction.step),
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(hours=24)
    return (
        sum(1 for t in history if _naive(t.created_at) >= one_hour_ago),
        sum(1 for t in history if _naive(t.created_at) >= one_day_ago),
    )


def _naive(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value
