import httpx
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from ingestion.dedupe import dedupe_cache
from ingestion.features import compute_features
from ingestion.scoring_client import ScoringClient, get_scoring_client
from shared.database import get_db, init_db
from shared.models import Transaction
from shared.schemas import TransactionIn, TransactionOut

init_db()

app = FastAPI(title="Fraud Detection - Ingestion Service")


@app.post("/transactions", response_model=TransactionOut, status_code=201)
def ingest_transaction(
    transaction: TransactionIn,
    db: Session = Depends(get_db),
    scoring: ScoringClient = Depends(get_scoring_client),
):
    existing = db.get(Transaction, transaction.id)
    if existing:
        return existing

    if dedupe_cache.seen_recently(transaction.id):
        raise HTTPException(status_code=409, detail="duplicate transaction event")

    try:
        result = scoring.score(transaction, compute_features(db, transaction))
    except httpx.HTTPError:
        dedupe_cache.discard(transaction.id)
        raise HTTPException(status_code=503, detail="scoring service unavailable")

    record = Transaction(
        id=transaction.id,
        account_id=transaction.account_id,
        amount=transaction.amount,
        currency=transaction.currency,
        merchant=transaction.merchant,
        type=transaction.type,
        step=transaction.step,
        oldbalance_org=transaction.oldbalance_org,
        newbalance_org=transaction.newbalance_org,
        oldbalance_dest=transaction.oldbalance_dest,
        newbalance_dest=transaction.newbalance_dest,
        score=result.score,
        is_flagged=result.is_flagged,
        reasons=result.reasons,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/health")
def health():
    return {"status": "ok"}
