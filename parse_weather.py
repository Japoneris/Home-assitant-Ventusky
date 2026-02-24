#!/usr/bin/env python3
"""
Parse Ventusky weather HTML into structured JSON.

The HTML embeds a JSON blob inside a <custom-forecast data-forecast='...'> element,
covering 8 days × 8 time slots (01:00, 04:00, 07:00, 10:00, 13:00, 16:00, 19:00, 22:00).
Dates are extracted from <select id="date_selector">.

The <div id="forecast_24"> section contains hour-by-hour data for the next 24 hours,
starting from the current hour.
"""

import json
import re
import sys
from datetime import datetime, timedelta
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
        "hourly_24h": _parse_hourly_24h(soup, date_map),
        "forecast": forecast_days,
    }


def _parse_hourly_24h(soup: BeautifulSoup, date_map: dict) -> list:
    """Parse the next-24-hours table from <div id='forecast_24'>."""
    section = soup.find("div", id="forecast_24")
    if not section:
        return []

    table = section.find("table")
    if not table:
        return []

    # Derive today's date from d_1 (tomorrow) minus 1 day
    today = None
    tomorrow = None
    if "d_1" in date_map:
        tomorrow = datetime.strptime(date_map["d_1"], "%Y/%m/%d")
        today = tomorrow - timedelta(days=1)

    # Parse time headers; detect which slots belong to "tomorrow"
    headers = []
    for th in table.find("thead").find_all("th"):
        time_str = th.get_text(separator=" ").strip()
        is_tomorrow = "tomorrow" in time_str
        hour = time_str.split()[0]  # e.g. "14:00"
        date = tomorrow if is_tomorrow else today
        headers.append({
            "time": hour,
            "date": date.strftime("%Y/%m/%d") if date else "unknown",
        })

    # Parse each cell in the single tbody row
    row = table.find("tbody").find("tr")
    cells = row.find_all("td")

    slots = []
    for i, td in enumerate(cells):
        header = headers[i] if i < len(headers) else {"time": "??:??", "date": "unknown"}

        img = td.find("img")
        weather_desc = img["alt"] if img else "unknown"

        temp_div = td.find("div", class_=re.compile(r"temperature_line"))
        temp_text = temp_div.get_text(strip=True) if temp_div else ""
        temp_c = int(re.search(r"-?\d+", temp_text).group()) if re.search(r"-?\d+", temp_text) else None

        spans = td.find_all("span")
        precip_mm = None
        precip_pct = None
        for span in spans:
            text = span.get_text(strip=True)
            if "mm" in text:
                m = re.search(r"[\d.]+", text)
                precip_mm = float(m.group()) if m else None
            elif "%" in text:
                m = re.search(r"\d+", text)
                precip_pct = int(m.group()) if m else None

        wind_div = td.find("div", class_=re.compile(r"wind_ico"))
        wind_dir = wind_div.get_text(strip=True) if wind_div else None
        wind_deg = None
        if wind_div:
            m = re.search(r"arrow_(\d+)", " ".join(wind_div.get("class", [])))
            wind_deg = int(m.group(1)) if m else None

        speed_divs = td.find_all("div")
        wind_speed_kmh = None
        for div in speed_divs:
            text = div.get_text(strip=True)
            if "km/h" in text:
                m = re.search(r"\d+", text)
                wind_speed_kmh = int(m.group()) if m else None
                break

        slots.append({
            "date": header["date"],
            "time": header["time"],
            "weather_description": weather_desc,
            "temperature_c": temp_c,
            "precipitation_mm": precip_mm,
            "precipitation_probability_pct": precip_pct,
            "wind_direction": wind_dir,
            "wind_direction_deg": wind_deg,
            "wind_speed_kmh": wind_speed_kmh,
        })

    return slots


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
