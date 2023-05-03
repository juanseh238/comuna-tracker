from dash import dcc, html, Input, Output
import dash
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
    },
    "comunas": {
        "violencia_de_genero": gpd.read_file(
            "data/final/violencia-de-genero.geojson", driver="GeoJSON"
        )
    },
}


with open("config.json", "r") as f:
    CONFIG = json.load(f)
    FEATURE_CONFIG = CONFIG["FEATURES"]
    SETTINGS_CONFIG = CONFIG["SETTINGS"]

DEFAULT_SCOPE = "radios_censales"

app = dash.Dash(__name__)
server = app.server

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
        html.H3("Nivel", style={"margin-right": "10px", "text-align": "center", "font-size": "20px"}),
        dcc.RadioItems(
            id="scope-radio",
            options=[
                {"label": "Comunas", "value": "comunas"},
                {"label": "Radios Censales", "value": "radios_censales"},
            ],
            value=DEFAULT_SCOPE,
            labelStyle={
                "font-size": "18px",
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
    style={"display": "flex", "flex-direction": "row", "justify-content": "center","gap": "30px"}
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
                        html.P("Seleccioná el indicador de interés para graficar:"),
                        dcc.Dropdown(
                            id="feature-dropdown",
                            clearable=False,
                            # default options to radios censales
                            options=[
                                {
                                    "label": FEATURE_CONFIG[feature]["name"],
                                    "value": feature,
                                }
                                for feature in FEATURE_CONFIG
                                if DEFAULT_SCOPE in FEATURE_CONFIG[feature]["scope"]
                            ],
                            # add a default text hinting at selecting a radio item first
                            placeholder="Seleccioná un indicador",
                        ),
                    ]
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
    Output("feature-dropdown", "options"),
    [Input("scope-radio", "value")],
)
def update_dropdown(scope_radio_value):
    """
    Update dropdown options bsaed on radio button selection.
    The radio button selection value matches the 'scope' field in the FEATURES config dict.
    """
    scope = SETTINGS_CONFIG[scope_radio_value]["scope"]
    print([feature for feature in FEATURE_CONFIG])
    options = [
        {"label": FEATURE_CONFIG[feature]["name"], "value": feature}
        for feature in FEATURE_CONFIG
        if scope in FEATURE_CONFIG[feature]["scope"]
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
        Input("feature-dropdown", "value"),
        Input("scope-radio", "value"),
    ],
)
def update_plot(slider_value, feature_dropdown_value, scope_radio_value):
    # hide graph if no feature is selected
    if not feature_dropdown_value:
        hidden_graph_style = {"display": "none"}
        return hidden_graph_style, None, None

    # hide graph if selected feature is not available for selected scope
    if scope_radio_value not in FEATURE_CONFIG[feature_dropdown_value]["scope"]:
        hidden_graph_style = {"display": "none"}
        return hidden_graph_style, None, None

    source = FEATURE_CONFIG[feature_dropdown_value]["source"]
    data = DATA[scope_radio_value][source]

    location_field = SETTINGS_CONFIG[scope_radio_value]["location_field"]
    print("Location field: ", location_field)
    print("Feature dropdown value: ", feature_dropdown_value)
    print("Scope radio value: ", scope_radio_value)

    # draw a new figure when dropdown changes
    fig = px.choropleth_mapbox(
        data,
        geojson=data.set_index(location_field).geometry,
        color=feature_dropdown_value,
        color_discrete_map=FEATURE_CONFIG[feature_dropdown_value]["color_sequence"],
        category_orders={
            feature_dropdown_value: list(
                FEATURE_CONFIG[feature_dropdown_value]["color_sequence"].keys()
            )
        },
        opacity=slider_value,
        locations=location_field,
        labels={
            feature_dropdown_value: FEATURE_CONFIG[feature_dropdown_value]["name"],
            location_field: SETTINGS_CONFIG[scope_radio_value]["location_field_label"],
        },
    ).update_layout(
        mapbox={
            "style": "open-street-map",
            "center": {"lon": -58.4, "lat": -34.6},
            "zoom": 11,
        },
    )

    fig.update_traces(marker_opacity=slider_value)
    fig.update_layout(uirevision="constant")

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
