import json

import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
import cvxpy as cp
from core.planner.day_ahead_planner import create_charging_plans
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data, create_time_horizon
from core.utility.kpi.eval_performance import compute_energetic_kpi
import plotly.graph_objects as go
import plotly.express as px


def simple_cpo_fixed_capacity():

    # Meta-parameters
    nVE = 40
    time_step = 900         # [Seconds]
    horizon_length = 96     # [Time Step]
    capacity = 200          # [kW] grid capacity
    n_sols = 250
    solver_options_1 = {"solver": cp.CLARABEL, "time_limit": 60.0, "verbose": False, "warm_start": False}
    solver_options_2 = {"solver": cp.SCIPY, "time_limit": 60.0, "verbose": False, "warm_start": False}

    # Data Preparation
    data_planning = generate_demand_data(nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step)
    data_planning = prepare_planning_data(data_demand=data_planning, time_step=time_step)

    # Planning
    _, powerProfiles, evcsp = create_charging_plans(
        data_planning, horizon_length=horizon_length, time_step=time_step,
        nbr_vehicle=nVE, capacity_grid=capacity, n_sols=n_sols,
        formulation="milp", solver_options=solver_options_2
    )

    # KPI
    kpi_station, kpi_per_ev = compute_energetic_kpi(
        power_profiles=powerProfiles,
        power_grid=capacity,
        planning_input=data_planning,
        time_step=time_step
    )

    print(evcsp.solver_stats)
    print(kpi_station)

    # Visualization
    fig, axs = plt.subplots(1, 2)  # 2x2 grid of subplots
    plt.plot(range(horizon_length), powerProfiles.sum(axis=1))
    plt.hlines(capacity, 0, horizon_length, linestyles='--')
    plt.xlabel("Time Idx")
    plt.ylabel("Total Charging Power (kW)")
    plt.show()


def simple_cpo_variable_capacity():

    """
        Variable infrastructure limit

    """

    # Meta-parameters
    nVE = 40
    time_step = 900         # [Seconds]
    horizon_length = 96     # [Time Step]
    capacity = 200          # [kW] grid capacity
    n_sols = 250
    capacity_grid = np.array([100] * horizon_length)
    # capacity_grid[40:57] = 80
    solver_options = {"solver": cp.CLARABEL, "time_limit": 60.0, "verbose": False, "warm_start": False}
    # solver_options = {"solver": cp.SCIPY, "time_limit": 60.0, "verbose": False, "warm_start": False}

    horizon_start = np.datetime64('today')
    horizon_datetime = create_time_horizon(start=horizon_start, time_step=time_step, horizon_length=horizon_length)

    # Data Preparation
    data_sessions = generate_demand_data(
        nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step, horizon_start=horizon_start
    )
    data_planning = prepare_planning_data(data_demand=data_sessions, time_step=time_step)

    # PLANNING
    _, powerProfiles, evcsp = create_charging_plans(
        data_planning, horizon_length=horizon_length, time_step=time_step,
        nbr_vehicle=nVE, capacity_grid=capacity_grid, n_sols=n_sols,
        formulation="lp", solver_options=solver_options
    )

    # KPI
    kpi_station, kpi_per_ev = compute_energetic_kpi(
        power_profiles=powerProfiles,
        power_grid=capacity,
        planning_input=data_planning,
        time_step=time_step
    )

    print(evcsp.solver_stats)
    print(kpi_station)

    # Visualization
    plt.plot(horizon_datetime, powerProfiles.sum(axis=1))
    plt.plot(horizon_datetime, capacity_grid, '--')
    plt.xlabel("Time Idx")
    plt.ylabel("Total Charging Power (kW)")
    plt.show()

    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=horizon_datetime, y=powerProfiles.sum(axis=1), name="Total Charging Power (kW)"))
    # fig.add_trace(go.Scatter(x=horizon_datetime, y=capacity_grid, name="Infras Capacity (kW)"))
    # # fig = px.area(x=horizon_datetime, y=powerProfiles.sum(axis=1))
    #
    # fig.update_layout(
    #     title={"text": "Station Power Profiles"},
    #     xaxis={"title": {"text": "Time Step"}},
    #     yaxis={"title": {"text": "Power (kW)"}}
    # )
    # fig.show()

    # Temp - export sample demand to json files
    # selected_columns = ["vehicle", "powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"]
    # demand_json = data_planning[selected_columns].to_dict('records')
    # demand_json_str = json.dumps(demand_json, indent=4)
    # print(demand_json_str)


if __name__ == '__main__':

    simple_cpo_variable_capacity()
