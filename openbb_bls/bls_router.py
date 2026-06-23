"""BLS Router.

Thin assembly point that mounts one sub-router per survey topic. Each topic
lives in its own module under ``openbb_bls.routers`` so that the routes,
file-viewer choices/download endpoints, and chart packages for a survey are
co-located. Sub-routers are merged with no path prefix, so the public
``/bls/<command>`` routes are unchanged.
"""

from pathlib import Path

from openbb_core.app.router import Router

from openbb_bls.routers.ces import router as ces_router
from openbb_bls.routers.cpi import router as cpi_router
from openbb_bls.routers.ppi import router as ppi_router
from openbb_bls.routers.productivity import router as productivity_router

router = Router(prefix="", description="BLS provider router.")

for _subrouter in (
    cpi_router,
    ppi_router,
    ces_router,
    productivity_router,
):
    router.include_router(_subrouter)

_APPS_JSON = Path(__file__).parent / "assets" / "apps.json"
