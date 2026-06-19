"""Integration coordinator - orchestrates all gateways and devices."""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_SLAVE_ID,
    CONF_DEVICE_TYPE,
    CONF_DEVICES,
    CONF_GATEWAY_HOST,
    CONF_GATEWAY_KEEPALIVE,
    CONF_GATEWAY_NAME,
    CONF_GATEWAY_PORT,
    CONF_GATEWAY_TIMEOUT,
    DEFAULT_GATEWAY_KEEPALIVE,
    DEFAULT_GATEWAY_PORT,
    DEFAULT_GATEWAY_TIMEOUT,
    DOMAIN,
    ERROR_TYPE_CHECKSUM,
    ERROR_TYPE_COMMUNICATION,
    ERROR_TYPE_NO_RESPONSE,
    ERROR_TYPE_TIMEOUT,
    REQUEST_MIN_DELAY_MS,
)
from .core.exceptions import (
    GatewayConnectionError,
    GatewayTimeoutError,
    ModbusCRCError,
    ModbusError,
)
from .core.gateway import ConnectionPool, GatewayConnection
from .core.protocol import ModbusRTU
from .devices.base import BaseDevice
from .devices.registry import DeviceRegistry
from .errors import ErrorTrackerRegistry
from .health import HealthMonitor

_LOGGER = logging.getLogger(__name__)


class GatewayCoordinator:
    """Coordinator for a single Eth2X gateway."""

    def __init__(
        self,
        hass: HomeAssistant,
        gateway_id: str,
        host: str,
        port: int,
        timeout: float = 10.0,
        keepalive_interval: float = 300.0,
        name: str = "",
    ):
        """Initialize gateway coordinator.
        
        Args:
            hass: Home Assistant instance
            gateway_id: Unique gateway identifier
            host: Gateway IP address
            port: Gateway port
            timeout: Connection timeout
            keepalive_interval: Keep-alive interval
            name: Optional friendly name for this gateway
        """
        self.hass = hass
        self.gateway_id = gateway_id
        self.name = name or gateway_id
        self.host = host
        self.port = port
        self.timeout = timeout
        self.keepalive_interval = keepalive_interval
        
        self.connection: Optional[GatewayConnection] = None
        self.devices: Dict[int, BaseDevice] = {}
        self.health_monitor = HealthMonitor()
        self.error_tracker = ErrorTrackerRegistry()
        
        self._last_request_time = time.time()
        self._connected = False
        self._request_lock = asyncio.Lock()
        self._keepalive_task: Optional[asyncio.Task] = None

    async def async_setup(self) -> bool:
        """Set up gateway coordinator.
        
        Returns:
            True if successful
        """
        try:
            self.connection = GatewayConnection(
                host=self.host,
                port=self.port,
                timeout=self.timeout,
                keepalive_interval=self.keepalive_interval,
            )
            
            await self.connection.connect()
            self._connected = True
            
            _LOGGER.info("Gateway %s connected successfully", self.gateway_id)
            
            # Start keep-alive task
            if self._keepalive_task is None:
                self._keepalive_task = asyncio.create_task(self._keepalive_loop())
            
            return True
            
        except Exception as err:
            _LOGGER.error("Failed to setup gateway %s: %s", self.gateway_id, err)
            self._connected = False
            return False

    async def async_teardown(self) -> None:
        """Tear down gateway coordinator."""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
        
        if self.connection:
            await self.connection.disconnect()
        
        self._connected = False

    def add_device(self, device: BaseDevice) -> None:
        """Add a device to this gateway.
        
        Args:
            device: Device instance
        """
        self.devices[device.slave_id] = device
        self.health_monitor.get_device_health(self.gateway_id, device.slave_id)
        self.error_tracker.get_device_tracker(self.gateway_id, device.slave_id)

    async def async_read_registers(
        self,
        slave_id: int,
        register_names: List[str],
    ) -> Dict[str, Any]:
        """Read register values from a device.
        
        Args:
            slave_id: Modbus slave ID
            register_names: Register names to read
            
        Returns:
            Dictionary of register name to value
        """
        if slave_id not in self.devices:
            raise ValueError(f"Device {slave_id} not found on gateway {self.gateway_id}")
        
        device = self.devices[slave_id]
        result = {}
        
        start_time = time.time()
        
        try:
            # Group registers by address for efficient reading
            registers_to_read = {}
            for reg_name in register_names:
                if reg_name in device.register_map:
                    reg_def = device.register_map[reg_name]
                    registers_to_read[reg_name] = reg_def
            
            if not registers_to_read:
                raise ValueError(f"No valid registers found for {slave_id}")
            
            # Read registers from device
            modbus_data = await self._read_modbus_registers(
                slave_id,
                registers_to_read,
            )
            
            # Parse values
            for reg_name, reg_def in registers_to_read.items():
                try:
                    # Get registers needed for this value
                    if reg_def.data_type in ("uint32", "int32", "float"):
                        regs = [
                            modbus_data.get(reg_def.address),
                            modbus_data.get(reg_def.address + 1),
                        ]
                    else:
                        regs = [modbus_data.get(reg_def.address)]
                    
                    if None not in regs:
                        value = ModbusRTU.parse_register_value(
                            regs,
                            reg_def.data_type,
                            reg_def.scale,
                            reg_def.offset,
                        )
                        result[reg_name] = value
                
                except Exception as err:
                    _LOGGER.warning(
                        "Error parsing register %s: %s",
                        reg_name,
                        err,
                    )
            
            # Record success
            response_time_ms = (time.time() - start_time) * 1000
            self.health_monitor.record_device_success(
                self.gateway_id,
                slave_id,
                response_time_ms,
            )
            self.error_tracker.record_device_attempt(self.gateway_id, slave_id)
            
            return result
            
        except ModbusCRCError:
            self.health_monitor.record_device_failure(self.gateway_id, slave_id)
            self.error_tracker.record_device_attempt(
                self.gateway_id,
                slave_id,
                ERROR_TYPE_CHECKSUM,
            )
            raise
        except GatewayTimeoutError:
            self.health_monitor.record_device_failure(self.gateway_id, slave_id)
            self.error_tracker.record_device_attempt(
                self.gateway_id,
                slave_id,
                ERROR_TYPE_TIMEOUT,
            )
            raise
        except (GatewayConnectionError, ModbusError):
            self.health_monitor.record_device_failure(self.gateway_id, slave_id)
            self.error_tracker.record_device_attempt(
                self.gateway_id,
                slave_id,
                ERROR_TYPE_COMMUNICATION,
            )
            raise
        except Exception as err:
            self.health_monitor.record_device_failure(self.gateway_id, slave_id)
            self.error_tracker.record_device_attempt(
                self.gateway_id,
                slave_id,
                ERROR_TYPE_NO_RESPONSE,
            )
            raise

    async def _read_modbus_registers(
        self,
        slave_id: int,
        registers_to_read: Dict[str, Any],
    ) -> Dict[int, int]:
        """Read raw Modbus registers.
        
        Args:
            slave_id: Modbus slave ID
            registers_to_read: Dict of register name to RegisterDef
            
        Returns:
            Dictionary of address to value
        """
        if not self.connection or not self._connected:
            raise GatewayConnectionError("Gateway not connected")
        
        # Respect minimum delay between requests
        async with self._request_lock:
            elapsed = time.time() - self._last_request_time
            min_delay = REQUEST_MIN_DELAY_MS / 1000.0
            if elapsed < min_delay:
                await asyncio.sleep(min_delay - elapsed)
            
            # Find min and max addresses
            addresses = [reg_def.address for reg_def in registers_to_read.values()]
            min_addr = min(addresses)
            max_addr = max(addresses)
            
            # Calculate quantity needed (handle 32-bit registers)
            quantity = 0
            for reg_def in registers_to_read.values():
                if reg_def.data_type in ("uint32", "int32", "float"):
                    quantity = max(quantity, reg_def.address - min_addr + 2)
                else:
                    quantity = max(quantity, reg_def.address - min_addr + 1)
            
            # Build and send request
            request = ModbusRTU.frame_read_holding_registers(
                slave_id=slave_id,
                start_address=min_addr,
                quantity=quantity,
            )
            
            response = await self.connection.send_modbus_request(request)
            parsed = ModbusRTU.parse_response(response, slave_id)
            
            # Map response data to addresses
            result = {}
            if "registers" in parsed:
                for i, reg_value in enumerate(parsed["registers"]):
                    result[min_addr + i] = reg_value
            
            self._last_request_time = time.time()
            return result

    async def _keepalive_loop(self) -> None:
        """Keep-alive loop to maintain connection."""
        while True:
            try:
                await asyncio.sleep(self.keepalive_interval)
                
                if self.connection and self._connected:
                    try:
                        await self.connection.keepalive_probe()
                    except Exception as err:
                        _LOGGER.debug("Keep-alive probe failed: %s", err)
                        self._connected = False
                        
            except asyncio.CancelledError:
                break
            except Exception as err:
                _LOGGER.error("Error in keep-alive loop: %s", err)

    def is_connected(self) -> bool:
        """Check if gateway is connected."""
        return self._connected and (self.connection is not None and self.connection.connected)

    def get_health_state(self) -> str:
        """Get gateway health state."""
        return self.health_monitor.get_gateway_state(self.gateway_id)

    def get_device_health_state(self, slave_id: int) -> str:
        """Get device health state."""
        return self.health_monitor.get_device_state(self.gateway_id, slave_id)


class IntegrationCoordinator:
    """Top-level coordinator for the entire integration."""

    def __init__(self, hass: HomeAssistant):
        """Initialize integration coordinator.
        
        Args:
            hass: Home Assistant instance
        """
        self.hass = hass
        self.gateways: Dict[str, GatewayCoordinator] = {}
        self._update_callbacks: List[Callable[[], None]] = []
        self._data_update_task: Optional[asyncio.Task] = None

    async def async_setup(self, config_entries: List[Dict[str, Any]]) -> bool:
        """Set up integration with config entries.
        
        Args:
            config_entries: List of config entry data
            
        Returns:
            True if setup successful
        """
        try:
            for entry_data in config_entries:
                await self._setup_gateway_from_config(entry_data)
            
            _LOGGER.info(
                "Integration setup complete with %d gateway(s)",
                len(self.gateways),
            )
            return True
            
        except Exception as err:
            _LOGGER.error("Failed to setup integration: %s", err)
            return False

    async def _setup_gateway_from_config(self, entry_data: Dict[str, Any]) -> None:
        """Set up a single gateway from config entry.
        
        Args:
            entry_data: Configuration entry data
        """

        
        host = entry_data[CONF_GATEWAY_HOST]
        port = entry_data.get(CONF_GATEWAY_PORT, DEFAULT_GATEWAY_PORT)
        timeout = entry_data.get(CONF_GATEWAY_TIMEOUT, DEFAULT_GATEWAY_TIMEOUT)
        keepalive = entry_data.get(CONF_GATEWAY_KEEPALIVE, DEFAULT_GATEWAY_KEEPALIVE)
        
        gateway_id = f"{host}_{port}"
        
        # Create gateway coordinator
        gateway_name = entry_data.get(CONF_GATEWAY_NAME, "").strip()

        gateway = GatewayCoordinator(
            self.hass,
            gateway_id,
            host,
            port,
            timeout,
            keepalive,
            gateway_name,
        )
        
        # Set up gateway
        if not await gateway.async_setup():
            raise Exception(f"Failed to connect to gateway {gateway_id}")
        
        # Add devices
        for device_config in entry_data.get(CONF_DEVICES, []):
            device_type = device_config[CONF_DEVICE_TYPE]
            slave_id = device_config[CONF_DEVICE_SLAVE_ID]
            raw_name = device_config.get(CONF_DEVICE_NAME, f"Device {slave_id}")
            device_name = f"{gateway_name} {raw_name}".strip() if gateway_name else raw_name
            
            device = DeviceRegistry.create_device(
                device_type,
                gateway_id,
                slave_id,
                device_name,
            )
            
            if device:
                gateway.add_device(device)
                _LOGGER.info(
                    "Added device %s (slave %d) to gateway %s",
                    device_name,
                    slave_id,
                    gateway_id,
                )
            else:
                _LOGGER.warning(
                    "Failed to create device type %s for slave %d",
                    device_type,
                    slave_id,
                )
        
        self.gateways[gateway_id] = gateway

    async def async_teardown(self) -> None:
        """Tear down the integration."""
        if self._data_update_task:
            self._data_update_task.cancel()
            try:
                await self._data_update_task
            except asyncio.CancelledError:
                pass
        
        for gateway in self.gateways.values():
            await gateway.async_teardown()
        
        self.gateways.clear()

    def register_update_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback for data updates.
        
        Args:
            callback: Callback function
            
        Returns:
            Unregister function
        """
        self._update_callbacks.append(callback)
        
        def unregister():
            if callback in self._update_callbacks:
                self._update_callbacks.remove(callback)
        
        return unregister

    def notify_update(self) -> None:
        """Notify all listeners of data update."""
        for callback in self._update_callbacks:
            try:
                callback()
            except Exception as err:
                _LOGGER.error("Error in update callback: %s", err)

    def get_gateway(self, gateway_id: str) -> Optional[GatewayCoordinator]:
        """Get a gateway coordinator.
        
        Args:
            gateway_id: Gateway identifier
            
        Returns:
            GatewayCoordinator or None
        """
        return self.gateways.get(gateway_id)

    def get_all_gateways(self) -> List[GatewayCoordinator]:
        """Get all gateway coordinators.
        
        Returns:
            List of GatewayCoordinator instances
        """
        return list(self.gateways.values())

    def get_all_devices(self) -> List[tuple[str, BaseDevice]]:
        """Get all devices from all gateways.
        
        Returns:
            List of (gateway_id, device) tuples
        """
        result = []
        for gateway_id, gateway in self.gateways.items():
            for device in gateway.devices.values():
                result.append((gateway_id, device))
        return result
