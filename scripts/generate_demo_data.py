"""Generate demo transactions and POST them to a running API instance."""

import random
import uuid

import httpx

API_URL = "http://localhost:8000/transactions"
MERCHANTS = ["coffee-shop", "electronics-store", "unknown", "crypto-exchange", "grocery"]


def random_transaction() -> dict:
    return {
        "id": str(uuid.uuid4()),
        "account_id": f"acct-{random.randint(1, 20)}",
        "amount": round(random.uniform(5, 8000), 2),
        "currency": "USD",
        "merchant": random.choice(MERCHANTS),
    }


def main(count: int = 20) -> None:
    with httpx.Client() as client:
        for _ in range(count):
            response = client.post(API_URL, json=random_transaction())
            print(response.status_code, response.json())


if __name__ == "__main__":
    main()
