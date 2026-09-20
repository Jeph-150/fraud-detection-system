def _score(scoring_client, amount, merchant="grocery", **features):
    return scoring_client.post(
        "/score",
        json={
            "transaction": {"id": "t", "account_id": "a", "amount": amount, "merchant": merchant},
            "features": features,
        },
    ).json()


def test_high_risk_transaction_is_flagged(scoring_client):
    body = _score(scoring_client, 9000.0, "crypto-exchange")
    assert body["is_flagged"] is True
    assert "large_amount" in body["reasons"]


def test_low_risk_transaction_not_flagged(scoring_client):
    assert _score(scoring_client, 20.0)["is_flagged"] is False


def test_velocity_burst_reason(scoring_client):
    assert "velocity_burst" in _score(scoring_client, 20.0, txn_count_1h=6)["reasons"]


def test_amount_spike_needs_history_and_deviation(scoring_client):
    baseline = dict(prior_count=10, prior_mean_amount=50.0, prior_std_amount=10.0)
    assert "amount_spike" in _score(scoring_client, 400.0, **baseline)["reasons"]
    assert "amount_spike" not in _score(scoring_client, 60.0, **baseline)["reasons"]
    assert "amount_spike" not in _score(scoring_client, 400.0)["reasons"]


def test_new_merchant_large_amount(scoring_client):
    known = _score(scoring_client, 1500.0, prior_count=3, merchant_seen_before=True)
    new = _score(scoring_client, 1500.0, prior_count=3, merchant_seen_before=False)
    assert "new_merchant_large_amount" not in known["reasons"]
    assert "new_merchant_large_amount" in new["reasons"]


def _paysim(scoring_client, type_, amount, old_org, new_org, old_dest, new_dest):
    return scoring_client.post(
        "/score",
        json={
            "transaction": {
                "id": "t", "account_id": "a", "amount": amount, "type": type_,
                "oldbalance_org": old_org, "newbalance_org": new_org,
                "oldbalance_dest": old_dest, "newbalance_dest": new_dest,
            }
        },
    ).json()


def test_drained_transfer_to_untouched_destination_is_flagged(scoring_client):
    body = _paysim(scoring_client, "TRANSFER", 181.0, 181.0, 0.0, 0.0, 0.0)
    assert body["is_flagged"] is True
    assert {"account_emptied", "dest_balance_untouched"} <= set(body["reasons"])


def test_ordinary_payment_not_flagged(scoring_client):
    body = _paysim(scoring_client, "PAYMENT", 9839.64, 170136.0, 160296.36, 0.0, 0.0)
    assert body["is_flagged"] is False


def test_paysim_rules_only_apply_to_transfer_and_cash_out(scoring_client):
    body = _paysim(scoring_client, "PAYMENT", 181.0, 181.0, 0.0, 0.0, 0.0)
    assert "account_emptied" not in body["reasons"]


def test_generic_rules_cannot_flag_on_their_own():
    from scoring.pipeline import FLAG_THRESHOLD
    from scoring.rules import GENERIC_RULES_CAP, evaluate_rules
    from shared.schemas import AccountFeatures, TransactionIn

    txn = TransactionIn(id="t", account_id="a", amount=9000.0, merchant="crypto-exchange")
    features = AccountFeatures(
        txn_count_1h=9, prior_count=10, prior_mean_amount=50.0, prior_std_amount=10.0
    )
    score, reasons = evaluate_rules(txn, features)
    assert len(reasons) >= 3
    assert score <= GENERIC_RULES_CAP < FLAG_THRESHOLD
