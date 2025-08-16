from typing import List, Dict

from dash import html, dcc
import dash_bootstrap_components as dbc
from core.dashboard.markups import generate_table

button_config = {"outline": True, "color": "primary", "className": "me-1", "n_clicks": 0}


def create_station_layout(charging_demand: List[Dict]) -> dbc.Container:

    components = [
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
                            generate_table(data=charging_demand, id_tag="table-charging-demand"),
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
        ]

    # Wrap layout components around a spinner
    station_layout = dbc.Container(
        dcc.Loading(
            components,
            overlay_style={"visibility": "visible", "opacity": .5, "backgroundColor": "white"},
            type="circle",
            target_components={
                "table-charging-plans": ["derived_virtual_data"],
                "table-charging-demand": ["data", "derived_virtual_data"]
            }, delay_hide=1000., delay_show=1000.,
        )
        , fluid=True
    )

    return station_layout
