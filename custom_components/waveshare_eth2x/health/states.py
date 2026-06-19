"""Health state definitions and utilities."""

from ..const import (
    HEALTH_STATE_DEGRADED,
    HEALTH_STATE_ERROR,
    HEALTH_STATE_HEALTHY,
    HEALTH_STATE_OFFLINE,
    HEALTH_STATE_WARNING,
)

# Health state descriptions
HEALTH_STATE_DESCRIPTIONS = {
    HEALTH_STATE_HEALTHY: "Connection is healthy",
    HEALTH_STATE_DEGRADED: "Connection is degraded, some errors detected",
    HEALTH_STATE_WARNING: "Connection has issues, slow response times",
    HEALTH_STATE_ERROR: "Multiple consecutive failures",
    HEALTH_STATE_OFFLINE: "Connection is offline",
}

# Health state icons
HEALTH_STATE_ICONS = {
    HEALTH_STATE_HEALTHY: "mdi:check-circle",
    HEALTH_STATE_DEGRADED: "mdi:alert-circle",
    HEALTH_STATE_WARNING: "mdi:alert",
    HEALTH_STATE_ERROR: "mdi:close-circle",
    HEALTH_STATE_OFFLINE: "mdi:wifi-off",
}

# Health state colors
HEALTH_STATE_COLORS = {
    HEALTH_STATE_HEALTHY: "#00FF00",  # Green
    HEALTH_STATE_DEGRADED: "#FFAA00",  # Orange
    HEALTH_STATE_WARNING: "#FF6600",  # Dark orange
    HEALTH_STATE_ERROR: "#FF0000",  # Red
    HEALTH_STATE_OFFLINE: "#808080",  # Gray
}


def get_health_state_description(state: str) -> str:
    """Get human-readable description for health state."""
    return HEALTH_STATE_DESCRIPTIONS.get(state, "Unknown state")


def get_health_state_icon(state: str) -> str:
    """Get Material Design Icon for health state."""
    return HEALTH_STATE_ICONS.get(state, "mdi:help-circle")


def get_health_state_color(state: str) -> str:
    """Get color hex code for health state."""
    return HEALTH_STATE_COLORS.get(state, "#808080")
