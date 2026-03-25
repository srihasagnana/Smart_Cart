import streamlit as st
import requests

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
    weight = st.number_input("Weight")
    barcode = st.text_input("Barcode")
    if st.button("Add Product"):
        data = {
            "product_name": product_name,
            "product_description": product_description,
            "category": category,
            "price": price,
            "qty": qty,
            "weight": weight,
            "barcode": barcode
        }

        response = requests.post(f"{BASE_URL}/product", params=data)

        if response.status_code == 200:
            st.success("Product Added")
        else:
            st.error("Failed to add product")


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


    st.header("Get Product by ID")
    product_id = st.number_input("Enter Product ID", step=1)
    if st.button("Get Product"):
        response = requests.get(f"{BASE_URL}/product/{product_id}")

        if response.status_code == 200:
            st.write(response.json())
        else:
            st.error("Product not found")


    st.header("📷 Scan Product")
    scan_barcode = st.text_input("Enter Barcode to Scan")
    if st.button("Scan Product"):
        response = requests.get(f"{BASE_URL}/product/barcode/{scan_barcode}")

        if response.status_code == 200 and response.json():
            st.success("Product Found")
            st.write(response.json())
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

    st.header("🛒 Add to Cart")

    response = requests.get(f"{BASE_URL}/products")

    if response.status_code == 200:
        products = response.json()

        if not products:
            st.warning("No products available")
            st.stop()
    else:
        st.error("Failed to load products")
        st.stop()

    product_map = {
        f"{p[1]} - ₹{p[4]} (ID: {p[0]})": p[0] for p in products
    }

    selected_product = st.selectbox("Select Product", list(product_map.keys()))
    cart_product_id = product_map[selected_product]
    # 🔥 SHOW RECOMMENDATIONS IMMEDIATELY
    rec_response = requests.get(
        f"{BASE_URL}/recommend/{cart_product_id}"
    )

    if rec_response.status_code == 200:
        rec_ids = rec_response.json()["recommended_products"]

        st.subheader("🤖 Recommended for you")

        if rec_ids:
            all_products = requests.get(f"{BASE_URL}/products").json()
            product_dict = {p[0]: (p[1], p[4]) for p in all_products}

            for r in rec_ids:
                col1, col2 = st.columns([3, 1])

                with col1:
                    name, price = product_dict.get(r, ("Unknown", 0))
                    st.write(f"👉 {name} - ₹{price}")

                with col2:
                    if st.button(f"Add", key=f"rec_add_{r}"):
                        add_response = requests.post(
                            f"{BASE_URL}/cart",
                            params={
                                "user_id": st.session_state.user_id,
                                "product_id": r,
                                "qty": 1
                            }
                        )

                        if add_response.status_code == 200:
                            st.success(f"Added {product_dict.get(r)} to cart")
                        else:
                            st.error("Failed to add")
        else:
            st.write("No recommendations available")

    cart_qty = st.number_input("Quantity", min_value=1, step=1)

    st.write("DEBUG → Selected ID:", cart_product_id)

    if st.button("Add to Cart", key="add_cart_btn"):
        response = requests.post(
            f"{BASE_URL}/cart",
            params={
                "user_id": st.session_state.user_id,
                "product_id": cart_product_id,
                "qty": cart_qty
            }
        )

        if response.status_code == 200:
            st.success("Added to Cart")
        else:
            st.error("Failed to add")
    

    st.header("📦 View Cart")

    if st.button("Show Cart", key="show_cart_btn"):
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
                st.dataframe(df)
        else:
            st.error("Error fetching cart")

    st.header("❌ Remove Item")
    delete_id = st.number_input("Cart ID", step=1, key="delete_id")

    if st.button("Delete Item"):
        response = requests.delete(f"{BASE_URL}/cart/{delete_id}")

        if response.status_code == 200:
            st.success("Item removed")
        else:
            st.error("Failed to delete")

   
