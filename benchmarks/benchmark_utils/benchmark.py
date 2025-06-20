"""
Benchmarking wrappers
"""

import functools
import time
from typing import Any, Callable


# Time benchmarking
def timeit(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps
    def timed_function(*args, **kwargs) -> Any:
        start_s: float = time.perf_counter()
        # actual function call
        results: Any = func(*args, **kwargs)
        end_s: float = time.perf_counter()
        print(f"function: {func.__name__} took {end_s - start_s} s")
        return results

    return timed_function()
