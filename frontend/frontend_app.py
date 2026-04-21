import streamlit as st
import requests
import pandas as pd
import time
from collections import deque
import statistics

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Smart Shopping Cart",
    page_icon="🛒",
    layout="wide"
)

# ============================
# RECEIPT DISPLAY
# ============================

query_params = st.query_params
receipt_id = query_params.get("receipt_id", None)

# Handle receipt_id from URL (after Razorpay redirect)
if receipt_id:
    st.session_state.last_order_id = receipt_id
    st.session_state.payment_success = True
    st.session_state.show_receipt_page = True
    st.session_state.page = "RECEIPT"
    # Clear the query parameter to avoid showing receipt again on refresh
    st.query_params.clear()
    st.rerun()

from gtts import gTTS
import base64


def speak_warning(text):
    tts = gTTS(text)
    file_path = "warning.mp3"
    tts.save(file_path)

    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    b64 = base64.b64encode(audio_bytes).decode()

    audio_html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """

    st.markdown(audio_html, unsafe_allow_html=True)


# FIXED WEIGHT FUNCTIONS
def get_weight_instant():
    """Get a single weight reading from the scale"""
    try:
        response = requests.get(f"{BASE_URL}/weight", timeout=1.0)
        if response.status_code == 200:
            weight = response.json().get("weight", 0)
            return float(weight)
    except Exception as e:
        print(f"Weight read error: {e}")
    return 0


def get_stable_weight_for_calibration():
    """Take multiple readings and return stable weight"""
    readings = []
    for i in range(10):
        weight = get_weight_instant()
        if weight > 0:
            readings.append(weight)
        time.sleep(0.2)

    if readings:
        return statistics.median(readings)
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
# ============================
# RECEIPT DISPLAY
# ============================


if "previous_total_weight" not in st.session_state:
    st.session_state.previous_total_weight = 0.0
if "receipt_data" not in st.session_state:
    st.session_state.receipt_data = None
if "voice_played" not in st.session_state:
    st.session_state.voice_played = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "last_weight" not in st.session_state:
    st.session_state.last_weight = 0.0
if "weight_readings" not in st.session_state:
    st.session_state.weight_readings = deque(maxlen=10)
if "last_receipt" not in st.session_state:
    st.session_state.last_receipt = None
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
if "payment_success" not in st.session_state:
    st.session_state.payment_success = False
if "last_order_id" not in st.session_state:
    st.session_state.last_order_id = None
if "show_receipt_page" not in st.session_state:
    st.session_state.show_receipt_page = False

# FIXED: Added key to selectbox
if st.session_state.get("page") == "RECEIPT":
    role = "User"  # dummy value, UI won't show
else:
    role = st.sidebar.selectbox(
        "Select Role",
        ["Admin", "User"],
        key="role_selector"
    )

# ============================================
# ADMIN PANEL
# ============================================
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
            import os

            UPLOAD_FOLDER = "images"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            image_file = st.file_uploader("Upload Image", type=["jpg", "png"])

            image_path = None

            if image_file is not None:
                file_path = os.path.join(UPLOAD_FOLDER, image_file.name)

                with open(file_path, "wb") as f:
                    f.write(image_file.getbuffer())

                image_path = file_path

        st.markdown("---")
        st.subheader("⚖️ Calibrate Weight")
        st.write("Place the product on the scale and click 'Capture Weight'")

        if st.button("📡 Capture Weight", key="capture_weight", use_container_width=True):
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

        if st.button("✅ Save Product", key="save_product", type="primary", use_container_width=True):
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
                    "barcode": barcode,
                    "image": image_path
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

        if st.button("Update Quantity", key="update_qty", use_container_width=True):
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

# ============================================
# USER PANEL
# ============================================
else:
    st.title("🛒 Smart Shopping Cart")

    # User login
    if st.session_state.user_id is None and st.session_state.get("page") != "RECEIPT":
        st.header("👤 Welcome! Please Identify Yourself")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your Name", key="user_name")
        with col2:
            phone = st.text_input("Phone Number", key="user_phone")

        if st.button("Start Shopping", key="start_shopping", type="primary", use_container_width=True):
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

    # FIXED: Added key to radio button
    if "page" not in st.session_state:
        st.session_state.page = "🛍️ Shop"

    if st.session_state.page != "RECEIPT":
        page = st.radio(
            "Navigation",
            ["🛍️ Shop", "📦 Cart", "📜 Orders"],
            horizontal=True,
            key="nav_radio"
        )
    else:
        page = "RECEIPT"

    # ============================================
    # SHOP PAGE - WITH AUTO DETECTION
    # ============================================
    if page == "🛍️ Shop":
        st.header("Add Items to Cart")
        st.info(
            "💡 **How to use:** Scan barcode, then place the NEW item on the scale (without removing existing items). The system will auto-detect the weight and add the item if it matches.")

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

        # Barcode input
        barcode = st.text_input("Scan Barcode", key="barcode_input")

        # Reset state when barcode changes
        if barcode and barcode != st.session_state.get("last_barcode", ""):
            st.session_state.last_barcode = barcode
            st.session_state.item_added = False
            st.session_state.scan_complete = False
            st.session_state.weight_readings.clear()
            st.session_state.reading_count = 0

            # ✅ IMPORTANT: Capture stable baseline BEFORE detection
            st.info("Stabilizing scale... please wait")

            stable_weight = get_stable_weight_for_calibration()

            if stable_weight > 0:
                st.session_state.previous_total_weight = stable_weight
            else:
                st.warning("⚠️ Could not get stable baseline weight. Try again.")

            time.sleep(1)  # small delay for stability

        if barcode:
            try:
                response = requests.get(f"{BASE_URL}/product/barcode/{barcode}", timeout=3)
                if response.status_code == 200 and response.json():
                    product = response.json()

                    if "error" not in product:
                        if product.get("image"):
                            st.image(product["image"], width=150)
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

                        # AUTO DETECTION - No button needed
                        if not st.session_state.item_added and not st.session_state.scan_complete:
                            if st.session_state.reading_count is None:
                                st.session_state.reading_count = 0

                            if st.session_state.reading_count < 10:
                                # Get fresh weight reading
                                current_total_weight = get_stable_weight_for_calibration()

                                if current_total_weight > 0:
                                    # Calculate weight difference (NEW ITEM WEIGHT = TOTAL - CART)
                                    weight_difference = current_total_weight - st.session_state.previous_total_weight
                                    CHANGE_THRESHOLD = 5  # grams

                                    if abs(current_total_weight - st.session_state.previous_total_weight) < CHANGE_THRESHOLD:
                                        st.warning("Waiting for weight change...")
                                        time.sleep(0.5)
                                        st.rerun()
                                    # Display current readings
                                    if st.session_state.get("is_detecting", False):
                                        st.warning("⚖️ Detecting new weight... please wait")
                                    else:
                                        st.metric("Total Weight on Scale", f"{current_total_weight:.1f} g")
                                    st.metric("Weight Difference (New Item)", f"{weight_difference:.1f} g",
                                              delta=f"Expected: {expected_wt:.1f}g")
                                    st.session_state.current_total_weight = current_total_weight

                                    # Add to readings
                                    if weight_difference > 1:
                                        st.session_state.weight_readings.append(weight_difference)
                                        st.session_state.reading_count += 1

                                        # Show progress
                                        st.progress(st.session_state.reading_count / 10,
                                                    text=f"Reading {st.session_state.reading_count}/10: {weight_difference:.1f}g")
                                        delta = current_total_weight - st.session_state.previous_total_weight

                                        st.metric(
                                            "Weight Change",
                                            f"{delta:.1f} g",
                                            delta=f"{delta:.1f} g"
                                        )
                                        # Auto-refresh for next reading
                                        time.sleep(0.5)
                                        st.rerun()
                                else:
                                    st.warning("No weight detected - check scale connection")
                                    time.sleep(0.5)
                                    st.rerun()

                            # After collecting 10 readings, verify
                            elif st.session_state.reading_count >= 10 and not st.session_state.scan_complete:
                                st.session_state.scan_complete = True

                                # Calculate average of readings (remove outliers)
                                readings_list = list(st.session_state.weight_readings)
                                readings_list.sort()
                                trimmed_readings = readings_list[2:-2] if len(readings_list) > 4 else readings_list
                                avg_difference = sum(trimmed_readings) / len(trimmed_readings)

                                st.write("---")
                                st.subheader("📊 Measurement Results")
                                st.write(f"**Average Weight:** {avg_difference:.1f} g")
                                st.write(f"**Expected Weight:** {expected_wt:.1f} g")

                                # Check if weight matches (15% tolerance)
                                min_allowed = expected_wt * 0.85
                                max_allowed = expected_wt * 1.15

                                if min_allowed <= avg_difference <= max_allowed:
                                    st.success(f"✅ Weight matches! Adding to cart...")
                                    st.session_state.previous_total_weight = st.session_state.current_total_weight

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
                                            st.session_state.scan_complete = False
                                            st.session_state.weight_readings.clear()
                                            st.session_state.reading_count = 0
                                            st.rerun()
                                        else:
                                            st.success(f"✅ {product['product_name']} added to cart!")
                                            st.session_state.item_added = True
                                            speak_warning("Item added")
                                            st.balloons()
                                            time.sleep(2)
                                            st.rerun()
                                    else:
                                        st.error("Failed to add to cart")
                                else:
                                    diff = abs(avg_difference - expected_wt)
                                    diff_percent = (diff / expected_wt) * 100 if expected_wt > 0 else 0

                                    if not st.session_state.get("voice_played", False):
                                        speak_warning(
                                            "Weight mismatch detected. Please place the correct item on the scale")
                                        st.session_state.voice_played = True

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("🔄 Try Again", key="try_again"):
                                            st.session_state.scan_complete = False
                                            st.session_state.weight_readings.clear()
                                            st.session_state.reading_count = 0
                                            st.rerun()
                                    with col2:
                                        if st.button("➕ Add Manually", key="add_manually"):
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
        if barcode:
            st.subheader("🧠 Recommended for You")

            try:
                rec_response = requests.get(
                    f"{BASE_URL}/recommend/user/{st.session_state.user_id}",
                    timeout=3
                )

                if rec_response.status_code == 200:
                    recommended_products = rec_response.json().get("recommended_products", [])

                    if recommended_products:
                        products_res = requests.get(f"{BASE_URL}/products", timeout=3)

                        if products_res.status_code == 200:
                            all_products = products_res.json()

                            for p in recommended_products:
                                col1, col2, col3 = st.columns([4, 2, 2])

                                with col1:
                                    if p.get("image"):
                                        st.image(p["image"], width=150)
                                    else:
                                        st.write("🖼️ No image available")
                                    st.write(f"**{p['product_name']}**")

                                with col2:
                                    st.write(f"₹{p['price']}")



                    else:
                        st.info("No recommendations yet. Add items to cart first.")

                else:
                    st.warning("Failed to load recommendations")

            except Exception as e:
                st.error(f"Recommendation error: {e}")
        # Show all products button
        with st.expander("📋 Browse All Products"):
            if st.button("Show Products", key="show_products"):
                try:
                    response = requests.get(f"{BASE_URL}/products", timeout=3)
                    if response.status_code == 200:
                        products = response.json()
                        if products:
                            df = pd.DataFrame(products)
                            st.dataframe(df, use_container_width=True)
                except Exception as e:
                    st.error(f"Error: {e}")

    # ============================================
    # CART PAGE
    # ============================================

    elif page == "RECEIPT":

        st.header("🧾 Payment Receipt")

        # Get order ID from session state

        if st.session_state.last_order_id:

            order_id = st.session_state.last_order_id

        else:

            st.error("No receipt found. Please contact support.")

            if st.button("🏠 Return to Shop"):
                st.session_state.page = "🛍️ Shop"

                st.session_state.payment_success = False

                st.session_state.show_receipt_page = False

                st.rerun()

            st.stop()

        # Show loading spinner while fetching receipt

        with st.spinner("Loading your receipt..."):

            res = requests.get(f"{BASE_URL}/order/receipt/{order_id}")

        if res.status_code == 200:

            receipt = res.json()

            # Show prominent success message with balloons

            st.balloons()

            st.success("🎉✅ PAYMENT SUCCESSFUL! Your order has been confirmed. ✅🎉")

            # Display receipt in a nice format

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric("Order ID", receipt['order_id'])

            with col2:

                st.metric("Date", receipt.get('date', 'Today')[:10])

            with col3:

                st.metric("Total Amount", f"₹{receipt['total_amount']}")

            st.markdown("---")

            st.subheader("📋 Order Items")

            # Display items in a dataframe

            df = pd.DataFrame(receipt["items"])

            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("---")

            st.subheader("📄 Download Your Receipt")

            st.info(
                "💡 Please download your receipt as proof of purchase. You may need to show it when leaving the store.")

            # Create PDF in memory

            from io import BytesIO

            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#1f77b4'),
                alignment=TA_CENTER,
                spaceAfter=30
            )

            content = []

            # Title
            content.append(Paragraph("SMART SHOPPING CART", title_style))
            content.append(Paragraph("Payment Receipt", styles["Heading2"]))
            content.append(Spacer(1, 12))

            # Order info
            content.append(Paragraph(f"<b>Order ID:</b> {receipt['order_id']}", styles["Normal"]))
            content.append(Paragraph(f"<b>Date:</b> {receipt.get('date', 'N/A')}", styles["Normal"]))
            content.append(Spacer(1, 12))

            # Table
            table_data = [['Product', 'Quantity', 'Price (₹)', 'Total (₹)']]

            for item in receipt["items"]:
                table_data.append([
                    item['product_name'],
                    str(item['qty']),
                    f"{item['price']:.2f}",
                    f"{item['total']:.2f}"
                ])

            table_data.append(['', '', 'Total:', f"{receipt['total_amount']:.2f}"])

            table = Table(table_data, colWidths=[200, 80, 80, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -2), 1, colors.black),
            ]))

            content.append(table)
            content.append(Spacer(1, 20))

            content.append(Paragraph("Thank you for shopping with us!", styles["Normal"]))
            content.append(Paragraph("Visit again soon! 🛒", styles["Normal"]))

            doc.build(content)

            pdf = buffer.getvalue()

            buffer.close()

            # Create download button prominently in the center

            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:

                st.download_button(

                    label="📥 DOWNLOAD RECEIPT (PDF) - CLICK HERE",

                    data=pdf_data,

                    file_name=f"receipt_{receipt['order_id']}.pdf",

                    mime="application/pdf",

                    key="download_receipt",

                    use_container_width=True,

                    type="primary"

                )

            st.markdown("---")

            st.warning(
                "⚠️ **IMPORTANT:** Please keep this receipt with you. You may need to show it at the store exit for verification.")

            # Action buttons

            col1, col2 = st.columns(2)

            with col1:

                if st.button("🛍️ Start New Shopping Session", use_container_width=True):
                    # Reset all session states for new shopping

                    st.session_state.page = "🛍️ Shop"

                    st.session_state.payment_success = False

                    st.session_state.last_order_id = None

                    st.session_state.show_receipt_page = False

                    st.session_state.item_added = False

                    st.session_state.scan_complete = False

                    st.session_state.weight_readings.clear()

                    st.session_state.cart_empty = True

                    st.rerun()

            with col2:

                if st.button("📜 View All Orders", use_container_width=True):
                    st.session_state.page = "📜 Orders"

                    st.session_state.payment_success = False

                    st.rerun()


        else:

            st.error("❌ Receipt not found. Please contact store support.")

            if st.button("🏠 Return to Shop"):
                st.session_state.page = "🛍️ Shop"

                st.session_state.payment_success = False

                st.session_state.show_receipt_page = False

                st.rerun()

        st.stop()
    elif page == "📦 Cart":
        st.header("Your Shopping Cart")

        try:
            response = requests.get(f"{BASE_URL}/cart", params={"user_id": st.session_state.user_id}, timeout=3)

            if response.status_code == 200:
                cart = response.json()

                if cart:
                    st.subheader("Cart Items")

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

                    for idx, item in enumerate(cart):
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 2, 2, 1])

                        with col1:
                            if item.get("image"):
                                st.image(item["image"], width=80)
                            st.write(f"**{item['product_name']}**")

                        with col2:
                            new_qty = st.number_input(
                                "Qty",
                                min_value=1,
                                max_value=100,
                                value=item['qty'],
                                key=f"qty_{item['cart_id']}",
                                label_visibility="collapsed"
                            )

                            if new_qty != item['qty']:
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
                            if st.button("🗑️ Delete", key=f"del_{item['cart_id']}"):

                                with st.spinner(f"Remove {item['product_name']} from scale..."):

                                    # Step 1: Calculate expected weight AFTER removal
                                    full_cart_weight = sum(i.get('weight', 0) * i['qty'] for i in cart)

                                    expected_weight = full_cart_weight - (item.get('weight', 0) * item['qty'])

                                    # Step 2: Wait for user to remove item physically
                                    tolerance = max(expected_weight * 0.10, 5)
                                    min_w = expected_weight - tolerance
                                    max_w = expected_weight + tolerance

                                    matched = False
                                    actual_weight = 0

                                    match_count = 0

                                    match_count = 0
                                    actual_weight = 0

                                    for _ in range(15):
                                        w = get_stable_weight_for_calibration()

                                        if min_w <= w <= max_w:
                                            match_count += 1
                                            actual_weight = w  # update only when valid

                                        time.sleep(0.4)

                                    matched = match_count >= 5

                                    st.write(f"Expected: {expected_weight:.1f}g")
                                    st.write(f"Actual: {actual_weight:.1f}g")

                                    # Step 4: ONLY DELETE if weight matches
                                    if matched:
                                        delete_response = requests.delete(
                                            f"{BASE_URL}/cart/{item['cart_id']}",
                                            timeout=3
                                        )

                                        if delete_response.status_code == 200:
                                            result = delete_response.json()

                                            if result.get("error"):
                                                st.error(f"❌ {result['error']}")
                                            else:
                                                st.success(f"✅ {item['product_name']} removed successfully!")
                                                st.session_state.previous_total_weight = actual_weight
                                                time.sleep(1)
                                                st.rerun()

                                    else:
                                        st.error(
                                            f"❌ Please remove the item from scale first!\n\n"
                                            f"Expected: {expected_weight:.1f}g\n"
                                            f"Actual: {actual_weight:.1f}g"
                                        )

                                    # 🔊 Voice alert (only once)

                                    if not st.session_state.voice_played:
                                        speak_warning("Please remove the item from the cart")
                    st.markdown("---")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Items", len(cart))
                    with col2:
                        st.metric("Total Weight", f"{total_weight:.1f} g")
                    with col3:
                        st.metric("Total Amount", f"₹{total_amount:.2f}")

                    st.markdown("---")

                    col1, col2 = st.columns(2)
                    with col1:

                        if st.button("🗑️ Clear Entire Cart", key="clear_cart", use_container_width=True):
                            for item in cart:
                                st.image(item["image"], width=100)
                                requests.delete(f"{BASE_URL}/cart/{item['cart_id']}", timeout=3)
                            st.session_state.last_weight = 0
                            st.session_state.weight_readings.clear()
                            st.success("Cart cleared!")
                            time.sleep(1)
                            st.rerun()

                    with col2:
                        if st.button("💳 Pay with Razorpay", use_container_width=True):
                            import streamlit.components.v1 as components

                            # Create order first
                            response = requests.post(
                                f"{BASE_URL}/order/create-razorpay-order",
                                params={"user_id": st.session_state.user_id}
                            )

                            if response.status_code == 200:
                                data = response.json()

                                # Check if there's an error
                                if "error" in data:
                                    st.error(f"Error: {data['error']}")
                                else:
                                    order_id = data["order_id"]
                                    amount = data["amount"]

                                    # Create the payment component
                                    razorpay_html = f"""
                                    <!DOCTYPE html>
                                    <html>
                                    <head>
                                        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
                                    </head>
                                    <body>
                                        <div id="payment-status" style="text-align: center; padding: 20px; font-family: Arial;">
                                            <h3>Processing Payment...</h3>
                                            <p>Please wait while we redirect you to payment gateway...</p>
                                        </div>
                                        <script>
                                            console.log("Initializing Razorpay...");
                                            console.log("Order ID:", "{order_id}");
                                            console.log("Amount:", "{amount}");

                                            var options = {{
                                                "key": "rzp_test_ScUj55hZVBL9QE",
                                                "amount": "{int(amount * 100)}",
                                                "currency": "INR",
                                                "name": "Smart Shopping Cart",
                                                "description": "Payment for your purchase",
                                                "order_id": "{order_id}",
                                                "handler": function (response){{
                                                    console.log("Payment successful:", response);

                                                    document.getElementById('payment-status').innerHTML = 
                                                        '<div style="background: green; color: white; padding: 20px; border-radius: 10px;">' +
                                                        '<h2>✅ Payment Successful!</h2>' +
                                                        '<p>Generating receipt...</p>' +
                                                        '</div>';

                                                    const confirmUrl = "http://127.0.0.1:8000/order/confirm-payment?user_id={st.session_state.user_id}&payment_method=upi";

                                                    fetch(confirmUrl, {{
                                                        method: "POST"
                                                    }})
                                                    .then(res => {{
                                                        console.log("Response status:", res.status);

                                                        if (!res.ok) {{
                                                            throw new Error("Server error: " + res.status);
                                                        }}

                                                        return res.json();
                                                    }})
                                                    .then(parsed => {{
                                                        console.log("Parsed response:", parsed);

                                                        if (parsed.order_id) {{
                                                            window.location.href = "/?receipt_id=" + parsed.order_id;
                                                        }} else {{
                                                            throw new Error("No order_id returned");
                                                        }}
                                                    }})
                                                    .catch(error => {{
                                                        console.error("Fetch error:", error);

                                                        document.getElementById('payment-status').innerHTML =
                                                            '<div style="background:red;color:white;padding:20px;border-radius:10px;">' +
                                                            '<h2>❌ Error</h2>' +
                                                            '<p>' + error.message + '</p>' +
                                                            '</div>';
                                                    }});
                                                }},
                                                "modal": {{
                                                    "ondismiss": function(){{
                                                        console.log("Payment modal dismissed");
                                                        document.getElementById('payment-status').innerHTML = 
                                                            '<div style="background: orange; color: white; padding: 20px; border-radius: 10px;">' +
                                                            '<h2>⚠️ Payment Cancelled</h2>' +
                                                            '<p>You cancelled the payment. Please try again.</p>' +
                                                            '<button onclick="window.location.reload()">Try Again</button>' +
                                                            '</div>';
                                                    }}
                                                }},
                                                "theme": {{
                                                    "color": "#3399cc"
                                                }},
                                                "prefill": {{
                                                    "name": "Customer",
                                                    "email": "customer@example.com"
                                                }}
                                            }};

                                            // Initialize Razorpay
                                            var rzp = new Razorpay(options);

                                            // Handle payment failure
                                            rzp.on('payment.failed', function (response){{
                                                console.error("Payment failed:", response);
                                                document.getElementById('payment-status').innerHTML = 
                                                    '<div style="background: red; color: white; padding: 20px; border-radius: 10px;">' +
                                                    '<h2>❌ Payment Failed</h2>' +
                                                    '<p>' + (response.error ? response.error.description : 'Unknown error') + '</p>' +
                                                    '<button onclick="window.location.reload()">Try Again</button>' +
                                                    '</div>';
                                            }});

                                            // Open the payment modal
                                            setTimeout(function() {{
                                                rzp.open();
                                            }}, 1000);
                                        </script>
                                    </body>
                                    </html>
                                    """

                                    # Display the component
                                    st.components.v1.html(razorpay_html, height=400)
                                    st.info("💳 Payment window opening... Please complete the payment.")
                            else:
                                st.error(f"Failed to create payment order. Status: {response.status_code}")
                else:
                    st.info("🛒 Your cart is empty")
                    if st.session_state.last_weight != 0:
                        st.session_state.last_weight = 0

        except Exception as e:
            st.error(f"Error fetching cart: {e}")

    # ============================================
    # ORDERS PAGE
    # ============================================
    elif page == "📜 Orders":
        st.header("Order History")

        try:
            response = requests.get(f"{BASE_URL}/order/orders/{st.session_state.user_id}", timeout=3)
            if response.status_code == 200:
                orders = response.json()
                if orders:
                    for order in orders:
                        st.markdown("### 🧾 Order #" + str(order["order_id"]))

                        st.write(f"📅 Date: {order['created_at']}")
                        st.write(f"💰 Total: ₹{order['total_amount']}")

                        df = pd.DataFrame(order["items"])
                        df.rename(columns={
                            "product_name": "Product",
                            "qty": "Quantity",
                            "price": "Price",
                            "total": "Total"
                        }, inplace=True)

                        st.dataframe(df, use_container_width=True)
                        if st.button(f"📄 View Receipt #{order['order_id']}"):
                            res = requests.get(f"{BASE_URL}/order/receipt/{order['order_id']}")

                            if res.status_code == 200:
                                receipt = res.json()

                                st.success(f"Receipt for Order #{order['order_id']}")

                                st.write(f"Total: ₹{receipt['total_amount']}")

                                df = pd.DataFrame(receipt["items"])
                                st.dataframe(df, use_container_width=True)

                                # Optional: Download button
                                from io import BytesIO
                                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                                from reportlab.lib.pagesizes import letter
                                from reportlab.lib import colors
                                from reportlab.lib.enums import TA_CENTER

                                buffer = BytesIO()
                                doc = SimpleDocTemplate(buffer, pagesize=letter)
                                styles = getSampleStyleSheet()

                                title_style = ParagraphStyle(
                                    'CustomTitle',
                                    parent=styles['Title'],
                                    fontSize=24,
                                    textColor=colors.HexColor('#1f77b4'),
                                    alignment=TA_CENTER,
                                    spaceAfter=30
                                )

                                content = []

                                content.append(Paragraph("SMART SHOPPING CART", title_style))
                                content.append(Paragraph("Payment Receipt", styles["Heading2"]))
                                content.append(Spacer(1, 12))

                                content.append(Paragraph(f"<b>Order ID:</b> {receipt['order_id']}", styles["Normal"]))
                                content.append(
                                    Paragraph(f"<b>Date:</b> {receipt.get('date', 'N/A')}", styles["Normal"]))
                                content.append(Spacer(1, 12))

                                table_data = [['Product', 'Quantity', 'Price (₹)', 'Total (₹)']]

                                for item in receipt["items"]:
                                    table_data.append([
                                        item['product_name'],
                                        str(item['qty']),
                                        f"{item['price']:.2f}",
                                        f"{item['total']:.2f}"
                                    ])

                                table_data.append(['', '', 'Total:', f"{receipt['total_amount']:.2f}"])

                                table = Table(table_data, colWidths=[200, 80, 80, 100])
                                table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                                    ('GRID', (0, 0), (-1, -2), 1, colors.black),
                                ]))

                                content.append(table)
                                content.append(Spacer(1, 20))

                                content.append(Paragraph("Thank you for shopping with us!", styles["Normal"]))
                                content.append(Paragraph("Visit again soon! 🛒", styles["Normal"]))

                                doc.build(content)
                                pdf = buffer.getvalue()
                                doc.build(content)

                                st.download_button(
                                    "Download Receipt",
                                    data=pdf,
                                    file_name=f"receipt_{order['order_id']}.pdf",
                                    mime="application/pdf"
                                )

                        st.markdown("---")
                else:
                    st.info("No orders yet")
        except Exception as e:
            st.error(f"Error: {e}")