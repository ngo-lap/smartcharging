from typing import Dict, List

import numpy as np
from dash import Dash, html, dash_table, dcc
from dash.dash_table.Format import Format, Scheme
import pandas as pd
import plotly.graph_objects as go


def generate_table(data: List[Dict], id_tag: str) -> dash_table.DataTable:
    """
    Format and Generate DataTable
    :param data: raw data, should come from the .to_dict("records") method of a pd.DataFrame
    :param id_tag: id for the table
    :return:
    """
    # Formating Data Table
    df = pd.DataFrame.from_records(data)
    columns = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            columns.append({
                "name": col,
                "id": col,
                "type": "numeric",
                "format": Format(precision=1, scheme=Scheme.fixed).group(True)  # 1,234.567 style
            })
        else:
            columns.append({"name": col, "id": col, "type": "text"})

    # Creating formated DataTable
    formated_table = dash_table.DataTable(
        id=id_tag,
        data=data,
        page_size=8, style_table={'overflowX': 'auto'},
        style_as_list_view=True,
        columns=columns,
        style_cell={'textAlign': 'right'}
    )
    return formated_table


def generate_fig_station_power(x, power_profile, capacity_grid) -> go.Figure:
    """
        Return Figure of Station Power
    :param x:
    :param power_profile:
    :param capacity_grid:
    :return:
    """

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=x, y=power_profile, name="Total Power"))

    if hasattr(capacity_grid, "__len__"):
        fig.add_trace(go.Scatter(x=x, y=capacity_grid, name="Infrastructure Capacity"))
    else:
        fig.add_hline(y=capacity_grid, line_dash="dash", line_color="red", name="Infrastructure Capacity")

    fig.update_layout(
        xaxis={"title": {"text": "Time Step"}},
        yaxis={"title": {"text": "Power (kW)"}},
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )
    return fig


def generate_fig_station_kpi(kpi_station: Dict[str, float]) -> go.Figure:
    """
        Return Figure of Station KPIs
    :param kpi_station:
    :return:
    """
    fig_kpi = go.Figure()
    fig_kpi.add_trace(
        go.Indicator(
            mode="number",
            value=kpi_station["energykWh"],
            title={'text': "Planned Charging Energy (kWh)"},
            domain={'row': 0, 'column': 1}
        )
    )
    fig_kpi.add_trace(
        go.Indicator(
            mode="number",
            value=kpi_station["peakPowerkW"],
            title={'text': "Peak Power (kW)"},
            domain={'row': 1, 'column': 1}
        )
    )
    fig_kpi.update_layout(
        grid={'rows': 2, 'columns': 1, 'pattern': "independent"}, title={"text": "Station KPIs"}
    )

    return fig_kpi


def generate_fig_heatmap_power(power_profiles_vehicles: np.array) -> go.Figure:

    nbr_vehicles = power_profiles_vehicles.shape[1]
    nbr_timestep = power_profiles_vehicles.shape[0]

    fig = go.Figure(
        go.Heatmap(
            z=power_profiles_vehicles.T,
            y=[str(v) for v in range(nbr_vehicles)],
            x=[str(t) for t in range(nbr_timestep)],
            hovertemplate="Vehicle: %{y}<br>"
                          "Time Step: %{x}<br>"
                          "Power: %{z:.1f} (kW) <br>"
                          "<extra></extra>",
            colorscale='gnbu'
        )
    )
    fig.update_layout(
        # title={"text": "Vehicle Charging Powers"},
        yaxis={"title": {"text": "Vehicle"}},
        xaxis={"title": {"text": "Time Step"}},
    )

    return fig
