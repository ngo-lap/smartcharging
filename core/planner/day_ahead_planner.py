# day_ahead_planner.py
# Translate real charging demand data to optimization input file
from typing import List
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
import cvxpy as cp
from core.planner.optimization import evcsp_milp
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data
from core.utility.kpi.eval_performance import compute_energetic_kpi
from core.utility.logger.custom_loggers import setup_logger

plt.rcParams["figure.figsize"] = (20, 12)
logger = setup_logger(__name__)


def create_charging_plans(
        data_demand: pd.DataFrame, horizon_length: int, time_step: int,
        nbr_vehicle: int, capacity_grid: float | List[float] | np.array, n_sols: int,
        formulation: str = "milp", solver_options: dict = None
) -> (np.array, np.array, cp.Problem):

    """
        Return the charging plans of all vehicles

    :param solver_options:
    :param formulation: optimization formulation, either "milp" or "lp"
    :param data_demand: charging demand data
    :param horizon_length: length of horizon [time steps]
    :param time_step: time step [seconds]
    :param nbr_vehicle: number of vehicles
    :param capacity_grid: grid capacity [kW]
    :param n_sols:
    :return:
        profile: charging profile of individual vehicles [kW]
        totalPowerProfile: total charging profiles of all vehicles [kW]
    """

    if nbr_vehicle == len(data_demand):
        logger.info("Planner called")
    else:
        logger.error(f"Number of vehicles: {nbr_vehicle} but data length is {len(data_demand)}")

    # Data preparation
    arrival = data_demand.loc[:, "arrivalTime"].tolist()
    departure = data_demand.loc[:, "departureTime"].tolist()
    power = data_demand.loc[:, "powerNom"].tolist()
    duration = data_demand.loc[:, "chargingDuration"].tolist()
    energyRequired = data_demand.loc[:, "energyRequired"].tolist()
    energyMax = data_demand.loc[:, "energyMax"].tolist()

    assert all((np.array(departure) - np.array(arrival) - duration) >= 0), \
        "Charging duration must be shorter than parking time"

    # Calling the EVCSP planner: either CP (constraint programming), MILP or Heuristics.
    # profile, totalPowerProfile = EVCSP(data_mobility, horizon_length, 'CP')

    # if formulation == "milp":

    activationProfiles, powerProfiles, evcsp = evcsp_milp(
        nbr_vehicle, arrival, departure, power, energyRequired,
        energyMax, capacity_grid, horizon_length, time_step,
        solver_options
    )

    # elif formulation == "lp":
    #
    #     profile, totalPower, evcsp = evcsp_lp(
    #         nbr_vehicle=nbr_vehicle, arrival_idx=arrival, departure_idx=departure,
    #         power_nom=power, required_energy=energyRequired, energy_max=energyMax, capacity_grid=capacity_grid,
    #         horizon_length=horizon_length, time_step=time_step,
    #         solver_options=solver_options
    #     )

    return activationProfiles, powerProfiles, evcsp


if __name__ == '__main__':

    nVE = 100
    time_step = 900         # [Seconds]
    horizon_length = 96     # [Time Step]
    capacity = 200          # [kW] grid capacity
    n_sols = 250
    solver_options_1 = {"solver": cp.CLARABEL, "time_limit": 60.0, "verbose": False, "warm_start": False}
    solver_options_2 = {"solver": cp.SCIPY, "time_limit": 60.0, "verbose": False, "warm_start": False}

    # Data Preparation
    data_mobility = generate_demand_data(
        nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step
    )
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

    # f, ax = gantt_chart(
    #     n_task=nVE,
    #     duration=data_planning.chargingDuration.values, start_time=startTime,
    #     duration_available=data_planning.parkingDuration.values,
    #     start_time_available=data_planning.arrivalTime.values
    # )
    # plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    # plt.show()
