from dash import dcc, html, Input, Output
import dash
import os

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import plotly.express as px

# Load data
data_criminalidad = gpd.read_file(
    "data/final/data_criminalidad.geojson", driver="GeoJSON"
)

FEATURES = [
    col
    for col in data_criminalidad.columns.tolist()
    if col not in ["geometry", "CO_FRAC_RA"]
]


app = dash.Dash(__name__)

# Mapbox Choropleth
fig = px.choropleth_mapbox(
    data_criminalidad,
    geojson=data_criminalidad.set_index("CO_FRAC_RA").geometry,
    color="score_robo",
    color_discrete_sequence="score_robo",
    opacity=0.5,
    locations="CO_FRAC_RA",
).update_layout(
    mapbox={
        "style": "open-street-map",
        "center": {"lon": -58.4, "lat": -34.6},
        "zoom": 10,
    },
)
## Description box
# Make a custom div with a box holding description of the plot, a slider for reducing opacity and
# a dropdown to select the variable to plot
description_box = html.Div(
    [
        html.H2("Mapa de criminalidad en la CABA"),
        html.P(
            "Este mapa muestra la cantidad de robos por cada 1000 habitantes en cada barrio de la CABA. \
        El color de cada barrio indica la cantidad de robos, siendo el rojo el color que indica mayor \
        cantidad de robos y el amarillo el que indica menor cantidad de robos. \
        El mapa se puede filtrar por año y por tipo de robo."
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
                            options=[
                                {"label": "Robos", "value": "score_robo"},
                                {"label": "Hurtos", "value": "score_hurtos"},
                                {"label": "Lesiones", "value": "score_lesiones"},
                                {
                                    "label": "Homicidio reportado",
                                    "value": "homicidio_reportado",
                                },
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
        )
    ],
    # add a light background color and some padding to the box
    style={"background-color": "lightgrey", "padding": "10px"},
)


app.layout = html.Div(
    [
        description_box,
        dcc.Graph(figure=fig, id="map", style={"height": "100vh"}),
    ],
    style={"margin": "auto", "padding": "10px"},
)


## Callbacks
# update plot opacity based on slider value
@app.callback(
    Output("map", "figure"),
    [Input("opacity-slider", "value"), Input("feature-dropdown", "value")],
)
def update_opacity(slider_value, feature_dropdown_value):

    # draw a new figure when dropdown changes
    fig = px.choropleth_mapbox(
        data_criminalidad,
        geojson=data_criminalidad.set_index("CO_FRAC_RA").geometry,
        color=feature_dropdown_value,
        color_continuous_scale="Reds",
        opacity=slider_value,
        locations="CO_FRAC_RA",
    ).update_layout(
        mapbox={
            "style": "open-street-map",
            "center": {"lon": -58.4, "lat": -34.6},
            "zoom": 10,
        },
    )

    fig.update_traces(marker_opacity=slider_value)
    fig.update_layout(uirevision="constant")
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
