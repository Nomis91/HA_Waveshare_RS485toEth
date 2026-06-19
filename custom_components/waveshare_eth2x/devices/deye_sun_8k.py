"""Deye Sun 8K inverter device definition (skeleton)."""

from typing import Dict

from ..const import (
    DEVICE_TYPE_DEYE_SUN_8K,
    FEATURE_BATTERY,
    FEATURE_GRID,
    FEATURE_SOLAR,
)
from .deye_sun_12k import DeyeSun12K


class DeyeSun8K(DeyeSun12K):
    """Deye Sun 8K inverter device.
    
    Similar register layout to Sun 12K but with 8kW capacity.
    """

    device_model = DEVICE_TYPE_DEYE_SUN_8K
    device_name = "Deye Sun 8K"
    supported_features = [FEATURE_SOLAR, FEATURE_BATTERY, FEATURE_GRID]
