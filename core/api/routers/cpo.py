from datetime import datetime
from typing import Literal
import pandas as pd
from fastapi import HTTPException, APIRouter
from core.api.config import format_time
from core.planner.day_ahead_planner import create_charging_plans
import cvxpy as cp
from core.schemas.cpo import DemandData, ChargingPlanData, PlanningParameters
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data


router = APIRouter(prefix="/cpo", tags=["cpo"])


@router.get("/predict-charging-demand/{source}")
async def predict_charging_demand(
        source: Literal['synthetic', 'from_file'] = 'synthetic',
        nbr_vehicles: int = 10,
        horizon_length: int = 96,
        time_step: int = 900
) -> DemandData:

    created_at = datetime.now().strftime(format_time)
    if source == 'synthetic':

        demand_df = generate_demand_data(nbr_vehicles=nbr_vehicles, horizon_length=horizon_length, time_step=time_step)
        data_planning = prepare_planning_data(data_demand=demand_df, time_step=time_step)
        return DemandData(creation_date=created_at, source="synthetic", demand=data_planning.to_dict("records"))

    else:
        return DemandData(creation_date=created_at, source="from_file", demand=[])


@router.post("/charging-plan/{algorithm}", )
async def get_charging_plans(
        algorithm: Literal["milp", "lp"],
        demand: DemandData,
        planning_params: PlanningParameters
) -> ChargingPlanData:

    demand_df = pd.DataFrame.from_records(demand.demand)

    if algorithm == "milp" or "lp":

        _, powerVehicles, _ = create_charging_plans(
            data_demand=demand_df,
            horizon_length=planning_params.horizon_length,
            time_step=planning_params.time_step,
            nbr_vehicle=planning_params.nbr_vehicles,
            capacity_grid=planning_params.pmax_infrastructure,
            n_sols=0,
            formulation=algorithm,
            solver_options={
                "solver": cp.SCIPY if algorithm == "milp" else cp.CLARABEL,
                "time_limit": 60.0, "verbose": False, "warm_start": False
            }
        )

    else:
        raise HTTPException(status_code=500, detail=f"Invalid algorithm {algorithm}, must be milp or lp")

    charging_plans = ChargingPlanData(
        creation_date=datetime.now().strftime(format_time),
        algorithm=algorithm,
        plans=pd.DataFrame(powerVehicles).to_dict("records")
    )
    return charging_plans
