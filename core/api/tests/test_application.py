"""
Test with TestClient instead of real application, i.e. test interacts directly with the router's code.
"""

from typing import Dict, List
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from core.api.main import app
from core.utility.data.data_processor import verify_planning_data
from data.charging_demand import charging_demand_columns as required_columns

client = TestClient(app)


@pytest.fixture
def demand_sample() -> List[Dict]:

    return [
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
            "powerNom": 11,
            "energyRequired": 8.72,
            "energyMax": 100,
            "arrivalTime": 38,
            "departureTime": 43
        }
    ]


def test_create_demand():

    """
    Test predict-charging-demand endpoint.
    """

    response = client.get(
        "/cpo/predict-charging-demand/synthetic",
        params={"nbr_vehicles": 2, "horizon_length": 96, "time_step": 900}
    )
    response_content = response.json()
    demand_df: pd.DataFrame = pd.DataFrame.from_records(response_content["demand"])

    assert response.status_code == 200
    assert response_content["source"] == "synthetic"
    assert len(demand_df) == 2
    # assert len(set(required_columns) - set(demand_df.columns)) == 0
    verify_planning_data(df_planning=demand_df)     # If required columns are missing


def test_create_charging_plans_lp(demand_sample):

    """
    Test create charging plans endpoint.
    Maximum Infrastructure Power is twice the sum of all vehicles nominal powers to ensure that all vehicles are
    charged unlimited.
    """

    # PREPARATION
    p_max_infra = 1 * sum([v["powerNom"] for v in demand_sample])

    # ACT
    response = client.post(
        "/cpo/charging-plan/lp",
        json={
            "planning_params": {
                "creation_date": "", "nbr_vehicles": 2, "horizon_length": 96,
                "time_step": 900, "pmax_infrastructure": p_max_infra
            },
            "demand": {"creation_date": "", "source": "synthetic", "demand": demand_sample}
        }
    )
    response_content = response.json()
    plans_df: pd.DataFrame = pd.DataFrame.from_records(response_content["plans"])

    # ASSERT
    assert response.status_code == 200
    assert response_content["algorithm"] == "lp"
    assert len(plans_df) == 96
    assert len(plans_df.columns) == 2

    # Test Charging Plans for each vehicle
    for v in demand_sample:
        assert min(plans_df.iloc[:, v["vehicle"]]) == 0, "Minimum charging power > 0"
        assert pytest.approx(max(plans_df.iloc[:, v["vehicle"]])) == v['powerNom'], "Maximum power is not at PNom"
        assert (pytest.approx(plans_df.iloc[0:v["arrivalTime"], v["vehicle"]]) == 0.), "Vehicle charged before arrival"
        assert (pytest.approx(plans_df.iloc[v["departureTime"]::, v["vehicle"]]) == 0.), "Vehicle charged after departure"
        assert (900 / 3600) * plans_df.iloc[:, v["vehicle"]].sum() >= v["energyRequired"], "Required energy not met"
        assert (900 / 3600) * plans_df.iloc[:, v["vehicle"]].sum() <= v["energyMax"], "More charging energy than max energy"


def test_create_charging_plans_milp(demand_sample):

    """
    Test create charging plans endpoint.
    Maximum Infrastructure Power is twice the sum of all vehicles nominal powers to ensure that all vehicles are
    charged unlimited.
    """

    # PREPARATION
    p_max_infra = 1 * sum([v["powerNom"] for v in demand_sample])

    # ACT
    response = client.post(
        "/cpo/charging-plan/milp",
        json={
            "planning_params": {
                "creation_date": "", "nbr_vehicles": 2, "horizon_length": 96,
                "time_step": 900, "pmax_infrastructure": p_max_infra
            },
            "demand": {"creation_date": "", "source": "synthetic", "demand": demand_sample}
        }
    )
    response_content = response.json()
    plans_df: pd.DataFrame = pd.DataFrame.from_records(response_content["plans"])

    # ASSERT
    assert response.status_code == 200
    assert response_content["algorithm"] == "milp"
    assert len(plans_df) == 96
    assert len(plans_df.columns) == 2

    # Test Charging Plans for each vehicle
    for v in demand_sample:
        assert min(plans_df.iloc[:, v["vehicle"]]) == 0, "Minimum charging power > 0"
        assert pytest.approx(max(plans_df.iloc[:, v["vehicle"]])) == v['powerNom'], "Maximum power is not at PNom"
        assert (pytest.approx(plans_df.iloc[0:v["arrivalTime"], v["vehicle"]]) == 0.), "Vehicle charged before arrival"
        assert (pytest.approx(plans_df.iloc[v["departureTime"]::, v["vehicle"]]) == 0.), "Vehicle charged after departure"
        assert (900 / 3600) * plans_df.iloc[:, v["vehicle"]].sum() >= v["energyRequired"], "Required energy not met"
        assert (900 / 3600) * plans_df.iloc[:, v["vehicle"]].sum() <= v["energyMax"], "More charging energy than max energy"
