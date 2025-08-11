from matplotlib import pyplot as plt
import pandas as pd
import cvxpy as cp
from core.planner.day_ahead_planner import create_charging_plans
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data
from core.utility.kpi.eval_performance import compute_energetic_kpi


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
    data_mobility = generate_demand_data(nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step)
    data_planning = prepare_planning_data(data_demand=data_mobility, time_step=time_step)

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

    # Visualization
    fig, axs = plt.subplots(1, 2)  # 2x2 grid of subplots
    plt.plot(range(horizon_length), powerProfiles.sum(axis=1))
    plt.hlines(capacity, 0, horizon_length, linestyles='--')
    plt.xlabel("Time Idx")
    plt.ylabel("Total Charging Power (kW)")
    plt.show()
