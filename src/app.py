from dash import dcc, html, Input, Output
import dash
import os

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import plotly.express as px
import simplejson as json

# Load data

DATA = {
    "delitos": gpd.read_file(
    "data/final/data_criminalidad.geojson", driver="GeoJSON"
),
    "comisarias": gpd.read_file(
    "data/final/comisarias.geojson", driver="GeoJSON"
)
}


with open("config.json", "r") as f:
    FEATURE_CONFIG = json.load(f)["FEATURES"]


app = dash.Dash(__name__)
server = app.server

# Mapbox Choropleth
# initialized with robos
fig = px.choropleth_mapbox(
    DATA["delitos"],
    geojson=DATA["delitos"].set_index("CO_FRAC_RA").geometry,
    color="score_robo",
    category_orders={"score_robo": ["1", "2", "3", "4", "5"]},
    color_discrete_map=FEATURE_CONFIG["score_robo"]["color_sequence"],
    opacity=0.5,
    locations="CO_FRAC_RA",
    labels={
        "score_robo": FEATURE_CONFIG["score_robo"]["name"],
        "CO_FRAC_RA": "Código RC"},
).update_layout(
    mapbox={
        "style": "open-street-map",
        "center": {"lon": -58.4, "lat": -34.6},
        "zoom": 10,
    },
)
## Description box
## add feature description
description_box = html.Div(
    [
        html.H3(FEATURE_CONFIG["score_robo"]["name"], id="feature-name"),
        html.P(
            FEATURE_CONFIG["score_robo"]["description"], id="feature-description"
        ),
    ], id="description-box", style={"margin-top": "25px", "margin-bottom": "25px"}
)

# Make a custom div with a box holding description of the plot, a slider for reducing opacity and
# a dropdown to select the variable to plot
control_box = html.Div(
    [
        html.H2("Indicadores de Nivel de Servicio en CABA"),
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
                            options=[
                                {"label": "Robos", "value": "score_robo"},
                                {"label": "Hurtos", "value": "score_hurtos"},
                                {"label": "Lesiones", "value": "score_lesiones"},
                                {
                                    "label": "Homicidio reportado",
                                    "value": "homicidio_reportado",
                                },
                                {"label": "Distancia a comisarias", "value": "quintil_distancia_comisaria"}
                            ],
                            value="score_robo",
                            clearable=False,
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
        description_box
    ],
    # add a light background color and some padding to the box
    style={"background-color": "lightgrey",
         "padding": "10px", "padding-left": "20px", "padding-right": "20px",
         "border-radius": "5px"},
)




app.layout = html.Div(
    [
        control_box,
        dcc.Graph(figure=fig, id="map", style={"height": "100vh"}),
    ],
    style={"margin": "auto", "padding": "10px"},
)


## Callbacks
# update plot opacity based on slider value
@app.callback(
    [Output("map", "figure"), Output("description-box", "children")],
    [Input("opacity-slider", "value"), Input("feature-dropdown", "value")],
)
def update_plot(slider_value, feature_dropdown_value):

    source = FEATURE_CONFIG[feature_dropdown_value]["source"]
    data = DATA[source]
    

    # draw a new figure when dropdown changes
    fig = px.choropleth_mapbox(
        data,
        geojson=data.set_index("CO_FRAC_RA").geometry,
        color=feature_dropdown_value,
        color_discrete_map=FEATURE_CONFIG[feature_dropdown_value]["color_sequence"],
        category_orders={feature_dropdown_value: list(FEATURE_CONFIG[feature_dropdown_value]["color_sequence"].keys())},
        opacity=slider_value,
        locations="CO_FRAC_RA",
    labels={feature_dropdown_value: FEATURE_CONFIG[feature_dropdown_value]["name"],
            "CO_FRAC_RA": "Código RC"},

    ).update_layout(
        mapbox={
            "style": "open-street-map",
            "center": {"lon": -58.4, "lat": -34.6},
            "zoom": 10,
        },
    )

    # update the feature description
    description_box_children = [
        html.H3(FEATURE_CONFIG[feature_dropdown_value]["name"], id="feature-name"),
        html.P(
            FEATURE_CONFIG[feature_dropdown_value]["description"],
            id="feature-description",
        ),
    ]

    fig.update_traces(marker_opacity=slider_value)
    fig.update_layout(uirevision="constant")
    return fig, description_box_children


if __name__ == "__main__":
    app.run_server(debug=True)
