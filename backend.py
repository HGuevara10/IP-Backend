from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app) 

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",          
        password="Imapilot10$#", 
        database="sakila"  
    )
    return conn

@app.route("/data", methods=["GET"])
def get_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        select 
        f.film_id,
        f.title,
        c.name AS category_name
        from film f
        join film_category fc ON f.film_id = fc.film_id
        join category c ON fc.category_id = c.category_id;

    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/add", methods=["POST"])
def add_item():
    data = request.json
    value = data.get("value")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO yourtable (column_name) VALUES (%s)", (value,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "value": value})

if __name__ == "__main__":
    app.run(debug=True)
