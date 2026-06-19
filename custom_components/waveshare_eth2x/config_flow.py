"""Configuration flow for Eth2X integration."""

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_SCAN_INTERVAL,
    CONF_DEVICE_SLAVE_ID,
    CONF_DEVICE_TYPE,
    CONF_DEVICES,
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_KEEPALIVE,
    CONF_GATEWAY_NAME,
    CONF_GATEWAY_PORT,
    CONF_GATEWAY_TIMEOUT,
    DEFAULT_DEVICE_SCAN_INTERVAL,
    DEFAULT_GATEWAY_KEEPALIVE,
    DEFAULT_GATEWAY_PORT,
    DEFAULT_GATEWAY_TIMEOUT,
    DOMAIN,
)
from .core.gateway import GatewayConnection
from .devices.registry import DeviceRegistry, DeviceDiscovery

_LOGGER = logging.getLogger(__name__)


class WaveshareEth2xConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Waveshare Eth2X."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize config flow."""
        super().__init__()
        self._gateway_data: Dict[str, Any] = {}
        self._discovered_devices: list[Dict[str, Any]] = []
        self._selected_devices: Dict[str, Any] = {}
        self._pending_device_indices: list[int] = []

    async def async_step_user(
        self,
        user_input: Optional[Dict[str, Any]] = None,
    ) -> FlowResult:
        """Handle the initial step - gateway connection."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate gateway connection
                await self._test_gateway_connection(
                    user_input[CONF_GATEWAY_HOST],
                    user_input.get(CONF_GATEWAY_PORT, DEFAULT_GATEWAY_PORT),
                    user_input.get(CONF_GATEWAY_TIMEOUT, DEFAULT_GATEWAY_TIMEOUT),
                )

                self._gateway_data = user_input
                return await self.async_step_device_discovery()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors[CONF_GATEWAY_HOST] = "invalid_host"
            except Exception as err:
                _LOGGER.exception("Unexpected error: %s", err)
                errors["base"] = "unknown"

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_GATEWAY_NAME,
                    default="",
                    description="Gateway name (e.g. 'Garage Roof')",
                ): str,
                vol.Required(
                    CONF_GATEWAY_HOST,
                    description="Gateway IP or hostname",
                ): str,
                vol.Optional(
                    CONF_GATEWAY_PORT,
                    default=DEFAULT_GATEWAY_PORT,
                    description="Gateway port (typically 8234)",
                ): int,
                vol.Optional(
                    CONF_GATEWAY_TIMEOUT,
                    default=DEFAULT_GATEWAY_TIMEOUT,
                    description="Connection timeout (seconds)",
                ): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"default_port": str(DEFAULT_GATEWAY_PORT)},
        )

    async def async_step_device_discovery(
        self,
        user_input: Optional[Dict[str, Any]] = None,
    ) -> FlowResult:
        """Discover devices on the gateway."""
        if user_input is not None:
            # Continue to device selection
            return await self.async_step_device_selection()

        try:
            # Create temporary gateway connection for discovery
            gateway = GatewayConnection(
                host=self._gateway_data[CONF_GATEWAY_HOST],
                port=self._gateway_data.get(CONF_GATEWAY_PORT, DEFAULT_GATEWAY_PORT),
                timeout=self._gateway_data.get(CONF_GATEWAY_TIMEOUT, DEFAULT_GATEWAY_TIMEOUT),
            )

            await gateway.connect()

            # Discover devices
            self._discovered_devices = await DeviceDiscovery.scan_gateway(gateway)

            await gateway.disconnect()

            if not self._discovered_devices:
                return self.async_abort(reason="no_devices_found")

        except Exception as err:
            _LOGGER.exception("Error discovering devices: %s", err)
            return self.async_abort(reason="discovery_error")

        return self.async_show_form(
            step_id="device_discovery",
            description_placeholders={
                "count": str(len(self._discovered_devices)),
            },
        )

    async def async_step_device_selection(
        self,
        user_input: Optional[Dict[str, Any]] = None,
    ) -> FlowResult:
        """Select devices to add."""
        if user_input is not None:
            selected_indices = user_input.get("devices", [])

            self._pending_device_indices = []
            for idx_str in selected_indices:
                try:
                    idx = int(idx_str)
                    if 0 <= idx < len(self._discovered_devices):
                        self._pending_device_indices.append(idx)
                except (ValueError, IndexError):
                    continue

            if not self._pending_device_indices:
                return self.async_abort(reason="no_devices_selected")

            # Proceed to naming step
            return await self.async_step_device_names()

        # Build device options
        device_options = {}
        for idx, device in enumerate(self._discovered_devices):
            device_key = str(idx)
            device_label = f"Slave {device['slave_id']}: {device.get('name', 'Unknown Device')}"
            device_options[device_key] = device_label

        schema = vol.Schema(
            {
                vol.Required(
                    "devices",
                    description="Select devices to add",
                ): cv.multi_select(device_options),
            }
        )

        return self.async_show_form(
            step_id="device_selection",
            data_schema=schema,
        )

    async def async_step_device_names(
        self,
        user_input: Optional[Dict[str, Any]] = None,
    ) -> FlowResult:
        """Let the user name each selected device."""
        if user_input is not None:
            # Build selected devices with user-provided names
            for idx in self._pending_device_indices:
                device = self._discovered_devices[idx]
                slave_id = device["slave_id"]
                user_key = f"device_{idx}"
                device_name = user_input.get(
                    user_key,
                    device.get("name", f"Device {slave_id}"),
                )
                self._selected_devices[user_key] = {
                    CONF_DEVICE_SLAVE_ID: slave_id,
                    CONF_DEVICE_TYPE: device["device_type"],
                    CONF_DEVICE_NAME: device_name,
                    CONF_DEVICE_SCAN_INTERVAL: DEFAULT_DEVICE_SCAN_INTERVAL,
                }

            # Build the config entry
            gateway_name = self._gateway_data.get(CONF_GATEWAY_NAME, "").strip()
            config_data = {
                CONF_GATEWAY_NAME: gateway_name,
                CONF_GATEWAY_HOST: self._gateway_data[CONF_GATEWAY_HOST],
                CONF_GATEWAY_PORT: self._gateway_data.get(
                    CONF_GATEWAY_PORT, DEFAULT_GATEWAY_PORT
                ),
                CONF_GATEWAY_TIMEOUT: self._gateway_data.get(
                    CONF_GATEWAY_TIMEOUT, DEFAULT_GATEWAY_TIMEOUT
                ),
                CONF_GATEWAY_KEEPALIVE: self._gateway_data.get(
                    CONF_GATEWAY_KEEPALIVE, DEFAULT_GATEWAY_KEEPALIVE
                ),
                CONF_DEVICES: list(self._selected_devices.values()),
            }

            # Use gateway name as entry title if provided
            title = gateway_name or self._gateway_data[CONF_GATEWAY_HOST]
            return self.async_create_entry(title=title, data=config_data)

        # Build naming form - one text field per selected device
        name_fields = {}
        for idx in self._pending_device_indices:
            device = self._discovered_devices[idx]
            slave_id = device["slave_id"]
            default_name = device.get("name", f"Device {slave_id}")
            name_fields[vol.Optional(f"device_{idx}", default=default_name)] = str

        schema = vol.Schema(name_fields)

        return self.async_show_form(
            step_id="device_names",
            data_schema=schema,
        )

    async def _test_gateway_connection(
        self,
        host: str,
        port: int,
        timeout: float,
    ) -> None:
        """Test connection to gateway."""
        try:
            gateway = GatewayConnection(
                host=host,
                port=port,
                timeout=timeout,
            )
            await gateway.connect()
            await gateway.disconnect()
        except Exception as err:
            if "Name or service not known" in str(err) or "getaddrinfo failed" in str(err):
                raise InvalidHost from err
            raise CannotConnect from err


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(HomeAssistantError):
    """Error to indicate invalid hostname."""