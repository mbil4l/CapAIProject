#!/usr/bin/env python3
"""
Measure what one /submit costs — seconds of compute, from the service's own
telemetry, not from a docs page.

    python measure_cost.py            # writes to logs/ (the kept run record)

Starts the service fresh (so the first request really is cold), sends one cold
request and ten warm ones with different creator_ids, then reads
`requests.jsonl` back and averages the warm ones.

The API cost of a run is $0.00 by construction: nothing here calls a hosted
service. The real cost is compute time on this machine.
"""

import statistics
import sys

import requests

import config
import servectl
import telemetry

PORT = 5056
TEXT = (
    "Last weekend my brother and I drove to the lake. We had planned to fish, "
    "but the wind was too strong, so we sat in the car and ate sandwiches "
    "instead. He told me about his new job. I told him about my exams. It was "
    "cold, and we forgot the blanket, but it was still a good day. On the way "
    "home we stopped for gas and he bought me a coffee. I want to go back in "
    "the spring when it is warmer and the water is calm."
)


def main():
    before = len(telemetry.read_records())
    proc, _ = servectl.start(PORT, out_path=config.LOG_DIR / "server_stdout.txt")
    try:
        ready = servectl.wait_ready(PORT, proc)
        print(f"service answered /health after {ready:.1f}s (model not yet loaded)")
        for i in range(11):
            r = requests.post(f"http://127.0.0.1:{PORT}/submit",
                              json={"text": TEXT, "creator_id": f"cost_{i}"}, timeout=120)
            print(i, r.status_code, r.headers.get("X-Request-Id"))
    finally:
        servectl.stop(proc)

    rows = telemetry.read_records()[before:]
    cold, warm = rows[0], rows[1:]
    dur = [r["duration_ms"] for r in warm]
    cpu = [r["cpu_ms"] for r in warm]
    print(f"\ncold request : {cold['duration_ms']:.0f} ms wall, {cold['cpu_ms']:.0f} ms cpu")
    print(f"warm requests: n={len(warm)}  mean {statistics.mean(dur):.0f} ms wall, "
          f"{statistics.mean(cpu):.0f} ms cpu  (min {min(dur):.0f}, max {max(dur):.0f})")
    print("API spend per run: $0.00 (no hosted service is called)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
