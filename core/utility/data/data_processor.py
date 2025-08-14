from typing import List
import numpy as np
import pandas as pd
import copy
from data.charging_demand import charging_demand_columns as required_columns


def generate_demand_data(
        nbr_vehicles: int, horizon_length: int = 24, time_step: int = 900
) -> pd.DataFrame:
    """
        Artificially generate mobility demand data

    :param nbr_vehicles: Number of vehicles
    :param horizon_length: [hour] the horizon length
    :param time_step: [second] time step of the planning problem
    :return:
    """

    # Data
    # --------------------------------
    powerNomSet: List[int] = [6, 7, 11, 22]  # kW
    capacitykWh: List[int] = [30, 52, 88, 100]  # kWh
    deltaT: int = int(3600 / time_step)  # 3600 / timestep
    powerNom: np.array = np.random.choice(powerNomSet, nbr_vehicles)    # Nominal Charging Power [kW]
    energyMax: np.array = np.random.choice(capacitykWh, nbr_vehicles)
    energyRequired: np.array = np.random.randint(5, 80, nbr_vehicles)   # Total charging energy [kWh]

    # Time Data [Seconds from 00:00]
    arrivalTime: np.array = np.random.randint(6 * 3600, 12 * 3600, nbr_vehicles)  # Arrival Time [Seconds]
    parkingDuration: np.array = np.random.randint(1 * 3600, 5 * 3600, nbr_vehicles)  # Parking duration [Seconds]
    departureTime: np.array = arrivalTime + parkingDuration

    durations: np.array = 3600 * energyRequired / powerNom  # Charging Duration [seconds]
    durations = np.minimum(parkingDuration, durations)  # Limit charging duration to parking time

    data_generated: pd.DataFrame = pd.DataFrame(
        {
            'powerNom': powerNom, 'energyRequired': (durations / 3600) * powerNom,
            'energyMax': energyMax,
            'arrivalTime': arrivalTime / 3600, 'departureTime': departureTime / 3600,
            'parkingDuration': parkingDuration / 3600,
            'chargingDuration': durations / 3600
        }, index=range(nbr_vehicles)
    )
    data_generated = data_generated.reset_index(names=["vehicle"])

    return data_generated


def prepare_planning_data(data_demand: pd.DataFrame, time_step: int = 900) -> pd.DataFrame:

    """
        Return indices of the arrival and departure time.
        Index 0 begins at 0:00 AM

    :param data_demand:
    :param time_step:
    :return:
    """

    fields2convert = ["arrivalTime", "departureTime"]       # , "parkingDuration", "chargingDuration"
    data_mobility_idx = copy.deepcopy(data_demand)
    data_mobility_idx.loc[:, fields2convert] = np.floor(
        data_demand.loc[:, fields2convert] * 3600 / time_step
    )
    data_mobility_idx[fields2convert] = data_mobility_idx[fields2convert].astype('int32')

    verify_planning_data(df_planning=data_mobility_idx)

    return data_mobility_idx


def verify_planning_data(df_planning: pd.DataFrame) -> None:
    """
        Check if planning data is correct: with proper field names and proper values.

    :param df_planning: Planning dataframe
    :return:

    """

    # Required Column Names
    # _required_field_names = ["powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"
    # Check column names
    assert (
        set(required_columns).issubset(df_planning.columns),
        f"Missing columns names {set(required_columns).difference(df_planning.columns)}"
    )

    # Check value types


if __name__ == '__main__':
    data_mobility = generate_demand_data(nbr_vehicles=5, horizon_length=24, time_step=900)
    data_planning = prepare_planning_data(data_mobility, time_step=900)
    print(data_mobility)
    print(data_planning)
