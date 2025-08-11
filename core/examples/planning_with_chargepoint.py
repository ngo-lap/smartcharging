from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import cvxpy as cp
from core.planner.day_ahead_planner import create_charging_plans
from core.planner.optimization import evcsp_milp, evcsp_lp
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data
from core.utility.kpi.eval_performance import compute_energetic_kpi
from core.utility.logger.custom_loggers import setup_logger
from data.data_converter import convert_chargepoint_data


if __name__ == '__main__':

    nVE = 100
    time_step = 900         # [Seconds]
    horizon_length = 96     # [Time Step]
    capacity = 200          # [kW] grid capacity
    n_sols = 250
    solver_options_1 = {"solver": cp.CLARABEL, "time_limit": 60.0, "verbose": False, "warm_start": False}
    solver_options_2 = {"solver": cp.SCIPY, "time_limit": 60.0, "verbose": False, "warm_start": False}

    # Data Preparation
    data_chargepoint = pd.read_excel("../../data/fleetScenarioSimu.xlsx", parse_dates=["session_start", "session_end"])
    data_planning = convert_chargepoint_data(df_raw=data_chargepoint)
    data_planning = prepare_planning_data(data_demand=data_planning, time_step=time_step)

    # Planning
    activationProfiles, powerProfiles, prob = create_charging_plans(
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

    print(prob.solver_stats)
    print(kpi_station)

    # _, _, prob2 = planner(
    #     data_planning, horizon_length=horizon_length, time_step=time_step,
    #     nbr_vehicle=nVE, capacity_grid=capacity, n_sols=n_sols,
    #     formulation="lp", solver_options=solver_options_2
    # )
    # print(prob2.solver_stats)

    # Visualization
    fig, axs = plt.subplots(1, 2)  # 2x2 grid of subplots
    plt.plot(range(horizon_length), powerProfiles.sum(axis=1))
    plt.hlines(capacity, 0, horizon_length, linestyles='--')
    plt.xlabel("Time Idx")
    plt.ylabel("Total Charging Power (kW)")
    plt.show()
