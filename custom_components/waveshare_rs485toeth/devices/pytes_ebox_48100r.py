"""Pytes E-Box 48100R battery device definition."""

from typing import Dict

from ..const import (
    DEVICE_TYPE_PYTES_EBOX_48100R,
    FEATURE_BATTERY,
    REG_TYPE_INT16,
    REG_TYPE_UINT16,
    REG_TYPE_UINT32,
    UNIT_CURRENT_A,
    UNIT_ENERGY_KWH,
    UNIT_POWER_W,
    UNIT_TEMPERATURE_C,
    UNIT_VOLTAGE_V,
)
from .base import BaseDevice, RegisterDef


class PytesEbox48100R(BaseDevice):
    """Pytes E-Box 48100R battery system."""

    device_model = DEVICE_TYPE_PYTES_EBOX_48100R
    device_name = "Pytes E-Box 48100R"
    supported_features = [FEATURE_BATTERY]

    @property
    def register_map(self) -> Dict[str, RegisterDef]:
        """Get register mapping for Pytes E-Box 48100R."""
        return {
            # Battery Voltage/Current/Power Registers
            "battery_voltage": RegisterDef(
                address=0x0000,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:battery-charging",
                scale=0.1,
            ),
            "battery_current": RegisterDef(
                address=0x0001,
                data_type=REG_TYPE_INT16,
                unit=UNIT_CURRENT_A,
                icon="mdi:current-dc",
                scale=0.01,
            ),
            "battery_power": RegisterDef(
                address=0x0002,
                data_type=REG_TYPE_INT16,
                unit=UNIT_POWER_W,
                icon="mdi:battery-charging",
                scale=1.0,
            ),
            "battery_soc": RegisterDef(
                address=0x0003,
                data_type=REG_TYPE_UINT16,
                unit="%",
                icon="mdi:battery-50",
                scale=1.0,
            ),
            
            # Temperature Registers
            "battery_temperature": RegisterDef(
                address=0x0004,
                data_type=REG_TYPE_INT16,
                unit="°C",
                icon="mdi:thermometer",
                scale=0.1,
            ),
            "mosfet_temperature": RegisterDef(
                address=0x0005,
                data_type=REG_TYPE_INT16,
                unit="°C",
                icon="mdi:thermometer",
                scale=0.1,
            ),
            
            # Energy Counters
            "total_discharged_energy": RegisterDef(
                address=0x0006,
                data_type=REG_TYPE_UINT32,
                unit="kWh",
                icon="mdi:battery-arrow-down",
                scale=0.001,
            ),
            "total_charged_energy": RegisterDef(
                address=0x0008,
                data_type=REG_TYPE_UINT32,
                unit="kWh",
                icon="mdi:battery-arrow-up",
                scale=0.001,
            ),
            
            # Battery Status
            "charge_discharge_status": RegisterDef(
                address=0x000A,
                data_type=REG_TYPE_UINT16,
                unit=None,
                icon="mdi:battery-sync",
                scale=1.0,
            ),
            
            # Cell Voltages (summary)
            "min_cell_voltage": RegisterDef(
                address=0x0010,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:battery-low",
                scale=0.001,
            ),
            "max_cell_voltage": RegisterDef(
                address=0x0011,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:battery-high",
                scale=0.001,
            ),
            "avg_cell_voltage": RegisterDef(
                address=0x0012,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:battery-medium",
                scale=0.001,
            ),
            
            # Cell Temperatures (summary)
            "min_cell_temperature": RegisterDef(
                address=0x0013,
                data_type=REG_TYPE_INT16,
                unit="°C",
                icon="mdi:thermometer-low",
                scale=0.1,
            ),
            "max_cell_temperature": RegisterDef(
                address=0x0014,
                data_type=REG_TYPE_INT16,
                unit="°C",
                icon="mdi:thermometer-high",
                scale=0.1,
            ),
            
            # System Status
            "bms_status": RegisterDef(
                address=0x0020,
                data_type=REG_TYPE_UINT16,
                unit=None,
                icon="mdi:state-machine",
                scale=1.0,
            ),
            "fault_code": RegisterDef(
                address=0x0021,
                data_type=REG_TYPE_UINT16,
                unit=None,
                icon="mdi:alert-circle",
                scale=1.0,
            ),
            "warning_code": RegisterDef(
                address=0x0022,
                data_type=REG_TYPE_UINT16,
                unit=None,
                icon="mdi:alert",
                scale=1.0,
            ),
            
            # Battery Info
            "remaining_capacity": RegisterDef(
                address=0x0030,
                data_type=REG_TYPE_UINT32,
                unit="mAh",
                icon="mdi:battery",
                scale=1.0,
            ),
            "full_charge_capacity": RegisterDef(
                address=0x0032,
                data_type=REG_TYPE_UINT32,
                unit="mAh",
                icon="mdi:battery-full",
                scale=1.0,
            ),
            "cycle_count": RegisterDef(
                address=0x0034,
                data_type=REG_TYPE_UINT16,
                unit=None,
                icon="mdi:counter",
                scale=1.0,
            ),
        }
