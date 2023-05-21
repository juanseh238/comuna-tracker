from dash import dcc, html, Input, Output
import dash
import dash_bootstrap_components as dbc
import os

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import plotly.express as px
import simplejson as json

# Load data

DATA = {
    "radios_censales": {
        "delitos": gpd.read_file(
            "data/final/data_criminalidad.geojson", driver="GeoJSON"
        ),
        "comisarias": gpd.read_file("data/final/comisarias.geojson", driver="GeoJSON"),
        "calidad_de_vida": gpd.read_file(
            "data/final/indicadores_cultura.geojson", driver="GeoJSON"
        ),
    },
    "comunas": {
        "violencia_de_genero": gpd.read_file(
            "data/final/violencia-de-genero.geojson", driver="GeoJSON"
        ),
        "basura": gpd.read_file(
            "data/final/basura_cumplimiento_med_nivel.geojson", driver="GeoJSON"
        ),
    },
}


with open("config.json", "r") as f:
    CONFIG = json.load(f)
    FEATURE_CONFIG = CONFIG["FEATURES"]
    SETTINGS_CONFIG = CONFIG["SETTINGS"]

DEFAULT_SCOPE = "comunas"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Parse the availble sources from the features
SOURCES = list(set([FEATURE_CONFIG[feature]["source"] for feature in FEATURE_CONFIG]))

## Description box
## add feature description
description_box = html.Div(
    [
        html.H3(FEATURE_CONFIG["score_robo"]["name"], id="feature-name"),
        html.P(FEATURE_CONFIG["score_robo"]["description"], id="feature-description"),
    ],
    id="description-box",
    style={"margin-top": "25px", "margin-bottom": "25px"},
)

## Scope Radio button
## use a radio button to select the scope of the plots: comunas or radios censales
scope_radio = html.Div(
    [
        html.H3(
            "Nivel",
            style={
                "margin-right": "10px",
                "text-align": "center",
                "font-size": "20px",
            },
        ),
        dcc.RadioItems(
            id="scope-radio",
            options=[
                {"label": "Comunas", "value": "comunas"},
                {"label": "Radios Censales", "value": "radios_censales"},
            ],
            value=DEFAULT_SCOPE,
            labelStyle={
                "font-size": "20px",
            },
            style={
                "display": "flex",
                "flex-direction": "row",
                "justify-content": "space-between",
                "align-items": "center",
                "gap": "30px",
            },
        ),
    ],
    style={
        "display": "flex",
        "flex-direction": "row",
        "align-items": "space-between",
        "justify-content": "center",
        "gap": "30px",
    },
)


# Make a custom div with a box holding description of the plot, a slider for reducing opacity and
# a dropdown to select the variable to plot
control_box = html.Div(
    [
        html.H2("Indicadores de Nivel de Servicio en CABA"),
        html.Div(
            scope_radio,
            style={
                "margin-bottom": "25px",
                "align-items": "center",
                "justify-content": "center",
                "display": "flex",
                "flex-direction": "row",
                "fontsize": "40px",
            },
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Opacidad"),
                        html.P("Manejá la opacidad del mapa con el slider: "),
                        dcc.Slider(
                            id="opacity-slider",
                            min=0,
                            max=1,
                            step=0.1,
                            value=0.5,
                            marks={0: "0", 1: "1"},
                            tooltip={"always_visible": True, "placement": "bottom"},
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.H3("Indicador"),
                        html.P(
                            "1. Seleccioná la dimensión de interés:",
                            style={"margin-top": "15px"},
                        ),
                        dcc.Dropdown(
                            id="source-dropdown",
                            clearable=False,
                            # Get all sources for the given scope
                            options=[
                                {
                                    "label": source.capitalize().replace("_", " "),
                                    "value": source,
                                }
                                for source in SOURCES
                            ],
                            placeholder="Seleccioná una dimensión",
                        ),
                        html.P(
                            "2. Seleccioná el indicador a graficar:",
                            style={"margin-top": "15px"},
                        ),
                        dcc.Dropdown(
                            id="feature-dropdown",
                            clearable=False,
                            # add a default text hinting at selecting a radio item first
                            placeholder="Seleccioná un indicador",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flex-direction": "column",
                        "justify-content": "space-between",
                        "gap": "5px",
                        "width": "60%",
                    },
                ),
            ],
            style={
                "display": "flex",
                "flex-direction": "row",
                "justify-content": "space-around",
            },
        ),
        description_box,
    ],
    # add a light background color and some padding to the box
    style={
        "background-color": "lightgrey",
        "padding": "10px",
        "padding-left": "20px",
        "padding-right": "20px",
        "border-radius": "5px",
    },
)


app.layout = html.Div(
    [
        control_box,
        html.Div(id="graph-container"),
    ],
    style={"margin": "auto", "padding": "10px"},
    id="main-container",
)


## Callbacks
# update dropdown options based on radio button selection
@app.callback(
    Output("source-dropdown", "options"),
    [Input("scope-radio", "value")],
)
def update_source_dropdown(scope_radio_value):
    """
    Update dropdown options bsaed on radio button selection.
    The radio button selection value matches the 'scope' field in the FEATURES config dict.
    """
    scope = SETTINGS_CONFIG[scope_radio_value]["scope"]
    SOURCES = list(
        set(
            [
                FEATURE_CONFIG[feature]["source"]
                for feature in FEATURE_CONFIG
                if scope in FEATURE_CONFIG[feature]["scope"]
            ]
        )
    )
    options = [
        {"label": source.capitalize().replace("_", " "), "value": source}
        for source in SOURCES
    ]
    return options


@app.callback(
    Output("feature-dropdown", "options"),
    [Input("source-dropdown", "value")],
)
def update_feature_dropdpwn(source_dropdown_value):
    """
    Update dropdown options based on radio button selection.
    The radio button selection value matches the 'scope' field in the FEATURES config dict.
    """
    if not source_dropdown_value:
        return []
    options = [
        {
            "label": FEATURE_CONFIG[feature]["name"],
            "value": feature,
        }
        for feature in FEATURE_CONFIG
        if source_dropdown_value in FEATURE_CONFIG[feature]["source"]
    ]
    return options


# update plot according to control box settings
@app.callback(
    [
        Output("graph-container", "style"),
        Output("graph-container", "children"),
        Output("description-box", "children"),
    ],
    [
        Input("opacity-slider", "value"),
        Input("source-dropdown", "value"),
        Input("feature-dropdown", "value"),
        Input("scope-radio", "value"),
    ],
)
def update_plot(
    slider_value, source_dropdown_value, feature_dropdown_value, scope_radio_value
):
    # hide graph if no feature is selected
    if not feature_dropdown_value:
        hidden_graph_style = {"display": "none"}
        return hidden_graph_style, None, None

    # hide graph if selected feature is not available for selected scope
    if scope_radio_value not in FEATURE_CONFIG[feature_dropdown_value]["scope"]:
        hidden_graph_style = {"display": "none"}
        return hidden_graph_style, None, None

    data = DATA[scope_radio_value][source_dropdown_value]
    # hide graph if the selected feature is not present in the dataset
    if feature_dropdown_value not in data.columns:
        hidden_graph_style = {"display": "none"}
        return hidden_graph_style, None, None

    location_field = SETTINGS_CONFIG[scope_radio_value]["location_field"]

    if FEATURE_CONFIG[feature_dropdown_value]["type"] == "continuous":
        colorbar_settings = FEATURE_CONFIG[feature_dropdown_value]["colorbar_settings"]
        range_color = (FEATURE_CONFIG[feature_dropdown_value]["range_color_min"], FEATURE_CONFIG[feature_dropdown_value]["range_color_max"])
        tickformat=colorbar_settings["tickformat"] if "tickformat" in colorbar_settings else ".2f"
        hovertemplate = f"<b>%{{customdata[0]}}</b><br><br>{FEATURE_CONFIG[feature_dropdown_value]['name']}: %{{z:{tickformat}}}<br><br>"
        # draw a new figure when dropdown changes
        fig = (
            px.choropleth_mapbox(
                data,
                geojson=data.set_index(location_field).geometry,
                color=feature_dropdown_value,
                color_continuous_scale="RdYlGn",
                range_color=range_color,
                opacity=slider_value,
                locations=location_field,
                labels={
                    feature_dropdown_value: FEATURE_CONFIG[feature_dropdown_value][
                        "name"
                    ],
                    location_field: SETTINGS_CONFIG[scope_radio_value][
                        "location_field_label"
                    ],
                },
                )
            .update_layout(
                mapbox={
                    "style": "open-street-map",
                    "center": {"lon": -58.4, "lat": -34.6},
                    "zoom": 11,
                },
                coloraxis={"colorbar":colorbar_settings},
            )
            .update_traces(marker_opacity=slider_value, 
                hovertemplate=hovertemplate
                           
                           )
            .update_layout(uirevision="constant")
        )

    elif FEATURE_CONFIG[feature_dropdown_value]["type"] == "discrete":
        # draw a new figure when dropdown changes
        fig = (
            px.choropleth_mapbox(
                data,
                geojson=data.set_index(location_field).geometry,
                color=feature_dropdown_value,
                color_discrete_map=FEATURE_CONFIG[feature_dropdown_value][
                    "color_sequence"
                ],
                category_orders={
                    feature_dropdown_value: list(
                        FEATURE_CONFIG[feature_dropdown_value]["color_sequence"].keys()
                    )
                },
                opacity=slider_value,
                locations=location_field,
                labels={
                    feature_dropdown_value: FEATURE_CONFIG[feature_dropdown_value][
                        "name"
                    ],
                    location_field: SETTINGS_CONFIG[scope_radio_value][
                        "location_field_label"
                    ],
                },
            )
            .update_layout(
                mapbox={
                    "style": "open-street-map",
                    "center": {"lon": -58.4, "lat": -34.6},
                    "zoom": 11,
                },
            )
            .update_traces(marker_opacity=slider_value)
            .update_layout(uirevision="constant")
        )

    # update the feature description
    description_box_children = [
        html.H3(FEATURE_CONFIG[feature_dropdown_value]["name"], id="feature-name"),
        html.P(
            FEATURE_CONFIG[feature_dropdown_value]["description"],
            id="feature-description",
        ),
    ]

    display_graph_style = {"display": "block"}

    graph = dcc.Graph(figure=fig, style={"height": "100vh"})

    return display_graph_style, graph, description_box_children


if __name__ == "__main__":
    app.run_server(debug=True)
