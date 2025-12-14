from flask import Flask, jsonify
import requests
from database import init_db, buy_book

app = Flask(__name__)

# ✅ Initialize orders database on startup (for EVERY replica)
init_db(service_type='order')

FRONTEND = "http://frontend_service:5000"

# Order replica (for order replication)
ORDER_REPLICA = "http://order_service_2:5001"

# Catalog replicas (for stock update + replication)
CATALOG_REPLICA_1 = "http://catalog_service_1:5000"
CATALOG_REPLICA_2 = "http://catalog_service_2:5000"


@app.route("/purchase/<int:book_id>", methods=["POST"])
def purchase(book_id):
    # 1. Invalidate cache
    requests.post(f"{FRONTEND}/invalidate/{book_id}")

    # 2. Record order
    buy_book(book_id)

    # 3. Update catalog (replica 1 ONLY)
    # Catalog service will handle replication internally
    requests.post(f"{CATALOG_REPLICA_1}/update/{book_id}")

    # 4. Replicate order
    requests.post(f"{ORDER_REPLICA}/sync/{book_id}")

    return jsonify({"status": "purchased"})


@app.route("/sync/<int:book_id>", methods=["POST"])
def sync(book_id):
    """
    Order replication endpoint
    """
    buy_book(book_id)
    return jsonify({"status": "replica synced"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
