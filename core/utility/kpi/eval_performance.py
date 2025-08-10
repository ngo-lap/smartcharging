from typing import Dict

import numpy as np
import pandas as pd


def compute_energetic_kpi(
        power_profiles: np.array,
        power_grid: pd.DataFrame | float,
        planning_input: pd.DataFrame,
        time_step: int
) -> (Dict[str, float], pd.DataFrame):
    """

    :param power_profiles: [kW]
    :param power_grid: [kW]
    :param planning_input:
    :param time_step: [seconds]
    :return:
    """

    # TODO: test

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
    kpi_station["workloadPct"] = 100 * energy_kWh.sum() / planning_input["energyRequired"].sum()
    kpi_station["energykWh"] = energy_kWh.sum()

    return kpi_station, df_per_vehicle


def compute_financial_kpi():
    return None
