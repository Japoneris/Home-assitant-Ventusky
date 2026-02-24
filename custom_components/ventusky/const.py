"""Constants for the Ventusky integration."""

DOMAIN = "ventusky"

CONF_LAT = "latitude"
CONF_LON = "longitude"
CONF_LOCATION_NAME = "location_name"
CONF_REFRESH_INTERVAL = "refresh_interval"

DEFAULT_REFRESH_INTERVAL = 60  # minutes

VENTUSKY_URL_TEMPLATE = "https://www.ventusky.com/{lat};{lon}"
USER_AGENT = "Mozilla/5.0 (compatible; HomeAssistant-Ventusky/1.0)"
