# Ventusky Home Assistant Integration — Installation Guide

## Prerequisites

- Home Assistant 2023.9 or newer
- Network access from HA to `ventusky.com`

---

## 1. Copy the integration

Copy the `custom_components/ventusky/` directory to your Home Assistant configuration folder:

```bash
cp -r custom_components/ventusky/ /config/custom_components/ventusky/
```

The result should look like:

```
/config/
  custom_components/
    ventusky/
      __init__.py
      manifest.json
      const.py
      config_flow.py
      coordinator.py
      weather_parser.py
      weather.py
      sensor.py
      strings.json
      translations/
        en.json
```

## 2. Copy the Lovelace card

```bash
mkdir -p /config/www/ventusky-card
cp www/ventusky-card/ventusky-card.js /config/www/ventusky-card/
```

## 3. Restart Home Assistant

**Settings → System → Restart**

Wait for HA to fully restart before continuing.

---

## 4. Add the integration

1. Go to **Settings → Integrations**
2. Click **+ Add Integration**
3. Search for **Ventusky Weather** and select it
4. Fill in the form:

   | Field | Example |
   |---|---|
   | Latitude | `48.941` |
   | Longitude | `2.159` |
   | Location name | `Sartrouville` |
   | Refresh interval (min) | `60` |

5. Click **Submit**. HA will test connectivity before saving.

This creates:
- `weather.ventusky_<location_name>` — WeatherEntity with hourly + daily forecasts
- `sensor.ventusky_<location_name>_temperature`
- `sensor.ventusky_<location_name>_rain_today`
- `sensor.ventusky_<location_name>_wind_speed`
- `sensor.ventusky_<location_name>_wind_bearing`

---

## 5. Register the Lovelace resource

1. Go to **Settings → Dashboards**
2. Click the **⋮ menu** (top-right) → **Resources**
3. Click **+ Add Resource**
4. URL: `/local/ventusky-card/ventusky-card.js`
5. Resource type: **JavaScript module**
6. Click **Create**

---

## 6. Add the card to a dashboard

Edit a dashboard, add a **Manual card**, and paste:

```yaml
type: custom:ventusky-card
entity: weather.ventusky_sartrouville   # replace with your entity id
```

Optional extra config:

```yaml
type: custom:ventusky-card
entity: weather.ventusky_sartrouville
title: "Sartrouville"   # override the display name
```

---

## Updating

Re-copy the files and restart HA. No database migration needed.

## Removing

1. **Settings → Integrations** → click the Ventusky entry → **Delete**
2. Remove `/config/custom_components/ventusky/`
3. Remove `/config/www/ventusky-card/`
4. Remove the Lovelace resource entry
5. Restart HA
