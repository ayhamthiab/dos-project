# frontend_service.py
from flask import Flask, jsonify, make_response
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

CATALOG_SERVICE_URL = 'http://catalog_service:5001'
ORDER_SERVICE_URL = 'http://order_service:5002'

# helper to call upstream safely
def safe_request(method, url, **kwargs):
    try:
        resp = requests.request(method, url, timeout=5, **kwargs)
        return resp
    except requests.RequestException as e:
        app.logger.error("Upstream request failed: %s %s -> %s", method, url, e)
        return None

@app.route('/search/<topic>', methods=['GET'])
def search(topic):
    resp = safe_request('GET', f"{CATALOG_SERVICE_URL}/search/{topic}")
    if resp is None:
        return make_response(jsonify({"error": "catalog unreachable"}), 503)
    try:
        return jsonify(resp.json()), resp.status_code
    except ValueError:
        app.logger.error("Catalog returned non-JSON: %s", resp.text[:200])
        return make_response(jsonify({"error": "catalog returned non-JSON"}), 502)

@app.route('/info/<int:item_id>', methods=['GET'])
def info(item_id):
    resp = safe_request('GET', f"{CATALOG_SERVICE_URL}/info/{item_id}")
    if resp is None:
        return make_response(jsonify({"error": "catalog unreachable"}), 503)
    try:
        return jsonify(resp.json()), resp.status_code
    except ValueError:
        app.logger.error("Catalog returned non-JSON for info: %s", resp.text[:200])
        return make_response(jsonify({"error": "catalog returned non-JSON"}), 502)

@app.route('/purchase/<int:item_id>', methods=['PUT', 'POST'])
def purchase(item_id):
    # forward the request to order service (use PUT as original code did)
    resp = safe_request('PUT', f"{ORDER_SERVICE_URL}/purchase/{item_id}")
    if resp is None:
        return make_response(jsonify({"error": "order service unreachable"}), 503)

    # try to parse JSON safely
    try:
        payload = resp.json()
    except ValueError:
        # upstream didn't return JSON — map it to a sensible JSON response
        body_text = resp.text.strip()
        if not body_text:
            # no body: interpret based on status code
            if resp.status_code in (200, 201, 204):
                payload = {"status": "success", "message": "Upstream returned no body"}
            else:
                payload = {"status": "error", "message": f"Upstream status {resp.status_code}"}
        else:
            payload = {"status": "error", "message": "Upstream returned non-JSON", "body": body_text}

    # return payload and use upstream status code
    return make_response(jsonify(payload), resp.status_code)

@app.route('/orders', methods=['GET'])
def get_all_orders():
    resp = safe_request('GET', f"{ORDER_SERVICE_URL}/orders")
    if resp is None:
        return make_response(jsonify({"error": "order service unreachable"}), 503)
    try:
        return jsonify(resp.json()), resp.status_code
    except ValueError:
        app.logger.error("Order service returned non-JSON for /orders: %s", resp.text[:200])
        return make_response(jsonify({"error": "order service returned non-JSON"}), 502)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
