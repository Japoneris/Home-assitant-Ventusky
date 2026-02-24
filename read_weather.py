#!/usr/bin/env python3
"""
Display a parsed Ventusky weather JSON in a human-readable format.

Usage:
    python3 read_weather.py [weather.json] [--day DATE] [--field FIELD]

Options:
    --day DATE      Show only a specific date (e.g. 2026/02/25)
    --field FIELD   Show only one field per slot (e.g. temperature_c, wind_speed_kmh)
"""

import json
import sys
import argparse

# Weather icons (approximate Unicode symbols)
WEATHER_ICONS = {
    "clear sky":                   "☀",
    "clear sky with few clouds":   "🌤",
    "partly cloudy":               "⛅",
    "mostly cloudy":               "🌥",
    "high clouds":                 "🌤",
    "overcast":                    "☁",
    "overcast with light rain":    "🌧",
    "unknown":                     "?",
}

WIND_ARROWS = {
    "N": "↓", "NE": "↙", "E": "←", "SE": "↖",
    "S": "↑", "SW": "↗", "W": "→", "NW": "↘",
}

# Emojis that occupy 2 terminal columns instead of 1
WIDE_ICONS = {"🌤", "⛅", "🌥", "🌧"}


def icon(desc: str) -> str:
    return WEATHER_ICONS.get(desc, "?")


def fmt_sky(desc: str, desc_width: int = 26) -> str:
    """Return 'ICON desc' padded to a consistent visual width."""
    ic = icon(desc)
    pad = desc_width - (1 if ic in WIDE_ICONS else 0)
    return f"{ic} {desc:<{pad}}"


def wind_arrow(direction: str) -> str:
    return WIND_ARROWS.get(direction, direction)


def print_hourly_24h(slots: list) -> None:
    if not slots:
        return

    print(f"\n{'═'*72}")
    print(f"  Next 24 hours — hour by hour")
    print(f"{'═'*72}")

    current_date = None
    for s in slots:
        # Print date separator when the date changes
        if s["date"] != current_date:
            current_date = s["date"]
            print(f"\n  ── {current_date} ──")
            print(f"  {'Time':>5}  {'Sky':<28}  {'Temp':>6}  {'Rain':>8}  {'Prob':>5}  {'Wind':>12}")
            print(f"  {'─'*5}  {'─'*28}  {'─'*6}  {'─'*8}  {'─'*5}  {'─'*12}")

        desc = s["weather_description"]
        wind = f"{wind_arrow(s['wind_direction'])} {s['wind_direction']} {s['wind_speed_kmh']} km/h"
        rain = f"{s['precipitation_mm']} mm" if s["precipitation_mm"] and s["precipitation_mm"] > 0 else "-"
        prob = f"{s['precipitation_probability_pct']}%" if s["precipitation_probability_pct"] and s["precipitation_probability_pct"] > 0 else "-"

        print(
            f"  {s['time']:>5}  "
            f"{fmt_sky(desc)}  "
            f"{s['temperature_c']:>4} °C  "
            f"{rain:>8}  "
            f"{prob:>5}  "
            f"{wind}"
        )


def print_day(day: dict) -> None:
    date = day["date"]
    slots = day["hourly"]

    print(f"\n{'='*72}")
    print(f"  {date}")
    print(f"{'='*72}")

    # Header
    print(f"  {'Time':>6}  {'Sky':<28}  {'Temp':>6}  {'Rain':>8}  {'Prob':>5}  {'Wind':>10}")
    print(f"  {'-'*6}  {'-'*28}  {'-'*6}  {'-'*8}  {'-'*5}  {'-'*10}")

    for s in slots:
        night_marker = "*" if s["is_night"] else " "
        desc = s["weather_description"]
        wind = f"{wind_arrow(s['wind_direction'])} {s['wind_direction']} {s['wind_speed_kmh']} km/h"
        rain = f"{s['precipitation_mm']} mm" if s["precipitation_mm"] > 0 else "-"
        prob = f"{s['precipitation_probability_pct']}%" if s["precipitation_probability_pct"] > 0 else "-"

        print(
            f"  {s['time']:>6}{night_marker} "
            f"{fmt_sky(desc)}  "
            f"{s['temperature_c']:>4} °C  "
            f"{rain:>8}  "
            f"{prob:>5}  "
            f"{wind}"
        )

    # Daily summary
    temps = [s["temperature_c"] for s in slots]
    rains = [s["precipitation_mm"] for s in slots]
    print(f"\n  Summary: {min(temps)}–{max(temps)} °C  |  Total rain: {sum(rains):.1f} mm")


def print_field(day: dict, field: str) -> None:
    date = day["date"]
    values = []
    for s in day["hourly"]:
        if field not in s:
            print(f"Unknown field '{field}'. Available: {', '.join(s.keys())}")
            sys.exit(1)
        values.append(f"{s['time']}: {s[field]}")
    print(f"{date}  |  " + "  ".join(values))


def main():
    parser = argparse.ArgumentParser(description="Display parsed weather forecast.")
    parser.add_argument("json_file", nargs="?", default="weather.json",
                        help="Path to weather JSON file (default: weather.json)")
    parser.add_argument("--day", metavar="DATE",
                        help="Filter to a specific date, e.g. 2026/02/25")
    parser.add_argument("--field", metavar="FIELD",
                        help="Show only one field per time slot, e.g. temperature_c")
    args = parser.parse_args()

    with open(args.json_file, encoding="utf-8") as f:
        data = json.load(f)

    location = data["location"]
    units = data["units"]
    forecast = data["forecast"]
    hourly_24h = data.get("hourly_24h", [])

    print(f"\nWeather forecast for {location}")
    print(f"Units: temperature={units['temperature']}  "
          f"precipitation={units['precipitation']}  "
          f"wind={units['wind_speed']}")

    if args.day:
        forecast = [d for d in forecast if d["date"] == args.day]
        if not forecast:
            print(f"No data found for date '{args.day}'.")
            sys.exit(1)
        print(f"* = night slot")
        if args.field:
            for day in forecast:
                print_field(day, args.field)
        else:
            for day in forecast:
                print_day(day)
    else:
        print_hourly_24h(hourly_24h)
        print(f"\n* = night slot")
        if args.field:
            for day in forecast:
                print_field(day, args.field)
        else:
            for day in forecast:
                print_day(day)

    print()


if __name__ == "__main__":
    main()
