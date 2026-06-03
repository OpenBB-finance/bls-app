"""Time-bounded in-process memoization."""

from __future__ import annotations

import os
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
from typing import Any

_TTL_ENV_VAR = "OPENBB_BLS_CACHE_TTL"
_FALLBACK_TTL_SECONDS = 6 * 60 * 60

_MISSING = object()

_REGISTRY: list[Callable] = []


def clear_all() -> None:
    """Clear every ``ttl_cache``-decorated function in the process."""
    for wrapper in _REGISTRY:
        wrapper.cache_clear()


def _default_ttl() -> float:
    """Return the configured default TTL in seconds."""
    raw = os.getenv(_TTL_ENV_VAR)
    if not raw:
        return _FALLBACK_TTL_SECONDS
    try:
        return float(raw)
    except ValueError:
        return _FALLBACK_TTL_SECONDS


def _make_key(args: tuple, kwargs: dict) -> Any:
    """Build a hashable cache key from arguments."""
    if not kwargs:
        return args
    return (args, tuple(sorted(kwargs.items())))


def ttl_cache(maxsize: int = 128, ttl: float | None = None) -> Callable:
    """Memoize a function for ``ttl`` seconds with LRU eviction at ``maxsize``."""

    def decorator(func: Callable) -> Callable:
        lock = threading.Lock()
        store: OrderedDict[Any, tuple[float, Any]] = OrderedDict()

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            effective_ttl = _default_ttl() if ttl is None else ttl
            if effective_ttl <= 0:
                return func(*args, **kwargs)

            key = _make_key(args, kwargs)
            now = time.monotonic()
            with lock:
                cached = store.get(key, _MISSING)
                if cached is not _MISSING:
                    stamped_at, value = cached
                    if now - stamped_at <= effective_ttl:
                        store.move_to_end(key)
                        return value
                    del store[key]

            value = func(*args, **kwargs)

            with lock:
                store[key] = (time.monotonic(), value)
                store.move_to_end(key)
                while len(store) > maxsize:
                    store.popitem(last=False)
            return value

        def cache_clear() -> None:
            """Drop all cached entries."""
            with lock:
                store.clear()

        wrapper.cache_clear = cache_clear
        _REGISTRY.append(wrapper)
        return wrapper

    return decorator
