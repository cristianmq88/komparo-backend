"""
api/rate_limit.py — Rate limiter sencillo en memoria.

Limitaciones:
- No comparte estado entre procesos/workers (si Railway escala a >1 worker,
  cada uno tendrá su propio contador). Suficiente para v1.
- Para producción seria, sustituir por slowapi+Redis.
"""
from __future__ import annotations

import threading
from collections import defaultdict, deque
from time import monotonic
from typing import Deque

from fastapi import HTTPException, Request, status

_lock = threading.Lock()
_buckets: dict[str, Deque[float]] = defaultdict(deque)
_MAX_TRACKED_IPS = 10_000


def _client_ip(request: Request) -> str:
    # Si hay proxy delante (Railway), usar la cabecera X-Forwarded-For
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(
    request: Request,
    scope: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    """Limita por (IP, scope). Levanta 429 si se excede el cupo."""
    key = f"{scope}:{_client_ip(request)}"
    now = monotonic()
    cutoff = now - window_seconds

    with _lock:
        bucket = _buckets[key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= max_requests:
            retry_after = int(bucket[0] + window_seconds - now) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas peticiones, espera un momento antes de reintentar",
                headers={"Retry-After": str(max(retry_after, 1))},
            )
        bucket.append(now)

        # Evita crecer indefinidamente: si hay demasiadas IPs, descartamos las más viejas
        if len(_buckets) > _MAX_TRACKED_IPS:
            _evict_oldest()


def _evict_oldest() -> None:
    """Borra los buckets vacíos o más antiguos para liberar memoria."""
    to_delete = [k for k, v in _buckets.items() if not v]
    for k in to_delete[: len(to_delete) // 2 or 1]:
        _buckets.pop(k, None)


def reset() -> None:
    """Limpia todos los buckets (uso interno: tests)."""
    with _lock:
        _buckets.clear()
