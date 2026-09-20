from fastapi import FastAPI

from scoring.pipeline import score_transaction
from shared.schemas import ScoreRequest, ScoreResult

app = FastAPI(title="Fraud Detection - Scoring Service")


@app.post("/score", response_model=ScoreResult)
def score(request: ScoreRequest):
    return score_transaction(request.transaction, request.features)


@app.get("/health")
def health():
    return {"status": "ok"}
