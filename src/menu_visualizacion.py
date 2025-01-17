# Fichero realizado por:
#  - Nombre: Beltrán Sánchez Careaga
#  - Nombre: Ignacio Queipo de Llano Pérez-Gascón

from PIL import Image
import pymongo
import pymysql
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
from configuaracion import *
from wordcloud import WordCloud
import os
import numpy as np

categorias = {
    "DigitalMusic": "DigitalMusic",
    "MusicalInstruments": "MusicalInstruments",
    "ToysGames": "ToysGames",
    "VideoGames": "VideoGames",
    "Todas": "Todas",
}


def get_mongo_client():
    return pymongo.MongoClient(f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}")


def get_mysql_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )


def queries_tab1(connection, category2, category4):
    cursor = connection.cursor()
    if category2 == "Todas":
        query = """
            SELECT asin, COUNT(*) AS cantidad_reviews
            FROM reviews
            GROUP BY asin
            ORDER BY cantidad_reviews DESC
        """
    else:
        query = f"""
            SELECT asin, COUNT(*) AS cantidad_reviews
            FROM reviews
            WHERE category = '{category2}'
            GROUP BY asin
            ORDER BY cantidad_reviews DESC
        """
    cursor.execute(query)
    result_mysql2 = cursor.fetchall()

    if category4 != "Todas":
        query = f"""
            SELECT FROM_UNIXTIME(unixReviewTime, '%Y-%m-%d') AS fecha, SUM(COUNT(*)) OVER (ORDER BY unixReviewTime) AS acumulado_reviews
            FROM reviews
            WHERE category = '{category4}'
            GROUP BY unixReviewTime
            ORDER BY unixReviewTime
        """
    else:
        query = """
            SELECT FROM_UNIXTIME(unixReviewTime, '%Y-%m-%d') AS fecha, SUM(COUNT(*)) OVER (ORDER BY unixReviewTime) AS acumulado_reviews
            FROM reviews
            GROUP BY unixReviewTime
            ORDER BY unixReviewTime
        """
    cursor.execute(query)
    result_mysql4 = cursor.fetchall()

    query = """
        SELECT DATE_FORMAT(FROM_UNIXTIME(unixReviewTime), '%Y-%m') AS periodo,
        COUNT(DISTINCT reviewerID) AS cantidad_revisores
        FROM reviews
        GROUP BY periodo
        ORDER BY periodo
        """
    cursor.execute(query)
    result_mysql6 = cursor.fetchall()
    cursor.close()

    return result_mysql2, result_mysql4, result_mysql6


def queries_tab2(connection, category1, category3, asin):
    cursor = connection.cursor()
    if category1 == "Todas":
        query = """
            SELECT YEAR(FROM_UNIXTIME(unixReviewTime)) AS año, COUNT(*) AS cantidad_reviews 
            FROM reviews
            GROUP BY YEAR(FROM_UNIXTIME(unixReviewTime))
        """
    else:
        query = f"""SELECT YEAR(FROM_UNIXTIME(unixReviewTime)) AS año, COUNT(*) AS cantidad_reviews 
                FROM reviews WHERE category = '{category1}'
                GROUP BY YEAR(FROM_UNIXTIME(unixReviewTime))"""
    cursor.execute(query)
    result1 = cursor.fetchall()

    if category3 != "Todas" and category3 in categorias:
        query = f"""
            SELECT overall, COUNT(*) AS cantidad_articulos
            FROM reviews
            WHERE category = '{category3}'
            GROUP BY overall
            ORDER BY overall
        """
    elif asin:
        query = f"""
            SELECT overall, COUNT(*) AS cantidad_articulos
            FROM reviews
            WHERE asin = '{asin}'
            GROUP BY overall
            ORDER BY overall
        """
    else:
        query = """
            SELECT overall, COUNT(*) AS cantidad_articulos
            FROM reviews
            GROUP BY overall
            ORDER BY overall
        """
    cursor.execute(query)
    result3 = cursor.fetchall()
    cursor.close()
    return result1, result3


def obtener_reviews_por_anio(result1, tipo="Todas"):
    df_mysql = pd.DataFrame(result1, columns=["año", "cantidad_reviews"])
    fig = px.scatter(
        df_mysql,
        x="año",
        y="cantidad_reviews",
        color="año",
        size="cantidad_reviews",
        title=f"Cantidad de reviews de {tipo} por año",
    )

    return fig


def evolucion_popularidad_articulos(result2, tipo="Todas"):
    df_mysql = pd.DataFrame(result2, columns=["productId", "cantidad_reviews"])

    fig = px.line(
        df_mysql,
        x=df_mysql.index + 1,
        y="cantidad_reviews",
        title=f"Evolución de la popularidad de {tipo}",
    )
    fig.update_layout(
        xaxis_title="Artículos (ordenados por popularidad)",
        yaxis_title="Cantidad de reviews",
    )

    return fig


def scatter_por_nota(result3, tipo, asin):
    df_mysql = pd.DataFrame(result3, columns=["overall", "cantidad_articulos"])
    if tipo in categorias and tipo != "Todas":
        titulo = f"Numero de reviews por nota para categoria {tipo}"
    elif asin:
        titulo = f"Numero de reviews por nota para producto {asin}"
    else:
        titulo = "Numero de reviews por nota para todos los productos"
    fig = px.scatter(
        df_mysql,
        x="overall",
        y="cantidad_articulos",
        color="overall",
        size="cantidad_articulos",
        title=titulo,
        labels={"overall": "Nota", "cantidad_articulos": "Cantidad de artículos"},
    )

    return fig


def evolucion_reviews_por_categoria(result4, tipo="Todas"):
    df_mysql = pd.DataFrame(result4, columns=["fecha", "acumulado_reviews"])
    if tipo != "Todas":
        titulo = f"Evolución de las reviews para la categoría {tipo}"
    else:
        titulo = "Evolución de las reviews para todas las categorías"
    fig = px.line(
        df_mysql,
        x="fecha",
        y="acumulado_reviews",
        title=titulo,
        labels={"fecha": "Fecha", "cantidad_reviews": "Cantidad de reviews"},
    )

    return fig


def histograma_reviews_por_usuario(connection):
    cursor = connection.cursor()
    query = """
        SELECT reviewerID, COUNT(*) AS num_reviews
        FROM reviews
        GROUP BY reviewerID
    """
    cursor.execute(query)
    result_mysql = cursor.fetchall()
    cursor.close()
    df_mysql = pd.DataFrame(result_mysql, columns=["reviewerID", "num_reviews"])

    users_per_reviews_count = df_mysql["num_reviews"].value_counts().sort_index()
    users_per_reviews_count = users_per_reviews_count[
        users_per_reviews_count.index <= 70
    ]

    fig = px.bar(
        x=users_per_reviews_count.index,
        y=users_per_reviews_count.values,
        labels={"x": "reviews por usuario", "y": "usuarios"},
        title="Histograma de reviews por usuario",
    )

    return fig


def nube_palabras(db, category):
    collection = db[category]

    mask = np.array(Image.open(f"imagenes/{category}.jpg"))

    text = " ".join([doc["summary"] for doc in collection.find()])

    stop_words = set(["a", "an", "the", "of", "for", "in", "on", "and", "with", "to"])
    text = " ".join(
        [
            word.strip()
            for word in text.split()
            if len(word) > 3 and word.lower() not in stop_words
        ]
    )
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        mask=mask,
        contour_color="steelblue",
        contour_width=3,
    ).generate(text)

    return wordcloud.to_image()


def participacion_reviewers(result6):
    df_mysql = pd.DataFrame(result6, columns=["periodo", "cantidad_revisores"])
    fig = px.line(
        df_mysql,
        x="periodo",
        y="cantidad_revisores",
        title="Participación de revisores por mes",
    )
    fig.update_layout(
        xaxis_title="Mes",
        yaxis_title="Cantidad de revisores",
    )

    return fig


if __name__ == "__main__":
    opciones = [{"label": i, "value": j} for i, j in categorias.items()]

    connection = get_mysql_connection()
    client = get_mongo_client()
    db = client[MONGODB_DATABASE]

    cursor = connection.cursor()
    query = "SELECT DISTINCT asin FROM reviews"
    cursor.execute(query)
    asins = [fila[0] for fila in cursor.fetchall()]
    cursor.close()

    # Cerrar el cursor y la conexión
    cursor.close()
    app = dash.Dash(__name__)
    app.title = "Proyecto Final BBDD"
    tabs_styles = {"height": "44px"}
    tab_style = {
        "borderBottom": "1px solid #d6d6d6",
        "padding": "6px",
        "fontWeight": "bold",
    }

    tab_selected_style = {
        "borderTop": "1px solid #d6d6d6",
        "borderBottom": "1px solid #d6d6d6",
        "backgroundColor": "#119DFF",
        "color": "white",
        "padding": "6px",
    }
    app.layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        id="shutdown-div",
                        children=[
                            html.Button(
                                "Detener Servidor", id="shutdown-button", n_clicks=0
                            ),
                        ],
                        style={"position": "fixed", "top": 20, "right": 20},
                    ),
                    html.Div(id="output-shutdown"),
                ]
            ),
            html.H1(
                "Visualización de Datos Reviews de Amazon",
                style={"text-align": "center"},
            ),
            dcc.Tabs(
                id="tabs-example-graph",
                value="tab_1",
                children=[
                    dcc.Tab(
                        label="PESTAÑA 1",
                        value="tab_1",
                        style=tab_style,
                        selected_style=tab_selected_style,
                    ),
                    dcc.Tab(
                        label="PESTAÑA 2",
                        value="tab_2",
                        style=tab_style,
                        selected_style=tab_selected_style,
                    ),
                ],
            ),
            html.Div(id="tabs-content-example-graph"),
        ]
    )

    @app.callback(
        Output("tabs-content-example-graph", "children"),
        Input("tabs-example-graph", "value"),
    )
    def render_content(tab):
        if tab == "tab_1":
            return html.Div(
                [
                    html.Div(
                        [
                            html.H1(
                                "Evoluciones temporales",
                                style={"text-align": "center"},
                            ),
                            html.H4(
                                "Popularidad de los productos - Reviews por categoría - Participación de revisores",
                                style={"text-align": "center", "color": "gray"},
                            ),
                        ]
                    ),
                    html.P("Selecciona una categoria:", style={"font-weight": "bold"}),
                    dcc.Dropdown(
                        id="dropdown2",
                        options=opciones,
                        value="Todas",
                    ),
                    dcc.Graph(id="graph2"),
                    html.P("Selecciona una categoria:", style={"font-weight": "bold"}),
                    dcc.Dropdown(
                        id="dropdown4",
                        options=opciones,
                        value="Todas",
                    ),
                    dcc.Graph(id="graph4"),
                    dcc.Graph(id="graph6"),
                ]
            )
        elif tab == "tab_2":
            return html.Div(
                [
                    html.Div(
                        [
                            html.H1(
                                "Scatters - Histogramas - Nube de palabras",
                                style={"text-align": "center"},
                            ),
                            html.H4(
                                "Cantidad reviews - Valoraciones por producto - Reviews por usuario - Palabras relevantes",
                                style={"text-align": "center", "color": "gray"},
                            ),
                        ]
                    ),
                    html.P("Selecciona una categoria:", style={"font-weight": "bold"}),
                    dcc.Dropdown(
                        id="dropdown1",
                        options=opciones,
                        value="Todas",
                    ),
                    dcc.Graph(id="graph1"),
                    html.P(
                        "Por favor, en caso de querer filtrar por categoría, asegúrese de que el campo de ID de producto esté vacío.",
                        style={"font-weight": "bold", "color": "black"},
                    ),
                    html.P("Selecciona una categoria:", style={"font-weight": "bold"}),
                    dcc.Dropdown(
                        id="dropdown3",
                        options=opciones,
                        value="Todas",
                    ),
                    html.P(
                        "Selecciona un ID de producto:", style={"font-weight": "bold"}
                    ),
                    dcc.Input(
                        id="id_input",
                        type="text",
                        placeholder="Ingresa el ID del producto...",
                        debounce=True,  # Evita que se hagan peticiones a cada letra
                    ),
                    html.Div(id="error_message"),
                    html.Div(id="output_div"),
                    dcc.Graph(id="graph3"),
                    html.Div(
                        [
                            dcc.Graph(
                                id="graph5",
                                figure=histograma_reviews_por_usuario(connection),
                            )
                        ]
                    ),
                    html.Div(
                        [
                            html.P(
                                "Para una mejor visualización del histograma, se ha decidido poner el límite del eje x en 70. No obstante, pueden existir usuarios que hayan realizado más de 70 reviews.",
                                style={"text-align": "center", "color": "gray"},
                            )
                        ]
                    ),
                    html.P("Selecciona una categoria:", style={"font-weight": "bold"}),
                    html.Div(
                        [
                            dcc.Dropdown(
                                id="dropdown6",
                                options=opciones[:-1],
                                value="DigitalMusic",
                            ),
                            html.Br(),
                            html.Img(
                                id="nube_palabras",
                                src=nube_palabras(db, category="DigitalMusic"),
                                style={
                                    "width": "80%",
                                    "height": "auto",
                                    "display": "block",
                                    "margin-left": "auto",
                                    "margin-right": "auto",
                                },
                            ),
                        ]
                    ),
                ]
            )

    @app.callback(
        [
            Output("graph2", "figure"),
            Output("graph4", "figure"),
            Output("graph6", "figure"),
        ],
        [
            Input("dropdown2", "value"),
            Input("dropdown4", "value"),
        ],
    )
    def update_tab1(category2, category4):

        r2, r4, r6 = queries_tab1(connection, category2, category4)
        fig2 = evolucion_popularidad_articulos(r2, tipo=category2)
        fig4 = evolucion_reviews_por_categoria(r4, tipo=category4)
        fig6 = participacion_reviewers(r6)

        return fig2, fig4, fig6

    @app.callback(
        [
            Output("graph1", "figure"),
            Output("graph3", "figure"),
            Output("nube_palabras", "src"),
        ],
        [
            Input("dropdown1", "value"),
            Input("dropdown3", "value"),
            Input("id_input", "value"),
            Input("dropdown6", "value"),
        ],
    )
    def update_tab2(category1, category3, asin, categoria):
        cursor = connection.cursor()
        if asin not in asins:
            asin = None
            category3 = category3
        else:
            category3 = None
            asin = asin

        r1, r3 = queries_tab2(connection, category1, category3, asin)
        fig1 = obtener_reviews_por_anio(r1, category1)
        fig3 = scatter_por_nota(r3, category3, asin)
        fig_nube = nube_palabras(db, categoria)

        cursor.close()

        return fig1, fig3, fig_nube

    @app.callback(
        [Output("error_message", "children"), Output("output_div", "children")],
        [Input("id_input", "value")],
        prevent_initial_call=True,
    )
    def verificar_input(value):
        if value in asins:
            error_message = ""
            output_message = f"El asin {value} es válido."
        else:
            error_message = "El asin ingresado no es válido."
            output_message = ""
        return error_message, output_message

    # Callback para detener el servidor cuando se hace clic en el botón
    @app.callback(
        Output("output-shutdown", "children"),
        [Input("shutdown-button", "n_clicks")],
        prevent_initial_call=True,
    )
    def detener_servidor(n_clicks):
        if n_clicks:
            print("Deteniendo el servidor Dash...")
            os._exit(0)

    app.run_server(debug=True, port=8040)
