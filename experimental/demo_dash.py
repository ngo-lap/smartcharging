# Import packages
import numpy as np
from dash import Dash, html, dash_table, dcc
import pandas as pd
import cvxpy as cp
import plotly.express as px
import dash_bootstrap_components as dbc

from core.planner.day_ahead_planner import create_charging_plans
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data
import plotly.graph_objects as go

from core.utility.kpi.eval_performance import compute_energetic_kpi

# %% DATA PREPARATION
# Meta-parameters
nVE = 40
time_step = 900  # [Seconds]
horizon_length = 96  # [Time Step]
capacity = 200  # [kW] grid capacity
n_sols = 250
capacity_grid = np.array([100] * horizon_length)
capacity_grid[40:57] = 80
solver_options_1 = {"solver": cp.CLARABEL, "time_limit": 60.0, "verbose": False, "warm_start": False}
solver_options_2 = {"solver": cp.SCIPY, "time_limit": 60.0, "verbose": False, "warm_start": False}

data_planning_raw = generate_demand_data(nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step)
data_planning = prepare_planning_data(data_demand=data_planning_raw, time_step=time_step)
data_planning_displayed = data_planning[["powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"]]

# %% DAY-AHEAD PLANNING

_, powerProfiles, evcsp = create_charging_plans(
    data_planning, horizon_length=horizon_length, time_step=time_step,
    nbr_vehicle=nVE, capacity_grid=capacity_grid, n_sols=n_sols,
    formulation="milp", solver_options=solver_options_2
)

kpi_station, kpi_per_ev = compute_energetic_kpi(
    power_profiles=powerProfiles,
    power_grid=capacity,
    planning_input=data_planning,
    time_step=time_step
)

# %% Visualization
# Figure - Power Profiles
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(horizon_length)), y=powerProfiles.sum(axis=1), name="Total Charging Power (kW)"))
fig.add_trace(go.Scatter(x=list(range(horizon_length)), y=capacity_grid, name="Infras Capacity (kW)"))
fig.update_layout(
    title={"text": "Station Power Profiles"},
    xaxis={"title": {"text": "Time Step"}},
    yaxis={"title": {"text": "Power (kW)"}},
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
)

#  Fig - KPI
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
    grid={'rows': 2, 'columns': 1, 'pattern': "independent"}, title={"text": "Station KPIs"},
)

# %% DASHBOARD APP

app = Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN])
app.layout = dbc.Container(
    [
        dbc.Row(
                html.Div(
                    className='row', children='Charging Station Supervisor',
                    style={'textAlign': 'center', 'color': 'red', 'fontSize': 25}
                )
        ),
        dbc.Row(
            [
                dbc.Col(
                    dash_table.DataTable(
                        id="charging-demand-table", data=data_planning_displayed.to_dict('records'),
                        page_size=10, style_table={'overflowX': 'auto'}
                    )
                ),
                dbc.Col(dcc.Graph(figure=fig_kpi))
            ]
        ),
        dbc.Row(dcc.Graph(figure=fig))
    ],
    fluid=True
)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
