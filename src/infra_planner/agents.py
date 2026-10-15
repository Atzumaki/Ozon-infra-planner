from __future__ import annotations

from dataclasses import dataclass

from infra_planner.forecasting import TrendSeasonalForecaster
from infra_planner.models import AnalysisResult, CapacityPlan, DemandForecast, PlanningRequest
from infra_planner.optimization import CapacityOptimizer


@dataclass
class ForecastAgent:
    forecaster: TrendSeasonalForecaster

    def run(self, request: PlanningRequest) -> DemandForecast:
        return self.forecaster.forecast(request.observations, request.horizon_days)


@dataclass
class BudgetAgent:
    optimizer: CapacityOptimizer

    def run(self, request: PlanningRequest, forecast: DemandForecast) -> CapacityPlan:
        required_cpu = max(point.cpu_upper for point in forecast.points) * (
            1 + request.reserve_ratio
        )
        required_ram = max(point.ram_upper for point in forecast.points) * (
            1 + request.reserve_ratio
        )
        return self.optimizer.optimize(
            required_cpu=required_cpu,
            required_ram=required_ram,
            server_types=request.server_types,
            planning_months=request.planning_months,
            owned_cpu=request.owned_cpu_cores,
            owned_ram=request.owned_ram_gb,
        )


class RiskAgent:
    def run(
        self, request: PlanningRequest, forecast: DemandForecast, plan: CapacityPlan
    ) -> list[str]:
        notes = []
        worst_mape = max(forecast.validation_mape.values())
        if worst_mape > 15:
            notes.append(
                f"Validation MAPE is {worst_mape:.1f}%; investigate regime changes before purchase."
            )
        if request.reserve_ratio < 0.15:
            notes.append("Reserve is below 15%; the plan may be sensitive to traffic spikes.")
        cpu_buffer = request.owned_cpu_cores + plan.purchased_cpu_cores - plan.required_cpu_cores
        ram_buffer = request.owned_ram_gb + plan.purchased_ram_gb - plan.required_ram_gb
        notes.append(f"Post-plan headroom: {cpu_buffer:.0f} CPU cores and {ram_buffer:.0f} GB RAM.")
        return notes


class PlanningOrchestrator:
    """Coordinates focused analytical agents through typed hand-offs."""

    def __init__(self) -> None:
        self.forecast_agent = ForecastAgent(TrendSeasonalForecaster())
        self.budget_agent = BudgetAgent(CapacityOptimizer())
        self.risk_agent = RiskAgent()

    def run(self, request: PlanningRequest) -> AnalysisResult:
        forecast = self.forecast_agent.run(request)
        plan = self.budget_agent.run(request, forecast)
        risks = self.risk_agent.run(request, forecast, plan)
        mix = ", ".join(f"{name}: {count}" for name, count in plan.server_counts.items())
        summary = (
            f"For the next {request.horizon_days} days, buy [{mix}] at a "
            f"{request.planning_months}-month TCO of {plan.total_cost:,.0f}."
        )
        return AnalysisResult(
            forecast=forecast,
            plan=plan,
            risk_notes=risks,
            executive_summary=summary,
        )

