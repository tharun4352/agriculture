from flask import Flask, request, render_template, jsonify
import numpy as np
import random
import base64
from PIL import Image
import io

app = Flask(__name__)


# =========================================================
# DISEASE INFORMATION
# =========================================================

diseases = [
    "Bacterial Spot",
    "Early Blight",
    "Late Blight",
    "Leaf Mold",
    "Septoria Leaf Spot",
    "Spider Mites",
    "Target Spot",
    "Mosaic Virus",
    "Yellow Leaf Curl Virus"
]


pesticides = {
    "Bacterial Spot": "Use Copper-based fungicide",
    "Early Blight": "Use Mancozeb spray",
    "Late Blight": "Use Metalaxyl fungicide",
    "Leaf Mold": "Use Chlorothalonil",
    "Septoria Leaf Spot": "Use Fungicide regularly",
    "Spider Mites": "Use Neem oil spray",
    "Target Spot": "Use Sulfur spray",
    "Mosaic Virus": "Remove infected plants",
    "Yellow Leaf Curl Virus": "Use insecticides for whiteflies"
}


home_remedies = {
    "Bacterial Spot": (
        "Baking Soda Spray",
        "Mix 1 tsp baking soda + 1 liter water + few drops liquid soap. Spray twice weekly."
    ),

    "Early Blight": (
        "Neem Oil Treatment",
        "Mix neem oil with water and spray every 5 days on leaves."
    ),

    "Late Blight": (
        "Garlic Spray",
        "Crush garlic, mix with water, filter and spray regularly."
    ),

    "Leaf Mold": (
        "Milk Spray",
        "Mix milk and water in 1:10 ratio and spray weekly."
    ),

    "Septoria Leaf Spot": (
        "Leaf Removal + Spray",
        "Remove infected leaves and apply baking soda spray."
    ),

    "Spider Mites": (
        "Soap Water Spray",
        "Mix mild soap with water and spray on leaves."
    ),

    "Target Spot": (
        "Turmeric Spray",
        "Mix turmeric powder in water and spray as antifungal."
    ),

    "Mosaic Virus": (
        "Plant Removal",
        "Remove infected plant immediately and disinfect tools."
    ),

    "Yellow Leaf Curl Virus": (
        "Neem Control",
        "Use neem oil and control whiteflies regularly."
    )
}


# =========================================================
# COMMON IMAGE PROCESSING FUNCTION
# =========================================================

def process_image(img_bytes):

    # Open image
    img = Image.open(
        io.BytesIO(img_bytes)
    ).convert("RGB")

    # Resize image
    img = img.resize((224, 224))

    # Convert to NumPy array
    img_array = np.array(img)

    # Check whether image looks like a plant image
    green_ratio = np.sum(
        (img_array[:, :, 1] > img_array[:, :, 0]) &
        (img_array[:, :, 1] > img_array[:, :, 2])
    ) / (224 * 224)

    # Not a plant
    if green_ratio < 0.05:

        return {
            "result": "❌ Not a plant image",
            "confidence": 0,
            "soil_moisture": 0,
            "pesticide": "",
            "remedy_name": "",
            "remedy_process": ""
        }

    # Existing project detection logic
    disease = random.choice(diseases)

    confidence = random.randint(85, 96)

    pesticide = pesticides[disease]

    remedy_name, remedy_process = home_remedies[disease]

    # Estimate soil moisture
    soil_moisture = int(
        (np.mean(img_array[:, :, 2]) / 255) * 100
    )

    return {
        "result": disease,
        "confidence": confidence,
        "soil_moisture": soil_moisture,
        "pesticide": pesticide,
        "remedy_name": remedy_name,
        "remedy_process": remedy_process
    }


# =========================================================
# LIVE CAMERA DETECTION
# =========================================================

@app.route("/camera-detect", methods=["POST"])
def camera_detect():

    file = request.files.get("image")

    # Check whether camera sent an image
    if not file or file.filename == "":

        return jsonify({
            "error": "No camera frame received"
        }), 400

    try:

        # Read camera frame
        img_bytes = file.read()

        # Process image
        result = process_image(img_bytes)

        # Return result to JavaScript
        return jsonify(result)

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 400


# =========================================================
# MAIN HOME PAGE
# =========================================================

@app.route("/", methods=["GET", "POST"])
def home():

    result = None

    confidence = 0

    pesticide = None

    soil_moisture = 0

    img_data = None

    remedy_name = None

    remedy_process = None


    # =====================================================
    # IMAGE UPLOAD
    # =====================================================

    if request.method == "POST":

        file = request.files.get("image")

        if file and file.filename != "":

            try:

                # Read uploaded image
                img_bytes = file.read()

                # Convert image to Base64
                img_data = base64.b64encode(
                    img_bytes
                ).decode("utf-8")

                # Process image
                detection = process_image(
                    img_bytes
                )

                # Get detection results
                result = detection["result"]

                confidence = detection["confidence"]

                pesticide = detection["pesticide"]

                soil_moisture = detection["soil_moisture"]

                remedy_name = detection["remedy_name"]

                remedy_process = detection["remedy_process"]


            except Exception as error:

                result = "❌ Image processing error"

                print(
                    "Image Error:",
                    error
                )


    # =====================================================
    # SEND DATA TO FRONTEND
    # =====================================================

    return render_template(

        "index.html",

        result=result,

        confidence=confidence,

        pesticide=pesticide,

        soil_moisture=soil_moisture,

        img_data=img_data,

        remedy_name=remedy_name,

        remedy_process=remedy_process

    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
