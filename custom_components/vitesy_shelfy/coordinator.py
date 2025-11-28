from datetime import timedelta
import logging
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

class VitesyDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api):
        super().__init__(
            hass,
            _LOGGER,
            name="vitesy_shelfy",
            update_interval=timedelta(minutes=15),
        )
        self.entry = entry
        self.api = api
        self.devices = []

    async def _async_update_data(self):
        try:
            self.devices = await self._get_devices()
            for device in self.devices:
                device_id = device["id"]
                device_type = device["type"]
                firmware_version = device["firmware_version"]
                # device["apikey"] = await self._get_or_create_api_key()
                device["measurements"] = await self._get_measurements(device_id)
                device["maintenancehistory"] = await self._get_maintenance(device_id)
                device["programs"] = await self._get_programs(device_type, firmware_version)
            return self.devices
        except Exception as err:
            raise UpdateFailed(f"Error fetching Vitesy data: {err}")

    async def _get_devices(self):
        return await self.hass.async_add_executor_job(self.api.get_devices)

    async def _get_measurements(self, device_id):
        return await self.hass.async_add_executor_job(self.api.get_measurements, device_id)

    async def _get_maintenance(self, device_id):
        return await self.hass.async_add_executor_job(self.api.get_maintenance, device_id)

    async def _get_programs(self, device_type, firmware_version):
        return await self.hass.async_add_executor_job(self.api.get_programs, device_type, firmware_version)

    # async def _get_or_create_api_key(self):
        # return await self.hass.async_add_executor_job(self.api.get_or_create_api_key)
