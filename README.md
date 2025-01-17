

# AmazonReviewsAnalysis 📊🛒

**AmazonReviewsAnalysis** is a project focused on analyzing **Amazon product reviews** by integrating relational and non-relational databases. The project leverages **MySQL** for structured data, **MongoDB** for semi-structured data, and **Neo4J** for graph-based analysis, enabling visualization and extraction of insights from user and product relationships.

This project was developed as part of a **Database and Machine Learning** course at **Universidad Pontificia Comillas, ICAI**.

## 📜 Table of Contents
- [📌 Project Overview](#-project-overview)
- [🛠️ Installation](#-installation)
- [⚙️ How It Works](#-how-it-works)
- [📂 Project Structure](#-project-structure)
- [🖥️ Technologies Used](#-technologies-used)
- [🙌 Credits](#-credits)

## 📌 Project Overview

AmazonReviewsAnalysis allows users to:
- **Analyze reviews and ratings** from Amazon users for various product categories.
- **Design relational and non-relational database schemas** for storing and processing reviews and reviewer data.
- **Visualize user-product relationships** using **Neo4J** to detect patterns and similarities.
- **Generate insights** such as most popular products, user similarities, and reviews over time.
- **Integrate Machine Learning** to predict product ratings using a Random Forest model.

## 🛠️ Installation

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/iqueipopg/AmazonReviewsAnalysis.git
```

### 2️⃣ Unzip the Data Folder
Since the dataset is large, it is stored as `data.zip`. Before running the program, unzip it:
```sh
unzip datos.zip -d data
```
This will extract the necessary .json files inside the `datos/` folder.

### 3️⃣ Run the GPS Application
```sh
python src/menu_visualizacion.py
```
You can interact with the program via the command line.

## ⚙️ How It Works

### 🗃️ Database Design & Integration
- **MySQL** stores structured, relational data (e.g., review details, ratings, and reviewer info).
- **MongoDB** is used for semi-structured data (e.g., lengthy text data in reviews).
- **Neo4J** is employed for **graph-based analysis**, where nodes represent users and products, and edges represent relationships (similarities or common products rated).
### 🧑‍🤝‍🧑 User Similarity Analysis
- The program calculates **Jaccard similarity** between users based on their common reviews.
- **Neo4J** visualizes these relationships, showing connections between users with similar tastes or behaviors.
### 📊 Product Popularity & Insights
- Extracts the **most popular products** with fewer than 40 reviews, displaying user interactions.
- Also, visualizes the **evolution of reviews** over time, with an option to filter by product category.
### 🤖 Machine Learning Model
- **Random Forest** is used to predict **product ratings** based on reviewer attributes and review content.
- The dataset is processed to normalize features and prepare them for training the model.

## 📂 Project Structure

```plaintext
├───.vscode/                  # Visual Studio Code configuration
├───datos/                    # Folder containing raw and processed data
├───imagenes/                 # Images for visualizations and banners
├───src/                      # Source code
│   ├── configuracion.py      # Configuration file with database details
│   ├── load_data.py          # Script for loading data into MySQL and MongoDB
│   ├── menu_visualizacion.py # Dash app for interactive visualizations
│   ├── neo4j_queries.py      # Neo4J queries and graph-based analysis
│   ├── inserta_data.py       # Script for inserting new data
├───__pycache__/              # Python cache files (ignored)
└───README.md                 # Project documentation
```

## 🖥️ Technologies Used

### 🔧 Development
- **Python** – Core programming language.
- **pandas** – Data manipulation and analysis.
- **pymysql** – MySQL client for database operations.
- **py2neo** – Neo4J Python client for graph-based queries and operations.
- **scikit-learn** – Machine learning library used for building predictive models.
- **Dash** – Framework for creating interactive web dashboards.
### 📊 Data Processing & Analysis
- **MongoDB** – NoSQL database for semi-structured data storage.
- **MySQL** – Relational database for structured data storage.
- **Neo4J** – Graph database for relationships and graph analysis.
### 🧑‍🤝‍🧑 Graph & Visualization
- **NetworkX** – Library for graph creation and analysis.
- **Matplotlib** – Used for visualizing data and graphs.

## 🙌 Credits

This project was developed as part of a **Database and Machine Learning course** at **Universidad Pontificia Comillas, ICAI**.

### 🎓 Special Thanks To:
- **Professors and mentors** for their guidance.
- **Universidad Pontificia Comillas, ICAI** for an excellent learning environment.
- **Open-source contributors** whose work made this possible.

### 👨‍💻 Developers:
- **Ignacio Queipo de Llano Pérez-Gascón**
- **Beltrán Sánchez Careaga**

We extend our gratitude to all **open-source projects** that contributed to the development of **AmazonReviewsAnalysis**. 🚀
