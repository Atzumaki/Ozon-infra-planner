from infra_planner.demo import demo_request
from infra_planner.forecasting import TrendSeasonalForecaster


def test_forecast_has_horizon_and_intervals() -> None:
    request = demo_request()
    result = TrendSeasonalForecaster().forecast(request.observations, 30)
    assert len(result.points) == 30
    assert result.points[0].ds > request.observations[-1].ds
    assert all(point.cpu_upper >= point.cpu_cores for point in result.points)
    assert result.validation_mape["cpu_cores"] < 10


def test_forecast_rejects_duplicate_dates() -> None:
    request = demo_request()
    request.observations[-1].ds = request.observations[-2].ds
    try:
        TrendSeasonalForecaster().forecast(request.observations, 7)
    except ValueError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate dates must fail")

