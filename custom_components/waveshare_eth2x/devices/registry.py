"""Device registry and discovery."""

import logging
from typing import Dict, List, Optional, Type

from ..const import (
    DEVICE_TYPE_DEYE_HYBRID_GW4137,
    DEVICE_TYPE_DEYE_SUN_12K,
    DEVICE_TYPE_DEYE_SUN_6K,
    DEVICE_TYPE_DEYE_SUN_8K,
    DEVICE_TYPE_GENERIC_MODBUS,
    DEVICE_TYPE_PYTES_EBOX_48100R,
    SUPPORTED_DEVICE_MODELS,
)
from .base import BaseDevice

_LOGGER = logging.getLogger(__name__)


class DeviceRegistry:
    """Registry for supported device types."""

    _device_classes: Dict[str, Type[BaseDevice]] = {}

    @classmethod
    def register(cls, device_type: str, device_class: Type[BaseDevice]) -> None:
        """Register a device type.
        
        Args:
            device_type: Device type identifier
            device_class: Device class (subclass of BaseDevice)
        """
        if not issubclass(device_class, BaseDevice):
            raise TypeError(f"{device_class} must be subclass of BaseDevice")
        
        cls._device_classes[device_type] = device_class
        _LOGGER.debug("Registered device type: %s -> %s", device_type, device_class.__name__)

    @classmethod
    def get_device_class(cls, device_type: str) -> Optional[Type[BaseDevice]]:
        """Get device class for type.
        
        Args:
            device_type: Device type identifier
            
        Returns:
            Device class or None if not found
        """
        return cls._device_classes.get(device_type)

    @classmethod
    def create_device(
        cls,
        device_type: str,
        gateway_id: str,
        slave_id: int,
        device_name: Optional[str] = None,
    ) -> Optional[BaseDevice]:
        """Create a device instance.
        
        Args:
            device_type: Device type identifier
            gateway_id: Parent gateway ID
            slave_id: Modbus slave ID
            device_name: Optional friendly name
            
        Returns:
            Device instance or None if type not found
        """
        device_class = cls.get_device_class(device_type)
        if not device_class:
            _LOGGER.warning("Unknown device type: %s", device_type)
            return None
        
        return device_class(
            gateway_id=gateway_id,
            slave_id=slave_id,
            device_name=device_name,
        )

    @classmethod
    def list_supported_types(cls) -> Dict[str, Dict]:
        """List all supported device types.
        
        Returns:
            Dictionary of device types to their metadata
        """
        return SUPPORTED_DEVICE_MODELS.copy()

    @classmethod
    def is_supported(cls, device_type: str) -> bool:
        """Check if device type is supported.
        
        Args:
            device_type: Device type identifier
            
        Returns:
            True if supported
        """
        return device_type in SUPPORTED_DEVICE_MODELS

    @classmethod
    def get_features(cls, device_type: str) -> List[str]:
        """Get supported features for a device type.
        
        Args:
            device_type: Device type identifier
            
        Returns:
            List of supported features
        """
        if device_type in SUPPORTED_DEVICE_MODELS:
            return SUPPORTED_DEVICE_MODELS[device_type].get("features", [])
        return []

    @classmethod
    def get_device_name(cls, device_type: str) -> str:
        """Get human-readable name for device type.
        
        Args:
            device_type: Device type identifier
            
        Returns:
            Device name
        """
        if device_type in SUPPORTED_DEVICE_MODELS:
            return SUPPORTED_DEVICE_MODELS[device_type].get("name", "Unknown")
        return "Unknown Device"


class DeviceDiscovery:
    """Device discovery for RS485 bus."""

    # Known device ID registers per manufacturer
    MODBUS_DEVICE_ID_ADDRESSES = {
        # Deye devices typically have device ID at 0x000B
        0x000B: "DEYE",
    }

    # Device signatures (device_id -> device_type)
    DEVICE_SIGNATURES = {
        # Deye Sun 12K
        0x0110: DEVICE_TYPE_DEYE_SUN_12K,
        # Deye Sun 8K
        0x0108: DEVICE_TYPE_DEYE_SUN_8K,
        # Deye Sun 6K
        0x0106: DEVICE_TYPE_DEYE_SUN_6K,
        # Deye Hybrid GW4137
        0x0200: DEVICE_TYPE_DEYE_HYBRID_GW4137,
        # Pytes E-Box 48100R
        0x4810: DEVICE_TYPE_PYTES_EBOX_48100R,
    }

    @staticmethod
    async def probe_device(
        gateway,
        slave_id: int,
    ) -> Optional[Dict]:
        """Probe a device to detect its type.
        
        Args:
            gateway: GatewayConnection instance
            slave_id: Modbus slave ID to probe
            
        Returns:
            Dictionary with device info, or None if no device found
        """
        try:
            from ..core.protocol import ModbusRTU
            from ..core.exceptions import ModbusError, GatewayConnectionError
            
            # Try to read device ID register
            for address in DeviceDiscovery.MODBUS_DEVICE_ID_ADDRESSES.keys():
                try:
                    request = ModbusRTU.frame_read_holding_registers(
                        slave_id=slave_id,
                        start_address=address,
                        quantity=1,
                    )
                    
                    response = await gateway.send_modbus_request(request)
                    parsed = ModbusRTU.parse_response(response, slave_id)
                    
                    if "registers" in parsed and len(parsed["registers"]) > 0:
                        device_id = parsed["registers"][0]
                        
                        if device_id in DeviceDiscovery.DEVICE_SIGNATURES:
                            device_type = DeviceDiscovery.DEVICE_SIGNATURES[device_id]
                            
                            return {
                                "slave_id": slave_id,
                                "device_type": device_type,
                                "device_id": device_id,
                                "manufacturer": "Deye",
                                "name": DeviceRegistry.get_device_name(device_type),
                            }
                        else:
                            # Unknown device, default to generic
                            return {
                                "slave_id": slave_id,
                                "device_type": DEVICE_TYPE_GENERIC_MODBUS,
                                "device_id": device_id,
                                "manufacturer": "Unknown",
                                "name": "Generic Modbus Device",
                            }
                        
                except (ModbusError, GatewayConnectionError):
                    continue
            
            return None
            
        except Exception as err:
            _LOGGER.warning("Error probing device %d: %s", slave_id, err)
            return None

    @staticmethod
    async def scan_gateway(
        gateway,
        slave_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        """Scan a gateway for devices.
        
        Args:
            gateway: GatewayConnection instance
            slave_ids: List of slave IDs to probe (1-247), defaults to all
            
        Returns:
            List of discovered devices
        """
        if slave_ids is None:
            slave_ids = list(range(1, 248))
        
        discovered = []
        
        _LOGGER.info("Scanning gateway for devices, %d addresses to probe", len(slave_ids))
        
        for slave_id in slave_ids:
            device_info = await DeviceDiscovery.probe_device(gateway, slave_id)
            if device_info:
                discovered.append(device_info)
                _LOGGER.info(
                    "Discovered device: %s (ID: 0x%04X) at slave ID %d",
                    device_info["name"],
                    device_info.get("device_id", 0),
                    slave_id,
                )
        
        _LOGGER.info("Device scan complete, found %d devices", len(discovered))
        return discovered
