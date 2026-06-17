"""Tests for ndbc.parse_txt and ndbc.merge_txt."""

from __future__ import annotations


def _read(fixtures_dir, name):
    return (fixtures_dir / name).read_text(encoding="utf-8")


def test_wave_decomposition(ndbc, fixtures_dir):
    data = ndbc.parse_txt(_read(fixtures_dir, "decomp.txt"))

    assert data["swell_height"] == 7.5
    assert data["swell_period"] == 9.1
    assert data["swell_direction"] == "WNW"
    assert data["wind_wave_height"] == 5.9
    assert data["wind_wave_period"] == 6.2
    assert data["wind_wave_direction"] == "NW"
    # Repeated "Period:"/"Direction:" labels must not cross sections.
    assert data["swell_period"] != data["wind_wave_period"]


def test_wind_from_txt(ndbc, fixtures_dir):
    data = ndbc.parse_txt(_read(fixtures_dir, "decomp.txt"))

    assert data["wind_cardinal"] == "NW"
    assert data["wind_bearing"] == 320.0
    assert data["wind_speed"] == 15.5
    assert data["wind_gust"] == 19.4
    # No inline significant-wave fields in a decomposition report.
    assert data["wave_height"] is None
    assert data["wave_period"] is None


def test_calm_wind_has_no_direction(ndbc, fixtures_dir):
    data = ndbc.parse_txt(_read(fixtures_dir, "calm.txt"))

    # "Wind:, 0.0 kt" -> speed parsed, direction absent.
    assert data["wind_speed"] == 0.0
    assert data["wind_gust"] == 3.9
    assert data["wind_cardinal"] is None
    assert data["wind_bearing"] is None
    assert data["swell_height"] == 9.2
    assert data["wind_wave_height"] == 1.3


def test_seas_variant(ndbc, fixtures_dir):
    data = ndbc.parse_txt(_read(fixtures_dir, "seas.txt"))

    # "Seas:" / "Peak Period:" populate the significant-wave fields...
    assert data["wave_height"] == 9.8
    assert data["wave_period"] == 7.0
    # ...and there is no decomposition.
    assert data["swell_height"] is None
    assert data["wind_wave_height"] is None


def test_merge_adds_decomposition_and_keeps_rss(ndbc):
    rss = {
        "name": "La Perouse Bank",
        "wind_speed": 23.3,
        "wind_bearing": 310.0,
        "wave_height": None,
        "wave_period": None,
    }
    txt = {
        "wind_speed": 27.2,  # should NOT overwrite RSS
        "swell_height": 7.5,
        "swell_period": 9.1,
        "swell_direction": "WNW",
        "wind_wave_height": 5.9,
        "wind_wave_period": 6.2,
        "wind_wave_direction": "NW",
        "wave_height": 9.8,  # RSS was None -> fill
    }

    merged = ndbc.merge_txt(rss, txt)

    assert merged["wind_speed"] == 23.3  # RSS wins
    assert merged["wave_height"] == 9.8  # gap filled from txt
    assert merged["swell_height"] == 7.5
    assert merged["wind_wave_direction"] == "NW"


def test_merge_sets_decomposition_none_when_txt_lacks_it(ndbc):
    rss = {"wind_speed": 5.0}
    merged = ndbc.merge_txt(rss, {})

    assert merged["swell_height"] is None
    assert merged["wind_wave_height"] is None
    assert merged["wind_speed"] == 5.0
