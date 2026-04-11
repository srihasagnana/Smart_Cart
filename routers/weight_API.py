from fastapi import APIRouter, HTTPException
from db.connection import Mysql
from serial_reader import weight_reader
import math
import traceback

router = APIRouter()


@router.post("/set-weight-range")
def set_weight_range(product_id: int, weights: list[float]):
    db = Mysql()

    try:
        if len(weights) < 3:
            return {"error": "Need at least 3 weights"}

        # Calculate statistics
        weights_sorted = sorted(weights)
        avg_weight = sum(weights_sorted) / len(weights_sorted)

        # Use 10% tolerance
        tolerance_percentage = 0.10
        tolerance_grams = max(avg_weight * tolerance_percentage, 10)

        min_w = avg_weight - tolerance_grams
        max_w = avg_weight + tolerance_grams

        db.execute("""
            UPDATE products 
            SET min_weight=%s, max_weight=%s, weight=%s
            WHERE product_id=%s
        """, (min_w, max_w, avg_weight, product_id), commit=True)

        return {
            "msg": "Weight range set",
            "avg": avg_weight,
            "min": min_w,
            "max": max_w,
            "tolerance_percentage": f"{tolerance_percentage * 100}%",
            "tolerance_grams": tolerance_grams
        }
    except Exception as e:
        print(f"Error in set-weight-range: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}
    finally:
        db.close()


@router.post("/check-weight")
def check_weight(product_id: int, weight: float = None):
    db = Mysql()

    try:
        print(f"DEBUG - Checking weight for product_id: {product_id}, weight: {weight}")

        # If weight not provided, get current weight from sensor
        if weight is None:
            weight = weight_reader.read_single_weight()
            print(f"DEBUG - Got weight from sensor: {weight}")

        # First, check what columns exist
        columns = db.fetchall("SHOW COLUMNS FROM products")
        column_names = [col[0] for col in columns]
        print(f"DEBUG - Available columns: {column_names}")

        # Build query based on available columns
        if 'min_weight' in column_names and 'max_weight' in column_names:
            query = """
                SELECT min_weight, max_weight, weight, product_name 
                FROM products 
                WHERE product_id=%s
            """
        else:
            # Fallback if columns don't exist
            query = """
                SELECT weight, product_name 
                FROM products 
                WHERE product_id=%s
            """

        product = db.fetchone(query, (product_id,))
        print(f"DEBUG - Query result: {product}")

        if not product:
            return {"error": f"Product with id {product_id} not found"}

        # Handle different result structures
        if len(product) == 4:
            min_w = product[0]
            max_w = product[1]
            expected_weight = product[2]
            product_name = product[3]
        else:
            # Fallback when min/max don't exist
            expected_weight = product[0]
            product_name = product[1]
            # Calculate 10% tolerance
            tolerance = max(expected_weight * 0.10, 10)
            min_w = expected_weight - tolerance
            max_w = expected_weight + tolerance
            print(f"DEBUG - Calculated tolerance: {min_w} - {max_w}")

        print(f"DEBUG - Product: {product_name}")
        print(f"DEBUG - Expected: {expected_weight}, Min: {min_w}, Max: {max_w}")
        print(f"DEBUG - Measured: {weight}")

        # Check if min_w and max_w exist
        if min_w is not None and max_w is not None:
            # Convert to float
            min_w = float(min_w)
            max_w = float(max_w)
            expected_weight = float(expected_weight)
            weight = float(weight)

            # Calculate difference percentage
            difference = abs(weight - expected_weight)
            difference_percentage = (difference / expected_weight) * 100 if expected_weight > 0 else 0

            # Check if weight is within range
            is_valid = min_w <= weight <= max_w

            print(f"DEBUG - Is valid: {is_valid} ( {min_w} <= {weight} <= {max_w} )")

            return {
                "status": "valid" if is_valid else "invalid",
                "product_name": product_name,
                "measured_weight": weight,
                "expected_weight": expected_weight,
                "difference": round(difference, 1),
                "difference_percentage": round(difference_percentage, 1),
                "tolerance_range": f"{min_w:.1f} - {max_w:.1f}g",
                "min_weight": min_w,
                "max_weight": max_w,
                "message": "Weight matches!" if is_valid else f"Weight out of range. Expected {expected_weight:.1f}g (±{((max_w - min_w) / 2):.1f}g)"
            }
        else:
            return {"error": "Weight range not set for this product"}

    except Exception as e:
        print(f"ERROR in check-weight: {e}")
        print(traceback.format_exc())
        return {"error": str(e)}
