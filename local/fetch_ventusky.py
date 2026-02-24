#!/usr/bin/env python3
"""Fetch a Ventusky page for a given geographic position and save it to a file."""

import argparse
import urllib.request


def fetch_ventusky(lat: float, lon: float, output: str) -> None:
    url = f"https://www.ventusky.com/{lat};{lon}"
    print(f"Fetching {url} ...")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; fetch_ventusky/1.0)"},
    )
    with urllib.request.urlopen(req) as response:
        content = response.read()

    with open(output, "wb") as f:
        f.write(content)

    print(f"Saved to {output} ({len(content)} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch a Ventusky page for a geographic position."
    )
    parser.add_argument("--lat", type=float, default=48.941, help="Latitude (default: 48.941)")
    parser.add_argument("--lon", type=float, default=2.159, help="Longitude (default: 2.159)")
    parser.add_argument("--output", "-o", default="test.html", help="Output file (default: test.html)")
    args = parser.parse_args()

    fetch_ventusky(args.lat, args.lon, args.output)


if __name__ == "__main__":
    main()
