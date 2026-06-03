"""Wrapper that adds a health check, Cache-Control headers, and a required
``x-openbb-user`` gate to the OpenBB BLS API.
"""

import os
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse
from openbb_platform_api.main import app, launch_api
from starlette.middleware.base import BaseHTTPMiddleware

PORT = int(os.environ.get("PORT", "6969"))

CACHE_PATHS = {"/api/v1/bls"}
MAX_AGE = int(os.environ.get("OPENBB_BLS_CACHE_TTL", "21600"))  # default 6 hours

STATIC_DIR = Path(__file__).parent / "openbb_bls" / "assets" / "static"
PUBLIC_STATIC_FILES = {
    "openbb-logo.png": ("openbb-logo.png", "image/png"),
    "bls-empsit-3.png": ("bls-empsit-3.png", "image/png"),
    "bls-empsit-4.png": ("bls-empsit-4.png", "image/png"),
    "bls-ppi-2.png": ("bls-ppi-2.png", "image/png"),
    "bls-productivity-1.png": ("bls-productivity-1.png", "image/png"),
}


@app.middleware("http")
async def add_cache_control(request, call_next):
    """Add a long-lived Cache-Control header to BLS data responses."""
    response = await call_next(request)
    if (
        request.method == "GET"
        and response.status_code == 200
        and any(request.url.path.startswith(p) for p in CACHE_PATHS)
    ):
        response.headers["Cache-Control"] = f"public, max-age={MAX_AGE}"
    return response


class RequireOpenBBUserMiddleware(BaseHTTPMiddleware):
    """Gate the API behind the ``x-openbb-user`` header (with exemptions)."""

    _EXEMPT_PATHS = {"/health", "/", "/widgets.json", "/apps.json"}
    _EXEMPT_PREFIXES = ("/static/",)

    async def dispatch(self, request: Request, call_next):
        """Reject requests that lack the ``x-openbb-user`` header."""
        if (
            request.method == "OPTIONS"
            or request.url.path in self._EXEMPT_PATHS
            or any(request.url.path.startswith(p) for p in self._EXEMPT_PREFIXES)
        ):
            return await call_next(request)
        if not request.headers.get("x-openbb-user"):
            return JSONResponse(
                status_code=403, content={"detail": "Missing required header."}
            )
        return await call_next(request)


app.add_middleware(RequireOpenBBUserMiddleware)


@app.get("/health")
async def health():
    """Liveness probe used by the container health check."""
    return {"status": "ok"}


@app.get("/static/{filename}")
def serve_static(filename: str):
    """Serve a whitelisted static asset from ``openbb_bls/assets/static``."""
    entry = PUBLIC_STATIC_FILES.get(filename)
    if entry is None:
        return JSONResponse({"detail": "Not found"}, status_code=404)
    name, media_type = entry
    return FileResponse(STATIC_DIR / name, media_type=media_type)


if __name__ == "__main__":
    launch_api(host="0.0.0.0", port=PORT)  # noqa: S104
