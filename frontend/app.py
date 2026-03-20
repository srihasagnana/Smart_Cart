import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

st.title("🛒 Smart Shopping Cart")

st.header("Add Product")

product_name = st.text_input("Product Name")
product_description = st.text_input("Description")
category = st.text_input("Category")
price = st.number_input("Price")
qty = st.number_input("Quantity", step=1)
weight = st.number_input("Weight")

if st.button("Add Product"):
    data = {
        "product_name": product_name,
        "product_description": product_description,
        "category": category,
        "price": price,
        "qty": qty,
        "weight": weight
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
        st.write(products)
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