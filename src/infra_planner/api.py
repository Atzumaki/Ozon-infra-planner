from fastapi import FastAPI, HTTPException

from infra_planner import __version__
from infra_planner.agents import PlanningOrchestrator
from infra_planner.models import AnalysisResult, PlanningRequest

app = FastAPI(
    title="Infrastructure Capacity Planner",
    version=__version__,
    description="Forecast-driven CAPEX/OPEX planning for compute infrastructure.",
)
orchestrator = PlanningOrchestrator()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/v1/plan", response_model=AnalysisResult)
def create_plan(request: PlanningRequest) -> AnalysisResult:
    try:
        return orchestrator.run(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

