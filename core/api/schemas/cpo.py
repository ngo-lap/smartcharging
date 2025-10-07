from typing import Dict, List, Optional
from pydantic import BaseModel


# %% Data Classes

class DemandData(BaseModel):
    creation_date: Optional[str] = None
    source: str = 'synthetic'
    demand: List[Dict]


class ChargingPlanData(BaseModel):
    creation_date: Optional[str] = None
    algorithm: str = "1C1S"
    plans: List[Dict]


class PlanningParameters(BaseModel):
    creation_date: Optional[str] = None
    nbr_vehicles: int
    horizon_length: int = 96
    time_step: int = 600
    pmax_infrastructure: float


class Station(BaseModel):
    nbr_terminals: int
    transformer_capacity: float
    planning_parameters: PlanningParameters
