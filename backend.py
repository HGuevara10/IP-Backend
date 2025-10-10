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

# ------------------------------
# 🔹 MOVIES & ACTORS ENDPOINTS
# ------------------------------
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

# ------------------------------
# 🔹 FILMS PAGE
# ------------------------------

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

# ------------------------------
# 🔹 RENT FILM
# ------------------------------
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

# ------------------------------
# 🔹 USERS / CUSTOMERS MANAGEMENT
# ------------------------------
@app.route("/users", methods=["GET"])
def get_users():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    search = request.args.get("search", "")
    offset = (page - 1) * limit

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if search:
        cur.execute("""
            SELECT c.customer_id, c.first_name, c.last_name, c.email,
                   COUNT(r.rental_id) AS count
            FROM customer c
            LEFT JOIN rental r ON c.customer_id = r.customer_id
            WHERE CONCAT(c.first_name, ' ', c.last_name) LIKE %s
               OR c.first_name LIKE %s OR c.last_name LIKE %s OR c.customer_id LIKE %s
            GROUP BY c.customer_id
            ORDER BY c.customer_id
            LIMIT %s OFFSET %s
        """, (
            f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%", limit, offset
        ))
    else:
        cur.execute("""
            SELECT c.customer_id, c.first_name, c.last_name, c.email,
                   COUNT(r.rental_id) AS count
            FROM customer c
            LEFT JOIN rental r ON c.customer_id = r.customer_id
            GROUP BY c.customer_id
            ORDER BY c.customer_id
            LIMIT %s OFFSET %s
        """, (limit, offset))

    users = cur.fetchall()
    cur.execute("SELECT COUNT(*) AS total FROM customer")
    total = cur.fetchone()["total"]

    cur.close()
    conn.close()
    return jsonify({"data": users, "total": total, "page": page})

@app.route("/users/<int:customer_id>", methods=["PUT"])
def update_user(customer_id):
    data = request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE customer
        SET first_name = %s, last_name = %s, email = %s
        WHERE customer_id = %s
    """, (first_name, last_name, email, customer_id))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Customer updated successfully"}), 200


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



@app.route("/edit-customer/<int:customer_id>", methods=["PUT"])
def edit_customer(customer_id):
    data = request.get_json()
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE customer
        SET first_name = %s, last_name = %s, email = %s, last_update = NOW()
        WHERE customer_id = %s
    """, (first_name, last_name, email, customer_id))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Customer updated successfully"})

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

@app.route("/users/<int:customer_id>/details", methods=["GET"])
def get_customer_details(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT customer_id, first_name, last_name, email, active, create_date, last_update
        FROM customer
        WHERE customer_id = %s
    """, (customer_id,))
    customer = cursor.fetchone()

    if not customer:
        conn.close()
        return jsonify({"error": "Customer not found"}), 404

    cursor.execute("""
        SELECT 
            r.rental_id,
            f.title AS film_title,
            r.rental_date,
            r.return_date,
            s.store_id
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        JOIN film f ON i.film_id = f.film_id
        JOIN store s ON i.store_id = s.store_id
        WHERE r.customer_id = %s
        ORDER BY r.rental_date DESC
    """, (customer_id,))

    rentals = cursor.fetchall()

    conn.close()

    return jsonify({
        "customer": customer,
        "rental_history": rentals
    })

@app.route("/return_rental/<int:rental_id>", methods=["POST"])
def return_rental(rental_id):
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT return_date FROM rental WHERE rental_id = %s", (rental_id,))
    rental = cur.fetchone()
    if not rental:
        conn.close()
        return jsonify({"error": "Rental not found"}), 404
    if rental["return_date"] is not None:
        conn.close()
        return jsonify({"error": "Rental already returned"}), 400

    cur.execute(
        "UPDATE rental SET return_date = NOW() WHERE rental_id = %s",
        (rental_id,)
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"success": True, "rental_id": rental_id})


if __name__ == "__main__":
    app.run(debug=True)
