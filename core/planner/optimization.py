import time
from typing import List
import cvxpy as cp
import numpy as np
from core.utility.logger.custom_loggers import setup_logger

logger = setup_logger(__name__)


# TODO: TOU

def evcsp_milp(nbr_vehicle: int, arrival_idx: List[int], departure_idx: List[int], power_nom: List[int],
               required_energy: List[int], capacity_nom: List[int], p_max_infra: float | List[float],
               horizon_length: int, time_step: int = 900, solver_options: dict = None) -> \
        (np.array, np.array, cp.Problem):

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
    :return:
    """

    assert (required_energy <= capacity_nom, "Required Energy must not exceed nom capacity")

    deltaT = time_step / 3600
    effCharging = 0.9
    priceElec = 0.13  # €/kWh
    penaltyUnsatisfied = 100  # [€ / kWh] Penalty for unsatisfied energy

    # VARIABLE
    # --------------------------------
    # activation[t, v] = 1 means the vehicle v is charged at time t
    activation: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), boolean=True)

    # soe[t,v] is the state of energy vehicle v at time t
    soe: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), nonneg=True)
    soeUnder: cp.Variable = cp.Variable(shape=nbr_vehicle, nonneg=True)  # Undercharged SOE
    soeOver: cp.Variable = cp.Variable(shape=nbr_vehicle, nonneg=True)  # Overcharged SOE

    # powerCharging[t,v] is the workload speed of vehicle v at time t
    powerCharging: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), nonneg=True)

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
        ctrs_power_bounds.append(powerCharging[:, v] <= power_nom[v] * activation[:, v])

    # Charging Energy [t+1] = activation[t] * Charging Power [t] + Charging Energy[t]
    for v in range(nbr_vehicle):
        ctrs_energy.append(
            soe[1:-1, v]
            ==
            effCharging * powerCharging[0:-2, v] * deltaT + soe[0:-2, v]
        )

        # ctrs_energy.append(soe[-1, v] >= reductionRatio * required_energy[v])
        ctrs_energy.append(soe[0, :] == 0)  # TODO: SOE init
        ctrs_energy.append(soe[:, v] <= capacity_nom[v])

        # Unsatisfied SOE
        ctrs_energy.append(
            soeUnder[v] - soeOver[v] == required_energy[v] - soe[departure_idx[v], v]
        )

    ctrs_energy.append(required_energy >= soeUnder)
    ctrs_energy.append(soeOver <= required_energy)

    # Power Limit
    ctrs_power.append(cp.sum(powerCharging, axis=1) <= p_max_infra)

    # Append all constraints
    ctrs_all = ctrs_arrival + ctrs_departure + ctrs_power_bounds + ctrs_energy + ctrs_power

    # OBJECTIVE
    # -------------------------------
    func_obj = cp.Minimize(
        penaltyUnsatisfied * cp.sum(soeUnder / capacity_nom)
        + priceElec * deltaT * cp.sum(powerCharging)
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

        activationProfile = activation.value
        powerProfile = powerCharging.value
        sSol = [0]
    else:
        print('Problems solving !!!')
        # print(f"Schedule: {schedule.value}")
        # print(f"Energy: {energyCharging.value}")
        # print(f"Power: {powerCharging.value}")

    return activationProfile, powerProfile, prob


def evcsp_lp(
        nbr_vehicle: int, arrival_idx: List[int], departure_idx: List[int],
        power_nom: List[int], required_energy: List[int], energy_max: List[int],
        capacity_grid: float, horizon_length: int, time_step: int = 900,
        solver_options: dict = None
) -> (np.array, np.array, cp.Problem):
    """
    LP version of EVCSP

    :param solver_options:
    :param time_step:
    :param nbr_vehicle:
    :param arrival_idx:
    :param departure_idx:
    :param power_nom:
    :param energy_max:
    :param required_energy:
    :param capacity_grid:
    :param horizon_length:
    :return:
    """

    # Solver setup
    verbose = solver_options["verbose"]
    warm_start = solver_options["warm_start"]
    solver = solver_options["solver"]
    other_options = {k: v for k, v in solver_options.items() if k not in ("solver", "verbose", "warm_start")}

    logger.info(f"LP Formulation with solver {solver}")

    # Additional Parameters
    deltaT = time_step / 3600
    reductionRatio = cp.Parameter(nonneg=False, value=0.75)

    # VARIABLE
    # --------------------------------
    # energyCharging[t,v] is the accumulated workload of vehicle v at time t
    energyCharging: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), nonneg=True)

    # powerCharging[t,v] is the workload speed of vehicle v at time t
    powerCharging: cp.Variable = cp.Variable(shape=(horizon_length, nbr_vehicle), nonneg=True)

    # CONSTRAINTS
    # --------------------------------
    ctrs_arrival = []
    ctrs_departure = []
    ctrs_power = []
    ctrs_power_bounds = []
    ctrs_energy = []

    # Arrival & Departure
    for v in range(nbr_vehicle):
        ctrs_arrival.append(powerCharging[0:arrival_idx[v], v] == 0)
        ctrs_departure.append(powerCharging[departure_idx[v]::, v] == 0)

    # Power Bounds
    for v in range(nbr_vehicle):
        ctrs_power_bounds.append(powerCharging[:, v] <= power_nom[v])

    # Charging Energy [t+1] = schedule[t] * Charging Power [t] + Charging Energy[t]
    for v in range(nbr_vehicle):
        ctrs_energy.append(
            energyCharging[1:-1, v]
            ==
            powerCharging[0:-2, v] * deltaT + energyCharging[0:-2, v]
        )

        ctrs_energy.append(
            energyCharging[-1, v] >= reductionRatio * required_energy[v]
        )

        ctrs_energy.append(
            energyCharging[:, v] <= energy_max[v]
        )

        ctrs_energy.append(energyCharging[0, :] == 0)

    # Power Capacity Limit
    ctrs_power.append(cp.sum(powerCharging, axis=1) <= capacity_grid)

    # Append all constraints
    ctrs_all = ctrs_arrival + ctrs_departure + ctrs_power_bounds + ctrs_energy + ctrs_power

    # OBJECTIVE
    # -------------------------------
    func_obj = cp.Maximize(cp.sum(energyCharging))

    # Solve the problem
    prob = cp.Problem(objective=func_obj, constraints=ctrs_all)
    # prob.is_mixed_integer()

    start_time = time.time()
    prob.solve(verbose=verbose, warm_start=warm_start, solver=solver, **other_options)

    if prob.status == cp.OPTIMAL:
        logger.info("Optimal Solution found")
        logger.info(f"Measured Solving Time: {time.time() - start_time} seconds")

    elif prob.status == cp.INFEASIBLE:
        logger.warning("Infeasible Problem, reducing the required energy.")
        reductionRatio.value = 0.2
        prob.solve(verbose=verbose, warm_start=warm_start, solver=solver, **other_options)

        if prob.status == cp.OPTIMAL:
            logger.info(f"Optimal solution found after reducing the required energy.")
        else:
            logger.info(f"Problem is still infeasible after reducing the required energy.")
    else:

        logger.exception('Problem not solved properly !')

    logger.info(f"Optimal function value {prob.value}")
    logger.info(
        f"Workload Completion: {np.round(sum(energyCharging[-1, :].value) / sum(required_energy) * 100)} %"
    )

    # logger.info(f"Solver Stats: {prob.solver_stats}")

    profile = powerCharging.value
    consumptionProfile = np.sum(powerCharging.value, axis=1)

    return profile, consumptionProfile, prob
