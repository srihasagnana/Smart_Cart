# save as debug_user_cart.py
import requests
from db.connection import Mysql

BASE_URL = "http://127.0.0.1:8000"

print("=" * 50)
print("CHECKING ALL USERS AND THEIR CARTS")
print("=" * 50)

# Query database directly
db = Mysql()

# Get all users
users = db.fetchall("SELECT user_id, name, phone FROM users")
print(f"\nFound {len(users)} users:")
for user in users:
    user_id = user[0]
    name = user[1]
    phone = user[2]

    # Get cart items for this user from database
    cart_items = db.fetchall("""
        SELECT c.cart_id, p.product_name, c.qty, c.weight 
        FROM cart c
        JOIN products p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    # Calculate total weight
    total_weight = 0
    for item in cart_items:
        weight = float(item[3]) if item[3] else 0
        qty = int(item[2]) if item[2] else 0
        total_weight += weight * qty

    print(f"\n📱 User ID: {user_id}")
    print(f"   Name: {name}")
    print(f"   Phone: {phone}")
    print(f"   Items in cart: {len(cart_items)}")
    print(f"   Total weight in cart: {total_weight:.1f}g")

    if cart_items:
        print("   Cart details:")
        for item in cart_items:
            print(f"     - {item[1]}: Qty={item[2]}, Weight={item[3]}g")

# Also check if there are any orphaned cart items
orphaned = db.fetchall("""
    SELECT c.* FROM cart c
    LEFT JOIN users u ON c.user_id = u.user_id
    WHERE u.user_id IS NULL
""")
if orphaned:
    print(f"\n⚠️ Found {len(orphaned)} orphaned cart items (user deleted):")
    for item in orphaned:
        print(f"   Cart ID: {item[0]}, User ID: {item[1]}, Product: {item[2]}, Qty: {item[3]}, Weight: {item[4]}")

db.close()

# Also test the API endpoints
print("\n" + "=" * 50)
print("TESTING API ENDPOINTS")
print("=" * 50)

# Try to get cart for a specific user (user_id=1)
test_user_id = 1
print(f"\nTesting API for user_id={test_user_id}:")
try:
    response = requests.get(f"{BASE_URL}/cart", params={"user_id": test_user_id}, timeout=3)
    print(f"GET /cart - Status: {response.status_code}")
    if response.status_code == 200:
        cart = response.json()
        print(f"  Cart data: {cart}")
        print(f"  Cart type: {type(cart)}")
        print(f"  Items count: {len(cart) if cart else 0}")
except Exception as e:
    print(f"  Error: {e}")

try:
    response = requests.get(f"{BASE_URL}/cart/total-weight", params={"user_id": test_user_id}, timeout=3)
    print(f"GET /cart/total-weight - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  Total weight: {response.json()}")
except Exception as e:
    print(f"  Error: {e}")