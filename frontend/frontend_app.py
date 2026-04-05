import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"
role = st.selectbox("Select Role", ["Admin", "User"])


st.title("🛒 Smart Shopping Cart")
st.write("App started")

if role == "Admin":
    st.header("Add Product")
    product_name = st.text_input("Product Name")
    product_description = st.text_input("Description")
    category = st.text_input("Category")
    price = st.number_input("Price")
    qty = st.number_input("Quantity", step=1)
    st.subheader("⚖️ Live Weight")

    if st.button("Get Weight", key="get_weight_btn"):
        res = requests.get(f"{BASE_URL}/product/weight")

        if res.status_code == 200:
            st.session_state.weight = res.json()["weight"]
            st.success(f"Weight detected: {st.session_state.weight} g")
        else:
            st.error("Failed to read weight")
    barcode = st.text_input("Barcode")
    if st.button("Add Product", key="add_product_btn"):

        if "weight" not in st.session_state:
            st.error("⚠️ Please measure weight first")
        else:
            data = {
                "product_name": product_name,
                "product_description": product_description,
                "category": category,
                "price": price,
                "qty": qty,
                "weight": st.session_state.weight,
                "barcode": barcode
            }

            response = requests.post(f"{BASE_URL}/product", params=data)

            if response.status_code == 200:
                st.success("Product Added")
            else:
                st.error("Failed to add product")





    st.header("📷 Scan Product")
    scan_barcode = st.text_input("Enter Barcode to Scan")

    if st.button("Scan Product"):
        response = requests.get(f"{BASE_URL}/product/barcode/{scan_barcode}")

        if response.status_code == 200 and response.json():
            st.success("Product Found")

            product = response.json()

            # Convert to table
            df = pd.DataFrame([product])

            st.table(df)   # or st.dataframe(df)
        else:
            st.error("Product not found")

    st.header("🔄 Update Quantity")
    update_id = st.number_input("Product ID to Update", step=1, key="update_id")
    new_qty = st.number_input("New Quantity", step=1, key="new_qty")
    if st.button("Update Quantity"):
        response = requests.put(
            f"{BASE_URL}/product/{update_id}/quantity",
            params={"qty": new_qty}
        )

        if response.status_code == 200:
            st.success("Quantity Updated")
        else:
            st.error("Failed to update quantity")


if role == "User":
    # USER IDENTIFICATION
    if "user_id" not in st.session_state:
        st.header("👤 Enter Details")

        name = st.text_input("Name")
        phone = st.text_input("Phone")

        if st.button("Continue"):
            response = requests.post(
                f"{BASE_URL}/user/create",
                params={"name": name, "phone": phone}
            )

            if response.status_code == 200:
                st.session_state.user_id = response.json()["user_id"]
                st.success("User created! Now you can shop ✅")
            else:
                st.error("Failed to create user")

        st.stop()  # 🚨 STOP further UI until user enters details

        # 🔥 ADD THIS HERE  
    page = st.radio(
        "Navigation",
        ["Shop", "Order History"],
        horizontal=True
    )

    if page == "Shop":
        st.header("All Products")
        if st.button("Show Products"):
            response = requests.get(f"{BASE_URL}/products")

            if response.status_code == 200:
                products = response.json()

                import pandas as pd

                columns = [
                    "product_id",
                    "product_name",
                    "description",
                    "category",
                    "price",
                    "qty",
                    "weight",
                    "created_at",
                    "barcode"
                ]

                df = pd.DataFrame(products, columns=columns)

                st.dataframe(df)
            else:
                st.error("Error fetching products")

        st.header("🛒 Add to Cart (Scan Barcode)")

        barcode_input = st.text_input("Scan / Enter Barcode")

        product_data = None

        if barcode_input:
            response = requests.get(f"{BASE_URL}/product/barcode/{barcode_input}")

            if response.status_code == 200 and response.json():
                product_data = response.json()

                st.success("✅ Product Found")

                st.write("### Product Details")
                st.write(f"🆔 ID: {product_data['product_id']}")
                st.write(f"📦 Name: {product_data['product_name']}")
                st.write(f"💰 Price: ₹ {product_data['price']}")
                st.write(f"🔢 Barcode: {product_data['barcode']}")

                cart_product_id = product_data["product_id"]

                # ✅ Quantity
                cart_qty = st.number_input("Quantity", min_value=1, step=1)

                # ✅ Add to Cart
                if st.button("Add to Cart"):
                    response = requests.post(
                        f"{BASE_URL}/cart",
                        params={
                            "user_id": st.session_state.user_id,
                            "product_id": cart_product_id,
                            "qty": cart_qty
                        }
                    )

                    if response.status_code == 200:
                        st.success("Added to Cart 🛒")
                    else:
                        st.error("Failed to add")

        # 🔥 RECOMMENDATIONS
                st.subheader("🤖 Recommended for you")

                rec_response = requests.get(f"{BASE_URL}/recommend/{cart_product_id}")

                if rec_response.status_code == 200:
                    rec_ids = rec_response.json()["recommended_products"]

                    if rec_ids:
                        all_products = requests.get(f"{BASE_URL}/products").json()

                        # Map full product details
                        product_dict = {
                            p[0]: {
                                "name": p[1],
                                "price": p[4]
                            }
                            for p in all_products
                        }

                        for r in rec_ids:
                            product = product_dict.get(r)

                            if product:
                                st.write(f"👉 {product['name']} - ₹ {product['price']}")

                                # 🔥 Add button for each product
                                if st.button(f"Add {product['name']} to Cart", key=f"rec_{r}"):
                                    response = requests.post(
                                        f"{BASE_URL}/cart",
                                        params={
                                            "user_id": st.session_state.user_id,
                                            "product_id": r,
                                            "qty": 1   # default quantity
                                        }
                                    )

                                    if response.status_code == 200:
                                        st.success(f"{product['name']} added to cart 🛒")
                                    else:
                                        st.error("Failed to add")

                    else:
                        st.write("No recommendations available")
                else:
                    st.error("Recommendation failed")

        # ✅ VIEW CART HEADER (FIXED POSITION)
        st.header("📦 View Cart")

        response = requests.get(
            f"{BASE_URL}/cart",
            params={"user_id": st.session_state.user_id}
        )

        if response.status_code == 200:
            cart = response.json()

            if not cart:
                st.warning("Cart is empty 🛒")
            else:
                import pandas as pd

                df = pd.DataFrame(cart)

                df = df.rename(columns={
                    "product_name": "Product",
                    "qty": "Quantity",
                    "price": "Price (₹)",
                    "weight": "Weight (g)"
                })
                if "Weight (g)" in df.columns:
                    df["Total Weight (g)"] = df["Weight (g)"] * df["Quantity"]

                df["Remove"] = False

                columns = ["Product", "Quantity", "Price (₹)"]

                if "Weight (g)" in df.columns:
                    columns += ["Weight (g)", "Total Weight (g)"]

                columns += ["Remove"]

                df = df[columns]

                edited_df = st.data_editor(df, use_container_width=True)

                # 🔥 Detect which row user clicked
                for i, row in edited_df.iterrows():
                    if row["Remove"] == True:
                        cart_id = cart[i]["cart_id"]

                        del_res = requests.delete(
                            f"{BASE_URL}/cart/{cart_id}"
                        )

                        res_json = del_res.json()

                        # 🔴 If scan required
                        if res_json.get("error") == "SCAN_REQUIRED":
                            st.warning("⚠️ Multiple items with same weight. Scan item to confirm.")

                            scan_input = st.text_input("Scan Barcode to Remove", key=f"scan_{cart_id}")

                            if scan_input:
                                confirm_res = requests.delete(
                                    f"{BASE_URL}/cart/{cart_id}",
                                    params={"barcode": scan_input}
                                )

                                confirm_json = confirm_res.json()

                                if confirm_json.get("message"):
                                    st.success("Item removed ✅")
                                    st.rerun()
                                else:
                                    st.error("Wrong item scanned ❌")

                        # ✅ Normal delete
                        elif res_json.get("message"):
                            st.success("Item removed")
                            st.rerun()

                        else:
                            st.error("Failed to delete")

                        if del_res.status_code == 200:
                            st.success(f"{row['Product']} removed")
                            st.rerun()
                        else:
                            st.error("Failed to delete")
        else:
            st.error("Error fetching cart")

        
        st.subheader("💰 Checkout")

        total_res = requests.get(
            f"{BASE_URL}/cart/total",
            params={"user_id": st.session_state.user_id}
        )

        if total_res.status_code == 200:
            total_amount = total_res.json().get("total", 0)
        else:
            st.error("Backend error in total")
            total_amount = 0

        st.write(f"### Total Amount: ₹ {total_amount}")

        payment_method = st.radio(
        "Select Payment Method",
        ["UPI", "Card", "Cash"]
        )

        if payment_method == "UPI":
            st.image("frontend/phonepe_qr.png", width=250)
            st.caption("Scan & Pay using UPI")

        elif payment_method == "Card":
            st.text_input("Card Number")
            st.text_input("Expiry (MM/YY)")
            st.text_input("CVV", type="password")
        elif payment_method == "Cash":
            st.write("Pay at counter")

        if st.button("Place Order"):
            response = requests.post(
            f"{BASE_URL}/order/checkout",
            params={
                "user_id": st.session_state.user_id,
                "payment_method": payment_method
            }
        )

            if response.status_code == 200:
                st.success("🎉 Order Placed Successfully!")
                st.balloons()
                
                # 🔥 CLEAR STATE (IMPORTANT)
                st.session_state.pop("cart", None)

                st.rerun()
            else:
                st.error("Checkout failed")
    elif page == "Order History":

        st.header("📦 Your Order History")

        response = requests.get(
        f"{BASE_URL}/order/orders/{st.session_state.user_id}"
    )

        if response.status_code == 200:
            data = response.json()

            if not data:
                st.warning("No orders yet")
            else:
                import pandas as pd
                df = pd.DataFrame(data)

                st.dataframe(df)
        else:
            st.error("Failed to fetch history")