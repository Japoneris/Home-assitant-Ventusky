/**
 * Ventusky Weather Card — custom Lovelace element.
 *
 * Config:
 *   type: custom:ventusky-card
 *   entity: weather.ventusky_<location>   # WeatherEntity entity_id
 *   title: "My Location"                  # optional override
 */

const WIND_ARROWS = ["↓", "↙", "←", "↖", "↑", "↗", "→", "↘"];

function bearingToArrow(deg) {
  if (deg == null) return "";
  const idx = Math.round(((deg % 360) + 360) / 45) % 8;
  return WIND_ARROWS[idx];
}

const CONDITION_ICONS = {
  "clear-night":       "🌙",
  "cloudy":            "☁️",
  "exceptional":       "⚠️",
  "fog":               "🌫️",
  "hail":              "🌨️",
  "lightning":         "⚡",
  "lightning-rainy":   "⛈️",
  "partlycloudy":      "⛅",
  "pouring":           "🌧️",
  "rainy":             "🌦️",
  "snowy":             "❄️",
  "snowy-rainy":       "🌨️",
  "sunny":             "☀️",
  "windy":             "💨",
  "windy-variant":     "💨",
};

function conditionIcon(cond) {
  return CONDITION_ICONS[cond] || "🌡️";
}

function formatDay(isoDate) {
  const d = new Date(isoDate);
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

function formatHour(isoDate) {
  const d = new Date(isoDate);
  return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", hour12: false });
}

function formatDate(isoDate) {
  const d = new Date(isoDate);
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

const CARD_CSS = `
  :host {
    display: block;
    font-family: var(--paper-font-body1_-_font-family, sans-serif);
  }
  .card-root {
    background: var(--card-background-color, #fff);
    border-radius: var(--ha-card-border-radius, 8px);
    box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,.15));
    padding: 16px;
    color: var(--primary-text-color, #212121);
    overflow: hidden;
  }
  /* ---- Banner ---- */
  .banner {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
  }
  .banner-left {
    flex: 1;
  }
  .location-name {
    font-size: 1rem;
    color: var(--secondary-text-color, #727272);
    margin: 0 0 4px;
  }
  .current-temp {
    font-size: 3rem;
    font-weight: 300;
    line-height: 1;
    margin: 0;
  }
  .current-condition {
    font-size: 0.9rem;
    margin-top: 4px;
    color: var(--secondary-text-color, #727272);
  }
  .current-icon {
    font-size: 3.5rem;
    line-height: 1;
  }
  .wind-info {
    font-size: 0.85rem;
    color: var(--secondary-text-color, #727272);
    margin-top: 6px;
  }
  /* ---- Hourly table ---- */
  .section-title {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--secondary-text-color, #727272);
    margin: 0 0 6px;
  }
  .hourly-scroll {
    overflow-x: auto;
    margin-bottom: 16px;
  }
  table.hourly {
    border-collapse: collapse;
    white-space: nowrap;
    font-size: 0.8rem;
    width: 100%;
  }
  table.hourly th,
  table.hourly td {
    padding: 4px 8px;
    text-align: center;
  }
  table.hourly thead th {
    color: var(--secondary-text-color, #727272);
    font-weight: 600;
    border-bottom: 1px solid var(--divider-color, #e0e0e0);
  }
  table.hourly tr.date-sep td {
    background: var(--secondary-background-color, #f5f5f5);
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--secondary-text-color, #727272);
    text-align: left;
    padding: 3px 8px;
  }
  table.hourly tbody tr:not(.date-sep):hover td {
    background: var(--secondary-background-color, #f5f5f5);
  }
  /* ---- Daily grid ---- */
  .daily-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
    gap: 8px;
  }
  .day-card {
    background: var(--secondary-background-color, #f5f5f5);
    border-radius: 6px;
    padding: 8px 4px;
    text-align: center;
    font-size: 0.78rem;
  }
  .day-card .day-name {
    font-weight: 600;
    font-size: 0.7rem;
    color: var(--secondary-text-color, #727272);
    margin-bottom: 4px;
  }
  .day-card .day-icon {
    font-size: 1.6rem;
    line-height: 1.2;
  }
  .day-card .day-temps {
    margin-top: 4px;
  }
  .day-card .day-temps .hi { font-weight: 700; }
  .day-card .day-temps .lo { color: var(--secondary-text-color, #727272); }
  .day-card .day-rain {
    font-size: 0.7rem;
    color: #1565c0;
    margin-top: 2px;
  }
  /* ---- Misc ---- */
  .error {
    color: var(--error-color, red);
    padding: 8px;
  }
  .loading {
    color: var(--secondary-text-color, #727272);
    padding: 8px;
  }
`;

class VentuskyCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._hourlyUnsub = null;
    this._dailyUnsub = null;
    this._hourlyForecast = null;
    this._dailyForecast = null;
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("ventusky-card: 'entity' is required");
    }
    this._config = config;
    this._renderSkeleton();
  }

  set hass(hass) {
    const prev = this._hass;
    this._hass = hass;

    const entityId = this._config.entity;
    const stateObj = hass.states[entityId];
    if (!stateObj) {
      this._renderError(`Entity '${entityId}' not found.`);
      return;
    }

    // Subscribe forecasts once (or when entity changes)
    if (!prev || prev.states[entityId] !== stateObj) {
      this._subscribeForecast("hourly");
      this._subscribeForecast("daily");
    }

    this._render(stateObj);
  }

  _subscribeForecast(forecastType) {
    const key = forecastType === "hourly" ? "_hourlyUnsub" : "_dailyUnsub";
    // Unsubscribe previous
    if (this[key]) {
      this[key]();
      this[key] = null;
    }
    const entityId = this._config.entity;
    if (!this._hass || !this._hass.connection) return;

    this._hass.connection
      .subscribeMessage(
        (msg) => {
          if (forecastType === "hourly") {
            this._hourlyForecast = msg.forecast || [];
          } else {
            this._dailyForecast = msg.forecast || [];
          }
          // Re-render with updated forecast
          const stateObj = this._hass && this._hass.states[entityId];
          if (stateObj) this._render(stateObj);
        },
        {
          type: "weather/subscribe_forecast",
          forecast_type: forecastType,
          entity_id: entityId,
        }
      )
      .then((unsub) => {
        this[key] = unsub;
      })
      .catch((err) => {
        console.warn(`ventusky-card: forecast subscription failed (${forecastType}):`, err);
      });
  }

  disconnectedCallback() {
    if (this._hourlyUnsub) { this._hourlyUnsub(); this._hourlyUnsub = null; }
    if (this._dailyUnsub)  { this._dailyUnsub();  this._dailyUnsub = null; }
  }

  // ---- Rendering ----

  _renderSkeleton() {
    this.shadowRoot.innerHTML = `
      <style>${CARD_CSS}</style>
      <div class="card-root">
        <div class="loading">Loading Ventusky data…</div>
      </div>`;
  }

  _renderError(msg) {
    this.shadowRoot.innerHTML = `
      <style>${CARD_CSS}</style>
      <div class="card-root"><div class="error">${msg}</div></div>`;
  }

  _render(stateObj) {
    const attr = stateObj.attributes || {};
    const condition = stateObj.state;
    const temp = attr.temperature;
    const tempUnit = attr.temperature_unit || "°C";
    const windSpeed = attr.wind_speed;
    const windBearing = attr.wind_bearing;
    const windUnit = attr.wind_speed_unit || "km/h";
    const locationName = this._config.title || attr.friendly_name || this._config.entity;

    const arrow = bearingToArrow(windBearing);
    const icon = conditionIcon(condition);

    const hourlyHtml = this._buildHourlyTable(this._hourlyForecast);
    const dailyHtml = this._buildDailyGrid(this._dailyForecast);

    this.shadowRoot.innerHTML = `
      <style>${CARD_CSS}</style>
      <div class="card-root">
        <!-- Banner -->
        <div class="banner">
          <div class="banner-left">
            <p class="location-name">${locationName}</p>
            <p class="current-temp">${temp != null ? Math.round(temp) : "—"}${tempUnit}</p>
            <p class="current-condition">${condition || ""}</p>
            <p class="wind-info">${arrow} ${windSpeed != null ? windSpeed : "—"} ${windUnit}</p>
          </div>
          <div class="current-icon">${icon}</div>
        </div>

        <!-- Hourly -->
        <p class="section-title">Next 24 hours</p>
        <div class="hourly-scroll">
          ${hourlyHtml}
        </div>

        <!-- Daily -->
        <p class="section-title">8-day forecast</p>
        <div class="daily-grid">
          ${dailyHtml}
        </div>
      </div>`;
  }

  _buildHourlyTable(forecast) {
    if (!forecast || forecast.length === 0) {
      return '<p class="loading">Hourly data loading…</p>';
    }

    let rows = "";
    let lastDate = null;

    for (const slot of forecast) {
      const dt = slot.datetime;
      const dateLabel = formatDate(dt);
      const hour = formatHour(dt);
      const cond = slot.condition || "";
      const icon = conditionIcon(cond);
      const temp = slot.temperature != null ? `${Math.round(slot.temperature)}°` : "—";
      const precip = slot.precipitation != null ? `${slot.precipitation.toFixed(1)} mm` : "—";
      const prob = slot.precipitation_probability != null
        ? `${slot.precipitation_probability}%`
        : "—";
      const wind = slot.wind_speed != null ? `${Math.round(slot.wind_speed)}` : "—";
      const windArrow = bearingToArrow(slot.wind_bearing);

      if (dateLabel !== lastDate) {
        rows += `<tr class="date-sep"><td colspan="6">${dateLabel}</td></tr>`;
        lastDate = dateLabel;
      }

      rows += `<tr>
        <td>${hour}</td>
        <td>${icon}</td>
        <td>${temp}</td>
        <td>${precip}</td>
        <td>${prob}</td>
        <td>${windArrow} ${wind}</td>
      </tr>`;
    }

    return `
      <table class="hourly">
        <thead>
          <tr>
            <th>Time</th>
            <th>Sky</th>
            <th>Temp</th>
            <th>Rain</th>
            <th>Prob</th>
            <th>Wind</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>`;
  }

  _buildDailyGrid(forecast) {
    if (!forecast || forecast.length === 0) {
      return '<p class="loading">Daily data loading…</p>';
    }

    return forecast
      .slice(0, 8)
      .map((day) => {
        const cond = day.condition || "";
        const icon = conditionIcon(cond);
        const hi = day.temperature != null ? `${Math.round(day.temperature)}°` : "—";
        const lo = day.templow != null ? `${Math.round(day.templow)}°` : "—";
        const rain = day.precipitation != null && day.precipitation > 0
          ? `${day.precipitation.toFixed(1)} mm`
          : "";
        const dayLabel = formatDay(day.datetime).split(",")[0]; // weekday short

        return `<div class="day-card">
          <div class="day-name">${dayLabel}</div>
          <div class="day-icon">${icon}</div>
          <div class="day-temps">
            <span class="hi">${hi}</span>
            <span class="lo"> / ${lo}</span>
          </div>
          ${rain ? `<div class="day-rain">${rain}</div>` : ""}
        </div>`;
      })
      .join("");
  }

  // ---- Card size hint for Lovelace layout ----
  getCardSize() {
    return 5;
  }

  static getConfigElement() {
    // No visual editor; return undefined to use YAML only.
    return undefined;
  }

  static getStubConfig() {
    return { entity: "weather.ventusky_home" };
  }
}

customElements.define("ventusky-card", VentuskyCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ventusky-card",
  name: "Ventusky Weather Card",
  description: "Shows Ventusky weather: current conditions, 24-hour table, and 8-day forecast.",
  preview: false,
});
