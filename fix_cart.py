from db.connection import Mysql

db = Mysql()

# Move all items from User 1 to User 16
db.execute("UPDATE cart SET user_id = 16 WHERE user_id = 1", commit=True)

print("✅ Done! Cart items moved to your current user")

# Verify
items = db.fetchall("SELECT user_id, product_id, qty, weight FROM cart")
print("\nCart items now:")
for item in items:
    print(f"  User ID: {item[0]}, Product: {item[1]}, Qty: {item[2]}, Weight: {item[3]}")

db.close()