"""Diagnostics support for Wiser by Feller integration."""

from __future__ import annotations

import json
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from . import DOMAIN

TO_REDACT = ["token", "serial_nr", "serial_number"]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    _coordinator = hass.data[DOMAIN][entry.entry_id]
    _loads_json = [load.raw_data for load in _coordinator.loads]

    _devices_json = [
        _coordinator.devices[device_id].raw_data for device_id in _coordinator.devices
    ]

    return {
        "entry_data": async_redact_data(entry.data, TO_REDACT),
        "loads": async_redact_data(_loads_json, TO_REDACT),
        "rooms": async_redact_data(_coordinator.rooms, TO_REDACT),
        "devices": async_redact_data(_devices_json, TO_REDACT),
        # TODO:  Gateway data
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry, device: DeviceEntry
) -> dict[str, Any]:
    """Return diagnostics for a device."""
    _coordinator = hass.data[DOMAIN][entry.entry_id]
    _device_id = next(iter(device.identifiers))[1].partition("_")[0]
    _device_data = _coordinator.devices[_device_id].raw_data

    return {
        "device": async_redact_data(json.loads(device.json_repr), TO_REDACT),
        "device_data": async_redact_data(_device_data, TO_REDACT),
    }
