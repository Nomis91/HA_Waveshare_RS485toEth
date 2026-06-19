"""Deye Sun 12K inverter device definition."""

from typing import Dict

from ..const import (
    DEVICE_TYPE_DEYE_SUN_12K,
    FEATURE_BATTERY,
    FEATURE_GRID,
    FEATURE_SOLAR,
    REG_TYPE_FLOAT,
    REG_TYPE_INT16,
    REG_TYPE_UINT16,
    REG_TYPE_UINT32,
    UNIT_CURRENT_A,
    UNIT_ENERGY_KWH,
    UNIT_FREQUENCY_HZ,
    UNIT_PERCENTAGE,
    UNIT_POWER_W,
    UNIT_TEMPERATURE_C,
    UNIT_VOLTAGE_V,
)
from .base import BaseDevice, RegisterDef


class DeyeSun12K(BaseDevice):
    """Deye Sun 12K inverter device."""

    device_model = DEVICE_TYPE_DEYE_SUN_12K
    device_name = "Deye Sun 12K"
    supported_features = [FEATURE_SOLAR, FEATURE_BATTERY, FEATURE_GRID]

    @property
    def register_map(self) -> Dict[str, RegisterDef]:
        """Get register mapping for Deye Sun 12K."""
        return {
            # Solar/PV Registers
            "solar_pv1_voltage": RegisterDef(
                address=0x0100,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:solar-panel",
                scale=0.1,
            ),
            "solar_pv1_current": RegisterDef(
                address=0x0101,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_CURRENT_A,
                icon="mdi:current-dc",
                scale=0.01,
            ),
            "solar_pv1_power": RegisterDef(
                address=0x0102,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_POWER_W,
                icon="mdi:solar-power",
                scale=1.0,
            ),
            "solar_pv2_voltage": RegisterDef(
                address=0x0103,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:solar-panel",
                scale=0.1,
            ),
            "solar_pv2_current": RegisterDef(
                address=0x0104,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_CURRENT_A,
                icon="mdi:current-dc",
                scale=0.01,
            ),
            "solar_pv2_power": RegisterDef(
                address=0x0105,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_POWER_W,
                icon="mdi:solar-power",
                scale=1.0,
            ),
            "solar_total_power": RegisterDef(
                address=0x0106,
                data_type=REG_TYPE_UINT32,
                unit=UNIT_POWER_W,
                icon="mdi:solar-power",
                scale=1.0,
            ),
            "solar_total_energy_today": RegisterDef(
                address=0x0108,
                data_type=REG_TYPE_UINT32,
                unit=UNIT_ENERGY_KWH,
                icon="mdi:solar-power",
                scale=0.01,
            ),
            
            # Battery Registers
            "battery_voltage": RegisterDef(
                address=0x0200,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:battery",
                scale=0.01,
            ),
            "battery_current": RegisterDef(
                address=0x0201,
                data_type=REG_TYPE_INT16,
                unit=UNIT_CURRENT_A,
                icon="mdi:current-dc",
                scale=0.01,
            ),
            "battery_power": RegisterDef(
                address=0x0202,
                data_type=REG_TYPE_INT16,
                unit=UNIT_POWER_W,
                icon="mdi:battery-charging",
                scale=1.0,
            ),
            "battery_soc": RegisterDef(
                address=0x0203,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_PERCENTAGE,
                icon="mdi:battery-50",
                scale=1.0,
            ),
            "battery_soh": RegisterDef(
                address=0x0204,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_PERCENTAGE,
                icon="mdi:battery-heart",
                scale=1.0,
            ),
            "battery_temperature": RegisterDef(
                address=0x0205,
                data_type=REG_TYPE_INT16,
                unit=UNIT_TEMPERATURE_C,
                icon="mdi:thermometer",
                scale=0.1,
            ),
            
            # Grid Registers
            "grid_voltage": RegisterDef(
                address=0x0300,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:transmission-tower",
                scale=0.1,
            ),
            "grid_current": RegisterDef(
                address=0x0301,
                data_type=REG_TYPE_INT16,
                unit=UNIT_CURRENT_A,
                icon="mdi:current-ac",
                scale=0.01,
            ),
            "grid_power": RegisterDef(
                address=0x0302,
                data_type=REG_TYPE_INT16,
                unit=UNIT_POWER_W,
                icon="mdi:lightning-bolt",
                scale=1.0,
            ),
            "grid_frequency": RegisterDef(
                address=0x0303,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_FREQUENCY_HZ,
                icon="mdi:sine-wave",
                scale=0.01,
            ),
            "grid_import_energy_today": RegisterDef(
                address=0x0304,
                data_type=REG_TYPE_UINT32,
                unit=UNIT_ENERGY_KWH,
                icon="mdi:transmission-tower",
                scale=0.01,
            ),
            "grid_export_energy_today": RegisterDef(
                address=0x0306,
                data_type=REG_TYPE_UINT32,
                unit=UNIT_ENERGY_KWH,
                icon="mdi:transmission-tower",
                scale=0.01,
            ),
            
            # Inverter Status Registers
            "inverter_temperature": RegisterDef(
                address=0x0400,
                data_type=REG_TYPE_INT16,
                unit=UNIT_TEMPERATURE_C,
                icon="mdi:thermometer",
                scale=0.1,
            ),
            "inverter_status": RegisterDef(
                address=0x0401,
                data_type=REG_TYPE_UINT16,
                unit=None,
                icon="mdi:state-machine",
                scale=1.0,
            ),
            "inverter_fault_code": RegisterDef(
                address=0x0402,
                data_type=REG_TYPE_UINT16,
                unit=None,
                icon="mdi:alert-circle",
                scale=1.0,
            ),
            
            # Output Registers (if available)
            "output_voltage": RegisterDef(
                address=0x0500,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_VOLTAGE_V,
                icon="mdi:power-outlet",
                scale=0.1,
                mode="read",
            ),
            "output_current": RegisterDef(
                address=0x0501,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_CURRENT_A,
                icon="mdi:current-ac",
                scale=0.01,
                mode="read",
            ),
            "output_power": RegisterDef(
                address=0x0502,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_POWER_W,
                icon="mdi:power-outlet",
                scale=1.0,
                mode="read",
            ),
            "output_frequency": RegisterDef(
                address=0x0503,
                data_type=REG_TYPE_UINT16,
                unit=UNIT_FREQUENCY_HZ,
                icon="mdi:sine-wave",
                scale=0.01,
                mode="read",
            ),
        }
