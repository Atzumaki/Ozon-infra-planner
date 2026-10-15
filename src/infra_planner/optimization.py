from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from infra_planner.models import CapacityPlan, ServerType


class CapacityOptimizer:
    """Find the minimum TCO integer server mix under CPU/RAM constraints."""

    def optimize(
        self,
        *,
        required_cpu: float,
        required_ram: float,
        server_types: list[ServerType],
        planning_months: int,
        owned_cpu: float = 0,
        owned_ram: float = 0,
    ) -> CapacityPlan:
        net_cpu = max(required_cpu - owned_cpu, 0)
        net_ram = max(required_ram - owned_ram, 0)
        costs = np.array(
            [item.capex + planning_months * item.monthly_opex for item in server_types]
        )
        capacities = np.array(
            [
                [item.cpu_cores for item in server_types],
                [item.ram_gb for item in server_types],
            ],
            dtype=float,
        )
        result = milp(
            c=costs,
            integrality=np.ones(len(server_types)),
            bounds=Bounds(np.zeros(len(server_types)), [item.max_count for item in server_types]),
            constraints=LinearConstraint(capacities, [net_cpu, net_ram], [np.inf, np.inf]),
            options={"time_limit": 10},
        )
        if not result.success or result.x is None:
            raise ValueError(f"no feasible capacity plan: {result.message}")

        counts = np.rint(result.x).astype(int)
        capex = sum(count * item.capex for count, item in zip(counts, server_types, strict=True))
        opex = sum(
            count * item.monthly_opex * planning_months
            for count, item in zip(counts, server_types, strict=True)
        )
        purchased_cpu = sum(
            count * item.cpu_cores for count, item in zip(counts, server_types, strict=True)
        )
        purchased_ram = sum(
            count * item.ram_gb for count, item in zip(counts, server_types, strict=True)
        )
        return CapacityPlan(
            server_counts={
                item.name: int(count)
                for count, item in zip(counts, server_types, strict=True)
                if count > 0
            },
            required_cpu_cores=round(required_cpu, 2),
            required_ram_gb=round(required_ram, 2),
            purchased_cpu_cores=round(purchased_cpu, 2),
            purchased_ram_gb=round(purchased_ram, 2),
            capex=round(capex, 2),
            opex=round(opex, 2),
            total_cost=round(capex + opex, 2),
            status="optimal" if result.status == 0 else "feasible",
        )

