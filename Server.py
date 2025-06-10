from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from io import BytesIO
from backend import draw_family_tree  # Assumes this is your script for generating the family tree
import tempfile
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
        family_data = request.get_json()

        if not family_data:
            return jsonify({"error": "No family data provided"}), 400

        # Use a temporary file to save the image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            image_path = tmp_file.name

        # Generate the family tree image using the provided function
        draw_family_tree(family_data, output_file=image_path)

        # Load image into memory and send
        with open(image_path, "rb") as f:
            img_bytes = BytesIO(f.read())

        # Clean up the temporary file
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
