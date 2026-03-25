import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from db.connection import Mysql

def recommend_products(product_id):
    db = Mysql()

    # Step 1: get category of selected product
    product = db.fetchall(
        "SELECT category FROM products WHERE product_id = %s",
        (product_id,)
    )

    if not product:
        return []

    category = product[0][0]

    # Step 2: get products in same category
    data = db.fetchall(
        "SELECT product_id, price, weight FROM products WHERE category = %s",
        (category,)
    )

    if not data:
        return []

    df = pd.DataFrame(data, columns=["product_id", "price", "weight"])

    # If only one product → no recommendations
    if len(df) <= 1:
        return []

    # Step 3: similarity calculation
    features = df[["price", "weight"]]

    similarity = cosine_similarity(features)

    similarity_df = pd.DataFrame(
        similarity,
        index=df["product_id"],
        columns=df["product_id"]
    )

    # Step 4: check existence
    if product_id not in similarity_df.columns:
        return []

    # Step 5: REMOVE same product
    similar = similarity_df[product_id].drop(product_id)

    # Step 6: sort by similarity
    similar = similar.sort_values(ascending=False)

    # Step 7: return top 3
    return similar.head(3).index.tolist()