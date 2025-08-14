import pandas as pd

# _charging_demand = ["powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"]


def convert_chargepoint_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
        Converts data columns from chargepoint to required columns.
        TODO: remove this from GitRepo
    :param df_raw:
    :return: df_converted: dataframe with converted columns
    """

    # Rename columns
    name_column = {
        "session_start": "arrival", "session_end": "departure",
        "energy_kwh": "energyRequired", "peak_power_kW": "powerNom",
        "capacity_nom_kWh": "energyMax"
    }

    df_converted = df_raw.rename(columns=name_column)

    return df_converted


def convert_acn_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    return None
