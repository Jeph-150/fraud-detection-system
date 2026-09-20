import os
from typing import List, Optional

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.database import get_db, init_db
from shared.models import Transaction
from shared.schemas import Stats, TransactionOut

init_db()

app = FastAPI(title="Fraud Detection - Alerting Service")

# The dashboard is served from its own origin, so browsers need CORS to let it call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:8080").split(","),
    allow_methods=["GET"],
)


@app.get("/alerts", response_model=List[TransactionOut])
def list_alerts(limit: Optional[int] = Query(None, ge=1, le=1000), db: Session = Depends(get_db)):
    query = (
        db.query(Transaction)
        .filter(Transaction.is_flagged.is_(True))
        .order_by(Transaction.created_at.desc())
    )
    return query.limit(limit).all() if limit else query.all()


@app.get("/stats", response_model=Stats)
def stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Transaction.id)).scalar()
    flagged = (
        db.query(func.count(Transaction.id)).filter(Transaction.is_flagged.is_(True)).scalar()
    )
    return Stats(total=total, flagged=flagged, flag_rate=flagged / total if total else 0.0)


@app.get("/health")
def health():
    return {"status": "ok"}
