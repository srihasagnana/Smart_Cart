# fix_database.py - Run this once to fix your database
from db.connection import Mysql

db = Mysql()

# Move all cart items from User 1 to User 16
db.execute("UPDATE cart SET user_id = 16 WHERE user_id = 1", commit=True)

# Delete old User 1
db.execute("DELETE FROM users WHERE user_id = 1", commit=True)

print("✅ Database fixed!")
print("   - Moved cart items to User 16")
print("   - Deleted old User 1")
print("\nNow login with phone number: 1234567890")

db.close()