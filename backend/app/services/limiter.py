"""Rate limiter singleton used by API routes.

Uses SlowAPI (Starlette-compatible wrapper around the `limits` library).
The key function reads the real client IP from the X-Forwarded-For header,
which AWS App Runner's load balancer sets. Falls back to the direct socket
address for local development where no proxy is present.
"""

from fastapi import Request
from slowapi import Limiter


def _get_real_ip(request: Request) -> str:
    """Return the real client IP, honouring proxy forwarding headers."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For may be a comma-separated list; the first entry is
        # the original client.
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=_get_real_ip)
