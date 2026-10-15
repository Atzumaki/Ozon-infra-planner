import argparse
from pathlib import Path

from infra_planner.agents import PlanningOrchestrator
from infra_planner.demo import demo_request
from infra_planner.models import PlanningRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="Forecast infrastructure demand and optimize TCO")
    parser.add_argument("--input", type=Path, help="JSON file matching the PlanningRequest schema")
    parser.add_argument("--output", type=Path, help="optional path for the result JSON")
    args = parser.parse_args()
    request = (
        PlanningRequest.model_validate_json(args.input.read_text(encoding="utf-8"))
        if args.input
        else demo_request()
    )
    result = PlanningOrchestrator().run(request)
    rendered = result.model_dump_json(indent=2)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()

