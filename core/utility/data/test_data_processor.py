import datetime
import pandas as pd
import numpy as np
import pytest
from core.utility.data.data_processor import indexing_arrival_departure_time, create_time_horizon


@pytest.fixture
def df_sessions() -> pd.DataFrame:
    return pd.read_excel("sample_sessions.xlsx")


def test_indexing_arrival_departure_time(df_sessions):

    converted_time = indexing_arrival_departure_time(
        data=df_sessions[["session_start", "session_end"]], time_step=900, horizon_start=np.datetime64("today")
    )

    df_sessions[["arrivalTime", "departureTime"]] = converted_time

    assert len(converted_time) == len(df_sessions), \
        "converted time DataFrame must be of the same length as session data"
    assert all(converted_time > 0), "indexes must be positive"
    assert (df_sessions["arrivalTime"] <= df_sessions["departureTime"]).all(), \
        "Departure indexes must be greater than arrival indexes"

    for col in converted_time:
        assert pd.api.types.is_integer_dtype(converted_time[col]), "Column {col} is not integer".format(col=col)


def test_create_time_horizon():

    time_step, horizon_length = 900, 5
    start_1 = np.datetime64("2025-02-01 10:00")

    horizon = create_time_horizon(start=np.datetime64("today"), time_step=time_step, horizon_length=horizon_length)
    horizon_1 = create_time_horizon(start=start_1, time_step=time_step, horizon_length=horizon_length)

    assert isinstance(horizon, np.ndarray), "horizon must be a list"
    assert isinstance(horizon[0], np.datetime64), "horizon is of type numpy.datetime64"
    assert len(horizon) == horizon_length, "horizon is of length {length}".format(length=len(horizon))
    assert (np.diff(horizon) == time_step).all(), f"Points in horizon not separated by {time_step} seconds"

    assert horizon_1[0] == start_1, f"Start time is not {start_1}"
    assert (np.diff(horizon_1) == time_step).all(), f"Points in horizon not separated by {time_step} seconds"
