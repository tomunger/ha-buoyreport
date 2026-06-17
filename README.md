# NDBC Ocean Buoy — Home Assistant integration

Displays current marine observations from [NOAA's National Data Buoy Center](https://www.ndbc.noaa.gov)
buoys in Home Assistant. Add a buoy by its station ID and get one device per
station with sensors for the observations that station reports.

## What it does

- One config entry = one station = one HA **device**.
- Data sources, merged per update:
  - `latest_obs/<station>.rss` — backbone (name, location, metric temps/pressure,
    wind, significant wave height). Required.
  - `latest_obs/<station>.txt` — adds the **swell / wind-wave decomposition** the
    RSS feed often omits, and fills wind/wave gaps. Best-effort: if it is
    unavailable, that cycle simply has no decomposition.
- Polls every 10 minutes by default (NDBC updates roughly hourly). Adjustable
  per station via the integration's **Configure** button.
- Creates a sensor only for observations a station actually reports, so a
  land station that only sends pressure and water temperature won't get empty
  wind/wave entities.

### Sensors (created when reported)

| Sensor | Unit |
|---|---|
| Observation time | timestamp |
| Wind direction | ° (with `cardinal` attribute, e.g. `NW`) |
| Wind speed / Wind gust | knots |
| Wave height (significant) | feet |
| Wave period (dominant) | seconds |
| Swell height / period / direction | feet / seconds / cardinal text |
| Wind wave height / period / direction | feet / seconds / cardinal text |
| Pressure | hPa |
| Pressure tendency | hPa (diagnostic) |
| Air temperature / Dew point / Water temperature | °C |
| Location | `lat, lon` string with `latitude`, `longitude`, `map_url` attributes |

> Units are stored as NDBC reports them (knots/feet for wind and waves; metric
> for temperature and pressure). Home Assistant converts them for display
> according to your unit settings.

> The swell vs. wind-wave breakdown comes from the free-text `.txt` feed and
> exists only for buoys with directional wave sensors. Stations without it still
> report significant wave height + dominant wave period when available.

## Installation (HACS)

1. HACS → Integrations → ⋮ → **Custom repositories**.
2. Add this repository's URL, category **Integration**.
3. Install **NDBC Ocean Buoy**, then restart Home Assistant.
4. **Settings → Devices & Services → Add Integration → NDBC Ocean Buoy**, and
   enter a station ID (e.g. `46206` or `neaw1`). Repeat for each buoy.

## Dashboard examples

Entity IDs follow the pattern `sensor.buoy_<id>_<name>_<measurement>`. Check the
actual IDs in **Developer Tools → States** and adjust the examples below.

### See the buoy on a map

```yaml
type: map
entities:
  - sensor.buoy_46206_la_perouse_bank_location
```

### Human-readable card with a Google Maps link

```yaml
type: markdown
content: >
  ## {{ state_attr('sensor.buoy_46206_la_perouse_bank_location','friendly_name')
  | replace(' Location','') }}

  [📍 Confirm location on map]({{
  state_attr('sensor.buoy_46206_la_perouse_bank_location','map_url') }})


  **Wind:** {{ states('sensor.buoy_46206_la_perouse_bank_wind_speed') }} kn
  ({{ state_attr('sensor.buoy_46206_la_perouse_bank_wind_direction','cardinal') }}),
  gusting {{ states('sensor.buoy_46206_la_perouse_bank_wind_gust') }} kn

  **Seas:** {{ states('sensor.buoy_46206_la_perouse_bank_wave_height') }} ft
  @ {{ states('sensor.buoy_46206_la_perouse_bank_wave_period') }} s

  **Air:** {{ states('sensor.buoy_46206_la_perouse_bank_air_temperature') }} °C
  · **Water:** {{ states('sensor.buoy_46206_la_perouse_bank_water_temperature') }} °C

  *Observed {{ relative_time(states('sensor.buoy_46206_la_perouse_bank_observation_time') | as_datetime) }} ago*
```

### Plain entities list

```yaml
type: entities
title: La Perouse Bank
entities:
  - sensor.buoy_46206_la_perouse_bank_wind_speed
  - sensor.buoy_46206_la_perouse_bank_wind_gust
  - sensor.buoy_46206_la_perouse_bank_wind_direction
  - sensor.buoy_46206_la_perouse_bank_wave_height
  - sensor.buoy_46206_la_perouse_bank_wave_period
  - sensor.buoy_46206_la_perouse_bank_pressure
  - sensor.buoy_46206_la_perouse_bank_air_temperature
  - sensor.buoy_46206_la_perouse_bank_water_temperature
  - sensor.buoy_46206_la_perouse_bank_observation_time
```
