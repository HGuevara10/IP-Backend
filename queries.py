top5movies_query = '''
    SELECT
        f.film_id,
        f.title,
        f.release_year,
        f.rating,
        f.description,
        c.name AS category,
        COUNT(r.rental_id) AS rented
    FROM film f
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    JOIN inventory i ON f.film_id = i.film_id
    JOIN rental r ON i.inventory_id = r.inventory_id
    GROUP BY f.film_id, f.title, f.release_year, f.rating, f.description, c.name
    ORDER BY rented DESC
    LIMIT 5;
'''

top5actors_list_query = '''
    SELECT 
        a.actor_id,
        a.first_name,
        a.last_name,
        COUNT(fa.film_id) AS movie_count
    FROM actor a
    JOIN film_actor fa ON a.actor_id = fa.actor_id
    GROUP BY a.actor_id, a.first_name, a.last_name
    ORDER BY movie_count DESC
    LIMIT 5;
'''

top5actors_query = '''
    SELECT f.film_id, f.title, COUNT(r.rental_id) AS rental_count
    FROM film f
    JOIN film_actor fa ON f.film_id = fa.film_id
    JOIN inventory i ON f.film_id = i.film_id
    JOIN rental r ON i.inventory_id = r.inventory_id
    WHERE fa.actor_id = %s
    GROUP BY f.film_id, f.title
    ORDER BY rental_count DESC
    LIMIT 5;
'''

moviesbygenre_query = '''
    SELECT f.title
    FROM film f
    JOIN film_category fc ON f.film_id = fc.film_id
    JOIN category c ON fc.category_id = c.category_id
    WHERE c.name = %s;
'''

actors_query = '''
    SELECT 
        a.actor_id,
        a.first_name,
        a.last_name,
        COUNT(fa.film_id) AS movie_count
    FROM actor a
    JOIN film_actor fa ON a.actor_id = fa.actor_id
    GROUP BY a.actor_id, a.first_name, a.last_name
    ORDER BY movie_count DESC;
'''

users_query = '''
    SELECT 
        c.customer_id,
        c.first_name,
        c.last_name,
        COUNT(r.rental_id) AS count
    FROM rental r
    JOIN customer c ON r.customer_id = c.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name
    ORDER BY count DESC;
'''
