from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TransactionIn(BaseModel):
    id: str
    account_id: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    merchant: Optional[str] = None
    type: Optional[str] = None
    step: Optional[int] = Field(default=None, ge=0)
    oldbalance_org: Optional[float] = None
    newbalance_org: Optional[float] = None
    oldbalance_dest: Optional[float] = None
    newbalance_dest: Optional[float] = None


class AccountFeatures(BaseModel):
    txn_count_1h: int = 0
    txn_count_24h: int = 0
    prior_count: int = 0
    prior_mean_amount: float = 0.0
    prior_std_amount: float = 0.0
    merchant_seen_before: bool = False


class ScoreRequest(BaseModel):
    transaction: TransactionIn
    features: AccountFeatures = AccountFeatures()


class ScoreResult(BaseModel):
    score: float
    is_flagged: bool
    reasons: List[str] = []


class TransactionOut(BaseModel):
    id: str
    account_id: str
    amount: float
    currency: str
    merchant: Optional[str]
    type: Optional[str] = None
    step: Optional[int] = None
    oldbalance_org: Optional[float] = None
    newbalance_org: Optional[float] = None
    oldbalance_dest: Optional[float] = None
    newbalance_dest: Optional[float] = None
    score: float
    is_flagged: bool
    reasons: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Stats(BaseModel):
    total: int
    flagged: int
    flag_rate: float
