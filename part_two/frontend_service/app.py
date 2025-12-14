
from flask import Flask, request, jsonify
import requests
from collections import OrderedDict

app = Flask(__name__)

CATALOG_REPLICAS = [
    "http://catalog_service_1:5000",
    "http://catalog_service_2:5000"
]

ORDER_REPLICAS = [
    "http://order_service_1:5001",
    "http://order_service_2:5001"
]

catalog_rr = 0
order_rr = 0

CACHE_SIZE = 5
cache = OrderedDict()

def get_catalog_replica():
    global catalog_rr
    replica = CATALOG_REPLICAS[catalog_rr]
    catalog_rr = (catalog_rr + 1) % len(CATALOG_REPLICAS)
    return replica

def get_order_replica():
    global order_rr
    replica = ORDER_REPLICAS[order_rr]
    order_rr = (order_rr + 1) % len(ORDER_REPLICAS)
    return replica

def cache_get(key):
    if key in cache:
        cache.move_to_end(key)
        return cache[key]
    return None

def cache_put(key, value):
    cache[key] = value
    cache.move_to_end(key)
    if len(cache) > CACHE_SIZE:
        cache.popitem(last=False)

@app.route("/info/<int:book_id>", methods=["GET"])
def book_info(book_id):
    cached = cache_get(book_id)
    if cached:
        print("CACHE HIT for book", book_id)
        return jsonify(cached)

    print("CACHE MISS for book", book_id)
    replica = get_catalog_replica()
    resp = requests.get(f"{replica}/info/{book_id}")
    data = resp.json()
    cache_put(book_id, data)
    return jsonify(data)


@app.route("/purchase/<int:book_id>", methods=["POST"])
def purchase(book_id):
    for replica in ORDER_REPLICAS:
        try:
            resp = requests.post(f"{replica}/purchase/{book_id}", timeout=2)
            return jsonify(resp.json())
        except requests.exceptions.RequestException:
            continue

    return jsonify({"error": "All order replicas are down"}), 500

@app.route("/invalidate/<int:book_id>", methods=["POST"])
def invalidate(book_id):
    if book_id in cache:
        del cache[book_id]
    return jsonify({"status": "cache invalidated"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
