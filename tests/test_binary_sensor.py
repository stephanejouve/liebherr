"""Tests for custom_components.liebherr.binary_sensor.

Vérifie que les binary sensors "alarms" reflètent correctement l'état
des notifications remontées par le coordinator :

- Sensor ON ssi au moins une notification non-acknowledged du bon type
  pour le bon deviceId existe.
- Sensor OFF sinon (aucune notif, notif ack, notif d'un autre device,
  notif d'un autre type).

Pattern positif + contre-exemple (feedback CD 6701 : test négatif miroir).
"""

from __future__ import annotations

import pytest

from custom_components.liebherr.binary_sensor import (
    ALARM_DEFINITIONS,
    LiebherrAlarmBinarySensor,
)


def _find_alarm(alarm_key: str):
    """Retrouve la définition (suffix, notif_types, device_class, icon) par key."""
    for k, suffix, notif_types, device_class, icon in ALARM_DEFINITIONS:
        if k == alarm_key:
            return suffix, notif_types, device_class, icon
    raise KeyError(f"unknown alarm_key: {alarm_key}")


def _make_sensor(coordinator, appliance, alarm_key: str) -> LiebherrAlarmBinarySensor:
    suffix, notif_types, device_class, icon = _find_alarm(alarm_key)
    return LiebherrAlarmBinarySensor(
        coordinator=coordinator,
        appliance=appliance,
        alarm_key=alarm_key,
        suffix=suffix,
        notification_types=notif_types,
        device_class=device_class,
        icon=icon,
    )


# ─── door_alarm ────────────────────────────────────────────────────────────


def test_door_alarm_on_when_active_door_alarm_notification(
    make_coordinator, appliance_boree, notification_door_alarm_active
):
    """Sensor door_alarm = ON quand notif door_alarm active pour ce device."""
    coord = make_coordinator([notification_door_alarm_active])
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.is_on is True


def test_door_alarm_off_when_no_notification(make_coordinator, appliance_boree):
    """Sensor door_alarm = OFF quand aucune notif."""
    coord = make_coordinator([])
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.is_on is False


def test_door_alarm_off_when_notification_acknowledged(
    make_coordinator, appliance_boree, notification_door_alarm_acknowledged
):
    """Sensor door_alarm = OFF quand la notif door_alarm est acknowledged."""
    coord = make_coordinator([notification_door_alarm_acknowledged])
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.is_on is False


def test_door_alarm_off_when_notification_for_other_device(
    make_coordinator, appliance_boree, notification_other_device
):
    """Sensor door_alarm = OFF quand la notif est pour un autre appareil."""
    coord = make_coordinator([notification_other_device])
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.is_on is False


def test_door_alarm_off_when_notification_of_wrong_type(
    make_coordinator, appliance_boree, notification_temperature_upper
):
    """Sensor door_alarm = OFF quand la notif est temperature_alarm (mauvais type)."""
    coord = make_coordinator([notification_temperature_upper])
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.is_on is False


# ─── temperature_alarm (couvre upper_temperature_alarm ET lower_temperature_alarm) ──


def test_temperature_alarm_on_when_upper_temperature_alarm_active(
    make_coordinator, appliance_boree, notification_temperature_upper
):
    """Sensor temperature_alarm = ON quand upper_temperature_alarm active."""
    coord = make_coordinator([notification_temperature_upper])
    sensor = _make_sensor(coord, appliance_boree, "temperature_alarm")

    assert sensor.is_on is True


def test_temperature_alarm_on_when_lower_temperature_alarm_active(
    make_coordinator, appliance_boree
):
    """Sensor temperature_alarm = ON aussi pour lower_temperature_alarm (couverture 2 types)."""
    coord = make_coordinator(
        [
            {
                "deviceId": appliance_boree["deviceId"],
                "notificationId": "notif-temp-lo",
                "notificationType": "lower_temperature_alarm",
                "isAcknowledged": False,
                "createdAt": "2026-09-20T15:00:00Z",
            }
        ]
    )
    sensor = _make_sensor(coord, appliance_boree, "temperature_alarm")

    assert sensor.is_on is True


def test_temperature_alarm_off_when_door_alarm_only(
    make_coordinator, appliance_boree, notification_door_alarm_active
):
    """Sensor temperature_alarm = OFF quand la notif est door_alarm (mauvais type)."""
    coord = make_coordinator([notification_door_alarm_active])
    sensor = _make_sensor(coord, appliance_boree, "temperature_alarm")

    assert sensor.is_on is False


# ─── availability ──────────────────────────────────────────────────────────


def test_available_true_when_coordinator_last_update_success(
    make_coordinator, appliance_boree
):
    """available = True quand coordinator.last_update_success = True."""
    coord = make_coordinator([])
    coord.last_update_success = True
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.available is True


def test_available_false_when_coordinator_last_update_failed(
    make_coordinator, appliance_boree
):
    """available = False quand coordinator.last_update_success = False."""
    coord = make_coordinator([])
    coord.last_update_success = False
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.available is False


def test_is_on_returns_false_when_coordinator_data_is_none(
    appliance_boree,
):
    """is_on = False (safe fallback) si coordinator.data est None (initial state)."""
    from tests.conftest import FakeCoordinator

    coord = FakeCoordinator()
    coord.data = None
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.is_on is False


# ─── unique_id + naming ────────────────────────────────────────────────────


def test_unique_id_scoped_by_device_and_alarm_key(make_coordinator, appliance_boree):
    """unique_id combine deviceId + alarm_key pour éviter les collisions cross-appliance."""
    coord = make_coordinator([])
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.unique_id == "boree-device-uuid_door_alarm"


def test_name_uses_appliance_nickname(make_coordinator, appliance_boree):
    """Le name affiché utilise le nickname de l'appliance (ex Borée)."""
    coord = make_coordinator([])
    sensor = _make_sensor(coord, appliance_boree, "door_alarm")

    assert sensor.name == "Borée Door alarm"


# ─── alarm definitions coverage ────────────────────────────────────────────


def test_alarm_definitions_cover_the_5_documented_alarm_types():
    """Guarde-fou : on doit toujours exposer les 5 types d'alarmes documentés."""
    keys = {k for k, *_ in ALARM_DEFINITIONS}
    expected = {
        "door_alarm",
        "temperature_alarm",
        "door_overheat_alarm",
        "obstacle_alarm",
        "power_failure_alarm",
    }
    assert keys == expected
