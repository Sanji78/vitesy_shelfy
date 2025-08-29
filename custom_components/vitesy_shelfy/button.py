import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for device in coordinator.data:
        device_id = device["id"].replace(":", "")
        device_id_orig = device["id"]
        device_type = device.get("type", "Unknown").capitalize()
        entities.append(VitesyResetFilterButton(coordinator, device_id, device_id_orig, device_type))
        entities.append(VitesyResetFridgeButton(coordinator, device_id, device_id_orig, device_type))

    async_add_entities(entities, True)


class VitesyResetFilterButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, device_id, device_id_orig, device_type):
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_id_orig = device_id_orig
        self.device_type = device_type
        self._attr_unique_id = f"vitesy_{device_type.lower()}_{device_id}_filter_washed"
        self._attr_translation_key = "filter_washed"
        self._attr_has_entity_name = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "manufacturer": "Vitesy",
            "model": self.device_type,
            "name": f"Vitesy {self.device_type.title()}",
        }

    async def async_press(self):
        """Call the API to reset the filter maintenance period."""
        api = self.coordinator.api
        try:
            result = await self.hass.async_add_executor_job(api.reset_filter, self.device_id_orig)
            _LOGGER.info("Filter reset successful for %s: %s", self.device_id_orig, result)
        except Exception as e:
            _LOGGER.error("Failed to reset filter for %s: %s", self.device_id_orig, e)
            raise

class VitesyResetFridgeButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, device_id, device_id_orig, device_type):
        super().__init__(coordinator)
        self.device_id = device_id
        self.device_id_orig = device_id_orig
        self.device_type = device_type
        self._attr_unique_id = f"vitesy_{device_type.lower()}_{device_id}_fridge_washed"
        self._attr_translation_key = "fridge_washed"
        self._attr_has_entity_name = True

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "manufacturer": "Vitesy",
            "model": self.device_type,
            "name": f"Vitesy {self.device_type.title()}",
        }

    async def async_press(self):
        """Call the API to reset the fridge maintenance period."""
        api = self.coordinator.api
        try:
            result = await self.hass.async_add_executor_job(api.reset_fridge, self.device_id_orig)
            _LOGGER.info("Fridge reset successful for %s: %s", self.device_id_orig, result)
        except Exception as e:
            _LOGGER.error("Failed to reset fridge for %s: %s", self.device_id_orig, e)
            raise