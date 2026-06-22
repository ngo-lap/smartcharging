from typing import Dict
import numpy as np
import pandas as pd
import cvxpy as cp

_SIGNIFICANT_NUMBER_ = 2


def compute_energetic_kpi(
        power_profiles: np.array,
        power_grid: pd.DataFrame | float,
        planning_input: pd.DataFrame,
        time_step: int
) -> tuple[Dict[str, float], pd.DataFrame]:
    """

    :param power_profiles: [kW]
    :param power_grid: [kW]
    :param planning_input:
    :param time_step: [seconds]
    :return:
    """


    # Per vehicle KPI
    energy_kWh = (time_step / 3600) * power_profiles.sum(axis=0)
    peak_power_kW = power_profiles.max(axis=0)
    workload_pct = 100 * energy_kWh / planning_input["energyRequired"]
    df_per_vehicle = pd.DataFrame(
        data=[energy_kWh, peak_power_kW, workload_pct],
        index=["energy", "power", "workload"]
    ).T

    # Overall KPI
    kpi_station = dict()
    kpi_station["energykWh"] = round(energy_kWh.sum(), _SIGNIFICANT_NUMBER_)
    kpi_station["nbrVehicles"] = power_profiles.shape[-1]
    kpi_station["energyPlannedkWh"] = round(planning_input["energyRequired"].sum(), _SIGNIFICANT_NUMBER_)
    kpi_station["workloadPct"] = round(100 * kpi_station["energykWh"] / kpi_station["energyPlannedkWh"], 2)
    kpi_station["peakPowerkW"] = round(power_profiles.sum(axis=1).max(), 2)

    return kpi_station, df_per_vehicle


def compute_financial_kpi():
    return None


def compute_other_optim_kpi(
        data_planning: pd.DataFrame,
        horizon_length: int,
        evcsp: cp.Problem,
) -> pd.DataFrame:

    # Compute SOC (%) from SOE
    df_soc = pd.DataFrame(
        100 * evcsp.var_dict["SOE"].value / np.tile(data_planning.energyMax.values, (horizon_length, 1))
    ).round(1)

    return df_soc