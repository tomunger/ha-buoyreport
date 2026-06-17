"""Config and options flow for the NDBC Ocean Buoy integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_STATION_ID,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)
from .ndbc import StationFetchError, StationNotFound, async_fetch_station


class NdbcBuoyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle adding a single buoy by station ID."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID].strip().lower()
            await self.async_set_unique_id(station_id)
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            try:
                data = await async_fetch_station(session, station_id)
            except StationNotFound:
                errors["base"] = "invalid_station"
            except StationFetchError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=data["name"] or station_id.upper(),
                    data={
                        CONF_STATION_ID: station_id,
                        "name": data["name"],
                        "latitude": data["latitude"],
                        "longitude": data["longitude"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_STATION_ID): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return NdbcBuoyOptionsFlow(config_entry)


class NdbcBuoyOptionsFlow(OptionsFlow):
    """Allow the poll interval to be changed after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL_MINUTES,
                            max=MAX_SCAN_INTERVAL_MINUTES,
                        ),
                    )
                }
            ),
        )
