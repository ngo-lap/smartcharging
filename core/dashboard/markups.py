from typing import Dict

from dash import Dash, html, dash_table, dcc
import pandas as pd
import plotly.graph_objects as go


def generate_table(dataframe: pd.DataFrame, id_tag: str):
    return dash_table.DataTable(
        id=id_tag,
        data=dataframe.to_dict('records'),
        page_size=8, style_table={'overflowX': 'auto'}
    )


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
