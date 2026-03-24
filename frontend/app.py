import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"
role = st.selectbox("Select Role", ["Admin", "User"])
st.title("🛒 Smart Shopping Cart")

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
    cart_product_id = st.number_input("Product ID", step=1, key="cart_pid")
    cart_qty = st.number_input("Quantity", step=1, key="cart_qty")
    if st.button("Add to Cart"):
        response = requests.post(
            f"{BASE_URL}/cart",
            params={"product_id": cart_product_id, "qty": cart_qty}
        )

        if response.status_code == 200:
            st.success("Added to Cart")
        else:
            st.error("Failed to add")

    st.header("📦 View Cart")
    if st.button("Show Cart"):
        response = requests.get(f"{BASE_URL}/cart")

        if response.status_code == 200:
            cart = response.json()

            import pandas as pd

            columns = ["cart_id", "product_name", "price", "qty", "total"]
            df = pd.DataFrame(cart, columns=columns)

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
