from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import queries

app = Flask(__name__)
CORS(app)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",          
        password="Imapilot10$#", 
        database="sakila"
    )

@app.route("/top5_movies")
def top5_movies():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(queries.top5movies_query)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/top5_actors")
def top5_actors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(queries.top5actors_list_query)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/actor_top_movies/<int:actor_id>")
def actor_top_movies(actor_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(queries.top5actors_query, (actor_id,))
    result = cursor.fetchall()
    conn.close()
    return jsonify(result)

@app.route("/movies_by_genre/<genre>")
def movies_by_genre(genre):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(queries.moviesbygenre_query, (genre,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/actors")
def actors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(queries.actors_query)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/users")
def users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(queries.users_query)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True)
