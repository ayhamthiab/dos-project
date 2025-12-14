from flask import Flask, jsonify
import requests
from database import init_db, get_book, update_stock

app = Flask(__name__)
init_db()

FRONTEND = "http://frontend_service:5000"
REPLICA = "http://catalog_service_2:5000"

@app.route("/info/<int:book_id>", methods=["GET"])
def info(book_id):
    """
    Read-only request (can be cached at frontend)
    """
    return jsonify(get_book(book_id))

@app.route("/update/<int:book_id>", methods=["POST"])
def update(book_id):
    """
    Write request:
    1. Invalidate cache
    2. Update local DB
    3. Replicate write
    """
    # invalidate cache before write
    requests.post(f"{FRONTEND}/invalidate/{book_id}")

    # update local stock
    update_stock(book_id, -1)

    # replicate to the other catalog replica
    requests.post(f"{REPLICA}/sync/{book_id}")

    return jsonify({"status": "updated"})

@app.route("/sync/<int:book_id>", methods=["POST"])
def sync(book_id):
    """
    Replication endpoint
    """
    update_stock(book_id, -1)
    return jsonify({"status": "replica synced"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
