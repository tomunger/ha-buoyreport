"""Tests for ndbc.parse_rss."""

from __future__ import annotations

import pytest


def _read(fixtures_dir, name):
    return (fixtures_dir / name).read_text(encoding="utf-8")


def test_full_station_parses_every_field(ndbc, fixtures_dir):
    data = ndbc.parse_rss(_read(fixtures_dir, "full.rss"))

    assert data["name"] == "La Perouse Bank"
    assert data["latitude"] == 48.84
    assert data["longitude"] == -126.0
    assert data["wind_bearing"] == 310.0
    assert data["wind_cardinal"] == "NW"
    assert data["wind_speed"] == 27.2
    assert data["wind_gust"] == 35.0
    assert data["wave_height"] == 9.8
    assert data["wave_period"] == 7.0
    # Metric value from the parentheses is used, not the English "30.06 in".
    assert data["pressure"] == 1018.1
    assert data["pressure_tendency"] == 0.1
    assert data["air_temp"] == 12.6
    assert data["dew_point"] == 11.2
    assert data["water_temp"] == 12.0


def test_observation_time_is_timezone_aware_utc(ndbc, fixtures_dir):
    data = ndbc.parse_rss(_read(fixtures_dir, "full.rss"))
    obs = data["observation_time"]

    assert obs is not None
    # HA's timestamp device class requires a tz-aware value.
    assert obs.tzinfo is not None
    assert obs.utcoffset().total_seconds() == 0
    assert (obs.year, obs.month, obs.day) == (2026, 6, 17)


def test_land_station_omits_absent_observations(ndbc, fixtures_dir):
    data = ndbc.parse_rss(_read(fixtures_dir, "land.rss"))

    assert data["name"] == "Neah Bay, WA"
    assert data["pressure"] == 1021.4
    assert data["water_temp"] == 11.3

    for key in (
        "wind_speed",
        "wind_gust",
        "wind_bearing",
        "wind_cardinal",
        "wave_height",
        "wave_period",
        "air_temp",
        "dew_point",
    ):
        assert data[key] is None, f"{key} should be None for a land station"


def test_negative_and_zero_values(ndbc, fixtures_dir):
    data = ndbc.parse_rss(_read(fixtures_dir, "negative.rss"))

    assert data["wind_bearing"] == 0.0  # "N (0°)"
    assert data["pressure_tendency"] == -1.3
    assert data["air_temp"] == -2.5
    assert data["water_temp"] == -0.5


def test_missing_item_raises(ndbc):
    with pytest.raises(ndbc.StationFetchError):
        ndbc.parse_rss("<rss><channel></channel></rss>")


def test_malformed_xml_raises(ndbc):
    with pytest.raises(ndbc.StationFetchError):
        ndbc.parse_rss("this is not < xml")
