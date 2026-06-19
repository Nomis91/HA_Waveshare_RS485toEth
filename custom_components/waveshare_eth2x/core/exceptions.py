"""Exceptions for Deye Sun 12K integration."""


class DeyeIntegrationError(Exception):
    """Base exception for Deye integration."""

    pass


class GatewayConnectionError(DeyeIntegrationError):
    """Raised when unable to connect to gateway."""

    pass


class GatewayTimeoutError(DeyeIntegrationError):
    """Raised when gateway connection times out."""

    pass


class ModbusError(DeyeIntegrationError):
    """Raised when Modbus communication fails."""

    pass


class ModbusCRCError(ModbusError):
    """Raised when CRC check fails."""

    pass


class ModbusResponseError(ModbusError):
    """Raised when Modbus returns an exception."""

    pass


class DeviceNotFoundError(DeyeIntegrationError):
    """Raised when device is not detected."""

    pass


class InvalidConfigError(DeyeIntegrationError):
    """Raised when configuration is invalid."""

    pass


class HealthMonitorError(DeyeIntegrationError):
    """Raised when health monitoring fails."""

    pass


class ErrorTrackerError(DeyeIntegrationError):
    """Raised when error tracking fails."""

    pass


class RegisterDefinitionError(DeyeIntegrationError):
    """Raised when register definition is invalid."""

    pass
