import pytest

from infra_planner.models import ServerType
from infra_planner.optimization import CapacityOptimizer


def test_optimizer_selects_cheapest_feasible_mix() -> None:
    servers = [
        ServerType(name="small", cpu_cores=8, ram_gb=16, capex=100, monthly_opex=0),
        ServerType(name="large", cpu_cores=16, ram_gb=64, capex=150, monthly_opex=0),
    ]
    plan = CapacityOptimizer().optimize(
        required_cpu=16, required_ram=50, server_types=servers, planning_months=12
    )
    assert plan.server_counts == {"large": 1}
    assert plan.total_cost == 150


def test_optimizer_reports_infeasible_plan() -> None:
    servers = [
        ServerType(
            name="limited", cpu_cores=8, ram_gb=16, capex=100, monthly_opex=0, max_count=1
        )
    ]
    with pytest.raises(ValueError, match="no feasible"):
        CapacityOptimizer().optimize(
            required_cpu=100, required_ram=100, server_types=servers, planning_months=12
        )

