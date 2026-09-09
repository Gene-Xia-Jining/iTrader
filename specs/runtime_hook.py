# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller runtime hook: stub scipy.stats to avoid bundling ~32M of scipy.

tqsdk/tafunc.py does `from scipy import stats` at module level, but the only
two usages (stats.norm.cdf / stats.norm.pdf) live inside private helpers
(_get_cdf / _get_pdf) that are only called by options-pricing functions.
The client never calls those, so we provide a mathematically equivalent stub
and exclude scipy from the bundle.
"""
import math
import sys
import types

import numpy as np

scipy = types.ModuleType("scipy")
stats = types.ModuleType("scipy.stats")


class _Norm:
    """Minimal replacement for scipy.stats.norm (cdf / pdf only)."""

    @staticmethod
    def cdf(x):
        arr = np.asarray(x, dtype=float)
        return 0.5 * (1.0 + np.vectorize(math.erf)(arr / math.sqrt(2.0)))

    @staticmethod
    def pdf(x):
        arr = np.asarray(x, dtype=float)
        return np.exp(-0.5 * arr * arr) / math.sqrt(2.0 * math.pi)


stats.norm = _Norm()
scipy.stats = stats
sys.modules["scipy"] = scipy
sys.modules["scipy.stats"] = stats
