def test_ingest_transaction_returns_score(client):
    payload = {
        "id": "tx-1",
        "account_id": "acct-1",
        "amount": 100.0,
        "currency": "USD",
        "merchant": "coffee-shop",
    }
    response = client.post("/transactions", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "tx-1"
    assert "score" in body


def test_duplicate_transaction_id_is_idempotent(client):
    payload = {
        "id": "tx-2",
        "account_id": "acct-1",
        "amount": 50.0,
        "currency": "USD",
        "merchant": "grocery",
    }
    first = client.post("/transactions", json=payload)
    assert first.status_code == 201

    second = client.post("/transactions", json=payload)
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]


def test_rapid_transactions_trigger_velocity_burst(client):
    last = None
    for i in range(6):
        last = client.post(
            "/transactions",
            json={"id": f"burst-{i}", "account_id": "acct-burst", "amount": 25.0, "merchant": "grocery"},
        )
    assert "velocity_burst" in last.json()["reasons"]


def test_scoring_outage_returns_503_and_allows_retry(unreachable_scoring_client):
    payload = {"id": "tx-3", "account_id": "acct-1", "amount": 10.0}
    down = unreachable_scoring_client.post("/transactions", json=payload)
    assert down.status_code == 503

    from ingestion.dedupe import dedupe_cache

    assert dedupe_cache.seen_recently("tx-3") is False


def test_paysim_fields_round_trip(client):
    payload = {
        "id": "ps-1",
        "account_id": "C1305486145",
        "amount": 181.0,
        "type": "TRANSFER",
        "step": 1,
        "oldbalance_org": 181.0,
        "newbalance_org": 0.0,
        "oldbalance_dest": 0.0,
        "newbalance_dest": 0.0,
    }
    body = client.post("/transactions", json=payload).json()
    for field in ("type", "step", "oldbalance_org", "newbalance_org"):
        assert body[field] == payload[field]


def _post_at_step(client, i, step):
    return client.post(
        "/transactions",
        json={"id": f"v-{i}", "account_id": "acct-v", "amount": 20.0, "type": "PAYMENT", "step": step},
    ).json()


def test_velocity_uses_step_not_wall_clock(client):
    spread = [_post_at_step(client, i, step=i * 30) for i in range(7)]
    assert all("velocity_burst" not in t["reasons"] for t in spread)


def test_velocity_burst_within_one_step(client):
    burst = [_post_at_step(client, i, step=5) for i in range(7)]
    assert "velocity_burst" in burst[-1]["reasons"]
