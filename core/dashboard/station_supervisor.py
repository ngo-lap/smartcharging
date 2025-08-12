# Import packages
from typing import List, Dict
import numpy as np
from dash import Dash, html, dash_table, dcc, callback, Input, Output
import pandas as pd
import cvxpy as cp
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


@app.callback(
    [Output(component_id="table-charging-demand", component_property="data")],
    [Input(component_id="button-charging-demand", component_property="n_clicks")],
)
def predict_charging_demand(n_clicks: int = 1) -> List[List[Dict]]:
    """
    Predict Charging demand data
    Notice that returned data for DataTable has to be a list of length 1
    :param n_clicks:
    :return:
    """
    demand_raw = generate_demand_data(nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step)
    selected_columns = ["powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"]
    return [demand_raw[selected_columns].to_dict("records")]


charging_demand = generate_demand_data(nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step)
charging_demand_evcsp = prepare_planning_data(data_demand=charging_demand, time_step=time_step)
charging_demand_displayed = charging_demand[["powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"]]


# %% DAY-AHEAD PLANNING


@app.callback(
    [
        Output(component_id="fig-station-power", component_property="figure"),
        Output(component_id="fig-station-kpi", component_property="figure"),
        Output(component_id="fig-vehicles-powers", component_property="figure")
    ],
    [
        Input(component_id="table-charging-demand", component_property="data"),
        Input(component_id="slider-pgrid", component_property="value")
    ]
)
def run_planner(demand: List[Dict], pmax: List | np.array):

    demand_evcsp = prepare_planning_data(data_demand=pd.DataFrame.from_records(demand), time_step=time_step)
    demand_df = pd.DataFrame.from_records(demand_evcsp)

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


# %% DASHBOARD APP

app.layout = dbc.Container(
    [
        dbc.Row([html.H4("Charging Station Supervisor", className="bg-primary text-white p-1 text-center")]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Button(children="Predict Charging Demand", n_clicks=0, id="button-charging-demand"),
                        generate_table(data=charging_demand_displayed.to_dict("records"), id_tag="table-charging-demand")
                    ]
                ),
                dbc.Col(
                    [
                        # html.H4(children="Planned Station KPI", className="text-center"),
                        dcc.Graph(figure={}, id="fig-station-kpi")
                    ]
                )
            ],
        ),
        dbc.Row(
            [
                html.H4(children="Max Power (kW)"),
                dcc.Slider(id="slider-pgrid", min=50, max=400, value=100, step=20)
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

# %% Run the app
if __name__ == '__main__':
    # run_planner(pmax=capacity_grid)
    app.run(debug=True)
