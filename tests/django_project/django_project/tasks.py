from __future__ import annotations

import time

from django_rabbitmq_oddjob import oddjob


@oddjob
def add(x: int, y: int, sleep: int = 0) -> dict[str, int]:
    if sleep:
        time.sleep(sleep)

    return {"x": x, "y": y, "sum": x + y}
