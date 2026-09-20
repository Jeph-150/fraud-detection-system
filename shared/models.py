from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String
from sqlalchemy.sql import func

from shared.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    account_id = Column(String, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="USD")
    merchant = Column(String, nullable=True)
    type = Column(String, nullable=True)
    step = Column(Integer, nullable=True)
    oldbalance_org = Column(Float, nullable=True)
    newbalance_org = Column(Float, nullable=True)
    oldbalance_dest = Column(Float, nullable=True)
    newbalance_dest = Column(Float, nullable=True)
    score = Column(Float, nullable=False)
    is_flagged = Column(Boolean, nullable=False, default=False)
    reasons = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
