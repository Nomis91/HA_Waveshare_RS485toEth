"""Init file for core module."""

from .exceptions import (
    DeyeIntegrationError,
    DeviceNotFoundError,
    ErrorTrackerError,
    GatewayConnectionError,
    GatewayTimeoutError,
    HealthMonitorError,
    InvalidConfigError,
    ModbusCRCError,
    ModbusError,
    ModbusResponseError,
    RegisterDefinitionError,
)

__all__ = [
    "DeyeIntegrationError",
    "DeviceNotFoundError",
    "ErrorTrackerError",
    "GatewayConnectionError",
    "GatewayTimeoutError",
    "HealthMonitorError",
    "InvalidConfigError",
    "ModbusCRCError",
    "ModbusError",
    "ModbusResponseError",
    "RegisterDefinitionError",
]
