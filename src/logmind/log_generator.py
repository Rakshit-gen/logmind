import argparse
import json
import random
from datetime import datetime, timedelta

SERVICES = ["checkout-api", "payments-api", "inventory-svc", "auth-svc", "email-worker"]
NORMAL_MESSAGES = [
    "request completed",
    "cache hit",
    "health check ok",
    "background job finished",
]
ERROR_SIGNATURES = {
    "checkout-api": "upstream payments-api returned 500",
    "payments-api": "connection pool exhausted",
}


def generate_incident_log(start: datetime, minutes: int, spike_service: str) -> list[dict]:
    """Build a synthetic log stream with a clear error spike in one service.

    The first third of the window is quiet, the middle third has a rising
    error rate in spike_service (and only that service), the last third
    tapers off, which is what a real "something just broke" window
    usually looks like.
    """
    rows = []
    spike_start = start + timedelta(minutes=minutes // 3)
    spike_end = start + timedelta(minutes=2 * minutes // 3)

    for offset in range(minutes * 60):
        ts = start + timedelta(seconds=offset)
        in_spike = spike_start <= ts <= spike_end

        for service in SERVICES:
            is_noisy = service == spike_service and in_spike
            error_chance = 0.4 if is_noisy else 0.01
            if random.random() < error_chance:
                level = "ERROR"
                message = ERROR_SIGNATURES.get(service, "unexpected error")
            else:
                level = "INFO"
                message = random.choice(NORMAL_MESSAGES)

            if level == "ERROR" or random.random() < 0.05:
                rows.append(
                    {
                        "timestamp": ts.isoformat(),
                        "service": service,
                        "level": level,
                        "message": message,
                    }
                )

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--minutes", type=int, default=30)
    parser.add_argument("--spike-service", default="checkout-api", choices=SERVICES)
    args = parser.parse_args()

    start = datetime.utcnow() - timedelta(minutes=args.minutes)
    rows = generate_incident_log(start, args.minutes, args.spike_service)

    with open(args.out, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")

    print(f"wrote {len(rows)} log lines to {args.out}")


if __name__ == "__main__":
    main()
