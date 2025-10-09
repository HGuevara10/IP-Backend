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
    search = request.args.get("search", "").strip().lower()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search:
        cursor.execute(
            queries.search_users_query,
            (
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                f"%{search}%",
                limit,
                offset,
            ),
        )
        rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) AS total FROM customer;")
        total = cursor.fetchone()["total"]
    else:
        cursor.execute(queries.users_query, (limit, offset))
        rows = cursor.fetchall()

        cursor.execute(queries.users_count_query)
        total = cursor.fetchone()["total"]

    conn.close()

    return jsonify({
        "data": rows,
        "page": page,
        "limit": limit,
        "total": total
    })  


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

@app.route('/films', methods=['GET'])
def get_films():
    search = request.args.get('search', '').strip().lower()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if search:
        cursor.execute(queries.search_film_actor_or_genre, (
            f"%{search}%", 
            f"%{search}%", 
            f"%{search}%", 
            f"%{search}%",
            f"%{search}%"
        ))
        films = cursor.fetchall()
        total = len(films)
    else:
        cursor.execute(queries.all_films_query, (limit, offset))
        films = cursor.fetchall()
        cursor.execute(queries.all_films_count_query)
        total = cursor.fetchone()["total"]

    conn.close()

    return jsonify({
        "data": films,
        "page": page,
        "total": total
    })

@app.route("/add_customer", methods=["POST"])
def add_customer():
    data = request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")

    if not first_name or not last_name or not email:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            INSERT INTO customer (store_id, first_name, last_name, email, address_id, active, create_date, last_update)
            VALUES (1, %s, %s, %s, 5, 1, NULL, NULL)
        """, (first_name, last_name, email))
        conn.commit()

        new_id = cursor.lastrowid

        cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (new_id,))
        new_customer = cursor.fetchone()

        return jsonify({
            "success": True,
            "customer": new_customer
        }), 201

    except Exception as e:
        print("Error adding customer:", e)
        conn.rollback()
        return jsonify({"error": "Failed to add customer"}), 500

    finally:
        cursor.close()
        conn.close()


@app.route("/customers", methods=["GET"])
def get_customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customer")
    customers = cursor.fetchall()
    conn.close()
    return jsonify(customers)


@app.route("/delete_customer", methods=["POST"])
def delete_customer():
    data = request.get_json()
    try:
        customer_id = int(data.get("customer_id"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid customer_id"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (customer_id,))
    customer = cursor.fetchone()
    if not customer:
        cursor.close()
        conn.close()
        return jsonify({"error": "Customer not found"}), 404

    try:
        cursor.execute("DELETE FROM customer WHERE customer_id = %s", (customer_id,))
        conn.commit()
    except Exception as e:
        print("Error deleting customer:", e)
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": "Failed to delete customer. Check foreign key constraints."}), 500

    cursor.close()
    conn.close()
    return jsonify({"success": True, "customer_id": customer_id})


if __name__ == "__main__":
    app.run(debug=True)
