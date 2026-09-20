# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Fraud detection system built on the public PaySim dataset: three FastAPI services (ingestion, scoring, alerting) share one SQLite database. Ingestion dedupes events, computes account features, calls scoring, and persists the result; alerting exposes flagged transactions. The project aims to stay lean and only use publicly available datasets.

## Commands

Setup:
```
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Run the services locally (one process each):
```
uvicorn scoring.main:app --port 8001
SCORING_SERVICE_URL=http://localhost:8001 uvicorn ingestion.main:app --port 8000
uvicorn alerting.main:app --port 8002
```

Run via Docker (not yet exercised against PaySim): `docker-compose up --build`

Run tests:
```
pytest
pytest tests/test_scoring.py::test_drained_transfer_to_untouched_destination_is_flagged   # single test
```

Train the model from `data/raw/paysim.csv` (writes `scoring/model.pkl`, prints held-out metrics; takes about a minute):
```
python scripts/train_model.py
```

Replay held-out PaySim rows through a running ingestion service and print caught/missed/false-alarm counts:
```
python scripts/replay_paysim.py --limit 5000
```

## Architecture

- Each service is a top-level package with a `main.py` holding its endpoints: `ingestion/` (`POST /transactions`), `scoring/` (`POST /score`), `alerting/` (`GET /alerts`). Each also has a `/health` endpoint and its own Dockerfile.
- `shared/` is imported by all three: `schemas.py` (Pydantic request/response models, including `TransactionIn`), `models.py` (SQLAlchemy `Transaction` table), `database.py` (engine, `init_db`, `DATABASE_URL`, default `data/fraud.db`).
- `ingestion/main.py` flow: existing-id lookup -> dedupe cache (`ingestion/dedupe.py`, in-memory TTL) -> `ingestion/features.py` account features -> `ingestion/scoring_client.py` HTTP call to scoring -> persist. A scoring outage returns 503.
- `ingestion/features.py` computes velocity windows from the PaySim `step` (one step = one simulated hour) when the transaction has one, otherwise from wall-clock `created_at`.
- `scoring/pipeline.py` combines `scoring/rules.py` and `scoring/ml_model.py` as `max(rule_score, ml_score)` with `FLAG_THRESHOLD = 0.6`. Averaging was rejected because a confident model would be diluted by quiet rules.
- `scoring/rules.py` has two groups: PaySim rules (`account_emptied`, `dest_balance_untouched`, only for `TRANSFER`/`CASH_OUT`, 0.35 each so both are needed to flag) and generic rules (capped at `GENERIC_RULES_CAP` below the threshold so they can't flag alone). The rule score is the stronger group, not their sum; summing caused 21k false alarms.
- `scoring/ml_features.py` builds model features and is shared by `scripts/train_model.py` and `scoring/ml_model.py` so training and serving cannot drift. `ml_model.py` falls back to `amount / 10000` when `model.pkl` is missing or the transaction has no `type`.
- Data notes: PaySim fraud occurs only in `TRANSFER` and `CASH_OUT`. A balance-mismatch rule is backwards on this data (fraud has consistent balances), so don't add one. `TransactionIn.amount` must be `> 0` by design, so PaySim's 16 zero-amount fraud rows are rejected with a 422.
- `infra/aws/README.md` has ECS/Fargate notes and the SQLite-vs-RDS caveat for multi-task deployments.

## Conventions

- Type hints throughout; request/response contracts are Pydantic models in `shared/schemas.py`, not raw dicts.
- New transaction fields go on `TransactionIn`/`TransactionOut` and the `Transaction` table together; they are optional so the older payload shape keeps working. `create_all` does not alter existing tables, so delete any stale `data/fraud.db` (and the Docker `fraud-data` volume) after a schema change.
- Tests use `pytest` with FastAPI's `TestClient`; `tests/conftest.py` points the app at a temporary SQLite database and recreates tables per test via the `reset_db` fixture. Scoring tests pass whether or not `scoring/model.pkl` exists.
- `data/` and `scoring/model.pkl` are git-ignored.
- Commit messages follow Conventional Commits.
