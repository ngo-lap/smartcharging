import pytest
from fastapi.testclient import TestClient
import pandas as pd

from core.api.main import app  # Change this to your actual FastAPI app import

@pytest.fixture
def client():
    return TestClient(app)

def test_predict_charging_demand_synthetic(client, monkeypatch):
    def fake_generate_demand_data(nbr_vehicles, horizon_length, time_step):
        return pd.DataFrame([{"vehicle_id": 1, "demand": 10}])

    def fake_prepare_planning_data(data_demand, time_step):
        return pd.DataFrame([{"vehicle_id": 1, "demand": 10, "prepared": True}])

    monkeypatch.setattr("core.api.routers.cpo.generate_demand_data", fake_generate_demand_data)
    monkeypatch.setattr("core.api.routers.cpo.prepare_planning_data", fake_prepare_planning_data)

    response = client.get("/cpo/predict-charging-demand/synthetic?nbr_vehicles=1&horizon_length=1&time_step=1")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "synthetic"
    assert isinstance(data["demand"], list)
    assert data["demand"][0]["vehicle_id"] == 1
    assert data["demand"][0]["prepared"] is True

def test_predict_charging_demand_from_file(client):
    response = client.get("/cpo/predict-charging-demand/from_file")
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "from_file"
    assert data["demand"] == []
    
    
def test_get_charging_plans_milp(client, monkeypatch):
    # Prepare fake input data
    demand_data = {
        "creation_date": "2024-01-01 00:00:00",
        "source": "synthetic",
        "demand": [{"vehicle_id": 1, "demand": 10}]
    }
    planning_params = {
        "creation_date": "2024-01-01 00:00:00",
        "horizon_length": 1,
        "time_step": 1,
        "nbr_vehicles": 1,
        "pmax_infrastructure": 100
    }

    # Fake create_charging_plans to avoid heavy computation
    def fake_create_charging_plans(**kwargs):
        return None, [{"vehicle_id": 1, "power": 5}], None

    monkeypatch.setattr("core.api.routers.cpo.create_charging_plans", fake_create_charging_plans)

    response = client.post(
        "/cpo/charging-plan/milp",
        json={
            "demand": demand_data,
            "planning_params": planning_params
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "milp"
    assert isinstance(data["plans"], list)
    assert data["plans"][0]["vehicle_id"] == 1
    assert data["plans"][0]["power"] == 5


def test_get_charging_plans_lp(client, monkeypatch):
    demand_data = {
        "creation_date": "2024-01-01 00:00:00",
        "source": "synthetic",
        "demand": [{"vehicle_id": 2, "demand": 20}]
    }
    planning_params = {
        "creation_date": "2024-01-01 00:00:00",
        "horizon_length": 1,
        "time_step": 1,
        "nbr_vehicles": 1,
        "pmax_infrastructure": 100
    }

    def fake_create_charging_plans(**kwargs):
        return None, [{"vehicle_id": 2, "power": 8}], None

    monkeypatch.setattr("core.api.routers.cpo.create_charging_plans", fake_create_charging_plans)

    response = client.post(
        "/cpo/charging-plan/lp",
        json={
            "demand": demand_data,
            "planning_params": planning_params
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "lp"
    assert isinstance(data["plans"], list)
    assert data["plans"][0]["vehicle_id"] == 2
    assert data["plans"][0]["power"] == 8


def test_get_charging_plans_invalid_algorithm(client):
    demand_data = {
        "creation_date": "2024-01-01 00:00:00",
        "source": "synthetic",
        "demand": [{"vehicle_id": 1, "demand": 10}]
    }
    planning_params = {
        "horizon_length": 1,
        "time_step": 1,
        "nbr_vehicles": 1,
        "pmax_infrastructure": 100
    }

    response = client.post(
        "/cpo/charging-plan/invalid_algo",
        json={
            "demand": demand_data,
            "planning_params": planning_params
        }
    )
    # The current implementation will not raise for invalid algorithm due to bug in the if condition,
    # but the test is written as if the bug is fixed.
    assert response.status_code == 500 or response.status_code == 422
