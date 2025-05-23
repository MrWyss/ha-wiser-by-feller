"""Base entity class for Wiser by Feller integration."""

from __future__ import annotations

from aiowiserbyfeller import Device, Load
from aiowiserbyfeller.util import parse_wiser_device_ref_c
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN
from .const import MANUFACTURER
from .coordinator import WiserCoordinator, get_unique_id
from .util import resolve_device_name


class WiserEntity(CoordinatorEntity):
    """Wiser by Feller base entity."""

    def __init__(
        self,
        coordinator: WiserCoordinator,
        load: Load | None,
        device: Device,
        room: dict | None,
    ) -> None:
        """Set up base entity."""
        super().__init__(coordinator)  # TODO: Is this required?
        info = parse_wiser_device_ref_c(device.c["comm_ref"])

        self.coordinator_context = (
            device.id if load is None else load.id
        )  # TODO: Suboptimal
        self.coordinator = coordinator
        self._attr_has_entity_name = True
        self._attr_name = None
        self._attr_raw_unique_id = get_unique_id(device, load)
        self._attr_unique_id = self._attr_raw_unique_id
        self._device = device
        self._device_name = resolve_device_name(device, room, load)
        self._is_gateway = info["wlan"]
        self._load = load
        self._room = room

    @property
    def raw_unique_id(self) -> str:
        """Raw unique ID based on device id and channel number (if applicable).

        This is required to identify the logical device in Home Assistant,
        as entities like the "identify" button, which do not have an own identifier,
        append their own suffix to the unique identifier for uniqueness. This would
        cause the same logical device to appear as two separate devices in HA.
        """
        return self._attr_raw_unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        model_id = (
            f"{self._device.c['comm_ref']} + {self._device.a['comm_ref']}"
            if self._device.c["comm_ref"] != self._device.a["comm_ref"]
            else self._device.a["comm_ref"]
        )
        model = (
            f"{self._device.c_name} + {self._device.a_name}"
            if self._device.c_name != self._device.a_name
            else self._device.a_name
        )
        firmware = (
            f"{self._device.c['fw_version']} (Controls) / {self._device.a['fw_version']} (Actuator)"
            if self._device.c["fw_version"] != self._device.a["fw_version"]
            else self._device.a["fw_version"]
        )
        url = f"http://{self.coordinator.api_host}" if self._is_gateway else None
        area = None if self._room is None else self._room["name"]
        via = (
            (DOMAIN, self.coordinator.gateway.combined_serial_number)
            if self.coordinator.gateway is not None and not self._is_gateway
            else None
        )

        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    self.raw_unique_id,
                ),  # Either "<device-id> or <device-id>_<load-channel>"
            },
            name=resolve_device_name(self._device, self._room, self._load),
            manufacturer=MANUFACTURER,
            model=model,
            model_id=model_id,
            sw_version=firmware,
            serial_number=self._device.combined_serial_number,
            suggested_area=area,
            configuration_url=url,
            via_device=via,
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated entity data from the coordinator."""
        self._load.raw_state = self.coordinator.states[self._load.id]
        self.async_write_ha_state()
