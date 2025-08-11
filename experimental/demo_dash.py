# Import packages
import numpy as np
from dash import Dash, html, dash_table, dcc
import pandas as pd
import cvxpy as cp
import plotly.express as px

from core.planner.day_ahead_planner import create_charging_plans
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data
import plotly.graph_objects as go

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


# %% DAY-AHEAD PLANNING

_, powerProfiles, evcsp = create_charging_plans(
    data_planning, horizon_length=horizon_length, time_step=time_step,
    nbr_vehicle=nVE, capacity_grid=capacity_grid, n_sols=n_sols,
    formulation="milp", solver_options=solver_options_2
)

# %% Visualization
fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(horizon_length)), y=powerProfiles.sum(axis=1), name="Total Charging Power (kW)"))
fig.add_trace(go.Scatter(x=list(range(horizon_length)), y=capacity_grid, name="Infras Capacity (kW)"))
fig.update_layout(
    title={"text": "Station Power Profiles"},
    xaxis={"title": {"text": "Time Step"}},
    yaxis={"title": {"text": "Power (kW)"}}
)

# %% DASHBOARD APP
# Initialize the app
app = Dash()

# App layout
app.layout = [
    html.Div(children='Charging Demand Data'),
    dash_table.DataTable(data=data_planning_raw.to_dict('records'), page_size=10),
    dcc.Graph(figure=fig)
]

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
