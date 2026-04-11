import streamlit as st
import requests
import pandas as pd
import time
from collections import deque
import json

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Smart Shopping Cart",
    page_icon="🛒",
    layout="wide"
)


# Fast weight reading
def get_weight_instant():
    """Get weight instantly"""
    try:
        response = requests.get(f"{BASE_URL}/weight", timeout=0.3)
        if response.status_code == 200:
            return response.json().get("weight", 0)
    except:
        pass
    return 0


def get_stable_weight_for_calibration():
    try:
        response = requests.get(f"{BASE_URL}/weight/stable", timeout=1.0)
        if response.status_code == 200:
            result = response.json()
            if "weight" in result:
                return result["weight"]
    except Exception as e:
        print(f"Error: {e}")
    return 0


def check_weight_match(product_id, measured_weight):
    try:
        response = requests.post(
            f"{BASE_URL}/check-weight",
            params={"product_id": product_id, "weight": measured_weight},
            timeout=2
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error: {e}")
    return {"status": "error"}


# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "last_weight" not in st.session_state:
    st.session_state.last_weight = 0.0
if "weight_readings" not in st.session_state:
    st.session_state.weight_readings = deque(maxlen=5)
if "item_added" not in st.session_state:
    st.session_state.item_added = False
if "scan_complete" not in st.session_state:
    st.session_state.scan_complete = False
if "last_barcode" not in st.session_state:
    st.session_state.last_barcode = ""
if "calibration_weights" not in st.session_state:
    st.session_state.calibration_weights = []
if "manual_refresh" not in st.session_state:
    st.session_state.manual_refresh = False

role = st.sidebar.selectbox("Select Role", ["Admin", "User"])

if role == "Admin":
    st.title("🛒 Admin Panel")

    tab1, tab2 = st.tabs(["Add Product", "Manage Products"])

    with tab1:
        st.header("Add New Product")

        col1, col2 = st.columns(2)
        with col1:
            product_name = st.text_input("Product Name", key="prod_name")
            category = st.text_input("Category", key="category")
            price = st.number_input("Price (₹)", min_value=0.0, step=10.0, key="price")
        with col2:
            qty = st.number_input("Quantity", min_value=1, step=1, key="qty")
            barcode = st.text_input("Barcode", key="barcode")
            product_description = st.text_area("Description", key="description")

        st.markdown("---")
        st.subheader("⚖️ Calibrate Weight")
        st.write("Place the product on the scale and click 'Capture Weight'")

        if st.button("📡 Capture Weight", use_container_width=True):
            with st.spinner("Measuring weight... Please hold the item still..."):
                weights = []
                for i in range(10):
                    weight = get_stable_weight_for_calibration()
                    if weight > 0:
                        weights.append(weight)
                    time.sleep(0.2)

                if weights:
                    st.session_state.calibration_weights = weights
                    st.success(f"✅ Captured {len(weights)} readings!")
                    st.write(f"**Average Weight:** {sum(weights) / len(weights):.1f} g")
                    st.write("**Readings:**", [f"{w:.1f}g" for w in weights])
                else:
                    st.error("❌ Failed to capture weight. Please check scale connection.")

        if st.button("✅ Save Product", type="primary", use_container_width=True):
            missing_fields = []
            if not product_name:
                missing_fields.append("Product Name")
            if not category:
                missing_fields.append("Category")
            if price <= 0:
                missing_fields.append("Price")
            if qty <= 0:
                missing_fields.append("Quantity")
            if not barcode:
                missing_fields.append("Barcode")
            if not st.session_state.calibration_weights:
                missing_fields.append("Weight calibration")

            if missing_fields:
                st.error(f"Please fill in: {', '.join(missing_fields)}")
            else:
                data = {
                    "product_name": product_name,
                    "product_description": product_description,
                    "category": category,
                    "price": price,
                    "qty": qty,
                    "weights": st.session_state.calibration_weights,
                    "barcode": barcode
                }

                try:
                    response = requests.post(f"{BASE_URL}/product", json=data, timeout=5)
                    if response.status_code == 200:
                        st.success(f"✅ Product '{product_name}' added successfully!")
                        st.balloons()
                        st.session_state.calibration_weights = []
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Failed to add product: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

    with tab2:
        st.header("Manage Products")

        try:
            response = requests.get(f"{BASE_URL}/products", timeout=3)
            if response.status_code == 200:
                products = response.json()
                if products:
                    df = pd.DataFrame(products)
                    st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

        st.markdown("---")
        st.subheader("Update Product Quantity")

        product_id = st.number_input("Product ID", min_value=1, step=1, key="update_id")
        new_qty = st.number_input("New Quantity", min_value=0, step=1, key="new_qty")

        if st.button("Update Quantity", use_container_width=True):
            try:
                response = requests.put(
                    f"{BASE_URL}/product/{product_id}/quantity",
                    params={"qty": new_qty},
                    timeout=3
                )
                if response.status_code == 200:
                    st.success(f"✅ Product {product_id} quantity updated to {new_qty}!")
                else:
                    st.error(f"Failed to update: {response.text}")
            except Exception as e:
                st.error(f"Error: {e}")

else:  # User role
    st.title("🛒 Smart Shopping Cart")

    # User login
    if st.session_state.user_id is None:
        st.header("👤 Welcome! Please Identify Yourself")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name", key="user_name")
        with col2:
            phone = st.text_input("Phone Number", key="user_phone")

        if st.button("Start Shopping", type="primary", use_container_width=True):
            if name and phone:
                try:
                    response = requests.post(
                        f"{BASE_URL}/user/create",
                        params={"name": name, "phone": phone},
                        timeout=3
                    )
                    if response.status_code == 200:
                        st.session_state.user_id = response.json()["user_id"]
                        st.success(f"Welcome {name}! 🎉")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter both name and phone number")
        st.stop()

    # Navigation
    page = st.radio("Navigation", ["🛍️ Shop", "📦 Cart", "📜 Orders"], horizontal=True)

    if page == "🛍️ Shop":
        st.header("Add Items to Cart")
        st.info(
            "💡 **How to use:** Scan barcode, then place the NEW item on the scale (without removing existing items). The system will detect the weight change and add the item if it matches.")

        # Get current cart total weight
        try:
            cart_weight_response = requests.get(f"{BASE_URL}/cart/total-weight",
                                                params={"user_id": st.session_state.user_id}, timeout=3)
            if cart_weight_response.status_code == 200:
                cart_total_weight = cart_weight_response.json().get("total_weight", 0)
            else:
                cart_total_weight = 0
        except:
            cart_total_weight = 0

        # Display current cart info
        with st.expander("📊 Current Cart Status", expanded=False):
            st.metric("Total Weight in Cart", f"{cart_total_weight:.1f} g")
            st.info(
                "💡 When adding a new item, place it on the scale WITH existing items. The system will calculate the weight difference.")

        # Barcode input
        barcode = st.text_input("Scan Barcode", key="barcode_input")

        # Reset state when barcode changes
        if barcode and barcode != st.session_state.get("last_barcode", ""):
            st.session_state.last_barcode = barcode
            st.session_state.item_added = False
            st.session_state.scan_complete = False
            st.session_state.weight_readings.clear()
            st.session_state.last_stable_weight = cart_total_weight
            st.session_state.reading_count = 0

        if barcode:
            try:
                response = requests.get(f"{BASE_URL}/product/barcode/{barcode}", timeout=3)
                if response.status_code == 200 and response.json():
                    product = response.json()

                    if "error" not in product:
                        st.success(f"✅ Product Found: {product['product_name']}")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Price", f"₹{product['price']}")
                        with col2:
                            expected_wt = product.get('weight', 0)
                            st.metric("Expected Weight", f"{expected_wt:.1f} g")
                        with col3:
                            qty = st.number_input("Quantity", min_value=1, value=1, step=1, key="qty_input")

                        st.markdown("---")
                        st.subheader("⚖️ Place NEW Item on Scale")
                        st.caption(
                            f"Current cart weight: {cart_total_weight:.1f}g. Place the new item on the scale (don't remove existing items)")

                        # Manual refresh button
                        if st.button("🔄 Start Measuring", key="start_measure"):
                            st.session_state.scan_complete = False
                            st.session_state.weight_readings.clear()
                            st.session_state.reading_count = 0
                            st.rerun()

                        # Check if item already added
                        if st.session_state.item_added:
                            st.success(f"✅ {product['product_name']} already added to cart!")
                            if st.button("🔄 Scan Another Item", key="next_item"):
                                st.session_state.item_added = False
                                st.session_state.scan_complete = False
                                st.session_state.weight_readings.clear()
                                st.session_state.reading_count = 0
                                st.rerun()
                        else:
                            # Take a new weight reading
                            if st.session_state.reading_count is None:
                                st.session_state.reading_count = 0

                            if st.session_state.reading_count < 5 and not st.session_state.scan_complete:
                                # Get fresh weight reading
                                current_total_weight = get_weight_instant()

                                if current_total_weight > 0:
                                    # Calculate weight difference
                                    weight_difference = current_total_weight - cart_total_weight

                                    # Display current readings
                                    st.metric("Total Weight on Scale", f"{current_total_weight:.1f} g")
                                    st.metric("Weight Difference (New Item)", f"{weight_difference:.1f} g",
                                              delta=f"Expected: {expected_wt:.1f}g")

                                    # Add to readings
                                    if weight_difference > 1:
                                        st.session_state.weight_readings.append(weight_difference)
                                        st.session_state.reading_count += 1

                                        # Show progress
                                        st.progress(st.session_state.reading_count / 5,
                                                    text=f"Reading {st.session_state.reading_count}/5: {weight_difference:.1f}g")

                                        # Auto-refresh for next reading
                                        time.sleep(0.5)
                                        st.rerun()
                                else:
                                    st.warning("No weight detected - check scale connection")
                                    time.sleep(0.5)
                                    st.rerun()

                            # After collecting 5 readings, verify
                            elif st.session_state.reading_count >= 5 and not st.session_state.scan_complete:
                                st.session_state.scan_complete = True

                                # Calculate average of readings
                                readings_list = list(st.session_state.weight_readings)
                                avg_difference = sum(readings_list) / len(readings_list)

                                st.write("---")
                                st.subheader("📊 Measurement Results")
                                st.write(f"**Readings:** {', '.join([f'{w:.1f}g' for w in readings_list])}")
                                st.write(f"**Average Weight:** {avg_difference:.1f} g")

                                # Check stability
                                is_stable = all(abs(w - avg_difference) < 5 for w in readings_list)

                                if not is_stable:
                                    st.warning("⚠️ Readings were not stable. Please try again.")
                                    if st.button("🔄 Try Again", key="retry_unstable"):
                                        st.session_state.scan_complete = False
                                        st.session_state.weight_readings.clear()
                                        st.session_state.reading_count = 0
                                        st.rerun()
                                else:
                                    with st.spinner(f"Verifying weight: {avg_difference:.1f}g..."):
                                        # Check weight against database
                                        check_result = check_weight_match(product["product_id"], avg_difference)

                                        if check_result.get("status") == "valid":
                                            # Add to cart
                                            add_response = requests.post(
                                                f"{BASE_URL}/cart",
                                                params={
                                                    "user_id": st.session_state.user_id,
                                                    "product_id": product["product_id"],
                                                    "qty": qty,
                                                    "weight": avg_difference
                                                },
                                                timeout=3
                                            )

                                            if add_response.status_code == 200:
                                                result = add_response.json()
                                                if result.get("error") == "INVALID_WEIGHT":
                                                    st.error(f"❌ {result.get('message', 'Weight mismatch!')}")
                                                    if st.button("🔄 Try Again", key="retry_invalid"):
                                                        st.session_state.scan_complete = False
                                                        st.session_state.weight_readings.clear()
                                                        st.session_state.reading_count = 0
                                                        st.rerun()
                                                else:
                                                    st.success(f"✅ {product['product_name']} added to cart!")
                                                    st.session_state.item_added = True
                                                    st.balloons()
                                                    time.sleep(2)
                                                    st.rerun()
                                            else:
                                                st.error("Failed to add to cart")
                                        else:
                                            expected = product.get('weight', 0)
                                            diff = abs(avg_difference - expected)
                                            diff_percent = (diff / expected) * 100 if expected > 0 else 0

                                            st.error(
                                                f"❌ Weight verification failed!\n\n"
                                                f"📦 Product: {product['product_name']}\n"
                                                f"⚖️ Expected: {expected:.1f}g\n"
                                                f"📊 Measured (difference): {avg_difference:.1f}g\n"
                                                f"📈 Difference: {diff:.1f}g ({diff_percent:.1f}%)\n"
                                                f"✅ Allowed: {product.get('min_weight', 0):.1f}g - {product.get('max_weight', 0):.1f}g\n\n"
                                                f"💡 Make sure you placed the CORRECT item on the scale."
                                            )

                                            col_btn1, col_btn2 = st.columns(2)
                                            with col_btn1:
                                                if st.button("🔄 Try Again", key="retry_failed"):
                                                    st.session_state.scan_complete = False
                                                    st.session_state.weight_readings.clear()
                                                    st.session_state.reading_count = 0
                                                    st.rerun()

                                            with col_btn2:
                                                if st.button("➕ Add Manually", key="manual"):
                                                    add_response = requests.post(
                                                        f"{BASE_URL}/cart",
                                                        params={
                                                            "user_id": st.session_state.user_id,
                                                            "product_id": product["product_id"],
                                                            "qty": qty,
                                                            "weight": avg_difference
                                                        },
                                                        timeout=3
                                                    )
                                                    if add_response.status_code == 200:
                                                        st.success("Item added manually!")
                                                        st.session_state.item_added = True
                                                        time.sleep(1)
                                                        st.rerun()
                    else:
                        st.error("Product not found")
                else:
                    st.error("Product not found")
            except Exception as e:
                st.error(f"Error: {e}")

        # Show all products button
        with st.expander("📋 Browse All Products"):
            if st.button("Show Products"):
                try:
                    response = requests.get(f"{BASE_URL}/products", timeout=3)
                    if response.status_code == 200:
                        products = response.json()
                        if products:
                            df = pd.DataFrame(products)
                            st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")


    elif page == "📦 Cart":

        st.header("Your Shopping Cart")

        try:

            response = requests.get(f"{BASE_URL}/cart", params={"user_id": st.session_state.user_id}, timeout=3)

            if response.status_code == 200:

                cart = response.json()

                if cart:

                    # Display cart as editable table with delete buttons

                    st.subheader("Cart Items")

                    # Create columns for header

                    col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])

                    with col1:

                        st.write("**Product**")

                    with col2:

                        st.write("**Quantity**")

                    with col3:

                        st.write("**Price**")

                    with col4:

                        st.write("**Total**")

                    with col5:

                        st.write("**Action**")

                    st.markdown("---")

                    total_amount = 0

                    total_weight = 0

                    # Display each cart item with delete button

                    for idx, item in enumerate(cart):

                        col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])

                        with col1:

                            st.write(f"**{item['product_name']}**")

                        with col2:

                            # Allow quantity update

                            new_qty = st.number_input(

                                "Qty",

                                min_value=1,

                                max_value=100,

                                value=item['qty'],

                                key=f"qty_{item['cart_id']}",

                                label_visibility="collapsed"

                            )

                            # If quantity changed, update cart

                            if new_qty != item['qty']:

                                # Remove old item and add with new quantity

                                delete_response = requests.delete(

                                    f"{BASE_URL}/cart/{item['cart_id']}",

                                    timeout=3

                                )

                                if delete_response.status_code == 200:

                                    add_response = requests.post(

                                        f"{BASE_URL}/cart",

                                        params={

                                            "user_id": st.session_state.user_id,

                                            "product_id": item['product_id'],

                                            "qty": new_qty,

                                            "weight": item.get('weight', 0)

                                        },

                                        timeout=3

                                    )

                                    if add_response.status_code == 200:
                                        st.success(f"Updated {item['product_name']} quantity to {new_qty}")

                                        time.sleep(0.5)

                                        st.rerun()

                        with col3:

                            st.write(f"₹{item['price']:.2f}")

                        with col4:

                            item_total = item['qty'] * item['price']

                            total_amount += item_total

                            total_weight += item.get('weight', 0) * item['qty']

                            st.write(f"₹{item_total:.2f}")

                        with col5:

                            # Delete button

                            if st.button("🗑️ Delete", key=f"del_{item['cart_id']}"):

                                with st.spinner(f"Removing {item['product_name']}..."):

                                    delete_response = requests.delete(

                                        f"{BASE_URL}/cart/{item['cart_id']}",

                                        timeout=3

                                    )

                                    if delete_response.status_code == 200:

                                        result = delete_response.json()

                                        # Check if barcode scan is required

                                        if result.get("error") == "SCAN_REQUIRED":

                                            st.warning(
                                                "⚠️ Multiple items with same weight. Please scan the barcode to confirm removal.")

                                            scan_barcode = st.text_input("Scan Barcode to Remove",
                                                                         key=f"scan_{item['cart_id']}")

                                            if scan_barcode:

                                                confirm_response = requests.delete(

                                                    f"{BASE_URL}/cart/{item['cart_id']}",

                                                    params={"barcode": scan_barcode},

                                                    timeout=3

                                                )

                                                if confirm_response.status_code == 200:

                                                    st.success(f"✅ {item['product_name']} removed from cart!")

                                                    # Update the total weight in session state

                                                    st.session_state.last_weight = max(0,
                                                                                       st.session_state.last_weight - item.get(
                                                                                           'weight', 0))

                                                    time.sleep(1)

                                                    st.rerun()

                                                else:

                                                    st.error("❌ Wrong barcode. Item not removed.")

                                        else:

                                            st.success(f"✅ {item['product_name']} removed from cart!")

                                            # Update the total weight in session state

                                            st.session_state.last_weight = max(0,
                                                                               st.session_state.last_weight - item.get(
                                                                                   'weight', 0))

                                            time.sleep(1)

                                            st.rerun()

                                    else:

                                        st.error("Failed to remove item")

                    st.markdown("---")

                    # Display totals

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.metric("Total Items", len(cart))

                    with col2:

                        st.metric("Total Weight", f"{total_weight:.1f} g")

                    with col3:

                        st.metric("Total Amount", f"₹{total_amount:.2f}")

                    st.markdown("---")

                    # Clear cart button

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button("🗑️ Clear Entire Cart", use_container_width=True):

                            for item in cart:
                                requests.delete(f"{BASE_URL}/cart/{item['cart_id']}", timeout=3)

                            st.session_state.last_weight = 0

                            st.session_state.weight_readings.clear()

                            st.success("Cart cleared!")

                            time.sleep(1)

                            st.rerun()

                    with col2:

                        if st.button("✅ Proceed to Checkout", type="primary", use_container_width=True):

                            response = requests.post(

                                f"{BASE_URL}/checkout",

                                params={"user_id": st.session_state.user_id, "payment_method": "cash"},

                                timeout=3

                            )

                            if response.status_code == 200:
                                st.success("Order placed successfully!")

                                st.session_state.item_added = False

                                st.session_state.weight_readings.clear()

                                st.session_state.last_weight = 0

                                time.sleep(1)

                                st.rerun()

                else:

                    st.info("🛒 Your cart is empty")

                    # Reset weight when cart is empty

                    if st.session_state.last_weight != 0:
                        st.session_state.last_weight = 0


        except Exception as e:

            st.error(f"Error fetching cart: {e}")