from db.connection import Mysql

def recommend_products(product_id: int):
    db = Mysql()

    result = db.fetchone(
        "SELECT category FROM products WHERE product_id = %s",
        (product_id,)
    )

    if not result:
        return []

    category = result[0]

    rows = db.fetchall(
        """
        SELECT product_id 
        FROM products 
        WHERE category = %s AND product_id != %s
        LIMIT 5
        """,
        (category, product_id)
    )

    return [r[0] for r in rows]