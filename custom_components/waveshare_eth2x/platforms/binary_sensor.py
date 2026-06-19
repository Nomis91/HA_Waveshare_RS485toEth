"""Binary sensor platform for Deye Sun 12K integration."""

import logging
from typing import List, Optional

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEVICE_CLASS_CONNECTIVITY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    ENTITY_CATEGORY_DIAGNOSTIC,
    HEALTH_STATE_HEALTHY,
    MANUFACTURER,
)
from .coordinators.integration import IntegrationCoordinator
from .devices.base import BaseDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    coordinator: IntegrationCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities: List[Entity] = []

    # Get all devices and create binary sensor entities
    for gateway_id, device in coordinator.get_all_devices():
        gateway = coordinator.get_gateway(gateway_id)
        
        # Add connection status binary sensor
        entities.append(
            DeyeConnectionStatusBinarySensor(coordinator, gateway, device)
        )

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d binary sensor entities", len(entities))


class DeyeBaseBinarySensor(BinarySensorEntity):
    """Base class for Deye binary sensors."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        gateway,
        device: BaseDevice,
    ):
        """Initialize binary sensor.
        
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
        return True  # Always available for status reporting

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


class DeyeConnectionStatusBinarySensor(DeyeBaseBinarySensor):
    """Binary sensor for connection status."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        gateway,
        device: BaseDevice,
    ):
        """Initialize connection status binary sensor."""
        super().__init__(coordinator, gateway, device)
        
        self._attr_name = "Connection Status"
        self._attr_unique_id = (
            f"{DOMAIN}_{device.gateway_id}_{device.slave_id}_connection_status"
        )
        self._attr_device_class = DEVICE_CLASS_CONNECTIVITY
        self._attr_entity_category = ENTITY_CATEGORY_DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        """Return True if connected."""
        state = self.gateway.get_device_health_state(self.device.slave_id)
        return state == HEALTH_STATE_HEALTHY
