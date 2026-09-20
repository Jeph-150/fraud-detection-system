# Fraud Detection System

Real-time transaction fraud detection, built and evaluated on the public
[PaySim](https://www.kaggle.com/datasets/mtalaltariq/paysim-data) dataset.

Three small FastAPI services share one SQLite database, and an nginx container serves a dashboard on top:

| Service | Port | Endpoints | Role |
|---|---|---|---|
| `ingestion/` | 8000 | `POST /transactions` | dedupes, computes account features, calls scoring, stores the result |
| `scoring/` | 8001 | `POST /score` | rules + ML model, returns a score, flag, and reasons |
| `alerting/` | 8002 | `GET /alerts`, `GET /stats` | lists flagged transactions (newest first, optional `?limit=`), plus processed/flagged totals |
| `dashboard/` | 8080 | static page | nginx serving a page that polls the alerting API every 5s |

## How scoring works

A transaction gets two scores, and the final score is `max(rule score, ML score)`.
It is flagged at 0.6 or above.

- **ML score:** a gradient-boosted classifier trained on PaySim (`scripts/train_model.py`).
  Features are the transaction type, amount, the four balances, and balance-difference checks.
- **Rule score:** readable checks that supply the `reasons`. The PaySim rules
  (`account_emptied`, `dest_balance_untouched`, only for `TRANSFER`/`CASH_OUT`) can flag
  together. The generic rules (large amount, risky merchant, velocity burst, amount spike,
  new merchant) are capped below the threshold, so they add reasons but can't flag alone.
- Without `scoring/model.pkl`, or for a transaction with no `type`, the ML score falls back to
  `amount / 10000`.

`amount` must be greater than 0; the API rejects zero-amount requests with a 422.

## Setup

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Data and model

Download PaySim from Kaggle (free account required) and save it as `data/raw/paysim.csv`.
`data/` is git-ignored.

```bash
python scripts/train_model.py     # writes scoring/model.pkl, prints held-out metrics
```

Training uses steps 1-600 and reports metrics on the later steps only.

## Run

Locally, one terminal per service:

```bash
uvicorn scoring.main:app --port 8001
SCORING_SERVICE_URL=http://localhost:8001 uvicorn ingestion.main:app --port 8000
uvicorn alerting.main:app --port 8002
```

Or `docker compose up --build`, then open http://localhost:8080 for the dashboard (run the replay below to populate it).

Replay PaySim through the running system and see how many frauds it catches:

```bash
python scripts/replay_paysim.py --limit 5000
curl localhost:8002/alerts
```

## Results

On the held-out later steps (103,565 accepted rows, 1,592 fraud): 1,592 caught, 1 false alarm.
A 5,000-row live replay caught 136 of 136 fraud with 0 false alarms, at about 5 ms per request.

**Read these numbers with care.** PaySim is synthetic and its fraud follows a very regular
pattern (draining an account into an untouched destination), so metrics this clean will not
carry over to real transactions. Its 16 zero-amount `CASH_OUT` rows are all fraud and are
rejected by the API, so they are never scored.

## Test

```bash
pytest
```

## License

MIT, see [LICENSE](LICENSE).
