import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN
from .coordinator import VitesyDataUpdateCoordinator
from .api import VitesyOAuth
# from .vitesy_api import VitesyAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    session = async_get_clientsession(hass)
    email = entry.data["email"]
    password = entry.data["password"]

    # ✅ Restore correct authentication+API layering
    api = VitesyOAuth(email, password, session)
    await hass.async_add_executor_job(api.login)
    # api = VitesyAPI(oauth)

    coordinator = VitesyDataUpdateCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "button"])

    return True