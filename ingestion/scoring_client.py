import os
from typing import Optional

import httpx

from shared.schemas import AccountFeatures, ScoreRequest, ScoreResult, TransactionIn


class ScoringClient:
    def __init__(self, client: httpx.Client):
        self._client = client

    def score(self, transaction: TransactionIn, features: AccountFeatures) -> ScoreResult:
        request = ScoreRequest(transaction=transaction, features=features)
        response = self._client.post("/score", json=request.model_dump())
        response.raise_for_status()
        return ScoreResult.model_validate(response.json())


_default_client: Optional[ScoringClient] = None


def get_scoring_client() -> ScoringClient:
    global _default_client
    if _default_client is None:
        base_url = os.getenv("SCORING_SERVICE_URL", "http://localhost:8001")
        _default_client = ScoringClient(httpx.Client(base_url=base_url, timeout=2.0))
    return _default_client
