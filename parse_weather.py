#!/usr/bin/env python3
"""
Parse Ventusky weather HTML into structured JSON.

The HTML embeds a JSON blob inside a <custom-forecast data-forecast='...'> element,
covering 8 days × 8 time slots (01:00, 04:00, 07:00, 10:00, 13:00, 16:00, 19:00, 22:00).
Dates are extracted from <select id="date_selector">.
"""

import json
import sys
from bs4 import BeautifulSoup

TIME_SLOTS = ["01:00", "04:00", "07:00", "10:00", "13:00", "16:00", "19:00", "22:00"]


def parse_weather_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # --- Extract dates from the day selector ---
    date_map = {}  # "d_1" -> "2026/02/25", etc.
    date_selector = soup.find("select", id="date_selector")
    if date_selector:
        for option in date_selector.find_all("option"):
            value = option.get("value")
            if value:
                date_map[f"d_{value}"] = option.text.strip()

    # --- Extract embedded forecast JSON ---
    forecast_elem = soup.find("custom-forecast")
    if not forecast_elem:
        raise ValueError("Could not find <custom-forecast> element in the HTML.")

    raw_json = forecast_elem.get("data-forecast")
    if not raw_json:
        raise ValueError("<custom-forecast> element has no data-forecast attribute.")

    raw = json.loads(raw_json)

    units = raw.get("units", {})
    s_desc = raw.get("sDesc", {})  # weather code -> description

    # --- Build structured output ---
    forecast_days = []

    for day_key in sorted(k for k in raw if k.startswith("d_")):
        day_data = raw[day_key]
        date = date_map.get(day_key, "unknown")

        slots = []
        for i, time in enumerate(TIME_SLOTS):
            weather_code = day_data["s"][i]
            # Negative codes are nighttime variants of the same condition
            is_night = weather_code < 0
            desc_key = str(abs(weather_code))
            slots.append({
                "time": time,
                "temperature_c": day_data["td"][i],
                "weather_code": weather_code,
                "weather_description": s_desc.get(desc_key, "unknown"),
                "is_night": is_night,
                "precipitation_mm": day_data["sr"][i],
                "precipitation_probability_pct": day_data["rp"][i],
                "wind_speed_kmh": day_data["vsd"][i],
                "wind_gust_kmh": day_data.get("vg", [None] * 8)[i],
                "wind_direction_deg": day_data["vd45"][i],
                "wind_direction": day_data["vdId"][i],
            })

        forecast_days.append({
            "day": day_key,
            "date": date,
            "hourly": slots,
        })

    return {
        "location": _extract_location(soup),
        "units": {
            "temperature": units.get("t", "°C"),
            "precipitation": units.get("ws", "mm"),
            "wind_speed": units.get("s", "km/h"),
        },
        "forecast": forecast_days,
    }


def _extract_location(soup: BeautifulSoup) -> str:
    """Try to extract location name from the page title."""
    title = soup.find("title")
    if title:
        # Title format: "Weather - Sartrouville - 14-Day Forecast & Rain | Ventusky"
        parts = title.text.split(" - ")
        if len(parts) >= 2:
            return parts[1].strip()
    return "unknown"


def main():
    html_path = sys.argv[1] if len(sys.argv) > 1 else "test.html"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "weather.json"

    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    result = parse_weather_html(html)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Parsed {len(result['forecast'])} days → {output_path}")
    print(f"Location: {result['location']}")
    print(f"Date range: {result['forecast'][0]['date']} to {result['forecast'][-1]['date']}")


if __name__ == "__main__":
    main()
