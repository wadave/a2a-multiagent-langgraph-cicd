from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from geopy.exc import GeocoderTimedOut

from mcp_servers.weather_mcp_server import weather_server as _mod

# Pure functions (not wrapped by @mcp.tool())
format_alert = _mod.format_alert
format_forecast_period = _mod.format_forecast_period
get_weather_response = _mod.get_weather_response
_internal_get_forecast = _mod._internal_get_forecast

# @mcp.tool() wraps functions in FunctionTool; access the original via .fn
get_active_alerts_by_state = _mod.get_active_alerts_by_state.fn
get_forecast = _mod.get_forecast.fn
get_forecast_by_city = _mod.get_forecast_by_city.fn


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

SAMPLE_ALERT_FEATURE = {
    "properties": {
        "event": "Winter Storm Warning",
        "areaDesc": "Northern Colorado",
        "severity": "Severe",
        "certainty": "Likely",
        "urgency": "Expected",
        "effective": "2026-01-15T10:00:00",
        "expires": "2026-01-16T10:00:00",
        "headline": "Winter Storm Warning issued",
        "description": "Heavy snow expected.",
        "instruction": "Stay indoors.",
    }
}

SAMPLE_FORECAST_PERIOD = {
    "name": "Tonight",
    "temperature": 28,
    "temperatureUnit": "F",
    "windSpeed": "10 mph",
    "windDirection": "NW",
    "shortForecast": "Partly Cloudy",
    "detailedForecast": "Partly cloudy, with a low around 28.",
}

SAMPLE_POINTS_DATA = {
    "properties": {
        "forecast": "https://api.weather.gov/gridpoints/OKX/33,37/forecast",
    }
}

SAMPLE_FORECAST_DATA = {
    "properties": {
        "periods": [SAMPLE_FORECAST_PERIOD],
    }
}


# ---------------------------------------------------------------------------
# Pure function tests: format_alert
# ---------------------------------------------------------------------------


class TestFormatAlert:
    def test_full_data(self):
        result = format_alert(SAMPLE_ALERT_FEATURE)
        assert "Winter Storm Warning" in result
        assert "Northern Colorado" in result
        assert "Severe" in result
        assert "Likely" in result
        assert "Stay indoors." in result

    def test_missing_properties(self):
        result = format_alert({})
        assert "Unknown Event" in result
        assert "N/A" in result


# ---------------------------------------------------------------------------
# Pure function tests: format_forecast_period
# ---------------------------------------------------------------------------


class TestFormatForecastPeriod:
    def test_basic(self):
        result = format_forecast_period(SAMPLE_FORECAST_PERIOD)
        assert "Tonight" in result
        assert "28" in result
        assert "F" in result
        assert "10 mph" in result
        assert "Partly Cloudy" in result

    def test_missing_keys(self):
        result = format_forecast_period({})
        assert "N/A" in result


# ---------------------------------------------------------------------------
# Async tests: get_weather_response
# ---------------------------------------------------------------------------


class TestGetWeatherResponse:
    @pytest.fixture(autouse=True)
    def _patch_client(self):
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"features": []}
        self.mock_response.raise_for_status = MagicMock()

        self.mock_client = AsyncMock()
        self.mock_client.get.return_value = self.mock_response

        with patch(
            "mcp_servers.weather_mcp_server.weather_server.http_client",
            self.mock_client,
        ):
            yield

    async def test_success(self):
        self.mock_response.json.return_value = {"features": [SAMPLE_ALERT_FEATURE]}
        result = await get_weather_response("/alerts/active/area/CO")
        assert result == {"features": [SAMPLE_ALERT_FEATURE]}

    async def test_http_error(self):
        self.mock_client.get.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        result = await get_weather_response("/alerts/active/area/CO")
        assert result is None

    async def test_request_error(self):
        self.mock_client.get.side_effect = httpx.RequestError("timeout")
        result = await get_weather_response("/alerts/active/area/CO")
        assert result is None


# ---------------------------------------------------------------------------
# MCP tool tests: get_active_alerts_by_state
# ---------------------------------------------------------------------------


class TestGetActiveAlertsByState:
    @patch(
        "mcp_servers.weather_mcp_server.weather_server.get_weather_response",
        new_callable=AsyncMock,
    )
    async def test_valid_state_with_alerts(self, mock_response):
        mock_response.return_value = {"features": [SAMPLE_ALERT_FEATURE]}
        result = await get_active_alerts_by_state("CO")
        assert "Winter Storm Warning" in result

    @patch(
        "mcp_servers.weather_mcp_server.weather_server.get_weather_response",
        new_callable=AsyncMock,
    )
    async def test_no_alerts(self, mock_response):
        mock_response.return_value = {"features": []}
        result = await get_active_alerts_by_state("CO")
        assert "No active weather alerts" in result

    async def test_invalid_state_too_long(self):
        result = await get_active_alerts_by_state("CAL")
        assert "Invalid input" in result

    async def test_invalid_state_numeric(self):
        result = await get_active_alerts_by_state("12")
        assert "Invalid input" in result

    @patch(
        "mcp_servers.weather_mcp_server.weather_server.get_weather_response",
        new_callable=AsyncMock,
    )
    async def test_api_failure(self, mock_response):
        mock_response.return_value = None
        result = await get_active_alerts_by_state("CO")
        assert "Failed to retrieve" in result


# ---------------------------------------------------------------------------
# Async tests: _internal_get_forecast
# ---------------------------------------------------------------------------


class TestInternalGetForecast:
    async def test_invalid_latitude(self):
        result = await _internal_get_forecast(100.0, 0.0)
        assert "Invalid latitude or longitude" in result

    async def test_invalid_longitude(self):
        result = await _internal_get_forecast(0.0, 200.0)
        assert "Invalid latitude or longitude" in result

    @patch(
        "mcp_servers.weather_mcp_server.weather_server.get_weather_response",
        new_callable=AsyncMock,
    )
    async def test_no_gridpoint(self, mock_response):
        mock_response.return_value = None
        result = await _internal_get_forecast(40.7128, -74.0060)
        assert "Unable to retrieve NWS gridpoint" in result

    @patch(
        "mcp_servers.weather_mcp_server.weather_server.get_weather_response",
        new_callable=AsyncMock,
    )
    async def test_no_forecast_url(self, mock_response):
        mock_response.return_value = {"properties": {}}
        result = await _internal_get_forecast(40.7128, -74.0060)
        assert "Could not find the NWS forecast endpoint" in result

    @patch("mcp_servers.weather_mcp_server.weather_server.http_client")
    @patch(
        "mcp_servers.weather_mcp_server.weather_server.get_weather_response",
        new_callable=AsyncMock,
    )
    async def test_success(self, mock_get_weather, mock_client):
        mock_get_weather.return_value = SAMPLE_POINTS_DATA

        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = SAMPLE_FORECAST_DATA
        mock_forecast_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_forecast_response)

        result = await _internal_get_forecast(40.7128, -74.0060)
        assert "Tonight" in result
        assert "28" in result

    @patch("mcp_servers.weather_mcp_server.weather_server.http_client")
    @patch(
        "mcp_servers.weather_mcp_server.weather_server.get_weather_response",
        new_callable=AsyncMock,
    )
    async def test_forecast_request_fails(self, mock_get_weather, mock_client):
        mock_get_weather.return_value = SAMPLE_POINTS_DATA
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("timeout"))

        result = await _internal_get_forecast(40.7128, -74.0060)
        assert "Failed to retrieve detailed forecast" in result

    @patch("mcp_servers.weather_mcp_server.weather_server.http_client")
    @patch(
        "mcp_servers.weather_mcp_server.weather_server.get_weather_response",
        new_callable=AsyncMock,
    )
    async def test_no_periods(self, mock_get_weather, mock_client):
        mock_get_weather.return_value = SAMPLE_POINTS_DATA

        mock_forecast_response = MagicMock()
        mock_forecast_response.json.return_value = {"properties": {"periods": []}}
        mock_forecast_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_forecast_response)

        result = await _internal_get_forecast(40.7128, -74.0060)
        assert "No forecast periods found" in result


# ---------------------------------------------------------------------------
# MCP tool tests: get_forecast
# ---------------------------------------------------------------------------


class TestGetForecast:
    @patch(
        "mcp_servers.weather_mcp_server.weather_server._internal_get_forecast",
        new_callable=AsyncMock,
    )
    async def test_delegates_to_internal(self, mock_internal):
        mock_internal.return_value = "forecast data"
        result = await get_forecast(40.7128, -74.0060)
        assert result == "forecast data"
        mock_internal.assert_awaited_once_with(40.7128, -74.0060)


# ---------------------------------------------------------------------------
# MCP tool tests: get_forecast_by_city
# ---------------------------------------------------------------------------


class TestGetForecastByCity:
    @patch(
        "mcp_servers.weather_mcp_server.weather_server._internal_get_forecast",
        new_callable=AsyncMock,
    )
    @patch("mcp_servers.weather_mcp_server.weather_server.geolocator")
    async def test_valid_city(self, mock_geolocator, mock_internal):
        mock_location = MagicMock()
        mock_location.latitude = 40.7128
        mock_location.longitude = -74.0060
        mock_geolocator.geocode.return_value = mock_location

        mock_internal.return_value = "forecast for NYC"
        result = await get_forecast_by_city("New York", "NY")
        assert result == "forecast for NYC"
        mock_internal.assert_awaited_once_with(40.7128, -74.0060)

    async def test_invalid_empty_city(self):
        result = await get_forecast_by_city("", "NY")
        assert "Invalid city name" in result

    async def test_invalid_state_too_long(self):
        result = await get_forecast_by_city("New York", "NYY")
        assert "Invalid state code" in result

    async def test_invalid_state_numeric(self):
        result = await get_forecast_by_city("New York", "12")
        assert "Invalid state code" in result

    @patch(
        "mcp_servers.weather_mcp_server.weather_server._internal_get_forecast",
        new_callable=AsyncMock,
    )
    @patch("mcp_servers.weather_mcp_server.weather_server.geolocator")
    async def test_geocode_not_found(self, mock_geolocator, mock_internal):
        mock_geolocator.geocode.return_value = None
        result = await get_forecast_by_city("Nonexistent", "XX")
        assert "Could not find location" in result

    @patch("mcp_servers.weather_mcp_server.weather_server.geolocator")
    async def test_geocode_timeout(self, mock_geolocator):
        mock_geolocator.geocode.side_effect = GeocoderTimedOut("timeout")
        result = await get_forecast_by_city("New York", "NY")
        assert "Geocoding service error" in result
