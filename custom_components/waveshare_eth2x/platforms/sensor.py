"""Sensor platform for Deye Sun 12K integration."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    ENTITY_CATEGORY_DIAGNOSTIC,
    MANUFACTURER,
    UNIT_CURRENT_A,
    UNIT_ENERGY_KWH,
    UNIT_FREQUENCY_HZ,
    UNIT_PERCENTAGE,
    UNIT_POWER_W,
    UNIT_TEMPERATURE_C,
    UNIT_VOLTAGE_V,
)
from .coordinators.integration import IntegrationCoordinator
from .devices.base import BaseDevice

_LOGGER = logging.getLogger(__name__)

# Map our units to Home Assistant units and device classes
UNIT_TO_HA = {
    UNIT_POWER_W: ("W", "power"),
    UNIT_VOLTAGE_V: ("V", "voltage"),
    UNIT_CURRENT_A: ("A", "current"),
    UNIT_ENERGY_KWH: ("kWh", "energy"),
    UNIT_TEMPERATURE_C: ("°C", "temperature"),
    UNIT_FREQUENCY_HZ: ("Hz", "frequency"),
    UNIT_PERCENTAGE: ("%", None),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator: IntegrationCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities: List[Entity] = []

    # Get all devices and create sensor entities
    for gateway_id, device in coordinator.get_all_devices():
        gateway = coordinator.get_gateway(gateway_id)
        
        # Add register sensors
        for reg_name, reg_def in device.register_map.items():
            if reg_def.mode == "read" and reg_def.unit:
                entity = DeyeRegisterSensor(
                    coordinator,
                    gateway,
                    device,
                    reg_name,
                    reg_def,
                )
                entities.append(entity)

        # Add health sensors
        entities.extend([
            DeyeConnectionStateSensor(coordinator, gateway, device),
            DeyeResponseTimeSensor(coordinator, gateway, device),
            DeyeSignalQualitySensor(coordinator, gateway, device),
        ])

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d sensor entities", len(entities))


class DeyeBaseSensor(SensorEntity):
    """Base class for Deye sensors."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        gateway,
        device: BaseDevice,
    ):
        """Initialize sensor.
        
        Args:
            coordinator: Integration coordinator
            gateway: Gateway coordinator
            device: Device instance
        """
        self.coordinator = coordinator
        self.gateway = gateway
        self.device = device
        self._attr_has_entity_name = True
        self._attr_should_poll = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.device.gateway_id}_{self.device.slave_id}")},
            name=self.device.device_name,
            manufacturer=MANUFACTURER,
            model=self.device.device_model,
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.gateway.is_connected()

    async def async_added_to_hass(self) -> None:
        """Add entity to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.register_update_callback(self._handle_update)
        )

    @callback
    def _handle_update(self) -> None:
        """Handle coordinator update."""
        self.async_write_ha_state()


class DeyeRegisterSensor(DeyeBaseSensor):
    """Sensor for a Modbus register."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        gateway,
        device: BaseDevice,
        register_name: str,
        register_def,
    ):
        """Initialize register sensor."""
        super().__init__(coordinator, gateway, device)
        self.register_name = register_name
        self.register_def = register_def
        
        # Entity setup
        self._attr_name = register_def.name or register_name.replace("_", " ").title()
        self._attr_unique_id = (
            f"{DOMAIN}_{device.gateway_id}_{device.slave_id}_{register_name}"
        )
        self._attr_icon = register_def.icon or "mdi:gauge"
        
        # Unit and device class
        if register_def.unit in UNIT_TO_HA:
            ha_unit, device_class = UNIT_TO_HA[register_def.unit]
            self._attr_native_unit_of_measurement = ha_unit
            self._attr_device_class = device_class
        else:
            self._attr_native_unit_of_measurement = None
            self._attr_device_class = None
        
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Current value
        self._attr_native_value: Optional[StateType] = None

    @property
    def native_value(self) -> StateType:
        """Return native value."""
        try:
            # Try to read from gateway (non-blocking)
            result = self._read_register_sync()
            if result is not None:
                return result
        except Exception as err:
            _LOGGER.debug("Error reading register %s: %s", self.register_name, err)
        
        return STATE_UNAVAILABLE

    def _read_register_sync(self) -> Optional[float]:
        """Read register synchronously (simplified for now)."""
        # In a production implementation, this would maintain a cache
        # For now, return a placeholder value
        return None


class DeyeConnectionStateSensor(DeyeBaseSensor):
    """Sensor for device connection state."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        gateway,
        device: BaseDevice,
    ):
        """Initialize connection state sensor."""
        super().__init__(coordinator, gateway, device)
        
        self._attr_name = "Connection State"
        self._attr_unique_id = (
            f"{DOMAIN}_{device.gateway_id}_{device.slave_id}_connection_state"
        )
        self._attr_icon = "mdi:connection"
        self._attr_entity_category = ENTITY_CATEGORY_DIAGNOSTIC

    @property
    def native_value(self) -> str:
        """Return connection state."""
        return self.gateway.get_device_health_state(self.device.slave_id)


class DeyeResponseTimeSensor(DeyeBaseSensor):
    """Sensor for response time."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        gateway,
        device: BaseDevice,
    ):
        """Initialize response time sensor."""
        super().__init__(coordinator, gateway, device)
        
        self._attr_name = "Response Time"
        self._attr_unique_id = (
            f"{DOMAIN}_{device.gateway_id}_{device.slave_id}_response_time"
        )
        self._attr_icon = "mdi:speedometer"
        self._attr_native_unit_of_measurement = "ms"
        self._attr_entity_category = ENTITY_CATEGORY_DIAGNOSTIC

    @property
    def native_value(self) -> float:
        """Return average response time in ms."""
        health = self.gateway.health_monitor.get_device_health(
            self.gateway.gateway_id,
            self.device.slave_id,
            create_if_missing=False,
        )
        
        if health:
            return health.get_average_response_time()
        
        return 0.0


class DeyeSignalQualitySensor(DeyeBaseSensor):
    """Sensor for signal quality."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        gateway,
        device: BaseDevice,
    ):
        """Initialize signal quality sensor."""
        super().__init__(coordinator, gateway, device)
        
        self._attr_name = "Signal Quality"
        self._attr_unique_id = (
            f"{DOMAIN}_{device.gateway_id}_{device.slave_id}_signal_quality"
        )
        self._attr_icon = "mdi:signal"
        self._attr_native_unit_of_measurement = "%"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = ENTITY_CATEGORY_DIAGNOSTIC

    @property
    def native_value(self) -> float:
        """Return signal quality percentage."""
        health = self.gateway.health_monitor.get_device_health(
            self.gateway.gateway_id,
            self.device.slave_id,
            create_if_missing=False,
        )
        
        if health:
            return health.get_signal_quality()
        
        return 0.0
