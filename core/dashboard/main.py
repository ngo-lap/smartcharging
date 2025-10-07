"""
Demo for a simple station supervisor. This should not be the final application
"""
import base64
import io
from typing import List, Dict
import numpy as np
from dash import Dash, dcc, Input, Output, State
import pandas as pd
import cvxpy as cp
import dash_bootstrap_components as dbc
from core.dashboard.markups import generate_fig_station_power, generate_fig_station_kpi, \
    generate_fig_heatmap_power
from core.dashboard.pages.layouts import create_station_layout
from core.api.schemas.cpo import Station, PlanningParameters
from core.planner.day_ahead_planner import create_charging_plans
from core.utility.data.data_processor import generate_demand_data, prepare_planning_data, create_time_horizon
from core.utility.kpi.eval_performance import compute_energetic_kpi
import plotly.graph_objects as go
from core.utility.data.charging_demand import charging_demand_columns as required_columns

# TODO: move schemas out of API module 

# App initialization
app = Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])

# %% DATA PREPARATION - STATION OBJECT CREATION

station: Station = Station(
    nbr_terminals=30,
    transformer_capacity=100,
    planning_parameters=PlanningParameters(
        nbr_vehicles=10, time_step=900, horizon_length=96, pmax_infrastructure=100, creation_date=""
    )
)

# Solver options: for LP formulation, CLARABEL performs much better in terms of time than SCIPY (HiGHs)
solver_options = {"solver": cp.CLARABEL, "time_limit": 60.0, "verbose": False, "warm_start": False}
# solver_options = {"solver": cp.SCIPY, "time_limit": 60.0, "verbose": False, "warm_start": False}

# Charging demand
charging_demand = generate_demand_data(
    nbr_vehicles=station.nbr_terminals,
    horizon_length=station.planning_parameters.horizon_length,
    time_step=station.planning_parameters.time_step
)

charging_demand_evcsp = prepare_planning_data(
    data_demand=charging_demand, time_step=station.planning_parameters.time_step
)
charging_demand_displayed = charging_demand[required_columns]

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
    demand_raw = generate_demand_data(
        nbr_vehicles=station.nbr_terminals,
        horizon_length=station.planning_parameters.horizon_length,
        time_step=station.planning_parameters.time_step
    )
    return [demand_raw[required_columns].to_dict("records")]


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

    demand_df = prepare_planning_data(
        data_demand=pd.DataFrame.from_records(demand),
        time_step=station.planning_parameters.time_step,
        horizon_start=np.datetime64("today")
    )

    nbr_vehicles = len(demand_df)

    _, powerProfiles, evcsp = create_charging_plans(
        demand_df,
        horizon_length=station.planning_parameters.horizon_length, time_step=station.planning_parameters.time_step,
        nbr_vehicle=nbr_vehicles, capacity_grid=pmax, n_sols=10,
        formulation="lp", solver_options=solver_options
    )

    kpi_station, kpi_per_ev = compute_energetic_kpi(
        power_profiles=powerProfiles,
        power_grid=pmax,
        planning_input=demand_df,
        time_step=station.planning_parameters.time_step
    )

    horizon_start = np.datetime64('today')
    horizon_datetime = create_time_horizon(
        start=horizon_start, time_step=station.planning_parameters.time_step,
        horizon_length=station.planning_parameters.horizon_length
    )

    fig_power = generate_fig_station_power(
        x=horizon_datetime,
        power_profile=powerProfiles.sum(axis=1),
        capacity_grid=pmax
    )

    fig_kpi = generate_fig_station_kpi(station=station, kpi_station=kpi_station)
    fig_vehicle_power = generate_fig_heatmap_power(horizon_datetime=horizon_datetime, power_profiles_vehicles=powerProfiles)

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
            # Assume that the user uploaded an Excel file
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return dbc.Alert("Invalid file extension", color="danger")

        return [df.to_dict('records')]

    except Exception as e:
        print(e)
        return dbc.Alert("Problem Loading Demand File", color="danger")


# %% DASHBOARD APP

app.layout = create_station_layout(charging_demand=charging_demand_displayed.to_dict("records"))

# %% Run the app
if __name__ == '__main__':
    # When running in Docker, you need to bind to 0.0.0.0 instead of 127.0.0.1 
    # so it’s accessible outside the container.
    app.run(debug=True, host="0.0.0.0", port=8050)
