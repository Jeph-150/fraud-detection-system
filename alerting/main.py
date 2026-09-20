from typing import List

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from shared.database import get_db, init_db
from shared.models import Transaction
from shared.schemas import TransactionOut

init_db()

app = FastAPI(title="Fraud Detection - Alerting Service")


@app.get("/alerts", response_model=List[TransactionOut])
def list_alerts(db: Session = Depends(get_db)):
    return (
        db.query(Transaction)
        .filter(Transaction.is_flagged.is_(True))
        .order_by(Transaction.created_at.desc())
        .all()
    )


@app.get("/health")
def health():
    return {"status": "ok"}
