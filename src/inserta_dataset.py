# Fichero realizado por:
#  - Nombre: Beltrán Sánchez Careaga
#  - Nombre: Ignacio Queipo de Llano Pérez-Gascón

from load_data import *

PATH_DATASET = {"GroceryFood": "datos/Grocery_and_Gourmet_Food_5.json"}


def inserta_mongodb(dbname: MongoClient, idx: int) -> None:
    columnas_deseadas = [
        "reviewText",
        "summary",
        "reviewTime",
    ]
    review_id = idx + 1
    for coleccion, path in PATH_DATASET.items():
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


def inserta_mysql(tabla1: str, tabla2: str, idx: int) -> None:
    cont_total = 0
    review_id = idx + 1
    for tabla, path in PATH_DATASET.items():
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

    conexion = pymysql.connect(
        host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD
    )
    cursor = conexion.cursor()
    conexion.select_db(MYSQL_DATABASE)

    cursor.execute(f"SELECT MAX(reviewID) FROM REVIEWS")
    review_id = cursor.fetchone()[0]

    conexion.commit()
    conexion.close()

    # * MONGODB
    print("Iniciando carga de datos en MongoDB")
    client = get_client()
    dbname = get_database(MONGODB_DATABASE)
    inserta_mongodb(dbname, review_id)

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

    inserta_mysql("REVIEWS", "REVIEWERS", review_id)

    conexion.commit()
    conexion.close()
