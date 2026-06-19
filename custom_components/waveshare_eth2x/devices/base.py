"""Base device class for all Deye devices."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..const import (
    FEATURE_AC_OUTPUT,
    FEATURE_BATTERY,
    FEATURE_GRID,
    FEATURE_SOLAR,
    REG_TYPE_FLOAT,
    REG_TYPE_INT16,
    REG_TYPE_INT32,
    REG_TYPE_UINT16,
    REG_TYPE_UINT32,
)
from ..core.protocol import ModbusRTU

_LOGGER = logging.getLogger(__name__)


class RegisterDef:
    """Definition of a Modbus register."""

    def __init__(
        self,
        address: int,
        data_type: str,
        unit: Optional[str] = None,
        icon: Optional[str] = None,
        mode: str = "read",
        scale: float = 1.0,
        offset: float = 0.0,
        name: Optional[str] = None,
    ):
        """Initialize register definition.
        
        Args:
            address: Modbus register address
            data_type: Data type (uint16, uint32, int16, int32, float)
            unit: Unit of measurement
            icon: Material Design Icon name
            mode: "read" or "write"
            scale: Scale factor to apply to raw value
            offset: Offset to add to scaled value
            name: Human-readable name
        """
        self.address = address
        self.data_type = data_type
        self.unit = unit
        self.icon = icon
        self.mode = mode
        self.scale = scale
        self.offset = offset
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "address": self.address,
            "data_type": self.data_type,
            "unit": self.unit,
            "icon": self.icon,
            "mode": self.mode,
            "scale": self.scale,
            "offset": self.offset,
            "name": self.name,
        }


class BaseDevice(ABC):
    """Base class for all device types."""

    # Device model identifier
    device_model: str = "UNKNOWN"
    
    # Supported features
    supported_features: List[str] = []
    
    # Human-readable device name
    device_name: str = "Unknown Device"

    def __init__(
        self,
        gateway_id: str,
        slave_id: int,
        device_name: Optional[str] = None,
    ):
        """Initialize device.
        
        Args:
            gateway_id: Parent gateway identifier
            slave_id: Modbus slave ID (1-247)
            device_name: Optional friendly name
        """
        self.gateway_id = gateway_id
        self.slave_id = slave_id
        self.device_name = device_name or self.device_name
        self._last_read_data: Dict[str, Any] = {}

    @property
    def register_map(self) -> Dict[str, RegisterDef]:
        """Get register mapping for this device.
        
        Must be implemented by subclass.
        
        Returns:
            Dictionary mapping register names to RegisterDef objects
        """
        return {}

    @property
    def health_sensors(self) -> Dict[str, str]:
        """Get health sensor definitions.
        
        Returns:
            Dictionary of health sensor names to descriptions
        """
        return {
            "connection_status": "Connection Status",
            "connection_state": "Connection State",
            "signal_quality": "Signal Quality",
            "response_time_ms": "Response Time (ms)",
            "last_successful_read": "Last Successful Read",
        }

    def has_feature(self, feature: str) -> bool:
        """Check if device supports a feature.
        
        Args:
            feature: Feature name (solar, battery, grid, ac_output)
            
        Returns:
            True if feature is supported
        """
        return feature in self.supported_features

    def get_feature_registers(self, feature: str) -> Dict[str, RegisterDef]:
        """Get all registers for a specific feature.
        
        Args:
            feature: Feature name
            
        Returns:
            Dictionary of registers belonging to this feature
        """
        if not self.has_feature(feature):
            return {}
        
        # Registers are grouped by prefix convention:
        # solar_*, battery_*, grid_*, output_*
        feature_prefix = f"{feature}_"
        return {
            name: reg_def
            for name, reg_def in self.register_map.items()
            if name.startswith(feature_prefix)
        }

    async def read_registers(
        self,
        register_names: List[str],
    ) -> Dict[str, Any]:
        """Read register values from device.
        
        This method should be implemented by integration coordinator,
        not by the device class itself.
        
        Args:
            register_names: List of register names to read
            
        Returns:
            Dictionary of register name to parsed value
        """
        # This is a placeholder - actual implementation in coordinator
        raise NotImplementedError("Must be implemented by coordinator")

    async def write_register(self, register_name: str, value: Any) -> bool:
        """Write value to a register.
        
        This method should be implemented by integration coordinator,
        not by the device class itself.
        
        Args:
            register_name: Register name
            value: Value to write
            
        Returns:
            True if successful
        """
        # This is a placeholder - actual implementation in coordinator
        raise NotImplementedError("Must be implemented by coordinator")

    def get_readable_registers(self) -> Dict[str, RegisterDef]:
        """Get all readable registers."""
        return {
            name: reg_def
            for name, reg_def in self.register_map.items()
            if reg_def.mode == "read"
        }

    def get_writable_registers(self) -> Dict[str, RegisterDef]:
        """Get all writable registers."""
        return {
            name: reg_def
            for name, reg_def in self.register_map.items()
            if reg_def.mode == "write"
        }

    def get_registers_by_address(self, start_addr: int, end_addr: int) -> Dict[str, RegisterDef]:
        """Get registers in address range.
        
        Args:
            start_addr: Start address (inclusive)
            end_addr: End address (inclusive)
            
        Returns:
            Dictionary of registers in range
        """
        return {
            name: reg_def
            for name, reg_def in self.register_map.items()
            if start_addr <= reg_def.address <= end_addr
        }

    def calculate_modbus_register_count(self) -> int:
        """Calculate total number of Modbus registers needed.
        
        Returns:
            Number of 16-bit registers
        """
        max_address = 0
        for reg_def in self.register_map.values():
            if reg_def.data_type in (REG_TYPE_UINT32, REG_TYPE_INT32, REG_TYPE_FLOAT):
                max_address = max(max_address, reg_def.address + 2)
            else:
                max_address = max(max_address, reg_def.address + 1)
        
        return max_address

    def get_device_info(self) -> Dict[str, Any]:
        """Get device information.
        
        Returns:
            Dictionary with device info
        """
        return {
            "model": self.device_model,
            "name": self.device_name,
            "gateway_id": self.gateway_id,
            "slave_id": self.slave_id,
            "features": self.supported_features,
            "register_count": len(self.register_map),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"{self.__class__.__name__}("
            f"model={self.device_model}, "
            f"slave_id={self.slave_id}, "
            f"name={self.device_name})"
        )
