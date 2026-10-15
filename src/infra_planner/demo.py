from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from infra_planner.models import Observation, PlanningRequest, ServerType


def demo_request(days: int = 120, seed: int = 42) -> PlanningRequest:
    random = np.random.default_rng(seed)
    start = date(2025, 1, 1)
    observations = []
    for day in range(days):
        weekly = 90 * np.sin(2 * np.pi * day / 7)
        business_growth = 3.2 * day
        cpu = 900 + business_growth + weekly + random.normal(0, 22)
        ram = 2600 + 7.5 * day + 160 * np.sin(2 * np.pi * day / 7) + random.normal(0, 45)
        observations.append(
            Observation(
                ds=start + timedelta(days=day),
                cpu_cores=max(cpu, 1),
                ram_gb=max(ram, 1),
            )
        )
    server_types = [
        ServerType(
            name="compute-64", cpu_cores=64, ram_gb=256, capex=720_000, monthly_opex=11_000
        ),
        ServerType(
            name="balanced-48", cpu_cores=48, ram_gb=384, capex=760_000, monthly_opex=10_000
        ),
        ServerType(
            name="memory-32", cpu_cores=32, ram_gb=768, capex=980_000, monthly_opex=13_000
        ),
    ]
    return PlanningRequest(
        observations=observations,
        server_types=server_types,
        horizon_days=30,
        reserve_ratio=0.20,
        planning_months=12,
        owned_cpu_cores=900,
        owned_ram_gb=2600,
    )

