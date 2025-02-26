from flask import Flask, request, jsonify
import re
import requests
from fuzzywuzzy import process

app = Flask(__name__)

# 🔹 Crunchbase API Key (Replace with your actual key)
CRUNCHBASE_API_KEY = "086b8252bb04f976c7c4d6e692f72544"

# 🏷️ Step 1: Normalize Company Name
def normalize_company_name(name):
    """Normalize company names by removing suffixes and punctuation."""
    name = name.upper().strip()
    suffixes = [" INC", " LLC", " CORP", " CORPORATION", " LTD", " LIMITED", " LP", " L.P."]
    
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    
    name = re.sub(r'[^A-Z0-9 ]', '', name)  # Remove special characters
    return name

# 🔍 Step 2: Search Crunchbase API
def search_crunchbase(company_name):
    """Search for a company in Crunchbase using its API."""
    url = "https://api.crunchbase.com/api/v4/searches/organizations"
    
    headers = {
        "Authorization": f"Bearer {CRUNCHBASE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": company_name,
        "field_ids": ["identifier"],
        "limit": 10
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return [entry["identifier"]["value"].upper() for entry in data.get("entities", [])]
    
    return None

# 🎯 Step 3: Apply Fuzzy Matching
def get_best_crunchbase_match(apollo_name, crunchbase_names):
    """Find the best match using fuzzy matching."""
    normalized_name = normalize_company_name(apollo_name)
    
    if not crunchbase_names:
        return None, 0  # No matches found

    best_match, score = process.extractOne(normalized_name, crunchbase_names)
    
    return (best_match, score) if score >= 85 else (None, score)  # Adjust threshold as needed

# 🚀 Step 4: API Route to Handle Requests
@app.route('/match_company', methods=['POST'])
def match_company():
    """API endpoint to get the best Crunchbase match for a given company."""
    data = request.get_json()

    if not data or "company_name" not in data:
        return jsonify({"error": "Missing company_name parameter"}), 400
    
    company_name = data["company_name"]
    crunchbase_results = search_crunchbase(company_name)
    
    if not crunchbase_results:
        return jsonify({"company_name": company_name, "match": None, "confidence_score": 0})
    
    best_match, score = get_best_crunchbase_match(company_name, crunchbase_results)
    
    return jsonify({
        "company_name": company_name,
        "match": best_match,
        "confidence_score": score
    })

# ✅ Run the Flask App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
