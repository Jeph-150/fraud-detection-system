"""Measure end-to-end POST /transactions latency against a running ingestion service."""

import statistics
import sys
import time
import uuid

import httpx

INGESTION_URL = "http://localhost:8000"


def percentile(sorted_values, pct):
    index = min(int(len(sorted_values) * pct / 100), len(sorted_values) - 1)
    return sorted_values[index]


def main(count: int = 500) -> None:
    latencies_ms = []
    with httpx.Client(base_url=INGESTION_URL) as client:
        for i in range(count):
            payload = {
                "id": str(uuid.uuid4()),
                "account_id": f"acct-{i % 20}",
                "amount": 10.0 + (i % 9000),
                "merchant": "unknown" if i % 7 == 0 else "grocery",
            }
            start = time.perf_counter()
            response = client.post("/transactions", json=payload)
            latencies_ms.append((time.perf_counter() - start) * 1000)
            response.raise_for_status()

    latencies_ms.sort()
    print(f"requests: {count}")
    print(f"mean: {statistics.mean(latencies_ms):.1f} ms")
    print(f"p50:  {percentile(latencies_ms, 50):.1f} ms")
    print(f"p95:  {percentile(latencies_ms, 95):.1f} ms")
    print(f"p99:  {percentile(latencies_ms, 99):.1f} ms")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 500)
