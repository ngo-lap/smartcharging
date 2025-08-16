import datetime
from typing import List
import numpy as np
import pandas as pd
import copy
from data.charging_demand import charging_demand_columns as required_columns


def generate_demand_data(
        nbr_vehicles: int, horizon_length: int = 24, time_step: int = 900,
        horizon_start: np.datetime64 = np.datetime64('today')
) -> pd.DataFrame:
    """
        Artificially generate mobility demand data

    :param nbr_vehicles: Number of vehicles
    :param horizon_length: [hour] the horizon length
    :param time_step: [second] time step of the planning problem
    :param horizon_start: the beginning of the horizon
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
    arrivalTime: np.array = np.random.randint(5 * 3600, 16 * 3600, nbr_vehicles)  # Arrival Time [Seconds]
    parkingDuration: np.array = np.random.randint(1 * 3600, 5 * 3600, nbr_vehicles)  # Parking duration [Seconds]
    departureTime: np.array = np.clip(a=arrivalTime + parkingDuration, a_min=0, a_max=23 * 3600)

    durations: np.array = 3600 * energyRequired / powerNom  # Charging Duration [seconds]
    durations = np.minimum(parkingDuration, durations)  # Limit charging duration to parking time

    data_generated: pd.DataFrame = pd.DataFrame(
        {
            'powerNom': powerNom, 'energyRequired': (durations / 3600) * powerNom,
            'energyMax': energyMax,
            'arrivalTime': horizon_start + np.timedelta64(1, 's') * arrivalTime,
            'departureTime': horizon_start + np.timedelta64(1, 's') * departureTime,
            'parkingDuration': parkingDuration / 3600,
            'chargingDuration': durations / 3600
        }, index=range(nbr_vehicles)
    )
    data_generated = data_generated.reset_index(names=["vehicle"])

    return data_generated


def prepare_planning_data(
        data_demand: pd.DataFrame, time_step: int = 900, horizon_start: np.datetime64 = np.datetime64('today'),
        arrival_column: str = "arrivalTime", departure_column: str = "departureTime"
) -> pd.DataFrame:

    """
        Return indices of the arrival and departure time.
        Index 0 begins at 0:00 AM:

    :param data_demand:
    :param time_step:
    :param arrival_column:
    :param departure_column:
    :param horizon_start:
    :return:
    """

    fields2convert = [arrival_column, departure_column]
    data_mobility_idx = copy.deepcopy(data_demand)

    # Convert to datetime64
    data_demand[arrival_column] = pd.to_datetime(data_demand[arrival_column])
    data_demand[departure_column] = pd.to_datetime(data_demand[departure_column])

    if all(pd.api.types.is_float_dtype(data_mobility_idx[c]) for c in fields2convert):
        data_mobility_idx.loc[:, fields2convert] = np.floor(
            data_demand.loc[:, fields2convert] * 3600 / time_step
        )
        data_mobility_idx[fields2convert] = data_mobility_idx[fields2convert].astype('int32')

    else:
        converted_time = indexing_arrival_departure_time(
            data_mobility_idx[[arrival_column, departure_column]],
            horizon_start=horizon_start
        )
        data_mobility_idx[fields2convert] = converted_time

    verify_planning_data(df_planning=data_mobility_idx)

    return data_mobility_idx


def indexing_arrival_departure_time(
        data: pd.DataFrame, time_step: int = 900, horizon_start: np.datetime64 | datetime.datetime = None
):

    """
    Convert arrival and departure time stamps to indices distance (1 index is 1 time_step) from horizon_start

    :param data: a dataframe containing arrival and departure time stamps.
        The first column is the arrival and the second column is the departure.
    :param time_step: time step in seconds
    :param horizon_start: timestamp of horizon start.
        If None is given, the beginning of the earliest arrival date is used, i.e. datetime.datetime(2025, 1, 27, 0, 0)

    :return: a DataFrame with arrival and departure integer indices,  the horizon_start is at 0

    """

    assert len(data.columns) == 2, "Arrival and Departure DataFrame must have 2 columns"

    if horizon_start is None:
        horizon_day = data.iloc[:, 0].dt.date.min()
        horizon_start = datetime.datetime(horizon_day.year, horizon_day.month, horizon_day.day, 0, 0, 0)

    arrival_horizon = (data.iloc[:, 0] - horizon_start) / np.timedelta64(time_step, 's')
    departure_horizon = (data.iloc[:, 1] - horizon_start) / np.timedelta64(time_step, 's')

    # Convert to integer distance
    arrival_horizon = arrival_horizon.astype('int')
    departure_horizon = departure_horizon.astype('int')

    return pd.concat([arrival_horizon, departure_horizon], axis=1)


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


def create_time_horizon(
        start: np.datetime64 = np.datetime64('today'),
        time_step: int | float = 900,
        horizon_length: int = 96
) -> np.ndarray:
    """
    Generate a time horizon.
    :param start: start time of the horizon
    :param time_step: time step in seconds
    :param horizon_length: horizon length, i.e. length of the output
    :return: time horizon in np.datetime64

    """
    horizon = start + np.timedelta64(time_step, 's') * np.linspace(0, horizon_length-1, num=horizon_length)
    return horizon


if __name__ == '__main__':
    data_mobility = generate_demand_data(nbr_vehicles=5, horizon_length=24, time_step=900)
    data_planning = prepare_planning_data(data_mobility, time_step=900)
    print(data_mobility)
    print(data_planning)
