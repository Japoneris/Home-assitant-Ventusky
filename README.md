# Ventusky Scrapper + Home Assistant Integration


Tools to scrape and display weather forecast data from [Ventusky](https://www.ventusky.com).


## Files

### Home Assistant

Move the `venstusky` folder from `custom_components/` and `www/` to the correct config location.


### Local

In `local/` folder, to try if everything fine.

| File | Role |
|---|---|
| `parse_weather.py` | Parses a Ventusky HTML page into a structured JSON file |
| `read_weather.py` | Displays the JSON forecast in a human-readable table |
| `test.html` | Sample HTML from Ventusky (Sartrouville, 8-day forecast) |
| `weather.json` | Output of the parser |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install beautifulsoup4
```

## Usage

### 1. Parse an HTML file

Save a Ventusky forecast page as an HTML file, then run:

```bash
python3 parse_weather.py test.html weather.json
```

Arguments:
- `test.html` — input HTML file (default: `test.html`)
- `weather.json` — output JSON file (default: `weather.json`)

### 2. Read the forecast

```bash
# Full 8-day forecast
python3 read_weather.py weather.json

# Single day
python3 read_weather.py weather.json --day 2026/02/25

# Single field across all days
python3 read_weather.py weather.json --field temperature_c
python3 read_weather.py weather.json --field wind_speed_kmh
```

## JSON Format

```json
{
  "location": "MyCityName",
  "units": {
    "temperature": "°C",
    "precipitation": "mm",
    "wind_speed": "km/h"
  },
  "forecast": [
    {
      "day": "d_1",
      "date": "2026/02/25",
      "hourly": [
        {
          "time": "01:00",
          "temperature_c": 10,
          "weather_code": -2,
          "weather_description": "clear sky with few clouds",
          "is_night": true,
          "precipitation_mm": 0,
          "precipitation_probability_pct": 0,
          "wind_speed_kmh": 5,
          "wind_gust_kmh": 11,
          "wind_direction_deg": 90,
          "wind_direction": "E"
        }
      ]
    }
  ]
}
```

**8 days of data, 8 time slots per day:** 01:00, 04:00, 07:00, 10:00, 13:00, 16:00, 19:00, 22:00.

**Weather codes:** positive = daytime, negative = nighttime variant of the same condition (`is_night: true`).

## How It Works

Ventusky embeds all forecast data as a JSON blob in a `<custom-forecast data-forecast='...'>` HTML element. The parser extracts this directly — no fragile DOM scraping needed. Dates are read from a `<select id="date_selector">` dropdown.
