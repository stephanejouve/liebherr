"""Pytest fixtures partagées — mocks coordinator, api, appliances, notifications.

Isole les tests du custom_component HA de toute vraie HA runtime (pas de need
`hass` fixture). On mock le coordinator et le payload notifications directement.

Stubs HA minimalistes ci-dessous : évite d'imposer un `pip install homeassistant`
(~200 MB) pour lancer les tests unitaires du binary_sensor. Suffit tant que le
sous-ensemble utilisé se limite à BinarySensorEntity + BinarySensorDeviceClass.
"""

from __future__ import annotations

import sys
from enum import Enum
from typing import Any
from unittest.mock import MagicMock

import pytest


# ─── HA stubs (à insérer AVANT tout import du custom_component) ────────────
class _BinarySensorDeviceClass(str, Enum):
    DOOR = "door"
    PROBLEM = "problem"


class _BinarySensorEntity:
    """Minimal stub of homeassistant.components.binary_sensor.BinarySensorEntity.

    Reproduit le contrat HA Entity : `.name` / `.unique_id` / `.device_class` /
    `.icon` lisent `_attr_*` (mécanisme HA standard depuis 2022).
    """

    @property
    def name(self):
        return getattr(self, "_attr_name", None)

    @property
    def unique_id(self):
        return getattr(self, "_attr_unique_id", None)

    @property
    def device_class(self):
        return getattr(self, "_attr_device_class", None)

    @property
    def icon(self):
        return getattr(self, "_attr_icon", None)


def _install_ha_stubs() -> None:
    if "homeassistant" in sys.modules:
        return  # HA vrai installé, on ne stub pas

    ha = MagicMock(name="homeassistant")
    ha_components = MagicMock(name="homeassistant.components")
    ha_bs = MagicMock(name="homeassistant.components.binary_sensor")
    ha_bs.BinarySensorEntity = _BinarySensorEntity
    ha_bs.BinarySensorDeviceClass = _BinarySensorDeviceClass
    ha_config_entries = MagicMock(name="homeassistant.config_entries")
    ha_core = MagicMock(name="homeassistant.core")

    sys.modules["homeassistant"] = ha
    sys.modules["homeassistant.components"] = ha_components
    sys.modules["homeassistant.components.binary_sensor"] = ha_bs
    sys.modules["homeassistant.config_entries"] = ha_config_entries
    sys.modules["homeassistant.core"] = ha_core


def _stub_liebherr_package() -> None:
    """Stub custom_components.liebherr package init to avoid pulling aiohttp
    / aiofiles / voluptuous just to unit-test binary_sensor.py.

    We create empty parent packages and inject a minimal `.const` module with
    just the DOMAIN constant that binary_sensor.py imports.
    """
    if "custom_components.liebherr" in sys.modules:
        return

    parent = MagicMock(name="custom_components")
    sys.modules.setdefault("custom_components", parent)

    liebherr_pkg = MagicMock(name="custom_components.liebherr")
    liebherr_pkg.__path__ = []  # marks as package
    sys.modules["custom_components.liebherr"] = liebherr_pkg

    const_stub = MagicMock(name="custom_components.liebherr.const")
    const_stub.DOMAIN = "liebherr"
    sys.modules["custom_components.liebherr.const"] = const_stub


_install_ha_stubs()
_stub_liebherr_package()


@pytest.fixture(scope="session")
def binary_sensor_module():
    """Load binary_sensor.py directly by file path to bypass package __init__."""
    import importlib.util
    from pathlib import Path

    module_path = (
        Path(__file__).resolve().parent.parent
        / "custom_components"
        / "liebherr"
        / "binary_sensor.py"
    )
    spec = importlib.util.spec_from_file_location(
        "custom_components.liebherr.binary_sensor",
        module_path,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["custom_components.liebherr.binary_sensor"] = module
    spec.loader.exec_module(module)
    return module


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
