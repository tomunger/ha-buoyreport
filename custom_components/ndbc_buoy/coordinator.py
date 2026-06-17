"""Data update coordinator for a single NDBC buoy."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .ndbc import StationFetchError, StationNotFound, async_fetch_station

_LOGGER = logging.getLogger(__name__)


class NdbcBuoyCoordinator(DataUpdateCoordinator[dict]):
    """Polls the NDBC RSS feed for one station."""

    def __init__(
        self, hass: HomeAssistant, station_id: str, interval_minutes: int
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{station_id}",
            update_interval=timedelta(minutes=interval_minutes),
        )
        self.station_id = station_id
        self._session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        try:
            return await async_fetch_station(self._session, self.station_id)
        except StationNotFound as err:
            raise UpdateFailed(f"Station {self.station_id} not found") from err
        except StationFetchError as err:
            raise UpdateFailed(str(err)) from err
