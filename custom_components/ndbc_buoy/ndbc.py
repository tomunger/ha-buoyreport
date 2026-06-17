"""Fetch and parse NDBC latest-observation RSS feeds.

Only the ``latest_obs/<station>.rss`` feed is used: it is the one feed that
covers both offshore buoys and land stations, and it provides decimal lat/lon,
the full station name, and metric values for temperature and pressure. The
swell / wind-wave decomposition is intentionally not parsed (it only exists in
the fragile free-text feed for a subset of stations).
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING

from .const import RSS_URL, TXT_URL

if TYPE_CHECKING:
    import aiohttp

# Fields the .txt feed can contribute in the same units we store. They are only
# used to fill gaps the RSS feed left empty (RSS wins to keep metric values).
_TXT_FILL_KEYS = (
    "wind_cardinal",
    "wind_bearing",
    "wind_speed",
    "wind_gust",
    "wave_height",
    "wave_period",
)

# Swell / wind-wave decomposition only ever comes from the .txt feed.
_TXT_DECOMP_KEYS = (
    "swell_height",
    "swell_period",
    "swell_direction",
    "wind_wave_height",
    "wind_wave_period",
    "wind_wave_direction",
)

_GEORSS_POINT = "{http://www.georss.org/georss}point"


class StationNotFound(Exception):
    """Raised when NDBC has no feed for the requested station."""


class StationFetchError(Exception):
    """Raised when the feed cannot be fetched or parsed."""


def _get_field(desc: str, label: str) -> str | None:
    """Return the text after ``<strong>Label:</strong>`` up to the next break."""
    match = re.search(
        rf"<strong>{re.escape(label)}:</strong>\s*(.*?)<br", desc, re.IGNORECASE
    )
    return match.group(1).strip() if match else None


def _lead_float(text: str | None) -> float | None:
    """Parse the first number in a string (e.g. ``1.9 knots`` -> 1.9)."""
    if not text:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def _paren_float(text: str | None, unit: str) -> float | None:
    """Parse the parenthesised value for ``unit`` (e.g. ``(1020.0 mb)`` -> 1020.0)."""
    if not text:
        return None
    match = re.search(r"\(([-+]?\d+(?:\.\d+)?)\s*" + unit + r"\)", text)
    return float(match.group(1)) if match else None


def _cardinal(text: str | None) -> str | None:
    """Parse the cardinal direction prefix (e.g. ``NW (310°)`` -> ``NW``)."""
    if not text:
        return None
    match = re.match(r"\s*([NSEW]+)", text)
    return match.group(1) if match else None


def _extract_name(title: str) -> str:
    """Strip the ``Station <id> - `` prefix from the RSS item title."""
    match = re.match(r"\s*Station\s+\S+\s*-\s*(.*)$", title, re.IGNORECASE)
    return match.group(1).strip() if match else title.strip()


def parse_rss(xml_text: str) -> dict:
    """Parse a station RSS document into a flat dict of observation fields.

    Missing observations are represented as ``None`` so callers can decide
    which sensors to create.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as err:
        raise StationFetchError(f"malformed RSS: {err}") from err

    item = root.find("./channel/item")
    if item is None:
        raise StationFetchError("RSS feed contained no observation item")

    title = item.findtext("title") or ""
    pub_date = item.findtext("pubDate")
    observation_time: datetime | None = None
    if pub_date:
        try:
            observation_time = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError):
            observation_time = None

    latitude = longitude = None
    point = item.findtext(_GEORSS_POINT)
    if point:
        parts = point.split()
        if len(parts) == 2:
            try:
                latitude, longitude = float(parts[0]), float(parts[1])
            except ValueError:
                latitude = longitude = None

    desc = html.unescape(item.findtext("description") or "")
    wind_dir = _get_field(desc, "Wind Direction")

    return {
        "name": _extract_name(title),
        "latitude": latitude,
        "longitude": longitude,
        "observation_time": observation_time,
        "wind_bearing": _paren_float(wind_dir, r"°"),
        "wind_cardinal": _cardinal(wind_dir),
        "wind_speed": _lead_float(_get_field(desc, "Wind Speed")),
        "wind_gust": _lead_float(_get_field(desc, "Wind Gust")),
        "wave_height": _lead_float(_get_field(desc, "Significant Wave Height")),
        "wave_period": _lead_float(_get_field(desc, "Dominant Wave Period")),
        "pressure": _paren_float(_get_field(desc, "Atmospheric Pressure"), "mb"),
        "pressure_tendency": _paren_float(_get_field(desc, "Pressure Tendency"), "mb"),
        "air_temp": _paren_float(_get_field(desc, "Air Temperature"), r"°?C"),
        "dew_point": _paren_float(_get_field(desc, "Dew Point"), r"°?C"),
        "water_temp": _paren_float(_get_field(desc, "Water Temperature"), r"°?C"),
    }


def _re_float(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None


def _re_str(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def _between(text: str, start: str, end: str) -> str:
    """Return the slice from ``start`` up to ``end`` (or end of text)."""
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start))
    return text[i:] if j < 0 else text[i:j]


def _after(text: str, start: str) -> str:
    i = text.find(start)
    return text[i:] if i >= 0 else ""


def parse_txt(text: str) -> dict:
    """Parse the free-text ``latest_obs/<id>.txt`` feed.

    Only the wave decomposition and a few same-unit scalar fields are extracted;
    temperatures and pressure are deliberately ignored (the txt reports them in
    °F / inHg, which would conflict with the metric values from the RSS feed).

    The "Wave Summary" block repeats the ``Period:`` and ``Direction:`` labels
    for both swell and wind wave, so those are parsed positionally by slicing
    the text into a swell section and a wind-wave section.
    """
    swell = _between(text, "Swell:", "Wind Wave:")
    windwave = _after(text, "Wind Wave:")

    return {
        "wind_cardinal": _re_str(text, r"Wind:\s*([NSEW]+)"),
        "wind_bearing": _re_float(text, r"Wind:[^(]*\((\d+)"),
        "wind_speed": _re_float(text, r"Wind:[^,]*,\s*([-+]?\d+(?:\.\d+)?)\s*kt"),
        "wind_gust": _re_float(text, r"Gust:\s*([-+]?\d+(?:\.\d+)?)\s*kt"),
        # "Seas:" / "Peak Period:" are the significant-wave fields some stations
        # report inline instead of a full decomposition.
        "wave_height": _re_float(text, r"Seas:\s*([-+]?\d+(?:\.\d+)?)\s*ft"),
        "wave_period": _re_float(text, r"Peak Period:\s*([-+]?\d+(?:\.\d+)?)\s*sec"),
        "swell_height": _re_float(swell, r"Swell:\s*([-+]?\d+(?:\.\d+)?)\s*ft"),
        "swell_period": _re_float(swell, r"Period:\s*([-+]?\d+(?:\.\d+)?)\s*sec"),
        "swell_direction": _re_str(swell, r"Direction:\s*([NSEW]+)"),
        "wind_wave_height": _re_float(
            windwave, r"Wind Wave:\s*([-+]?\d+(?:\.\d+)?)\s*ft"
        ),
        "wind_wave_period": _re_float(
            windwave, r"Period:\s*([-+]?\d+(?:\.\d+)?)\s*sec"
        ),
        "wind_wave_direction": _re_str(windwave, r"Direction:\s*([NSEW]+)"),
    }


def merge_txt(data: dict, txt: dict) -> dict:
    """Merge .txt-derived fields into the RSS-derived ``data`` in place.

    The decomposition is always taken from the txt feed; the remaining
    same-unit fields only fill gaps the RSS feed left empty (RSS wins).
    """
    for key in _TXT_DECOMP_KEYS:
        data[key] = txt.get(key)
    for key in _TXT_FILL_KEYS:
        if data.get(key) is None and txt.get(key) is not None:
            data[key] = txt[key]
    return data


async def _fetch(
    session: aiohttp.ClientSession, url: str, station_id: str, encoding: str
) -> str:
    """Fetch a URL as text, decoding with an explicit encoding.

    The .txt feed is served as Latin-1 (degree sign 0xB0); decoding RSS as
    UTF-8. ``errors="replace"`` keeps a stray byte from aborting a parse.
    """
    import aiohttp

    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 404:
                raise StationNotFound(station_id)
            resp.raise_for_status()
            raw = await resp.read()
    except aiohttp.ClientError as err:
        raise StationFetchError(str(err)) from err

    return raw.decode(encoding, errors="replace")


async def async_fetch_station(
    session: aiohttp.ClientSession, station_id: str
) -> dict:
    """Fetch and merge the RSS and .txt latest-observation feeds.

    The RSS feed is required (it carries the name, location, and metric values).
    The .txt feed is best-effort: if it fails, wave decomposition is simply
    absent for this cycle.
    """
    rss_text = await _fetch(
        session, RSS_URL.format(station_id=station_id), station_id, "utf-8"
    )
    if "<rss" not in rss_text.lower():
        # NDBC serves an HTML error page for unknown stations.
        raise StationNotFound(station_id)

    data = parse_rss(rss_text)

    try:
        txt_text = await _fetch(
            session, TXT_URL.format(station_id=station_id), station_id, "latin-1"
        )
    except (StationFetchError, StationNotFound):
        return data

    merge_txt(data, parse_txt(txt_text))
    return data
