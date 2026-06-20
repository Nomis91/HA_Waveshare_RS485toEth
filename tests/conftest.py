"""Pytest configuration: makes the integration importable as a top-level package.

Pytest runs from the repo root, so we add ``custom_components`` to ``sys.path``
before any test collection. This mirrors what Home Assistant does at runtime
when it loads ``custom_components/<domain>``.
"""

from __future__ import annotations

import os
import sys

# Add <repo>/custom_components to sys.path so `import waveshare_eth2x` works.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
_CUSTOM_COMPONENTS = os.path.join(_REPO_ROOT, "custom_components")
if _CUSTOM_COMPONENTS not in sys.path:
    sys.path.insert(0, _CUSTOM_COMPONENTS)
