# Fichero realizado por:
#  - Nombre: Beltrán Sánchez Careaga
#  - Nombre: Ignacio Queipo de Llano Pérez-Gascón


# Configuración para MySQL
MYSQL_HOST = "localhost"
MYSQL_USER = "iqueipo"
MYSQL_PASSWORD = "Madrid2022"
MYSQL_DATABASE = "reviews_proyecto"

# Configuración para MongoDB
MONGODB_HOST = "localhost"
MONGODB_PORT = 27017
MONGODB_DATABASE = "reviews_proyecto"
MONGODB_COLLECTION = "nombre_coleccion_mongodb"

# Configuración para Neo4J
URI = "bolt://localhost:7474"
NEO4J_USER = "__________"
NEO4J_PASSWORD = "__________"

# Rutas de los archivos de datos
#! Cambiar la ruta de los archivos de datos
REVIEWS_FILE_PATHS = {
    "DigitalMusic": "datos/Digital_Music_5.json",
    "MusicalInstruments": "datos/Musical_instruments_5.json",
    "ToysGames": "datos/Toys_and_Games_5.json",
    "VideoGames": "datos/Video_Games_5.json",
}
