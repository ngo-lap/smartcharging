"""
Test API with real online application, i.e. main.py must be executed
"""

import json
import pandas as pd
from fastapi.testclient import TestClient
from core.api.main import app


client = TestClient(app)


demand_sample = [
    {
        "vehicle": 0,
        "powerNom": 7,
        "energyRequired": 16.59,
        "energyMax": 52,
        "arrivalTime": 31,
        "departureTime": 41
    },
    {
        "vehicle": 1,
        "powerNom": 7,
        "energyRequired": 8.72,
        "energyMax": 100,
        "arrivalTime": 38,
        "departureTime": 43
    }
]

selected_columns = {"vehicle", "powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"}
demand_sample_str = json.dumps(demand_sample, indent=4)


def test_create_demand():

    response = client.get(
        "cpo/predict-charging-demand/",
        params={"source": "synthetic", "nbr_vehicles": 2, "horizon_length": 96, "time_step": 900}
    )

    assert response.status_code == 200

    demand_df: pd.DataFrame = pd.DataFrame.from_records(response.json())
    assert len(demand_df) == 2
    assert len(selected_columns - set(demand_df.columns)) == 0


# def test_create_charging_plans():
#     response = client.post("cpo/charging-plan/MILP")
#     assert response.status_code == 200
#     assert response.json() == {
#     }


