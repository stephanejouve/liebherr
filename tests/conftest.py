"""Pytest fixtures partagées — mocks coordinator, api, appliances, notifications.

Isole les tests du custom_component HA de toute vraie HA runtime (pas de need
`hass` fixture). On mock le coordinator et le payload notifications directement.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def appliance_boree() -> dict[str, Any]:
    """Sample appliance payload matching Liebherr HomeAPI shape."""
    return {
        "deviceId": "boree-device-uuid",
        "model": "RBbsb 525i",
        "image": "https://liebherr.example/img.jpg",
        "nickname": "Borée",
        "applianceType": "FRIDGE",
        "controls": [],
    }


@pytest.fixture
def notification_door_alarm_active() -> dict[str, Any]:
    """Sample non-acknowledged door_alarm notification for Borée."""
    return {
        "deviceId": "boree-device-uuid",
        "notificationId": "notif-door-1",
        "notificationType": "door_alarm",
        "isAcknowledged": False,
        "createdAt": "2026-09-20T15:00:00Z",
    }


@pytest.fixture
def notification_door_alarm_acknowledged() -> dict[str, Any]:
    """Same door_alarm but acknowledged — must NOT trigger sensor ON."""
    return {
        "deviceId": "boree-device-uuid",
        "notificationId": "notif-door-2",
        "notificationType": "door_alarm",
        "isAcknowledged": True,
        "createdAt": "2026-09-20T14:00:00Z",
    }


@pytest.fixture
def notification_temperature_upper() -> dict[str, Any]:
    """Upper temperature alarm — matched by temperature_alarm sensor."""
    return {
        "deviceId": "boree-device-uuid",
        "notificationId": "notif-temp-1",
        "notificationType": "upper_temperature_alarm",
        "isAcknowledged": False,
        "createdAt": "2026-09-20T15:00:00Z",
    }


@pytest.fixture
def notification_other_device() -> dict[str, Any]:
    """door_alarm but for a different appliance — must NOT trigger our sensor."""
    return {
        "deviceId": "someone-else-device-uuid",
        "notificationId": "notif-other-1",
        "notificationType": "door_alarm",
        "isAcknowledged": False,
        "createdAt": "2026-09-20T15:00:00Z",
    }


class FakeCoordinator:
    """Minimal DataUpdateCoordinator mock exposing `data` and `last_update_success`."""

    def __init__(self, notifications: list[dict[str, Any]] | None = None) -> None:
        self.data: dict[str, Any] = {
            "appliances": [],
            "notifications": notifications or [],
        }
        self.last_update_success: bool = True

    async def async_request_refresh(self) -> None:
        """No-op in tests — data is set directly."""
        return


@pytest.fixture
def make_coordinator():
    """Factory returning a FakeCoordinator with the given notifications."""

    def _factory(notifications: list[dict[str, Any]] | None = None) -> FakeCoordinator:
        return FakeCoordinator(notifications=notifications)

    return _factory
