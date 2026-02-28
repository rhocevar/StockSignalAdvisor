"""Rate limiter singleton used by API routes.

Uses SlowAPI (Starlette-compatible wrapper around the `limits` library).
The key function reads the real client IP from the X-Forwarded-For header,
which AWS App Runner's load balancer sets. Falls back to the direct socket
address for local development where no proxy is present.

Two-tier rate limiting for the /signal endpoint:
  - Uncached requests (hit the LLM): 5 per minute per IP
  - Cached requests (memory lookup): unlimited
"""

from threading import Lock

from cachetools import TTLCache
from fastapi import HTTPException, Request
from slowapi import Limiter

_UNCACHED_LIMIT_PER_MIN = 5

# TTL of 60 seconds means each IP's counter resets naturally after a minute.
_uncached_counter: TTLCache = TTLCache(maxsize=10_000, ttl=60)
_counter_lock = Lock()


def _get_real_ip(request: Request) -> str:
    """Return the real client IP, honouring proxy forwarding headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For may be a comma-separated list; the first entry is
        # the original client.
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_get_real_ip)


def check_uncached_rate_limit(request: Request) -> None:
    """Raise HTTP 429 if the calling IP has exceeded the uncached request limit."""
    ip = _get_real_ip(request)
    with _counter_lock:
        count = _uncached_counter.get(ip, 0) + 1
        _uncached_counter[ip] = count
    if count > _UNCACHED_LIMIT_PER_MIN:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a minute before requesting a new analysis.",
        )
