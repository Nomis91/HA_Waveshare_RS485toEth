"""Smoke test: every subpackage of the integration must be importable.

This is the test that would have caught the original
``No module named '...coordinators.const'`` bug (broken relative import
``from .const`` inside ``coordinators/integration.py``).
"""

from __future__ import annotations

import importlib

import pytest


SUBMODULES = [
    "waveshare_eth2x",
    "waveshare_eth2x.const",
    "waveshare_eth2x.config_flow",
    "waveshare_eth2x.coordinators",
    "waveshare_eth2x.coordinators.integration",
    "waveshare_eth2x.core",
    "waveshare_eth2x.core.exceptions",
    "waveshare_eth2x.core.gateway",
    "waveshare_eth2x.core.protocol",
    "waveshare_eth2x.devices",
    "waveshare_eth2x.devices.base",
    "waveshare_eth2x.devices.deye_hybrid_gw4137",
    "waveshare_eth2x.devices.deye_sun_12k",
    "waveshare_eth2x.devices.deye_sun_6k",
    "waveshare_eth2x.devices.deye_sun_8k",
    "waveshare_eth2x.devices.generic_modbus",
    "waveshare_eth2x.devices.pytes_ebox_48100r",
    "waveshare_eth2x.devices.registry",
    "waveshare_eth2x.errors",
    "waveshare_eth2x.errors.tracker",
    "waveshare_eth2x.health",
    "waveshare_eth2x.health.monitor",
    "waveshare_eth2x.health.states",
    "waveshare_eth2x.platforms",
    "waveshare_eth2x.platforms.binary_sensor",
    "waveshare_eth2x.platforms.number",
    "waveshare_eth2x.platforms.select",
    "waveshare_eth2x.platforms.sensor",
]


@pytest.mark.parametrize("module_name", SUBMODULES)
def test_module_imports(module_name: str) -> None:
    """Every listed subpackage must be importable without raising."""
    importlib.import_module(module_name)
