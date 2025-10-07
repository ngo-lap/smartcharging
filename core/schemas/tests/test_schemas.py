from pydantic import ValidationError
import pytest
from core.schemas.cpo import ChargingPlanData, PlanningParameters, Station, DemandData

def test_demand_data_defaults_and_required_fields():
    # Only required field is 'demand'
    data = DemandData(demand=[{"vehicle_id": 1, "demand": 10}])
    assert data.source == "synthetic"
    assert data.creation_date is None
    assert isinstance(data.demand, list)
    assert data.demand[0]["vehicle_id"] == 1

    # Test missing required field
    with pytest.raises(ValidationError):
        DemandData()

def test_charging_plan_data_defaults_and_required_fields():
    data = ChargingPlanData(plans=[{"vehicle_id": 1, "power": 5}])
    assert data.algorithm == "1C1S"
    assert data.creation_date is None
    assert isinstance(data.plans, list)
    assert data.plans[0]["vehicle_id"] == 1

    with pytest.raises(ValidationError):
        ChargingPlanData()

def test_planning_parameters_defaults_and_required_fields():
    params = PlanningParameters(
        nbr_vehicles=2,
        pmax_infrastructure=100.0
    )
    assert params.horizon_length == 96
    assert params.time_step == 600
    assert params.nbr_vehicles == 2
    assert params.pmax_infrastructure == 100.0
    assert params.creation_date is None

    # Test missing required fields
    with pytest.raises(ValidationError):
        PlanningParameters()


def test_station_model():
    """
    Test the creation of a Station object with specified parameters and verify its attributes.

    This test ensures that:
    - The number of terminals and transformer capacity are correctly assigned.
    - The planning_parameters attribute is an instance of PlanningParameters.
    """
    params = PlanningParameters(
        nbr_vehicles=3,
        pmax_infrastructure=200.0
    )
    station = Station(
        nbr_terminals=4,
        transformer_capacity=500.0,
        planning_parameters=params
    )
    assert station.nbr_terminals == 4
    assert station.transformer_capacity == 500.0
    assert isinstance(station.planning_parameters, PlanningParameters)


def test_missing_fields():
    """
    Test that creating instances of DemandData, ChargingPlanData, PlanningParameters, and Station
    without required fields raises a ValidationError.
    """
    # Test missing required field
    with pytest.raises(ValidationError):
        DemandData()

    with pytest.raises(ValidationError):
        ChargingPlanData()

    # Test missing required fields
    with pytest.raises(ValidationError):
        PlanningParameters()

    # Test missing required fields
    with pytest.raises(ValidationError):
        Station()

