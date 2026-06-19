"""Error tracking and statistics system."""

import json
import logging
from datetime import datetime, time as datetime_time
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..const import (
    ERROR_HISTORY_SIZE,
    ERROR_TYPE_CHECKSUM,
    ERROR_TYPE_COMMUNICATION,
    ERROR_TYPE_NO_RESPONSE,
    ERROR_TYPE_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class ErrorEvent:
    """Represents a single error event."""

    def __init__(self, error_type: str, timestamp: Optional[float] = None):
        """Initialize error event.
        
        Args:
            error_type: Type of error
            timestamp: Timestamp of error (defaults to now)
        """
        self.error_type = error_type
        self.timestamp = timestamp or datetime.now().timestamp()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error_type": self.error_type,
            "timestamp": self.timestamp,
        }


class ErrorTracker:
    """Tracks errors for a gateway or device."""

    def __init__(self):
        """Initialize error tracker."""
        # Lifetime counters
        self.total_errors = 0
        self.total_attempts = 0
        
        # Daily counters
        self.daily_errors = 0
        self.daily_attempts = 0
        self._daily_reset_date = self._get_date_key()
        
        # Monthly counters
        self.monthly_errors = 0
        self.monthly_attempts = 0
        self._monthly_reset_date = self._get_month_key()
        
        # Error type breakdown
        self.timeout_errors = 0
        self.checksum_errors = 0
        self.communication_errors = 0
        self.no_response_errors = 0
        
        # Error history
        self.error_history: List[ErrorEvent] = []

    def record_attempt(self, error_type: Optional[str] = None) -> None:
        """Record an attempt (successful or failed).
        
        Args:
            error_type: Type of error, or None if successful
        """
        self._check_daily_rollover()
        self._check_monthly_rollover()
        
        self.total_attempts += 1
        self.daily_attempts += 1
        self.monthly_attempts += 1
        
        if error_type:
            self.total_errors += 1
            self.daily_errors += 1
            self.monthly_errors += 1
            
            # Track error type
            if error_type == ERROR_TYPE_TIMEOUT:
                self.timeout_errors += 1
            elif error_type == ERROR_TYPE_CHECKSUM:
                self.checksum_errors += 1
            elif error_type == ERROR_TYPE_COMMUNICATION:
                self.communication_errors += 1
            elif error_type == ERROR_TYPE_NO_RESPONSE:
                self.no_response_errors += 1
            
            # Add to history
            event = ErrorEvent(error_type)
            self.error_history.append(event)
            if len(self.error_history) > ERROR_HISTORY_SIZE:
                self.error_history.pop(0)

    def get_daily_success_rate(self) -> float:
        """Get daily success rate 0-100%."""
        self._check_daily_rollover()
        if self.daily_attempts == 0:
            return 100.0
        return ((self.daily_attempts - self.daily_errors) / self.daily_attempts) * 100

    def get_monthly_success_rate(self) -> float:
        """Get monthly success rate 0-100%."""
        self._check_monthly_rollover()
        if self.monthly_attempts == 0:
            return 100.0
        return ((self.monthly_attempts - self.monthly_errors) / self.monthly_attempts) * 100

    def get_total_success_rate(self) -> float:
        """Get total success rate 0-100%."""
        if self.total_attempts == 0:
            return 100.0
        return ((self.total_attempts - self.total_errors) / self.total_attempts) * 100

    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by type."""
        return {
            "total": self.total_errors,
            "timeout": self.timeout_errors,
            "checksum": self.checksum_errors,
            "communication": self.communication_errors,
            "no_response": self.no_response_errors,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "total_errors": self.total_errors,
            "total_attempts": self.total_attempts,
            "daily_errors": self.daily_errors,
            "daily_attempts": self.daily_attempts,
            "monthly_errors": self.monthly_errors,
            "monthly_attempts": self.monthly_attempts,
            "daily_reset_date": self._daily_reset_date,
            "monthly_reset_date": self._monthly_reset_date,
            "error_breakdown": {
                "timeout": self.timeout_errors,
                "checksum": self.checksum_errors,
                "communication": self.communication_errors,
                "no_response": self.no_response_errors,
            },
            "error_history": [e.to_dict() for e in self.error_history],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorTracker":
        """Create from dictionary (for loading from storage)."""
        tracker = cls()
        
        tracker.total_errors = data.get("total_errors", 0)
        tracker.total_attempts = data.get("total_attempts", 0)
        tracker.daily_errors = data.get("daily_errors", 0)
        tracker.daily_attempts = data.get("daily_attempts", 0)
        tracker.monthly_errors = data.get("monthly_errors", 0)
        tracker.monthly_attempts = data.get("monthly_attempts", 0)
        tracker._daily_reset_date = data.get("daily_reset_date", tracker._get_date_key())
        tracker._monthly_reset_date = data.get(
            "monthly_reset_date", tracker._get_month_key()
        )
        
        # Check for daily/monthly rollover
        tracker._check_daily_rollover()
        tracker._check_monthly_rollover()
        
        error_breakdown = data.get("error_breakdown", {})
        tracker.timeout_errors = error_breakdown.get("timeout", 0)
        tracker.checksum_errors = error_breakdown.get("checksum", 0)
        tracker.communication_errors = error_breakdown.get("communication", 0)
        tracker.no_response_errors = error_breakdown.get("no_response", 0)
        
        # Load error history
        for event_data in data.get("error_history", []):
            event = ErrorEvent(
                event_data.get("error_type", "unknown"),
                event_data.get("timestamp"),
            )
            tracker.error_history.append(event)
        
        return tracker

    def _check_daily_rollover(self) -> None:
        """Check if day changed and reset daily counters."""
        current_date = self._get_date_key()
        if current_date != self._daily_reset_date:
            self.daily_errors = 0
            self.daily_attempts = 0
            self._daily_reset_date = current_date
            _LOGGER.debug("Daily error counters reset")

    def _check_monthly_rollover(self) -> None:
        """Check if month changed and reset monthly counters."""
        current_month = self._get_month_key()
        if current_month != self._monthly_reset_date:
            self.monthly_errors = 0
            self.monthly_attempts = 0
            self._monthly_reset_date = current_month
            _LOGGER.debug("Monthly error counters reset")

    @staticmethod
    def _get_date_key() -> str:
        """Get current date as string key (YYYY-MM-DD)."""
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def _get_month_key() -> str:
        """Get current month as string key (YYYY-MM)."""
        return datetime.now().strftime("%Y-%m")


class ErrorTrackerRegistry:
    """Registry for all error trackers."""

    def __init__(self):
        """Initialize registry."""
        self._gateway_trackers: Dict[str, ErrorTracker] = {}
        self._device_trackers: Dict[tuple[str, int], ErrorTracker] = {}

    def get_gateway_tracker(
        self,
        gateway_id: str,
        create_if_missing: bool = True,
    ) -> ErrorTracker:
        """Get error tracker for a gateway.
        
        Args:
            gateway_id: Gateway identifier
            create_if_missing: Create if not exists
            
        Returns:
            ErrorTracker instance
        """
        if gateway_id not in self._gateway_trackers:
            if not create_if_missing:
                return None
            self._gateway_trackers[gateway_id] = ErrorTracker()
        
        return self._gateway_trackers[gateway_id]

    def get_device_tracker(
        self,
        gateway_id: str,
        slave_id: int,
        create_if_missing: bool = True,
    ) -> ErrorTracker:
        """Get error tracker for a device.
        
        Args:
            gateway_id: Gateway identifier
            slave_id: Modbus slave ID
            create_if_missing: Create if not exists
            
        Returns:
            ErrorTracker instance
        """
        key = (gateway_id, slave_id)
        if key not in self._device_trackers:
            if not create_if_missing:
                return None
            self._device_trackers[key] = ErrorTracker()
        
        return self._device_trackers[key]

    def record_gateway_attempt(
        self,
        gateway_id: str,
        error_type: Optional[str] = None,
    ) -> None:
        """Record gateway attempt."""
        tracker = self.get_gateway_tracker(gateway_id)
        tracker.record_attempt(error_type)

    def record_device_attempt(
        self,
        gateway_id: str,
        slave_id: int,
        error_type: Optional[str] = None,
    ) -> None:
        """Record device attempt."""
        tracker = self.get_device_tracker(gateway_id, slave_id)
        tracker.record_attempt(error_type)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "gateways": {
                gw_id: tracker.to_dict()
                for gw_id, tracker in self._gateway_trackers.items()
            },
            "devices": {
                f"{gw_id}_{slave_id}": tracker.to_dict()
                for (gw_id, slave_id), tracker in self._device_trackers.items()
            },
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load from dictionary."""
        for gw_id, tracker_data in data.get("gateways", {}).items():
            self._gateway_trackers[gw_id] = ErrorTracker.from_dict(tracker_data)
        
        for key_str, tracker_data in data.get("devices", {}).items():
            parts = key_str.rsplit("_", 1)
            if len(parts) == 2:
                gw_id = parts[0]
                try:
                    slave_id = int(parts[1])
                    self._device_trackers[(gw_id, slave_id)] = ErrorTracker.from_dict(
                        tracker_data
                    )
                except ValueError:
                    _LOGGER.warning("Invalid device key: %s", key_str)
