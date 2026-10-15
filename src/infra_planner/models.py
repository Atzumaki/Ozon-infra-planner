from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, model_validator


class Observation(BaseModel):
    ds: date
    cpu_cores: float = Field(gt=0)
    ram_gb: float = Field(gt=0)


class ForecastPoint(BaseModel):
    ds: date
    cpu_cores: float
    ram_gb: float
    cpu_upper: float
    ram_upper: float


class DemandForecast(BaseModel):
    horizon_days: int
    points: list[ForecastPoint]
    validation_mape: dict[str, float]


class ServerType(BaseModel):
    name: str
    cpu_cores: int = Field(gt=0)
    ram_gb: int = Field(gt=0)
    capex: float = Field(gt=0)
    monthly_opex: float = Field(ge=0)
    max_count: int = Field(default=1000, ge=0)


class PlanningRequest(BaseModel):
    observations: list[Observation] = Field(min_length=21)
    server_types: list[ServerType] = Field(min_length=1)
    horizon_days: int = Field(default=30, ge=1, le=365)
    reserve_ratio: float = Field(default=0.20, ge=0, le=1)
    planning_months: int = Field(default=12, ge=1, le=60)
    owned_cpu_cores: float = Field(default=0, ge=0)
    owned_ram_gb: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def ensure_unique_server_names(self) -> PlanningRequest:
        names = [item.name for item in self.server_types]
        if len(names) != len(set(names)):
            raise ValueError("server type names must be unique")
        return self


class CapacityPlan(BaseModel):
    server_counts: dict[str, int]
    required_cpu_cores: float
    required_ram_gb: float
    purchased_cpu_cores: float
    purchased_ram_gb: float
    capex: float
    opex: float
    total_cost: float
    status: str


class AnalysisResult(BaseModel):
    forecast: DemandForecast
    plan: CapacityPlan
    risk_notes: list[str]
    executive_summary: str

