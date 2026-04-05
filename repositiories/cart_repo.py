class CartRepo:
    def __init__(self, db):
        self.db = db

    def add_to_cart(self, user_id, product_id, qty):
        existing = self.db.fetchone(
            "SELECT qty FROM cart WHERE user_id=%s AND product_id=%s",
            (user_id, product_id)
        )

        if existing:
            new_qty = existing[0] + qty

            self.db.execute(
                "UPDATE cart SET qty = %s WHERE user_id=%s AND product_id=%s",
                (new_qty, user_id, product_id),
                commit=True
            )
        else:
            self.db.execute(
                "INSERT INTO cart(user_id, product_id, qty) VALUES (%s,%s,%s)",
                (user_id, product_id, qty),
                commit=True
            )

    def get_cart(self, user_id):
       
        rows = self.db.fetchall("""
            SELECT 
                c.cart_id,
                c.product_id,
                p.product_name,
                c.qty,
                p.price,
                p.weight
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = %s
        """, (user_id,))

        return [
            {
                "cart_id": r[0],
                "product_id": r[1],
                "product_name": r[2],
                "qty": r[3],
                "price": r[4],
                "weight":r[5]
            }
            for r in rows
        ]

    def delete_cart_item(self, cart_id):
        self.db.execute(
            "DELETE FROM cart WHERE cart_id = %s",
            (cart_id,),
            commit=True
        )