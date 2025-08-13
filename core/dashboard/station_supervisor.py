"""
Demo for a simple station supervisor. This should not be the final application
"""
import base64
import io
# Import packages
from typing import List, Dict
import numpy as np
from dash import Dash, html, dash_table, dcc, callback, Input, Output, State
import pandas as pd
import cvxpy as cp
import dash_bootstrap_components as dbc
from select import error

from core.dashboard.markups import generate_table, generate_fig_station_power, generate_fig_station_kpi, \
    generate_fig_heatmap_power
from core.planner.day_ahead_planner import create_charging_plans
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data
from core.utility.kpi.eval_performance import compute_energetic_kpi
import plotly.graph_objects as go

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


# %% Callback Demand Predictor


@app.callback(
    [Output(component_id="table-charging-demand", component_property="data")],
    [Input(component_id="button-charging-demand", component_property="n_clicks")],
    prevent_initial_call=False
)
def predict_charging_demand(n_clicks: int = 1) -> List[List[Dict]]:
    """
    Predict Charging demand data
    Notice that returned data for DataTable has to be a list of length 1
    :param n_clicks:
    :return:
    """
    demand_raw = generate_demand_data(nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step)
    demand_raw = demand_raw.reset_index(names=["vehicle"])
    selected_columns = ["vehicle", "powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"]
    return [demand_raw[selected_columns].to_dict("records")]


charging_demand = generate_demand_data(nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step)
charging_demand_evcsp = prepare_planning_data(data_demand=charging_demand, time_step=time_step)
charging_demand_displayed = charging_demand[["powerNom", "energyRequired", "energyMax", "arrivalTime", "departureTime"]]
charging_demand_displayed = charging_demand_displayed.reset_index(names=["vehicle"])

# %% Callback - DAY-AHEAD PLANNING


@app.callback(
    [
        Output(component_id="fig-station-power", component_property="figure"),
        Output(component_id="fig-station-kpi", component_property="figure"),
        Output(component_id="fig-vehicles-powers", component_property="figure"),
        Output(component_id="table-charging-plans", component_property="derived_virtual_data")
    ],
    [
        Input(component_id="table-charging-demand", component_property="derived_virtual_data"),
        Input(component_id="slider-pgrid", component_property="value")
    ]
)
def run_planner(demand: List[Dict], pmax: List | np.array) -> (go.Figure, go.Figure, go.Figure, List[Dict]):

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

    return fig_power, fig_kpi, fig_vehicle_power, pd.DataFrame(powerProfiles).to_dict("records")


# %% Callbacks - Download


@app.callback(
    [Output(component_id="component-download-charging-demand", component_property="data")],
    [Input(component_id="button-download-charging-demand", component_property="n_clicks")],
    State(component_id="table-charging-demand", component_property="derived_virtual_data"),
    prevent_initial_call=True
)
def download_charging_demand(_, data: Dict) -> List[Dict]:
    df = pd.DataFrame.from_records(data)
    return [dcc.send_data_frame(df.to_excel, filename="charging_demand_forecast.xlsx")]


@app.callback(
    [Output(component_id="component-download-charging-plans", component_property="data")],
    [Input(component_id="button-download-charging-plans", component_property="n_clicks")],
    State(component_id="table-charging-plans", component_property="derived_virtual_data"),
    prevent_initial_call=True
)
def download_charging_plans(_, data: Dict) -> List[Dict]:
    df = pd.DataFrame.from_records(data)
    return [dcc.send_data_frame(df.to_excel, filename="charging_plans.xlsx")]

# %% Callback - Upload Charging Forecast


@app.callback(
    [Output(component_id="table-charging-demand", component_property="data", allow_duplicate=True)],
    [Input('component-upload-charging-demand', 'contents')],
    State('component-upload-charging-demand', 'filename'),
    prevent_initial_call=True
)
def upload_demand(raw_demand: str, filename) -> List[List[Dict]] | dbc.Alert:

    content_type, content_string = raw_demand.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return dbc.Alert("Invalid file extension", color="danger")

        return [df.to_dict('records')]

    except Exception as e:
        print(e)
        return dbc.Alert("Problem Loading Demand File", color="danger")


# %% DASHBOARD APP

button_config = {"outline": True, "color": "primary", "className": "me-1", "n_clicks": 0}

app.layout = dbc.Container(
    [
        dbc.Row([html.H2("Charging Station Day-Ahead Planning", className="bg-primary text-white p-1 text-center")]),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Upload(
                            id="component-upload-charging-demand",
                            children=dbc.Button(
                                children="Upload Demand", id="button-upload-charging-demand", **button_config
                            )
                        ),
                        dbc.Button(children="Predict Demand", id="button-charging-demand", **button_config),
                        html.Hr(),
                        generate_table(data=charging_demand_displayed.to_dict("records"),
                                       id_tag="table-charging-demand"),
                        dbc.Button(children="Download Demand", id="button-download-charging-demand", **button_config),
                        dcc.Download(id="component-download-charging-demand"),
                        dbc.Button("Download Charging Plans", id="button-download-charging-plans", **button_config),
                        dcc.Download(id="component-download-charging-plans"),
                        html.Hr(),
                    ],
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
                html.Hr(),
                html.H4(children="Max Power (kW)"),
                dcc.Slider(id="slider-pgrid", min=50, max=400, value=100, step=20),
                html.Hr()
            ]
        ),
        dbc.Row(
            [
                dcc.Tabs(
                    [
                        dcc.Tab(dcc.Graph(figure={}, id="fig-station-power"), label="Station Powers"),
                        dcc.Tab(dcc.Graph(figure={}, id="fig-vehicles-powers"), label="Vehicles Powers")
                    ]
                )
            ]
        ),
        dbc.Row(generate_table(data=[], id_tag="table-charging-plans"))
    ],
    fluid=True
)


# %% Run the app
if __name__ == '__main__':
    app.run(debug=True)
