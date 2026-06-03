"""Regenerate ``assets/ppi_wps_titles.json.gz`` from the BLS ``wp.series`` file."""

from __future__ import annotations

import gzip
import json
import urllib.request
from pathlib import Path

from openbb_bls.utils.constants import BLS_USER_AGENT

_SOURCE_URL = "https://download.bls.gov/pub/time.series/wp/wp.series"
_ASSET = Path(__file__).resolve().parent.parent / "assets" / "ppi_wps_titles.json.gz"
_PREFIX = "PPI Commodity data for "
_SUFFIXES = (", seasonally adjusted", ", not seasonally adjusted")


def _clean(title: str) -> str:
    """Strip the boilerplate prefix/suffix from a series title."""
    if title.startswith(_PREFIX):
        title = title[len(_PREFIX) :]
    for suffix in _SUFFIXES:
        if title.endswith(suffix):
            return title[: -len(suffix)]
    return title


def build_map() -> dict[str, str]:
    """Fetch ``wp.series`` and return ``{series_id: cleaned title}``."""
    req = urllib.request.Request(_SOURCE_URL, headers={"User-Agent": BLS_USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        lines = resp.read().decode("utf-8", "replace").splitlines()

    header = [h.strip() for h in lines[0].split("\t")]
    id_col, title_col = header.index("series_id"), header.index("series_title")

    out: dict[str, str] = {}
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) <= max(id_col, title_col):
            continue
        series_id = parts[id_col].strip()
        if series_id:
            out.setdefault(series_id, _clean(parts[title_col].strip()))
    return out


def main() -> None:
    """Write the gzipped title map to the assets directory."""
    mapping = build_map()
    blob = json.dumps(mapping, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    _ASSET.write_bytes(gzip.compress(blob, 9))
    print(f"Wrote {len(mapping)} WPS titles to {_ASSET} ({_ASSET.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
