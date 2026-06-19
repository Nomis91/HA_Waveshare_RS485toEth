"""Deye Sun 6K inverter device definition (skeleton)."""

from typing import Dict

from ..const import (
    DEVICE_TYPE_DEYE_SUN_6K,
    FEATURE_GRID,
    FEATURE_SOLAR,
)
from .deye_sun_12k import DeyeSun12K


class DeyeSun6K(DeyeSun12K):
    """Deye Sun 6K inverter device.
    
    Similar to Sun 12K but without battery features (6kW, grid-tie only).
    """

    device_model = DEVICE_TYPE_DEYE_SUN_6K
    device_name = "Deye Sun 6K"
    supported_features = [FEATURE_SOLAR, FEATURE_GRID]
