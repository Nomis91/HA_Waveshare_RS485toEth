"""Waveshare Eth2X Integration for Home Assistant.

This integration provides real-time monitoring and control of Solar Inverters
connected via Waveshare Eth2X devices.

Features:
- Support for multiple Eth2X gateways
- Multiple devices per gateway
- Connection health monitoring
- Comprehensive error tracking and statistics
- Device type abstraction (Deye Sun, Deye Hybrid, Generic Modbus)
- Dynamic entity creation based on device capabilities
"""

import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinators.integration import IntegrationCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: Dict) -> bool:
    """Set up the integration from configuration.yaml (legacy)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the integration from a config entry."""
    _LOGGER.debug("Setting up Deye Sun 12K integration for entry %s", entry.entry_id)
    
    hass.data.setdefault(DOMAIN, {})
    
    try:
        # Create integration coordinator
        coordinator = IntegrationCoordinator(hass)
        
        # Set up from config entry
        await coordinator.async_setup([entry.data])
        
        # Store the coordinator and config entry
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "config": entry.data,
            "options": entry.options,
        }
        
        # Set up platforms
        await hass.config_entries.async_forward_entry_setups(
            entry,
            ["sensor", "binary_sensor"],
        )
        
        # Listen for config option updates
        entry.async_on_unload(entry.add_update_listener(async_update_listener))
        
        _LOGGER.info("Deye Sun 12K integration setup complete for entry %s", entry.entry_id)
        return True
        
    except Exception as err:
        _LOGGER.error("Failed to setup Deye Sun 12K integration: %s", err)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Deye Sun 12K integration for entry %s", entry.entry_id)
    
    try:
        # Tear down coordinator
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            coordinator = hass.data[DOMAIN][entry.entry_id].get("coordinator")
            if coordinator:
                await coordinator.async_teardown()
        
        # Unload platforms
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry,
            ["sensor", "binary_sensor"],
        )
        
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id, None)
        
        return unload_ok
        
    except Exception as err:
        _LOGGER.error("Error unloading Deye Sun 12K integration: %s", err)
        return False


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Options updated for Deye Sun 12K integration")
    
    # Update the stored options
    if entry.entry_id in hass.data.get(DOMAIN, {}):
        hass.data[DOMAIN][entry.entry_id]["options"] = entry.options
        
        # Reload entry if needed
        await hass.config_entries.async_reload(entry.entry_id)
