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
    query = queries.top5movies_query
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/top5_actors")
def top5_actors():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = queries.top5actors_query
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/movies_by_genre/<genre>")
def movies_by_genre(genre):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = queries.moviesbygenre_query
    cursor.execute(query, (genre,))
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/actors")
def actors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = queries.actors_query
    cursor.execute(query) 
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/users")
def users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = queries.users_query
    cursor.execute(query) 
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True)
