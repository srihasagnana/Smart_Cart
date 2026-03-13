from db.connection import Mysql

def create_table():
    db=Mysql()
    db.execute("""
        create table if not exists products(
            product_id integer primary key auto_increment,
            product_name varchar(255) not null,
            product_description varchar(255) not null,
            category varchar(255) not null,
            price decimal(10,2) not null,
            qty integer not null,
            weight decimal(10,5) not null,
            created_at timestamp default current_timestamp
        )
    """)

def init_all():
    create_table()