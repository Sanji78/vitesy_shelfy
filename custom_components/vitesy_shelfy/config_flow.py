import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD
from .api import VitesyOAuth
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class VitesyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vitesy Shelfy."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            session = async_get_clientsession(self.hass)
            api = VitesyOAuth(email, password, session)
            try:
                await self.hass.async_add_executor_job(api.login)
                if not api.access_token:
                    errors["base"] = "invalid_auth"
                else:
                    return self.async_create_entry(title=email, data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        "access_token": api.access_token,
                        "refresh_token": api.refresh_token,
                        "token_expires": api.expires_at,
                    })
            except Exception as e:
                _LOGGER.exception("Error logging in to Vitesy API: %s", e)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return VitesyOptionsFlowHandler(config_entry)


class VitesyOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_create_entry(title="", data={})
