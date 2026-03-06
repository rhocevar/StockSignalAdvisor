import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import StockAnalysisOrchestrator
from app.models.request import AnalyzeRequest
from app.models.response import AnalyzeResponse
from app.providers.llm.base import LLMRateLimitError
from app.services.cache import get_cached
from app.services.limiter import check_uncached_rate_limit, refund_uncached_rate_limit

# Both endpoints share the same orchestrator instance and cache.
#
# POST /signal  — kept for direct API access and Bruno testing; not used by the
#                 frontend (which uses the SSE stream endpoint below).
# GET  /signal/stream — used by the frontend; streams pillar events progressively.

logger = logging.getLogger(__name__)

router = APIRouter()

_orchestrator = StockAnalysisOrchestrator()


@router.post("/signal", response_model=AnalyzeResponse)
async def analyze_stock(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    # Short-circuit for cached tickers: cheap memory lookup, no LLM involved.
    cached = get_cached(body.ticker.upper())
    if cached is not None:
        result = cached.model_copy(deep=True)
        result.metadata.cached = True
        return result

    # Only uncached requests consume the rate limit (they will hit the LLM).
    check_uncached_rate_limit(request)
    try:
        return await _orchestrator.analyze(body)
    except ValueError as e:
        # Ticker not found — the LLM was never called, so refund the rate-limit
        # slot to avoid punishing users for typos.
        refund_uncached_rate_limit(request)
        raise HTTPException(status_code=404, detail=str(e))
    except LLMRateLimitError:
        raise HTTPException(
            status_code=429,
            detail="LLM provider rate limit exceeded. Please try again later.",
        )
    except Exception:
        logger.exception("Unexpected error analyzing %s", body.ticker)
        raise HTTPException(
            status_code=502,
            detail="Analysis service temporarily unavailable. Please try again.",
        )


@router.get("/signal/stream")
async def stream_signal(
    request: Request,
    ticker: str = Query(..., min_length=1, max_length=10),
) -> StreamingResponse:
    """Stream analysis results as Server-Sent Events.

    Emits pillar events (``technical``, ``fundamental``, ``sentiment``) as
    each completes, followed by a ``complete`` event with the full response.
    Errors are emitted as ``error`` events (HTTP headers are already committed
    once the stream opens, so status codes cannot change mid-stream).

    Cached tickers short-circuit before the stream opens and emit a single
    ``complete`` event immediately. Only uncached requests are counted against
    the rate limit.
    """
    upper = ticker.upper()

    # Short-circuit for cached tickers: emit a single complete event without
    # consuming the rate limit or opening a long-lived stream.
    cached = get_cached(upper)
    if cached is not None:
        result = cached.model_copy(deep=True)
        result.metadata.cached = True
        payload = json.dumps({"type": "complete", "data": result.model_dump(mode="json")})

        async def cached_generate():
            yield f"data: {payload}\n\n"

        return StreamingResponse(
            cached_generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Only uncached requests consume the rate limit (they will hit the LLM).
    try:
        check_uncached_rate_limit(request)
    except HTTPException as exc:
        err = {"type": "error", "data": {"code": exc.status_code, "message": exc.detail}}

        async def rate_limit_generate():
            yield f"data: {json.dumps(err)}\n\n"

        return StreamingResponse(
            rate_limit_generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    async def generate():
        try:
            async for event in _orchestrator.analyze_streaming(upper):
                payload = {"type": event.type, "data": event.data}
                yield f"data: {json.dumps(payload)}\n\n"
        except ValueError as e:
            # Ticker not found — refund the rate-limit slot (no LLM was called).
            refund_uncached_rate_limit(request)
            err = {"type": "error", "data": {"code": 404, "message": str(e)}}
            yield f"data: {json.dumps(err)}\n\n"
        except LLMRateLimitError:
            err = {"type": "error", "data": {"code": 429, "message": "LLM provider rate limit exceeded. Please try again later."}}
            yield f"data: {json.dumps(err)}\n\n"
        except Exception:
            logger.exception("Unexpected error streaming %s", ticker)
            err = {"type": "error", "data": {"code": 502, "message": "Analysis service temporarily unavailable."}}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
