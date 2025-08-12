# Import packages
import numpy as np
from dash import Dash, html, dash_table, dcc, callback, Input, Output
import pandas as pd
import cvxpy as cp
import plotly.express as px
import dash_bootstrap_components as dbc

from core.dashboard.markups import generate_table, generate_fig_station_power, generate_fig_station_kpi, \
    generate_fig_heatmap_power
from core.planner.day_ahead_planner import create_charging_plans
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data
from core.utility.kpi.eval_performance import compute_energetic_kpi

# App initialization
app = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])

# %% DATA PREPARATION
# Meta-parameters
nVE = 40
time_step = 900  # [Seconds]
horizon_length = int(24 * 3600 / time_step)  # [Time Step]
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


@app.callback(
    [
        Output(component_id="fig-station-power", component_property="figure"),
        Output(component_id="fig-station-kpi", component_property="figure"),
        Output(component_id="fig-vehicles-powers", component_property="figure")
    ],
    [
        Input(component_id="charging-demand-table", component_property="data"),
        Input(component_id="pgrid-slider", component_property="value")
    ]
)
def run_planner(demand, pmax):
    demand_df = pd.DataFrame.from_records(demand)

    _, powerProfiles, evcsp = create_charging_plans(
        demand_df, horizon_length=horizon_length, time_step=time_step,
        nbr_vehicle=nVE, capacity_grid=pmax, n_sols=n_sols,
        formulation="milp", solver_options=solver_options_2
    )

    kpi_station, kpi_per_ev = compute_energetic_kpi(
        power_profiles=powerProfiles,
        power_grid=pmax,
        planning_input=demand_df,
        time_step=time_step
    )

    fig_power = generate_fig_station_power(
        x=list(range(horizon_length)),
        power_profile=powerProfiles.sum(axis=1),
        capacity_grid=pmax
    )

    fig_kpi = generate_fig_station_kpi(kpi_station=kpi_station)
    fig_vehicle_power = generate_fig_heatmap_power(power_profiles_vehicles=powerProfiles)

    return fig_power, fig_kpi, fig_vehicle_power


# %% Visualization
# Figure - Power Profiles
# fig = go.Figure()
# fig.add_trace(go.Scatter(x=list(range(horizon_length)), y=powerProfiles.sum(axis=1), name="Total Charging Power (kW)"))
# fig.add_trace(go.Scatter(x=list(range(horizon_length)), y=capacity_grid, name="Infras Capacity (kW)"))
# fig.update_layout(
#     xaxis={"title": {"text": "Time Step"}},
#     yaxis={"title": {"text": "Power (kW)"}},
#     legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
# )

#  Fig - KPI
# fig_kpi = go.Figure()
# fig_kpi.add_trace(
#     go.Indicator(
#         mode="number",
#         value=kpi_station["energykWh"],
#         title={'text': "Planned Charging Energy (kWh)"},
#         domain={'row': 0, 'column': 1}
#     )
# )
# fig_kpi.add_trace(
#     go.Indicator(
#         mode="number",
#         value=kpi_station["peakPowerkW"],
#         title={'text': "Peak Power (kW)"},
#         domain={'row': 1, 'column': 1}
#     )
# )
# fig_kpi.update_layout(
#     grid={'rows': 2, 'columns': 1, 'pattern': "independent"}, title={"text": "Station KPIs"}
# )

# %% DASHBOARD APP

app.layout = dbc.Container(
    [
        dbc.Row(
            html.H1("Charging Station Supervisor", className="bg-primary text-white p-1 text-center"),
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H5(children="Charging Demand"),
                        generate_table(dataframe=data_planning_displayed, id_tag="charging-demand-table")
                    ]
                ),
                dbc.Col(
                    [
                        # html.H4(children="Planned Station KPI", className="text-center"),
                        dcc.Graph(figure={}, id="fig-station-kpi")
                    ]
                )
            ]
        ),
        dbc.Row(
            [
                html.H4(children="Max Power (kW)"),
                dcc.Slider(id="pgrid-slider", min=50, max=400, value=100, step=20)
            ]
        ),
        dbc.Row(
            dcc.Tabs(
                [
                    dcc.Tab(dcc.Graph(figure={}, id="fig-station-power"), label="Station Powers"),
                    dcc.Tab(dcc.Graph(figure={}, id="fig-vehicles-powers"), label="Vehicles Powers")
                ]
            )
        )
    ],
    fluid=True
)

# Run the app
if __name__ == '__main__':
    # run_planner(pmax=capacity_grid)
    app.run(debug=True)
