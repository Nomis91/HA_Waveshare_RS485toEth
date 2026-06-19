"""Deye Hybrid GW4137 device definition (skeleton)."""

from typing import Dict

from ..const import (
    DEVICE_TYPE_DEYE_HYBRID_GW4137,
    FEATURE_AC_OUTPUT,
    FEATURE_BATTERY,
    FEATURE_GRID,
    FEATURE_SOLAR,
)
from .deye_sun_12k import DeyeSun12K


class DeyeHybridGW4137(DeyeSun12K):
    """Deye Hybrid GW4137 hybrid inverter device.
    
    Includes AC output/backup features.
    """

    device_model = DEVICE_TYPE_DEYE_HYBRID_GW4137
    device_name = "Deye Hybrid GW4137"
    supported_features = [FEATURE_SOLAR, FEATURE_BATTERY, FEATURE_GRID, FEATURE_AC_OUTPUT]
