from db.connection import Mysql

def create_products_table():
    db = Mysql()
    db.execute("""
        CREATE TABLE IF NOT EXISTS products(
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            product_description VARCHAR(255),
            category VARCHAR(100),
            price DECIMAL(10,2) NOT NULL,
            qty INT NOT NULL,
            weight DECIMAL(10,5),
            min_weight DECIMAL(10,5),
            max_weight DECIMAL(10,5),
            barcode VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,commit=True)


def create_users_table():
    db = Mysql()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            phone VARCHAR(20) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def create_cart_table():
    db = Mysql()
    db.execute("""
        CREATE TABLE IF NOT EXISTS cart(
            cart_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            product_id INT NOT NULL,
            qty INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            weight DECIMAL(10,2) NOT NULL,
            UNIQUE (user_id, product_id),

            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        )
    """)


def create_orders_table():
    db = Mysql()
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders(
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)


def create_order_items_table():
    db = Mysql()
    db.execute("""
        CREATE TABLE IF NOT EXISTS order_items(
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            qty INT NOT NULL,
            price DECIMAL(10,2) NOT NULL,

            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        )
    """)


def init_all():
    create_products_table()
    create_users_table()
    create_cart_table()
    create_orders_table()
    create_order_items_table()