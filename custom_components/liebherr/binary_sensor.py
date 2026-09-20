"""Support for Liebherr binary sensors (alarms).

Expose the door/temperature/power alarms surfaced by the Liebherr HomeAPI
notifications endpoint as binary_sensor entities suitable for automations
(door left open detection, over-temperature alerts, obstacle warnings, etc).

Each appliance gets 5 binary sensors:

- <nickname>_door_alarm            (door left open, device_class=door)
- <nickname>_temperature_alarm     (upper OR lower temperature alarm, problem)
- <nickname>_door_overheat_alarm   (auto-door overheat, problem)
- <nickname>_obstacle_alarm        (auto-door obstacle, problem)
- <nickname>_power_failure_alarm   (upper OR lower power failure, problem)

State is derived from the coordinator's `notifications` list: sensor is ON
iff at least one non-acknowledged notification of the matching type(s)
exists for this deviceId.
"""

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


# (alarm_key, human_suffix, notification_types_matched, device_class, icon)
ALARM_DEFINITIONS = [
    (
        "door_alarm",
        "Door alarm",
        ("door_alarm",),
        BinarySensorDeviceClass.DOOR,
        "mdi:door-open",
    ),
    (
        "temperature_alarm",
        "Temperature alarm",
        ("upper_temperature_alarm", "lower_temperature_alarm"),
        BinarySensorDeviceClass.PROBLEM,
        "mdi:thermometer-alert",
    ),
    (
        "door_overheat_alarm",
        "Auto door overheat alarm",
        ("auto_door_overheat_alarm",),
        BinarySensorDeviceClass.PROBLEM,
        "mdi:door-sliding-lock",
    ),
    (
        "obstacle_alarm",
        "Auto door obstacle alarm",
        ("auto_door_obstacle_alarm",),
        BinarySensorDeviceClass.PROBLEM,
        "mdi:door-sliding",
    ),
    (
        "power_failure_alarm",
        "Power failure alarm",
        ("upper_power_failure_alarm", "lower_power_failure_alarm"),
        BinarySensorDeviceClass.PROBLEM,
        "mdi:power-plug-off",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up Liebherr binary sensors (alarms)."""
    api = hass.data[DOMAIN][config_entry.entry_id]["api"]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    appliances = await api.get_appliances()

    entities = []
    for appliance in appliances:
        for alarm_key, suffix, notif_types, device_class, icon in ALARM_DEFINITIONS:
            entities.append(
                LiebherrAlarmBinarySensor(
                    coordinator,
                    appliance,
                    alarm_key,
                    suffix,
                    notif_types,
                    device_class,
                    icon,
                )
            )

    async_add_entities(entities)


class LiebherrAlarmBinarySensor(BinarySensorEntity):
    """Binary sensor reflecting the presence of an active alarm notification."""

    should_poll = True

    def __init__(
        self,
        coordinator,
        appliance,
        alarm_key,
        suffix,
        notification_types,
        device_class,
        icon,
    ) -> None:
        """Initialize the alarm binary sensor."""
        self._coordinator = coordinator
        self._appliance = appliance
        self._alarm_key = alarm_key
        self._notification_types = tuple(notification_types)
        self._attr_device_class = device_class
        self._attr_icon = icon
        self._attr_name = f"{appliance['nickname']} {suffix}"
        self._attr_unique_id = f"{appliance['deviceId']}_{alarm_key}"

    @property
    def device_info(self):
        """Return device information for the binary sensor."""
        return {
            "identifiers": {(DOMAIN, self._appliance["deviceId"])},
            "name": self._appliance.get(
                "nickname",
                f"Liebherr HomeAPI Appliance {self._appliance['deviceId']}",
            ),
            "manufacturer": "Liebherr",
            "model": self._appliance.get("model", self._appliance["model"]),
            "sw_version": self._appliance.get("softwareVersion", ""),
        }

    @property
    def is_on(self):
        """Return True if at least one active notification matches this alarm type."""
        if not self._coordinator.data:
            return False
        notifications = self._coordinator.data.get("notifications") or []
        my_device_id = self._appliance["deviceId"]
        for n in notifications:
            if n.get("deviceId") != my_device_id:
                continue
            if n.get("isAcknowledged"):
                continue
            if n.get("notificationType") in self._notification_types:
                return True
        return False

    @property
    def available(self):
        """Return True if the sensor is available."""
        return self._coordinator.last_update_success

    async def async_update(self):
        """Refresh via the shared coordinator."""
        await self._coordinator.async_request_refresh()
