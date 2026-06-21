import time
from typing import List
import cvxpy as cp
import numpy as np
from core.utility.logger.custom_loggers import setup_logger

logger = setup_logger(__name__)


# TODO: TOU


def evcsp_milp(
        nbr_vehicle: int, arrival_idx: List[int], departure_idx: List[int], power_nom: List[int],
        required_energy: List[int], capacity_nom: List[int], p_max_infra: float | List[float],
        horizon_length: int, time_step: int = 900, solver_options: dict = None, prices = None,
        efficiency_charging: float = 0.9
) -> tuple[np.ndarray, np.ndarray, cp.Problem]:
    """
    MILP version of EVCSP

    :param nbr_vehicle:
    :param arrival_idx:
    :param departure_idx:
    :param power_nom: nominal power of each vehicle [kW]
    :param capacity_nom: nominal capacity for each vehicle [kWh]
    :param required_energy: energy demand for each vehicle [kWh]
    :param p_max_infra: max power profile for the station [kW]
    :param horizon_length: horizon length [time steps]
    :param time_step: [seconds]
    :param solver_options:
    :param prices:
    :param efficiency_charging: charging efficiency (on the scale of 1, not 100%)
    :return:
    """

    if prices is None:
        prices = {"price_energy_buy": 0.13, "price_energy_sell": 0.13, "penalty_unsatisfied": 100}

    assert required_energy <= capacity_nom, "Required Energy must not exceed nom capacity"

    delta_t = time_step / 3600
    price_energy_buy = prices["price_energy_buy"]           # [currency/kWh]
    penalty_unsatisfied = prices["penalty_unsatisfied"]     # [currency/kWh] Penalty for unsatisfied energy

    # VARIABLE
    # --------------------------------
    # activation[t, v] = 1 means the vehicle v is charged at time t
    activation: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), boolean=True)

    # soe[t,v] is the state of energy vehicle v at time t
    soe: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), nonneg=True)
    soe_under: cp.Variable = cp.Variable(shape=nbr_vehicle, nonneg=True)  # Undercharged SOE
    soe_over: cp.Variable = cp.Variable(shape=nbr_vehicle, nonneg=True)  # Overcharged SOE

    # powerCharging[t,v] is the workload speed of vehicle v at time t
    power_charging: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), nonneg=True)

    # CONSTRAINTS
    # --------------------------------
    ctrs_arrival = []
    ctrs_departure = []
    ctrs_power = []
    ctrs_power_bounds = []
    ctrs_energy = []

    # Arrival & Departure
    for v in range(nbr_vehicle):
        ctrs_arrival.append(activation[0:arrival_idx[v], v] == 0)
        ctrs_departure.append(activation[departure_idx[v]::, v] == 0)

    # Power Bounds & Activation
    for v in range(nbr_vehicle):
        ctrs_power_bounds.append(power_charging[:, v] <= power_nom[v] * activation[:, v])

    # Charging Energy [t+1] = activation[t] * Charging Power [t] + Charging Energy[t]
    for v in range(nbr_vehicle):
        ctrs_energy.append(
            soe[1:-1, v]
            ==
            efficiency_charging * power_charging[0:-2, v] * delta_t + soe[0:-2, v]
        )

        # ctrs_energy.append(soe[-1, v] >= reductionRatio * required_energy[v])
        ctrs_energy.append(soe[0, :] == 0)  # TODO: SOE init
        ctrs_energy.append(soe[:, v] <= capacity_nom[v])

        # Unsatisfied SOE
        ctrs_energy.append(
            soe_under[v] - soe_over[v] == required_energy[v] - soe[departure_idx[v], v]
        )

    ctrs_energy.append(required_energy >= soe_under)
    ctrs_energy.append(soe_over <= required_energy)

    # Power Limit
    ctrs_power.append(cp.sum(power_charging, axis=1) <= p_max_infra)

    # Append all constraints
    ctrs_all = ctrs_arrival + ctrs_departure + ctrs_power_bounds + ctrs_energy + ctrs_power

    # OBJECTIVE
    # -------------------------------
    func_obj = cp.Minimize(
        penalty_unsatisfied * cp.sum(soe_under / capacity_nom)
        + price_energy_buy * delta_t * cp.sum(power_charging)
    )

    # Solve the problem
    prob = cp.Problem(objective=func_obj, constraints=ctrs_all)
    # prob.is_mixed_integer()

    start_time = time.time()
    # prob.solve(verbose=True, warm_start=False, solver=cp.SCIPY, scipy_options={'method': 'highs', 'time_limit': 30})
    prob.solve(verbose=True, warm_start=False, solver=solver_options["solver"])

    if prob.status == cp.OPTIMAL:
        print(f"Run Time:{time.time() - start_time} seconds")
        print(prob.status)
        print(prob.value)
        print(f"WORKLOAD COMPLETION: {np.round(sum(soe[-1, :].value) / sum(required_energy) * 100)} %")

        activation_profile = activation.value
        power_profile = power_charging.value
        sSol = [0]
    else:
        print('Problems solving !!!')
        # print(f"Schedule: {schedule.value}")
        # print(f"Energy: {energyCharging.value}")
        # print(f"Power: {powerCharging.value}")

    return activation_profile, power_profile, prob


def evcsp_lp(nbr_vehicle: int, arrival_idx: List[int], departure_idx: List[int], power_nom: List[int],
             required_energy: List[int], capacity_nom: List[float], soe_init: List[float], p_max_infra: float | List[float],
             horizon_length: int, time_step: int = 900, solver_options: dict = None, prices=None,
             efficiency_charging: float = 0.9) -> tuple[np.ndarray, np.ndarray, cp.Problem]:
    """
    LP version of EVCSP

    :param nbr_vehicle: number of vehicles / terminal considered in the horizon
    :param arrival_idx: index of arrival time
    :param departure_idx: index of departure time
    :param power_nom: nominal power of each vehicle [kW]
    :param capacity_nom: nominal capacity for each vehicle [kWh]
    :param soe_init: Initial SOE of vehicles at arrival [kWh]
    :param required_energy: energy demand for each vehicle [kWh]
    :param p_max_infra: max power profile for the station [kW]
    :param horizon_length: horizon length [time steps]
    :param time_step: [seconds]
    :param solver_options:
    :param prices: contain prices information for the optimization problem
    :param efficiency_charging: charging efficiency (on the scale of 1, not 100%)
    :return:
    """

    if prices is None:
        prices = {"price_energy_buy": 0.13, "price_energy_sell": 0.13, "penalty_unsatisfied": 100}

    verbose = solver_options["verbose"]
    warm_start = solver_options["warm_start"]
    solver = solver_options["solver"]
    other_options = {k: v for k, v in solver_options.items() if k not in ("solver", "verbose", "warm_start")}

    logger.info(f"LP Formulation with solver {solver}")

    # Additional Parameters
    delta_t = time_step / 3600
    price_energy_buy = prices["price_energy_buy"]           # [currency/kWh]
    penalty_unsatisfied = prices["penalty_unsatisfied"]     # [currency/kWh] Penalty for unsatisfied energy

    # VARIABLE
    # --------------------------------

    # soe[t,v] is the state of energy vehicle v at time t
    soe: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), nonneg=True, name="SOE")
    soe_under: cp.Variable = cp.Variable(shape=nbr_vehicle, nonneg=True, name="SOE Under")      # Undercharged SOE
    soe_over: cp.Variable = cp.Variable(shape=nbr_vehicle, nonneg=True, name="SOE Over")        # Overcharged SOE

    # powerCharging[t,v] is the charging power  of vehicle v at time t
    power_charging: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), nonneg=True)

    # CONSTRAINTS
    # --------------------------------
    ctrs_arrival = []
    ctrs_departure = []
    ctrs_power = []
    ctrs_power_bounds = []
    ctrs_energy = []

    for v in range(nbr_vehicle):

        # Arrival & Departure
        ctrs_arrival.append(power_charging[0:arrival_idx[v], v] == 0)
        ctrs_departure.append(power_charging[departure_idx[v]::, v] == 0)

        # Power Bounds
        ctrs_power_bounds.append(power_charging[:, v] <= power_nom[v])

        # Charging Energy [t+1] = Charging Power [t] + Charging Energy[t]
        ctrs_energy.append(
            soe[1:-1, v]
            ==
            efficiency_charging * power_charging[0:-2, v] * delta_t + soe[0:-2, v]
        )

        # Initial SOE
        ctrs_energy.append(soe[0:arrival_idx[v], v] == soe_init[v])

        # Bounds for SOE
        ctrs_energy.append(soe[:, v] <= capacity_nom[v])

        # Unsatisfied SOE
        ctrs_energy.append(
            soe_over[v] - soe_under[v] == (soe[departure_idx[v], v] - soe[arrival_idx[v], v]) - required_energy[v]
        )

    # Bounds f or SOE under and over
    ctrs_energy.append(required_energy >= soe_under)
    ctrs_energy.append(soe_over <= required_energy)

    # Power Limit.
    # TODO: soft constraint this
    # TODO: make it a Parameter object
    ctrs_power.append(cp.sum(power_charging, axis=1) <= p_max_infra)

    # Append all constraints
    ctrs_all = ctrs_arrival + ctrs_departure + ctrs_power_bounds + ctrs_energy + ctrs_power

    # -------------------------------
    # OBJECTIVE
    # -------------------------------
    # func_obj_service = cp.sum( cp.multiply(penalty_unsatisfied / np.array(capacity_nom), soe_under) )
    # func_obj_energy_cost = delta_t * cp.sum( cp.multiply(price_energy_buy, power_charging) )

    func_obj_service = penalty_unsatisfied * cp.sum(soe_under / capacity_nom)
    func_obj_energy_cost = price_energy_buy * delta_t * cp.sum(power_charging)
    func_obj = cp.Minimize( func_obj_service + func_obj_energy_cost)

    # Solve the problem
    prob = cp.Problem(objective=func_obj, constraints=ctrs_all)

    start_time = time.time()
    prob.solve(verbose=True, warm_start=False, solver=solver_options["solver"])

    if prob.status == cp.OPTIMAL or prob.status == cp.OPTIMAL_INACCURATE:
        logger.info(f"Solution found with status {prob.status}")
        logger.info(f"Measured Solving Time: {round(time.time() - start_time, 1)} seconds")
        activation_profile = power_charging.value > 0
        power_profile = power_charging.value

    else:
        logger.exception('Problem not solved properly !')
        activation_profile = np.zeros(shape=(horizon_length, nbr_vehicle), dtype=int)
        power_profile = np.zeros(shape=(horizon_length, nbr_vehicle), dtype=float)


    return activation_profile, power_profile, prob
