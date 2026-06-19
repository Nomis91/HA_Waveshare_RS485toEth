"""Health monitoring for gateways and devices."""

import logging
import time
from typing import Optional

from ..const import (
    DEFAULT_CONSECUTIVE_FAILURES_ERROR,
    DEFAULT_CONSECUTIVE_FAILURES_OFFLINE,
    DEFAULT_RESPONSE_TIME_WARNING,
    HEALTH_STATE_DEGRADED,
    HEALTH_STATE_ERROR,
    HEALTH_STATE_HEALTHY,
    HEALTH_STATE_OFFLINE,
    HEALTH_STATE_WARNING,
)

_LOGGER = logging.getLogger(__name__)


class HealthMetrics:
    """Tracks health metrics for a gateway or device."""

    def __init__(
        self,
        response_time_warning_ms: int = DEFAULT_RESPONSE_TIME_WARNING,
        consecutive_failures_error: int = DEFAULT_CONSECUTIVE_FAILURES_ERROR,
        consecutive_failures_offline: int = DEFAULT_CONSECUTIVE_FAILURES_OFFLINE,
    ):
        """Initialize health metrics tracker.
        
        Args:
            response_time_warning_ms: Response time threshold for warning state
            consecutive_failures_error: Failure count threshold for error state
            consecutive_failures_offline: Failure count threshold for offline state
        """
        self.response_time_warning_ms = response_time_warning_ms
        self.consecutive_failures_error = consecutive_failures_error
        self.consecutive_failures_offline = consecutive_failures_offline
        
        # Connection tracking
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._connection_start_time: Optional[float] = None
        self._last_successful_read: Optional[float] = None
        
        # Response time tracking
        self._response_times: list[float] = []
        self._max_response_times = 100  # Keep last 100 response times
        
        # Connection state
        self._current_state = HEALTH_STATE_HEALTHY

    def record_success(self, response_time_ms: float) -> str:
        """Record a successful read operation.
        
        Args:
            response_time_ms: Response time in milliseconds
            
        Returns:
            New health state
        """
        self._consecutive_failures = 0
        self._consecutive_successes += 1
        self._last_successful_read = time.time()
        
        # Track response times
        self._response_times.append(response_time_ms)
        if len(self._response_times) > self._max_response_times:
            self._response_times.pop(0)
        
        # Initialize connection time if needed
        if self._connection_start_time is None:
            self._connection_start_time = time.time()
        
        # Update state based on response time
        if response_time_ms > self.response_time_warning_ms:
            self._current_state = HEALTH_STATE_WARNING
        elif self._current_state in (HEALTH_STATE_ERROR, HEALTH_STATE_OFFLINE):
            self._current_state = HEALTH_STATE_HEALTHY
        elif self._current_state == HEALTH_STATE_DEGRADED and self._consecutive_successes > 3:
            self._current_state = HEALTH_STATE_HEALTHY
        
        return self._current_state

    def record_failure(self) -> str:
        """Record a failed read operation.
        
        Returns:
            New health state
        """
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        
        # Update state based on failure count
        if self._consecutive_failures > self.consecutive_failures_offline:
            self._current_state = HEALTH_STATE_OFFLINE
        elif self._consecutive_failures > self.consecutive_failures_error:
            self._current_state = HEALTH_STATE_ERROR
        elif self._consecutive_failures > 2:
            self._current_state = HEALTH_STATE_DEGRADED
        
        return self._current_state

    def get_state(self) -> str:
        """Get current health state."""
        return self._current_state

    def get_average_response_time(self) -> float:
        """Get average response time in milliseconds."""
        if not self._response_times:
            return 0.0
        return sum(self._response_times) / len(self._response_times)

    def get_last_successful_read(self) -> Optional[float]:
        """Get timestamp of last successful read."""
        return self._last_successful_read

    def get_uptime(self) -> float:
        """Get connection uptime in seconds."""
        if self._connection_start_time is None:
            return 0.0
        return time.time() - self._connection_start_time

    def get_consecutive_failures(self) -> int:
        """Get number of consecutive failures."""
        return self._consecutive_failures

    def get_signal_quality(self) -> float:
        """Calculate signal quality percentage (0-100%).
        
        Based on:
        - Success rate (weighted 60%)
        - Average response time (weighted 30%)
        - Uptime (weighted 10%)
        """
        # This will be calculated based on error tracker data
        # For now, return based on current state
        state_quality = {
            HEALTH_STATE_HEALTHY: 100.0,
            HEALTH_STATE_WARNING: 80.0,
            HEALTH_STATE_DEGRADED: 60.0,
            HEALTH_STATE_ERROR: 30.0,
            HEALTH_STATE_OFFLINE: 0.0,
        }
        return state_quality.get(self._current_state, 50.0)

    def reset(self) -> None:
        """Reset all health metrics."""
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._connection_start_time = None
        self._last_successful_read = None
        self._response_times = []
        self._current_state = HEALTH_STATE_HEALTHY


class HealthMonitor:
    """Monitors health of gateways and devices."""

    def __init__(self):
        """Initialize health monitor."""
        self._gateway_health: dict[str, HealthMetrics] = {}
        self._device_health: dict[tuple[str, int], HealthMetrics] = {}

    def get_gateway_health(
        self,
        gateway_id: str,
        create_if_missing: bool = True,
        **kwargs,
    ) -> HealthMetrics:
        """Get health metrics for a gateway.
        
        Args:
            gateway_id: Gateway identifier
            create_if_missing: Create if not exists
            **kwargs: Additional arguments for HealthMetrics
            
        Returns:
            HealthMetrics instance
        """
        if gateway_id not in self._gateway_health:
            if not create_if_missing:
                return None
            self._gateway_health[gateway_id] = HealthMetrics(**kwargs)
        
        return self._gateway_health[gateway_id]

    def get_device_health(
        self,
        gateway_id: str,
        slave_id: int,
        create_if_missing: bool = True,
        **kwargs,
    ) -> HealthMetrics:
        """Get health metrics for a device.
        
        Args:
            gateway_id: Gateway identifier
            slave_id: Modbus slave ID
            create_if_missing: Create if not exists
            **kwargs: Additional arguments for HealthMetrics
            
        Returns:
            HealthMetrics instance
        """
        key = (gateway_id, slave_id)
        if key not in self._device_health:
            if not create_if_missing:
                return None
            self._device_health[key] = HealthMetrics(**kwargs)
        
        return self._device_health[key]

    def record_gateway_success(
        self,
        gateway_id: str,
        response_time_ms: float,
    ) -> str:
        """Record successful gateway operation.
        
        Args:
            gateway_id: Gateway identifier
            response_time_ms: Response time in milliseconds
            
        Returns:
            New health state
        """
        health = self.get_gateway_health(gateway_id)
        return health.record_success(response_time_ms)

    def record_gateway_failure(self, gateway_id: str) -> str:
        """Record failed gateway operation.
        
        Args:
            gateway_id: Gateway identifier
            
        Returns:
            New health state
        """
        health = self.get_gateway_health(gateway_id)
        return health.record_failure()

    def record_device_success(
        self,
        gateway_id: str,
        slave_id: int,
        response_time_ms: float,
    ) -> str:
        """Record successful device read.
        
        Args:
            gateway_id: Gateway identifier
            slave_id: Modbus slave ID
            response_time_ms: Response time in milliseconds
            
        Returns:
            New health state
        """
        health = self.get_device_health(gateway_id, slave_id)
        return health.record_success(response_time_ms)

    def record_device_failure(self, gateway_id: str, slave_id: int) -> str:
        """Record failed device read.
        
        Args:
            gateway_id: Gateway identifier
            slave_id: Modbus slave ID
            
        Returns:
            New health state
        """
        health = self.get_device_health(gateway_id, slave_id)
        return health.record_failure()

    def get_gateway_state(self, gateway_id: str) -> str:
        """Get current health state of a gateway."""
        health = self.get_gateway_health(gateway_id, create_if_missing=False)
        return health.get_state() if health else HEALTH_STATE_HEALTHY

    def get_device_state(self, gateway_id: str, slave_id: int) -> str:
        """Get current health state of a device."""
        health = self.get_device_health(gateway_id, slave_id, create_if_missing=False)
        return health.get_state() if health else HEALTH_STATE_HEALTHY

    def get_all_gateway_states(self) -> dict[str, str]:
        """Get health states of all gateways."""
        return {gw_id: health.get_state() for gw_id, health in self._gateway_health.items()}

    def get_all_device_states(self, gateway_id: str) -> dict[int, str]:
        """Get health states of all devices on a gateway."""
        result = {}
        for (gw_id, slave_id), health in self._device_health.items():
            if gw_id == gateway_id:
                result[slave_id] = health.get_state()
        return result
