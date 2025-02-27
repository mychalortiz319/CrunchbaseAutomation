from flask import Flask, request, jsonify
import redis
from difflib import get_close_matches

app = Flask(__name__)

# Redis Connection Details
REDIS_HOST = "redis-13800.c276.us-east-1-2.ec2.redns.redis-cloud.com"
REDIS_PORT = 13800
REDIS_USERNAME = "default"
REDIS_PASSWORD = "7UykUJdubnrw7JCoMxlZOMUtK0TTNpQ5"

# Connect to Redis
r = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USERNAME,  # Only required if Redis has ACL authentication
    password=REDIS_PASSWORD,
    decode_responses=True  # Ensures responses are returned as strings
)

def get_cik_from_redis(company_name):
    """
    Searches Redis for a fuzzy and case-insensitive match and returns the CIK number.
    """
    if not company_name:
        return None  # Ensure input is valid

    company_name = company_name.strip().lower()

    # Fetch all keys from Redis (Company Names)
    keys = r.keys("*")
    normalized_keys = {key.strip().lower(): key for key in keys}  # Store original names for lookup

    # Use fuzzy matching to find the closest match
    closest_match = get_close_matches(company_name, normalized_keys.keys(), n=1, cutoff=0.6)

    if closest_match:
        best_match = normalized_keys[closest_match[0]]  # Get the original stored key
        return r.get(best_match)  # Return the corresponding CIK

    return None

@app.route("/get_cik", methods=["GET"])
def fetch_cik():
    """
    API Endpoint: /get_cik?company=CompanyName
    Takes a company name as a query parameter and returns the CIK number.
    """
    company_name = request.args.get("company")

    if not company_name:
        return jsonify({"error": "Company name required"}), 400

    cik = get_cik_from_redis(company_name)

    if cik:
        return jsonify({"company": company_name, "cik": cik})
    else:
        return jsonify({"error": "CIK not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Render prefers port 10000 or 8080
