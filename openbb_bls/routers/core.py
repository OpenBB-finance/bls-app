"""BLS Core (Calendar) sub-router."""

from openbb_core.app.model.command_context import CommandContext
from openbb_core.app.model.example import APIEx
from openbb_core.app.model.obbject import OBBject
from openbb_core.app.provider_interface import (
    ExtraParams,
    ProviderChoices,
    StandardParams,
)
from openbb_core.app.query import Query as OBBQuery
from openbb_core.app.router import Router

from openbb_bls import ECONOMY_INSTALLED

router = Router(prefix="", description="BLS Core (Calendar) router.")


if not ECONOMY_INSTALLED:

    @router.command(
        model="BlsEconomicCalendar",
        examples=[
            APIEx(
                description="Current-month BLS release schedule.",
                parameters={"provider": "bls"},
            ),
            APIEx(
                description="Filter releases to a specific name across a window.",
                parameters={
                    "provider": "bls",
                    "start_date": "2026-04-01",
                    "end_date": "2026-06-30",
                    "release": "Employment Situation",
                },
            ),
        ],
    )
    async def calendar(
        cc: CommandContext,
        provider_choices: ProviderChoices,
        standard_params: StandardParams,
        extra_params: ExtraParams,
    ) -> OBBject:
        """BLS Release Calendar."""
        return await OBBject.from_query(OBBQuery(**locals()))
