"""Number platform for Deye Sun 12K integration."""

import logging
from typing import List, Optional

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DEVICE_CLASS_POWER
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, ENTITY_CATEGORY_CONFIG, MANUFACTURER
from .coordinators.integration import IntegrationCoordinator
from .devices.base import BaseDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities from a config entry."""
    coordinator: IntegrationCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities: List[Entity] = []

    # Get all devices and create number entities for writable registers
    for gateway_id, device in coordinator.get_all_devices():
        gateway = coordinator.get_gateway(gateway_id)
        
        for reg_name, reg_def in device.register_map.items():
            # Only create entities for writable numeric registers
            if (
                reg_def.mode == "write"
                and reg_def.unit
                and reg_def.data_type in ("uint16", "uint32", "int16", "int32", "float")
            ):
                entity = DeyeNumberEntity(
                    coordinator,
                    gateway,
                    device,
                    reg_name,
                    reg_def,
                )
                entities.append(entity)

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d number entities", len(entities))


class DeyeNumberEntity(NumberEntity):
    """Number entity for a writable Modbus register."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        gateway,
        device: BaseDevice,
        register_name: str,
        register_def,
    ):
        """Initialize number entity.
        
        Args:
            coordinator: Integration coordinator
            gateway: Gateway coordinator
            device: Device instance
            register_name: Name of register
            register_def: Register definition
        """
        self.coordinator = coordinator
        self.gateway = gateway
        self.device = device
        self.register_name = register_name
        self.register_def = register_def
        
        # Entity setup
        self._attr_name = register_def.name or register_name.replace("_", " ").title()
        self._attr_unique_id = (
            f"{DOMAIN}_{device.gateway_id}_{device.slave_id}_{register_name}"
        )
        self._attr_has_entity_name = True
        self._attr_icon = register_def.icon or "mdi:tune"
        self._attr_entity_category = ENTITY_CATEGORY_CONFIG
        
        # Unit setup
        self._attr_native_unit_of_measurement = register_def.unit
        
        # Set min/max if available
        self._attr_native_min_value = 0
        self._attr_native_max_value = 32767  # Default for int16
        self._attr_native_step = 1

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

    @property
    def native_value(self) -> Optional[float]:
        """Return current value."""
        # In a real implementation, this would read from device
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        try:
            # Convert to raw value
            raw_value = int((value - self.register_def.offset) / self.register_def.scale)
            
            # In a real implementation, this would write to device
            _LOGGER.info(
                "Would write %s = %s (%d raw)",
                self.register_name,
                value,
                raw_value,
            )
        except Exception as err:
            _LOGGER.error("Error setting value: %s", err)
            raise

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
