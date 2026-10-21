"""Simple in‑memory cache helpers for the demo backend.
We use functools.lru_cache with a small maxsize; the cache is cleared
whenever a sync operation mutates data (sync_all, sync_provider, resource
updates). This gives a ~3‑level speed boost for repeated read‑only API
calls without adding external dependencies.
"""
import functools
from typing import Any, Callable

def cached(func: Callable) -> Callable:
    """Wrap a function with an LRU cache of size 128.
    The wrapper provides a ``clear_cache`` attribute to invalidate the
    cache when data changes.
    """
    wrapper = functools.lru_cache(maxsize=128)(func)
    wrapper.clear_cache = wrapper.cache_clear  # expose for callers
    return wrapper
