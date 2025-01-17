# Fichero realizado por:
#  - Nombre: Beltrán Sánchez Careaga
#  - Nombre: Ignacio Queipo de Llano Pérez-Gascón

import json
import pymysql
import pymongo
from pymongo import MongoClient
from pymongo.database import Database
from datetime import datetime
from configuaracion import *


def get_client() -> MongoClient:
    CONNECTION_STRING = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}"
    return MongoClient(CONNECTION_STRING)


def get_database(database: str) -> MongoClient:
    client = get_client()
    databases = client.list_database_names()
    if database in databases:
        print("La base de datos ya existe")
    return client[database]


def format_date(date_str: str) -> datetime:
    date_obj = datetime.strptime(date_str, "%m %d, %Y")
    return date_obj.strftime("%Y-%m-%d")


def inserta_mongodb(dbname: MongoClient) -> None:
    columnas_deseadas = [
        "reviewText",
        "summary",
        "reviewTime",
    ]
    review_id = 10000001
    for coleccion, path in REVIEWS_FILE_PATHS.items():
        cont = 0
        collection_name = dbname[coleccion]
        with open(path) as file:
            for line in file:
                file_data = json.loads(line)
                data_a_insertar = {
                    "_id": review_id,
                }
                for columna in columnas_deseadas:
                    try:
                        if columna == "reviewTime":
                            data_a_insertar[columna] = format_date(file_data[columna])
                        else:
                            data_a_insertar[columna] = file_data[columna]
                    except KeyError:
                        data_a_insertar[columna] = None
                collection_name.insert_one(data_a_insertar)
                cont += 1
                review_id += 1
                if cont % 10000 == 0:
                    print(f"Insertados {cont} datos en coleccion {coleccion}")
        print(f"Finalizada coleccion {coleccion} con {cont} datos insertados \n")


def inserta_mysql(tabla1: str, tabla2: str) -> None:
    cont_total = 0
    review_id = 10000001
    for tabla, path in REVIEWS_FILE_PATHS.items():
        cont_parcial = 0
        with open(path) as file:
            for line in file:
                file_data = json.loads(line)
                datos_insertar1 = (
                    review_id,
                    file_data["reviewerID"],
                    file_data["asin"],
                    file_data["overall"],
                    file_data["unixReviewTime"],
                    file_data["helpful"][0],
                    file_data["helpful"][1],
                    tabla,
                )
                try:
                    name = file_data["reviewerName"]
                except KeyError:
                    name = None
                datos_insertar2 = [file_data["reviewerID"], name]

                consulta1 = f"""
                    INSERT INTO {tabla1} 
                    (reviewID, reviewerID, asin, overall, unixReviewTime, min_helpful, max_helpful, category) 
                    VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                consulta2 = f"""
                    INSERT INTO {tabla2} 
                    (reviewerID, reviewerName) 
                    VALUES 
                    (%s, %s)
                    ON DUPLICATE KEY UPDATE reviewerID=reviewerID
                """

                cursor.execute(consulta1, datos_insertar1)
                cursor.execute(consulta2, datos_insertar2)

                cont_total += 1
                cont_parcial += 1
                review_id += 1
                if cont_total % 10000 == 0:
                    print(f"Insertados {cont_total} datos")
        print(f"Finalizado {tabla}.json con {cont_parcial} datos insertados \n")
    print(f"Finalizada insercion con {cont_total} datos insertados \n")


if __name__ == "__main__":
    # * MONGODB
    print("Iniciando carga de datos en MongoDB")
    client = get_client()
    dbname = get_database(MONGODB_DATABASE)
    inserta_mongodb(dbname)

    client.close()

    # * MYSQL
    print("Iniciando carga de datos en MySQL")
    conexion = pymysql.connect(
        host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD
    )
    cursor = conexion.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
    conexion.select_db(MYSQL_DATABASE)

    columnas_comunes1 = [
        "reviewID INT PRIMARY KEY AUTO_INCREMENT",
        "reviewerID VARCHAR(255)",
        "asin VARCHAR(255)",
        "overall FLOAT",
        "unixReviewTime INT",
        "min_helpful INT",
        "max_helpful INT",
        "category VARCHAR(255)",
    ]

    columnas_comunes2 = ["reviewerID VARCHAR(255) PRIMARY KEY", "reviewerName TEXT"]

    consulta1 = f"CREATE TABLE IF NOT EXISTS REVIEWS ({', '.join(columnas_comunes1)})"
    cursor.execute(consulta1)
    consulta2 = f"CREATE TABLE IF NOT EXISTS REVIEWERS ({', '.join(columnas_comunes2)})"
    cursor.execute(consulta2)

    inserta_mysql("REVIEWS", "REVIEWERS")

    conexion.commit()
    conexion.close()
