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

@app.route("/all_films")
def all_films():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(queries.all_films_query, (limit, offset))
    rows = cursor.fetchall()

    cursor.execute(queries.all_films_count_query)
    total = cursor.fetchone()["total"]

    conn.close()

    return jsonify({
        "data": rows,
        "page": page,
        "limit": limit,
        "total": total
    })

@app.route("/rent_film", methods=["POST"])
def rent_film():
    data = request.get_json()
    customer_id = data.get("customer_id")
    film_id = data.get("film_id")

    if not customer_id or not film_id:
        return jsonify({"error": "customer_id and film_id are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()
    if not customer:
        conn.close()
        return jsonify({"error": "Invalid Customer ID"}), 400

    cursor.execute(queries.fetch_inventory_copy, (film_id,))
    inventory = cursor.fetchone()

    if not inventory:
        conn.close()
        return jsonify({"error": "No available copies for this film"}), 400

    inventory_id = inventory["inventory_id"]

    cursor.execute(queries.insert_new_rental, (inventory_id, customer_id))
    conn.commit()

    # Fetch updated inventory info
    cursor.execute(queries.fetch_inventory_count, (film_id,))
    updated = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "film_id": film_id,
        "available": updated["available"],
        "rented": updated["rented"],
        "inventory_count": updated["inventory_count"]
    })

if __name__ == "__main__":
    app.run(debug=True)
