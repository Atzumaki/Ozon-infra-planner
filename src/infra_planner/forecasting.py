from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from infra_planner.models import DemandForecast, ForecastPoint, Observation


@dataclass
class _FitResult:
    coefficients: np.ndarray
    sigma: float


class TrendSeasonalForecaster:
    """Interpretable linear trend with weekly Fourier seasonality.

    The model is deliberately small: infrastructure forecasts often need a
    transparent baseline before more complex models are justified.
    """

    def __init__(self, interval_z: float = 1.96) -> None:
        self.interval_z = interval_z

    @staticmethod
    def _design(t: np.ndarray) -> np.ndarray:
        angle = 2 * np.pi * t / 7
        return np.column_stack(
            [np.ones_like(t), t, np.sin(angle), np.cos(angle), t**2]
        )

    def _fit(self, values: np.ndarray, t: np.ndarray) -> _FitResult:
        design = self._design(t)
        coefficients, *_ = np.linalg.lstsq(design, values, rcond=None)
        residuals = values - design @ coefficients
        sigma = float(np.std(residuals, ddof=min(design.shape[1], len(values) - 1)))
        return _FitResult(coefficients=coefficients, sigma=max(sigma, 1e-6))

    def _predict(self, fit: _FitResult, t: np.ndarray) -> np.ndarray:
        return np.maximum(self._design(t) @ fit.coefficients, 0)

    def forecast(
        self, observations: list[Observation], horizon_days: int
    ) -> DemandForecast:
        frame = pd.DataFrame([item.model_dump() for item in observations]).sort_values("ds")
        if frame["ds"].duplicated().any():
            raise ValueError("observation dates must be unique")
        if len(frame) < 21:
            raise ValueError("at least 21 observations are required")

        validation_size = min(14, max(7, len(frame) // 5))
        split = len(frame) - validation_size
        train_t = np.arange(split, dtype=float)
        validation_t = np.arange(split, len(frame), dtype=float)
        mape: dict[str, float] = {}
        for column in ("cpu_cores", "ram_gb"):
            fit = self._fit(frame[column].to_numpy(dtype=float)[:split], train_t)
            predicted = self._predict(fit, validation_t)
            actual = frame[column].to_numpy(dtype=float)[split:]
            mape[column] = round(
                float(np.mean(np.abs(actual - predicted) / np.maximum(actual, 1))) * 100, 2
            )

        all_t = np.arange(len(frame), dtype=float)
        future_t = np.arange(len(frame), len(frame) + horizon_days, dtype=float)
        fits = {
            column: self._fit(frame[column].to_numpy(dtype=float), all_t)
            for column in ("cpu_cores", "ram_gb")
        }
        predicted = {column: self._predict(fit, future_t) for column, fit in fits.items()}
        last_date = pd.Timestamp(frame["ds"].iloc[-1])
        points = []
        for index in range(horizon_days):
            cpu = float(predicted["cpu_cores"][index])
            ram = float(predicted["ram_gb"][index])
            points.append(
                ForecastPoint(
                    ds=(last_date + pd.Timedelta(days=index + 1)).date(),
                    cpu_cores=round(cpu, 2),
                    ram_gb=round(ram, 2),
                    cpu_upper=round(cpu + self.interval_z * fits["cpu_cores"].sigma, 2),
                    ram_upper=round(ram + self.interval_z * fits["ram_gb"].sigma, 2),
                )
            )
        return DemandForecast(
            horizon_days=horizon_days,
            points=points,
            validation_mape=mape,
        )

