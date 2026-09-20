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
