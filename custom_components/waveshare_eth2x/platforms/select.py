"""Select platform for Deye Sun 12K integration."""

import logging
from typing import List, Optional

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ENTITY_CATEGORY_CONFIG, MANUFACTURER
from .coordinators.integration import IntegrationCoordinator
from .devices.base import BaseDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities from a config entry."""
    coordinator: IntegrationCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]

    entities: List[Entity] = []

    # In future, add enum/mode selectors here
    # For now, this is a placeholder for future expansion

    if entities:
        async_add_entities(entities)
        _LOGGER.info("Added %d select entities", len(entities))
