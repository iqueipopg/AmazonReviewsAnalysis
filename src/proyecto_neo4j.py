# Fichero realizado por:
#  - Nombre: Beltrán Sánchez Careaga
#  - Nombre: Ignacio Queipo de Llano Pérez-Gascón

from neo4j import GraphDatabase
import pandas as pd
import random
import json
import pymysql
import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from configuaracion import *


def crear_nodo(session, etiqueta, **propiedades):

    consulta = f"CREATE (n:{etiqueta} $propiedades) RETURN n"

    return session.run(consulta, propiedades=propiedades).single()[0]


def crear_arista(session, nodo_inicio, nodo_fin, tipo_arista, **propiedades):

    consulta = f"""
    MATCH (inicio), (fin)
    WHERE id(inicio) = $id_inicio AND id(fin) = $id_fin
    CREATE (inicio)-[a:`{tipo_arista}` $propiedades]->(fin)
    RETURN a
    """

    return session.run(
        consulta, id_inicio=nodo_inicio.id, id_fin=nodo_fin.id, propiedades=propiedades
    ).single()[0]


def borrar_datos(session):
    try:
        with session.begin_transaction() as tx:
            tx.run("MATCH (n) DETACH DELETE (n)")
        print("Nodos eliminados correctamente.")
    except Exception as e:
        print(f"Error al eliminar nodos: {e}")


# ---------------------------------------------- 4.1 ----------------------------------------------


def usuarios_mas_resenas(numero):
    nodos = []
    consulta = f"""
        SELECT r.reviewerID, r.reviewerName, COUNT(t1.reviewerID) as total_reviews,
               GROUP_CONCAT(t1.asin) as asin_valorados
        FROM reviews t1
        INNER JOIN reviewers r ON t1.reviewerID = r.reviewerID
        GROUP BY r.reviewerID, r.reviewerName
        ORDER BY total_reviews DESC
        LIMIT {numero}
    """
    cursor.execute(consulta)
    resultados = cursor.fetchall()

    print(f"Las {numero} personas con más reviews son:")
    for resultado in resultados:
        nodo = crear_nodo(
            session,
            "Reviewer",
            reviewer_id=resultado[0],
            reviewer_name=resultado[1],
            num_reviews=resultado[2],
            reviews=resultado[3],
        )
        nodos.append(nodo)
        print(
            f"ReviewerID: {resultado[0]}, ReviewerNAME: {resultado[1]}, Total de Reviews: {resultado[2]}"
        )

    print(f"TOP {numero} USUARIOS CON MÁS RESEÑAS CARGADOS.")
    return nodos


def calcular_similitud(usuarios):
    similitudes = {}

    for i in range(len(usuarios)):
        for j in range(i + 1, len(usuarios)):
            usuario1 = usuarios[i]
            usuario2 = usuarios[j]
            interseccion = len(
                set(usuario1["reviews"]).intersection(set(usuario2["reviews"]))
            )
            union = len(set(usuario1["reviews"]).union(set(usuario2["reviews"])))

            similitud = interseccion / union
            crear_arista(
                session,
                usuario1,
                usuario2,
                tipo_arista="SIMILITUD",
                similitud=similitud,
            )

            if similitud != 0:
                similitudes[(usuario1["reviewer_id"], usuario2["reviewer_id"])] = (
                    similitud
                )

    # Archivo auxiliar
    with open("similitudes.txt", "w") as archivo:
        for par, similitud in similitudes.items():
            archivo.write(
                f"Usuarios {par[0]}-{par[1]}: Similitud de Jaccard = {similitud}\n"
            )

    print(f"SIMILITUDES ENTRE {len(usuarios)} USUARIOS CARGADAS.")
    return similitudes


def consultar_nodo_mas_vecinos():
    with driver.session() as session:
        result = session.run(
            """ MATCH (n)
                RETURN n, size([(n)-->() | 1]) AS vecinos
                ORDER BY vecinos DESC
                LIMIT 1
                """
        )
        record = result.single()
        nodo_mas_vecinos = record["n"]
        num_vecinos = record["vecinos"]
        print(
            f"El nodo con más vecinos es: {nodo_mas_vecinos}, con {num_vecinos} vecinos."
        )


def apartado_4_1(session, numero):
    borrar_datos(session)
    usuarios = usuarios_mas_resenas(numero)
    calcular_similitud(usuarios)
    consultar_nodo_mas_vecinos()


# ---------------------------------------------- 4.2 ----------------------------------------------


def articulos_aleatorios():
    dict_categorias = {
        1: "DigitalMusic",
        2: "MusicalInstruments",
        3: "ToysGames",
        4: "VideoGames",
    }
    running = True
    consulta = f"""
        select count(distinct(asin))
        from reviews
    """
    cursor.execute(consulta)
    resultados = cursor.fetchone()

    print(f"Número de artículos diferentes con reviews: {resultados[0]}.")

    while running:
        coleccion = input(
            """

        SELECCIONE LA COLECCIÓN DE ARTICULOS:
                    
            1. Digital Music
            2. Musical Instruments
            3. Toys and Games
            4. Video Games 
                          
   RESPUESTA:"""
        )
        try:
            coleccion = int(coleccion)
            if coleccion not in (1, 2, 3, 4):
                pass
            else:
                running = False
                coleccion = dict_categorias[coleccion]

        except ValueError as error:
            print(error)

    numero = int(input("    SELECCIONE NÚMERO DE ARTÍCULOS ALEATORIOS:"))

    consulta = f"""
        SELECT asin
        FROM reviews 
        WHERE category = '{coleccion}'
        ORDER BY RAND()
        LIMIT {numero}
    """
    cursor.execute(consulta)
    resultados = cursor.fetchall()

    return resultados


def estudio_articulos(articulos):
    producto_anterior = 0
    for articulo in articulos:
        consulta = f"""
            SELECT reviewerID, asin, overall, FROM_UNIXTIME(unixReviewTime, '%d/%m/%y-%H:%i:%s') AS reviewDateTime
            from reviews
            where asin = '{articulo[0]}'
        """
        cursor.execute(consulta)
        resultados = cursor.fetchall()
        for resultado in resultados:
            reviewer = resultado[0]
            producto = resultado[1]
            puntuacion = resultado[2]
            tiempo = resultado[3]

            nodo1 = crear_nodo(session, "Reviewer", element_id=reviewer)
            if not producto_anterior == producto:
                nodo2 = crear_nodo(session, "Product", element_id=producto)
                producto_anterior = producto
            crear_arista(
                session,
                nodo1,
                nodo2,
                tipo_arista="REVIEW",
                overall=puntuacion,
                date=tiempo,
            )

    print("------CARGA DE DATOS EN NEO4J COMPLETADA------")


def apartado_4_2(session):
    borrar_datos(session)
    articulos = articulos_aleatorios()
    estudio_articulos(articulos)


# ---------------------------------------------- 4.3 ----------------------------------------------


def estudio_tipos():
    nodos_tipos = {}

    consulta_revisores = """
    SELECT subquery.reviewerID, r.reviewerName, subquery.distinct_category
    FROM (
        SELECT reviewerID, COUNT(DISTINCT category) AS num_categories, GROUP_CONCAT(DISTINCT category) AS distinct_category
        FROM reviews
        GROUP BY reviewerID
        HAVING num_categories >= 2
    ) AS subquery
    JOIN reviewers r ON subquery.reviewerID = r.reviewerID
    ORDER BY subquery.reviewerID
    LIMIT 400
    """
    cursor.execute(consulta_revisores)
    resultados = cursor.fetchall()
    for resultado in resultados:
        reviewer_id = resultado[0]
        nombre = resultado[1]
        categorias_revisor = resultado[2].split(",")
        for categoria in categorias_revisor:
            if categoria not in nodos_tipos.keys():
                nodo_categoria = crear_nodo(
                    session, "Tipo_Producto", element_id=categoria.strip()
                )
                nodos_tipos[categoria] = nodo_categoria

        nodo_revisor = crear_nodo(
            session, "Reviewer", element_id=reviewer_id, nombre=nombre
        )
        for categoria in categorias_revisor:
            categoria = categoria.strip()
            consulta = f"""
                select count(category)
                from reviews
                where reviewerID = '{reviewer_id}' and category = '{categoria}'
            """
            cursor.execute(consulta)
            resultado = cursor.fetchone()
            num_articulos = resultado[0]

            if categoria in nodos_tipos.keys():
                nodo_categoria = nodos_tipos[categoria]
                crear_arista(
                    session,
                    nodo_revisor,
                    nodo_categoria,
                    tipo_arista="REVIEW",
                    num_articulos=num_articulos,
                )
    print("------CARGA DE DATOS EN NEO4J COMPLETADA------")


def apartado_4_3(session):
    borrar_datos(session)
    estudio_tipos()


# ---------------------------------------------- 4.4 ----------------------------------------------


def estudio_popularidades():
    nodos = []
    consulta = """
        SELECT asin, COUNT(*) AS total_reviews
        FROM reviews
        GROUP BY asin
        having total_reviews < 40
        ORDER BY total_reviews desc
        limit 5
    """
    cursor.execute(consulta)
    resultados = cursor.fetchall()
    for resultado in resultados:
        nodo_producto = crear_nodo(session, "Product", asin=resultado[0])
        consulta = f"""
        SELECT distinct(reviewerID)
        from reviews
        where asin ='{resultado[0]}'
        """
        cursor.execute(consulta)
        usuarios = cursor.fetchall()
        for usuario in usuarios:
            consulta = f"""
                select GROUP_CONCAT(distinct asin)
                from reviews
                where reviewerID ='{usuario[0]}'
            """
            cursor.execute(consulta)
            reviews = cursor.fetchall()[0]
            nodo_usuario = crear_nodo(
                session, "Reviewer", reviewer_id=usuario[0], reviews=reviews
            )
            crear_arista(session, nodo_usuario, nodo_producto, tipo_arista="REVIEW")
            nodos.append(nodo_usuario)

    print("------CARGA DE DATOS EN NEO4J COMPLETADA------")

    return nodos


def apartado_4_4(session):
    borrar_datos(session)
    usuarios = estudio_popularidades()
    calcular_similitud(usuarios)


# ---------------------------------------------- MAIN ----------------------------------------------

if __name__ == "__main__":
    driver = GraphDatabase.driver(URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    conexion = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )
    cursor = conexion.cursor()

    with driver.session() as session:
        apartado_4_1(session, 30)
        apartado_4_2(session)
        apartado_4_3(session)
        apartado_4_4(session)

        driver.close()
