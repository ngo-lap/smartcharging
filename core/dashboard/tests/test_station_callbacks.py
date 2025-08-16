from typing import List, Dict

import pandas as pd
import pytest
from core.dashboard.station_supervisor import run_planner


@pytest.fixture
def demand_raw() -> List[Dict]:

    charging_demand_raw = [
        {
            "vehicle": 0,
            "powerNom": 7,
            "energyRequired": 16.00,
            "energyMax": 52,
            "arrivalTime": "2025-08-16T05:15:44",
            "departureTime": "2025-08-16T09:04:16",
        },
        {
            "vehicle": 0,
            "powerNom": 7,
            "energyRequired": 16.00,
            "energyMax": 52,
            "arrivalTime": "2025-08-16T05:15:44",
            "departureTime": "2025-08-16T09:04:16",
        }
    ]

    return charging_demand_raw


def test_run_planner(demand_raw):

    fig_power, fig_kpi, fig_vehicle_power, plans_dict = run_planner(demand=demand_raw, pmax=100)
    plans_df = pd.DataFrame.from_records(plans_dict)
    assert len(plans_df.columns) == len(demand_raw)
    assert len(plans_df) == 96

