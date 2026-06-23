"""BLS Productivity supplemental tables."""

from __future__ import annotations

from datetime import date as dateType
from typing import Any, Literal

from openbb_core.app.service.system_service import SystemService
from openbb_core.provider.abstract.data import Data
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.abstract.query_params import QueryParams
from openbb_core.provider.utils.descriptions import QUERY_DESCRIPTIONS
from openbb_core.provider.utils.errors import EmptyDataError
from pydantic import ConfigDict, Field

from openbb_bls.utils.productivity_tables import (
    _DATASET_FILE,
    _DATASET_LABELS,
    fetch_xlsx,
    parse_dataset,
)

ProductivityDataset = Literal[
    "major-sectors-quarterly",
    "major-sectors-annual",
    "major-sectors-business-cycles",
    "total-economy-hours-employment",
]

_DATASET_DEFAULT_FILTERS: dict[str, dict[str, str | None]] = {
    "major-sectors-quarterly": {
        "sector": "Nonfarm business sector",
        "measure": "Labor productivity",
        "units": "Index (2017=100)",
    },
    "major-sectors-annual": {
        "sector": "Nonfarm business sector",
        "measure": "Labor productivity",
        "units": "Index (2017=100)",
    },
    "major-sectors-business-cycles": {
        "sector": "Nonfarm business sector",
        "measure": "Labor productivity",
        "units": "Compound annual growth rate",
    },
    "total-economy-hours-employment": {
        "sector": "Total economy",
        "measure": "Hours worked",
        "units": "Billions of hours",
    },
}

_DATASET_FILTER_OPTIONS: dict[str, dict[str, tuple[str, ...]]] = {
    "major-sectors-quarterly": {
        "sector": (
            "Nonfarm business sector",
            "Business sector",
            "Nonfinancial corporate sector",
            "Manufacturing sector",
            "Durable manufacturing sector",
            "Nondurable manufacturing sector",
        ),
        "measure": (
            "Labor productivity",
            "Output per worker",
            "Sectoral output",
            "Real sectoral output",
            "Value-added output",
            "Real value-added output",
            "Hours worked",
            "Employment",
            "Average weekly hours",
            "Labor compensation",
            "Hourly compensation",
            "Real hourly compensation",
            "Unit labor costs",
            "Unit nonlabor costs",
            "Unit nonlabor payments",
            "Unit combined input costs",
            "Unit profits",
            "Nonlabor costs",
            "Nonlabor payments",
            "Labor share",
            "Profits",
            "Consumer price deflator",
            "Sectoral output price deflator",
            "Value-added output price deflator",
        ),
        "units": (
            "Index (2017=100)",
            "% Change from previous quarter",
            "% Change from previous year",
            "% Change same quarter 1 year ago",
            "Billions of current dollars",
            "Billions of hours",
            "Millions of jobs",
            "Current dollars per hour worked",
            "CPI-adjusted dollars per hour worked",
            "Hours worked per job per week",
            "Percentage",
        ),
    },
    "major-sectors-annual": {
        "sector": (
            "Nonfarm business sector",
            "Business sector",
            "Nonfinancial corporate sector",
            "Manufacturing sector",
            "Durable manufacturing sector",
            "Nondurable manufacturing sector",
        ),
        "measure": (
            "Labor productivity",
            "Output per worker",
            "Sectoral output",
            "Real sectoral output",
            "Value-added output",
            "Real value-added output",
            "Hours worked",
            "Employment",
            "Average weekly hours",
            "Labor compensation",
            "Hourly compensation",
            "Real hourly compensation",
            "Unit labor costs",
            "Unit nonlabor costs",
            "Unit nonlabor payments",
            "Unit combined input costs",
            "Unit profits",
            "Nonlabor costs",
            "Nonlabor payments",
            "Labor share",
            "Profits",
            "Consumer price deflator",
            "Sectoral output price deflator",
            "Value-added output price deflator",
        ),
        "units": (
            "Index (2017=100)",
            "% Change from previous quarter",
            "% Change from previous year",
            "% Change same quarter 1 year ago",
            "Billions of current dollars",
            "Billions of hours",
            "Millions of jobs",
            "Current dollars per hour worked",
            "CPI-adjusted dollars per hour worked",
            "Hours worked per job per week",
            "Percentage",
        ),
    },
    "major-sectors-business-cycles": {
        "sector": (
            "Nonfarm business sector",
            "Business sector",
            "Nonfinancial corporate sector",
            "Manufacturing sector",
            "Durable manufacturing sector",
            "Nondurable manufacturing sector",
        ),
        "measure": (
            "Labor productivity",
            "Output per worker",
            "Sectoral output",
            "Real sectoral output",
            "Value-added output",
            "Real value-added output",
            "Hours worked",
            "Employment",
            "Average weekly hours",
            "Labor compensation",
            "Hourly compensation",
            "Real hourly compensation",
            "Unit labor costs",
            "Unit nonlabor costs",
            "Unit nonlabor payments",
            "Unit combined input costs",
            "Unit profits",
            "Nonlabor costs",
            "Nonlabor payments",
            "Labor share",
            "Profits",
            "Consumer price deflator",
            "Sectoral output price deflator",
            "Value-added output price deflator",
        ),
        "units": ("Compound annual growth rate",),
    },
    "total-economy-hours-employment": {
        "sector": ("Total economy",),
        "measure": (
            "Hours worked",
            "Employment",
            "Average weekly hours",
            "Labor productivity",
            "Output per worker",
            "Value-added output",
            "Real value-added output",
            "Labor compensation",
            "Hourly compensation",
            "Real hourly compensation",
            "Unit labor costs",
        ),
        "units": (
            "Billions of hours",
            "Millions of jobs",
            "Hours worked per job per week",
            "Index",
            "% Change from previous quarter",
            "% Change from previous year",
            "Billions of current dollars",
            "Current dollars per hour worked",
            "CPI-adjusted dollars per hour worked",
            "Index (2017=100)",
        ),
    },
}


_HIDE: dict[str, Any] = {"x-widget_config": {"hide": True}}
# Chart roles for the AgGrid table-to-chart view: a numeric ``value`` series
# plotted over the ``date`` time axis, grouped by the category dimensions the
# user narrows with the dropdowns.
_TIME: dict[str, Any] = {"x-widget_config": {"chartDataType": "time"}}
_CATEGORY: dict[str, Any] = {"x-widget_config": {"chartDataType": "category"}}
_SERIES: dict[str, Any] = {
    "x-widget_config": {"cellDataType": "number", "chartDataType": "series"}
}


class BlsProductivityTablesQueryParams(QueryParams):
    """BLS Productivity Tables Query Parameters."""

    __json_schema_extra__ = {
        "dataset": {
            "x-widget_config": {
                "options": [
                    {"label": f"{key} — {label}", "value": key}
                    for key, label in _DATASET_LABELS.items()
                ],
                "style": {"popupWidth": 950},
            }
        },
        "sector": {
            "x-widget_config": {
                "type": "endpoint",
                "optionsEndpoint": "table_choices",
                "optionsParams": {
                    "dataset": "$dataset",
                    "parameter": "sector",
                },
                "style": {"popupWidth": 350},
            }
        },
        "measure": {
            "x-widget_config": {
                "type": "endpoint",
                "optionsEndpoint": "table_choices",
                "optionsParams": {
                    "dataset": "$dataset",
                    "parameter": "measure",
                    "sector": "$sector",
                },
                "style": {"popupWidth": 350},
            }
        },
        "units": {
            "x-widget_config": {
                "type": "endpoint",
                "optionsEndpoint": "table_choices",
                "optionsParams": {
                    "dataset": "$dataset",
                    "parameter": "units",
                    "sector": "$sector",
                    "measure": "$measure",
                },
                "style": {"popupWidth": 350},
            }
        },
    }

    dataset: ProductivityDataset = Field(
        default="major-sectors-quarterly",
        description="Productivity supplemental dataset to load.",
    )
    start_date: dateType | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS["start_date"],
    )
    end_date: dateType | None = Field(
        default=None,
        description=QUERY_DESCRIPTIONS["end_date"],
    )
    sector: str | None = Field(
        default=None,
        description="Sector to restrict the results. Defaults to the headline"
        " Nonfarm business sector; clear it to load every sector.",
    )
    measure: str | None = Field(
        default=None,
        description="Measure to restrict the results. Defaults to Labor"
        " productivity; clear it to load every measure.",
    )
    units: str | None = Field(
        default=None,
        description="Units to restrict the results. Defaults to the 2017=100"
        " index (one row per period); clear it to load every units basis. The"
        " source is long-form, so leaving every dimension open returns one row"
        " per sector / measure / units / period.",
    )


class BlsProductivityTablesData(Data):
    """One observation from a BLS Productivity supplemental dataset."""

    model_config = ConfigDict(
        json_schema_extra={
            "x-widget_config": {
                "$.name": "BLS Productivity Tables",
                "$.description": (
                    "BLS Productivity prod2 supplemental tables — "
                    "quarterly / annual / business-cycle labor "
                    "productivity for major sectors, plus total-economy "
                    "hours and employment."
                ),
                "$.gridData": {"w": 40, "h": 20},
                "$.refetchInterval": False,
                "$.source": ["BLS"],
                "$.category": "Economy",
                "$.subCategory": "Productivity",
                "table": {
                    "showAll": True,
                    "enableCharts": True,
                    "chartView": {"enabled": False, "chartType": "line"},
                },
            }
        }
    )

    date: dateType | None = Field(
        default=None,
        description="First-of-period date the observation applies to.",
        json_schema_extra=_TIME,
    )
    period_kind: str = Field(
        description="Period kind for the row (quarter, annual, or business cycle).",
        json_schema_extra=_CATEGORY,
    )
    year: int | None = Field(
        default=None,
        description="Year reported in the source XLSX.",
        json_schema_extra=_HIDE,
    )
    quarter: int | str | None = Field(
        default=None,
        description="Quarter index reported in the source XLSX.",
        json_schema_extra=_HIDE,
    )
    sector: str | None = Field(
        default=None,
        description="BLS sector this row belongs to.",
        json_schema_extra=_CATEGORY,
    )
    basis: str | None = Field(
        default=None,
        description="Worker-counting basis used for the row.",
        json_schema_extra=_CATEGORY,
    )
    component: str | None = Field(
        default=None,
        description="Sub-sector component for the total-economy workbook.",
        json_schema_extra=_CATEGORY,
    )
    measure: str = Field(
        description="Productivity measure being reported.",
        json_schema_extra=_CATEGORY,
    )
    units: str = Field(
        description="Units the value is expressed in.",
        json_schema_extra=_CATEGORY,
    )
    value: float | None = Field(
        default=None,
        description="Numeric observation.",
        json_schema_extra=_SERIES,
    )
    value_string: str | None = Field(
        default=None,
        description="Raw cell text when the value isn't numeric.",
        json_schema_extra=_HIDE,
    )
    cycle_period: str | None = Field(
        default=None,
        description="Business-cycle period label as published by BLS.",
        json_schema_extra=_CATEGORY,
    )
    cycle_start_date: dateType | None = Field(
        default=None,
        description="First-of-quarter start date for the business-cycle period.",
        json_schema_extra=_HIDE,
    )
    cycle_end_date: dateType | None = Field(
        default=None,
        description="First-of-quarter end date for the business-cycle period.",
        json_schema_extra=_HIDE,
    )
    row_index: int = Field(
        description="Sequential parser order preserving the source layout.",
        json_schema_extra=_HIDE,
    )
    table_id: str = Field(
        description="Stable dataset identifier.",
        json_schema_extra=_HIDE,
    )
    table_title: str = Field(
        description="Human-readable dataset title.",
        json_schema_extra=_HIDE,
    )
    source_file: str = Field(
        description="Filename of the source XLSX on bls.gov.",
        json_schema_extra=_HIDE,
    )
    release_date: dateType | None = Field(
        default=None,
        description="Release date stamped in the workbook header.",
    )


class BlsProductivityTablesFetcher(
    Fetcher[BlsProductivityTablesQueryParams, list[BlsProductivityTablesData]]
):
    """BLS Productivity Tables Fetcher."""

    require_credentials = False

    @staticmethod
    def transform_query(
        params: dict[str, Any],
    ) -> BlsProductivityTablesQueryParams:
        """Validate and coerce the query."""
        query = BlsProductivityTablesQueryParams(**params)
        defaults = _DATASET_DEFAULT_FILTERS.get(query.dataset, {})
        if "sector" not in params:
            query.sector = defaults.get("sector")
        if "measure" not in params:
            query.measure = defaults.get("measure")
        if "units" not in params:
            query.units = defaults.get("units")

        allowed = _DATASET_FILTER_OPTIONS.get(query.dataset, {})
        for key in ("sector", "measure", "units"):
            value = getattr(query, key)
            if value is None:
                continue
            if value not in set(allowed.get(key, ())):
                setattr(query, key, defaults.get(key))
        return query

    @staticmethod
    def extract_data(
        query: BlsProductivityTablesQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Download the chosen prod2 workbook and parse it long-form."""
        filename, _ = _DATASET_FILE[query.dataset]
        content = fetch_xlsx(filename)
        # Drop the "Level - not available" placeholder rows: they carry no value
        # and only inflate the table with apparent duplicates of each period.
        rows = [
            r
            for r in parse_dataset(content, query.dataset)
            if r.get("units") != "Level - not available"
        ]
        sector_filter = query.sector.strip().lower() if query.sector else None
        measure_filter = query.measure.strip().lower() if query.measure else None
        units_filter = query.units.strip().lower() if query.units else None
        start, end = query.start_date, query.end_date
        if (
            sector_filter is None
            and measure_filter is None
            and units_filter is None
            and start is None
            and end is None
        ):
            return rows
        out: list[dict[str, Any]] = []
        for r in rows:
            if (
                sector_filter is not None
                and (r.get("sector") or "").lower() != sector_filter
            ):
                continue
            if (
                measure_filter is not None
                and (r.get("measure") or "").lower() != measure_filter
            ):
                continue
            if (
                units_filter is not None
                and (r.get("units") or "").lower() != units_filter
            ):
                continue
            if start is not None or end is not None:
                row_date = r.get("date")
                if row_date is None:
                    continue
                if start is not None and row_date < start:
                    continue
                if end is not None and row_date > end:
                    continue
            out.append(r)
        return out

    @staticmethod
    def transform_data(
        query: BlsProductivityTablesQueryParams,
        data: list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[BlsProductivityTablesData]:
        """Coerce parsed rows into ``BlsProductivityTablesData``."""
        if not data:
            raise EmptyDataError(
                f"No rows matched the productivity tables query "
                f"(dataset={query.dataset!r})."
            )
        return [BlsProductivityTablesData.model_validate(r) for r in data]
