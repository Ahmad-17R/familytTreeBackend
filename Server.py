from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from io import BytesIO
from backend import create_family_tree_graph  # Import the correct function
import json
import os

app = Flask(__name__)
# Enable CORS for the /generate-family-tree endpoint, allowing requests from any origin
CORS(app, resources={r"/generate-family-tree": {"origins": "*"}})

# Optional: Basic health/home route to avoid 404s
@app.route("/", methods=["GET"])
def home():
    return "🚀 Family Tree Generator API is Live!", 200

@app.route("/generate-family-tree", methods=["POST", "OPTIONS"])
def generate_family_tree():
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    try:
        # Get JSON data from request
        family_data = request.get_json()

        if not family_data:
            return jsonify({"error": "No family data provided"}), 400

        # Convert dictionary to JSON string for create_family_tree_graph
        family_data_json = json.dumps(family_data)

        # Generate the family tree image
        create_family_tree_graph(family_data_json)

        # Read the generated image
        image_path = "family_tree.png"
        if not os.path.exists(image_path):
            return jsonify({"error": "Family tree image not generated"}), 500

        with open(image_path, "rb") as f:
            img_bytes = BytesIO(f.read())

        # Clean up the image file
        os.remove(image_path)
        img_bytes.seek(0)

        return send_file(
            img_bytes,
            mimetype="image/png",
            as_attachment=False,
            download_name="family_tree.png"
        )

    except Exception as e:
        print(f"Error generating family tree: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)