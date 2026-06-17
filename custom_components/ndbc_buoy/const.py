"""Constants for the NDBC Ocean Buoy integration."""

from __future__ import annotations

DOMAIN = "ndbc_buoy"

CONF_STATION_ID = "station_id"

DEFAULT_SCAN_INTERVAL_MINUTES = 10
MIN_SCAN_INTERVAL_MINUTES = 5
MAX_SCAN_INTERVAL_MINUTES = 120

RSS_URL = "https://www.ndbc.noaa.gov/data/latest_obs/{station_id}.rss"
TXT_URL = "https://www.ndbc.noaa.gov/data/latest_obs/{station_id}.txt"
STATION_PAGE_URL = "https://www.ndbc.noaa.gov/station_page.php?station={station_id}"

MANUFACTURER = "NOAA National Data Buoy Center"
