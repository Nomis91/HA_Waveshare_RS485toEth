"""Generic Modbus device template."""

from typing import Dict, Optional

from ..const import (
    DEVICE_TYPE_GENERIC_MODBUS,
    REG_TYPE_UINT16,
    UNIT_PERCENTAGE,
)
from .base import BaseDevice, RegisterDef


class GenericModbusDevice(BaseDevice):
    """Generic Modbus device for user-defined registers."""

    device_model = DEVICE_TYPE_GENERIC_MODBUS
    device_name = "Generic Modbus Device"
    supported_features = []  # No predefined features

    def __init__(
        self,
        gateway_id: str,
        slave_id: int,
        device_name: Optional[str] = None,
        register_definitions: Optional[Dict[str, RegisterDef]] = None,
    ):
        """Initialize generic Modbus device.
        
        Args:
            gateway_id: Parent gateway ID
            slave_id: Modbus slave ID
            device_name: Friendly name
            register_definitions: User-defined register mappings
        """
        super().__init__(gateway_id, slave_id, device_name)
        self._register_definitions = register_definitions or {}

    @property
    def register_map(self) -> Dict[str, RegisterDef]:
        """Get user-defined register mapping."""
        return self._register_definitions

    def set_register_definitions(self, definitions: Dict[str, RegisterDef]) -> None:
        """Update register definitions.
        
        Args:
            definitions: Dictionary of register names to RegisterDef
        """
        self._register_definitions = definitions
