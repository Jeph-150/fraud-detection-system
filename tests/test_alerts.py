def test_alerts_lists_flagged_transactions(client, alerts_client):
    high_risk_payload = {
        "id": "tx-100",
        "account_id": "acct-9",
        "amount": 9000.0,
        "currency": "USD",
        "merchant": "crypto-exchange",
    }
    client.post("/transactions", json=high_risk_payload)

    response = alerts_client.get("/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert any(a["id"] == "tx-100" for a in alerts)


def _post(client, i, amount, merchant="grocery"):
    client.post(
        "/transactions",
        json={"id": f"s-{i}", "account_id": "acct-s", "amount": amount, "merchant": merchant},
    )


def test_stats_counts_total_and_flagged(client, alerts_client):
    assert alerts_client.get("/stats").json() == {"total": 0, "flagged": 0, "flag_rate": 0.0}

    _post(client, 1, 20.0)
    _post(client, 2, 9000.0, "crypto-exchange")
    assert alerts_client.get("/stats").json() == {"total": 2, "flagged": 1, "flag_rate": 0.5}


def test_alerts_limit(client, alerts_client):
    for i in range(3):
        _post(client, i, 9000.0, "crypto-exchange")
    assert len(alerts_client.get("/alerts").json()) == 3
    assert len(alerts_client.get("/alerts?limit=2").json()) == 2
    assert alerts_client.get("/alerts?limit=0").status_code == 422


def test_cors_allows_dashboard_origin(alerts_client):
    response = alerts_client.get("/alerts", headers={"Origin": "http://localhost:8080"})
    assert response.headers["access-control-allow-origin"] == "http://localhost:8080"
