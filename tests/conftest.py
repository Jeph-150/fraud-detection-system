import os
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mktemp(suffix='.db')}")

import httpx
import pytest
from fastapi.testclient import TestClient

from alerting.main import app as alerting_app
from ingestion.dedupe import dedupe_cache
from ingestion.main import app as ingestion_app
from ingestion.scoring_client import ScoringClient, get_scoring_client
from scoring.main import app as scoring_app
from shared.database import Base, engine


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    dedupe_cache._store.clear()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def scoring_client():
    return TestClient(scoring_app)


@pytest.fixture
def client(scoring_client):
    ingestion_app.dependency_overrides[get_scoring_client] = lambda: ScoringClient(
        scoring_client
    )
    yield TestClient(ingestion_app)
    ingestion_app.dependency_overrides.clear()


@pytest.fixture
def alerts_client():
    return TestClient(alerting_app)


@pytest.fixture
def unreachable_scoring_client():
    def _unreachable(request):
        raise httpx.ConnectError("scoring down")

    ingestion_app.dependency_overrides[get_scoring_client] = lambda: ScoringClient(
        httpx.Client(base_url="http://scoring", transport=httpx.MockTransport(_unreachable))
    )
    yield TestClient(ingestion_app)
    ingestion_app.dependency_overrides.clear()
