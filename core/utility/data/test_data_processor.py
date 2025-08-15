import datetime
import pandas as pd
import numpy as np
import pytest

from core.utility.data.data_processor import indexing_arrival_departure_time


@pytest.fixture
def df_sessions() -> pd.DataFrame:
    return pd.read_excel("sample_sessions.xlsx")


def test_indexing_arrival_departure_time(df_sessions):

    converted_time = indexing_arrival_departure_time(df_sessions[["session_start", "session_end"]])
    df_sessions[["arrivalTime", "departureTime"]] = converted_time

    assert len(converted_time) == len(df_sessions), \
        "converted time DataFrame must be of the same length as session data"
    assert all(converted_time > 0), "indexes must be positive"
    assert (df_sessions["arrivalTime"] <= df_sessions["departureTime"]).all(), \
        "Departure indexes must be greater than arrival indexes"

    for col in converted_time:
        assert pd.api.types.is_integer_dtype(converted_time[col]), "Column {col} is not integer".format(col=col)
