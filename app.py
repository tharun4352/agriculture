from flask import Flask, request, render_template, jsonify, session
from openai import OpenAI
import numpy as np
import random
import base64
from PIL import Image
import io
import os


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

# Secret used by Flask sessions
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "smart-agriculture-development-key"
)


# =========================================================
# OPENAI CLIENT
# =========================================================

# The API key is NOT written in this file.
# Render provides it through OPENAI_API_KEY.

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)


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
    "Bacterial Spot":
        "Use a suitable copper-based fungicide according to the product label.",

    "Early Blight":
        "Use an appropriate fungicide such as Mancozeb according to the product label.",

    "Late Blight":
        "Use an appropriate fungicide according to local agricultural guidance.",

    "Leaf Mold":
        "Use an appropriate fungicide such as Chlorothalonil according to the product label.",

    "Septoria Leaf Spot":
        "Use an appropriate fungicide and remove severely infected leaves.",

    "Spider Mites":
        "Neem-based treatment or an appropriate miticide may help. Follow the product label.",

    "Target Spot":
        "Use an appropriate fungicide according to the product label.",

    "Mosaic Virus":
        "Remove severely infected plants and control insect vectors such as aphids.",

    "Yellow Leaf Curl Virus":
        "Control whiteflies and remove severely infected plants."
}


home_remedies = {

    "Bacterial Spot": (
        "Baking Soda Spray",
        "Use a mild baking-soda-based spray only as a supplementary measure. "
        "Avoid spraying during strong sunlight and test on a small area first."
    ),

    "Early Blight": (
        "Neem Oil Support",
        "Neem-based treatment may help with general plant protection. "
        "Remove affected leaves and maintain good airflow."
    ),

    "Late Blight": (
        "Garlic Spray Support",
        "A homemade garlic spray may provide limited supportive protection, "
        "but serious late blight requires proper disease management."
    ),

    "Leaf Mold": (
        "Improve Airflow",
        "Remove heavily affected leaves, avoid wetting foliage unnecessarily, "
        "and improve ventilation around plants."
    ),

    "Septoria Leaf Spot": (
        "Remove Infected Leaves",
        "Remove badly affected leaves and keep foliage dry when possible. "
        "Disinfect gardening tools after use."
    ),

    "Spider Mites": (
        "Gentle Water Spray",
        "A gentle spray of water can help remove mites from leaves. "
        "Monitor the plant regularly."
    ),

    "Target Spot": (
        "Improve Plant Hygiene",
        "Remove badly affected leaves and plant debris and maintain good airflow."
    ),

    "Mosaic Virus": (
        "Remove Infected Plants",
        "Severely infected plants should generally be removed to reduce spread. "
        "Disinfect tools after handling them."
    ),

    "Yellow Leaf Curl Virus": (
        "Control Whiteflies",
        "Monitor and control whiteflies, which can spread the virus. "
        "Remove severely infected plants."
    )
}


# =========================================================
# IMAGE PROCESSING
# =========================================================

def process_image(img_bytes):

    try:

        image = Image.open(
            io.BytesIO(img_bytes)
        ).convert("RGB")

        image = image.resize(
            (224, 224)
        )

        image_array = np.array(image)

        # Basic plant-image check
        green_ratio = np.sum(
            (image_array[:, :, 1] > image_array[:, :, 0]) &
            (image_array[:, :, 1] > image_array[:, :, 2])
        ) / (224 * 224)


        if green_ratio < 0.05:

            return {
                "result": "Not a plant image",
                "confidence": 0,
                "soil_moisture": 0,
                "pesticide": "",
                "remedy_name": "",
                "remedy_process": ""
            }


        # -------------------------------------------------
        # CURRENT PROJECT DETECTION
        #
        # IMPORTANT:
        # This keeps the detection behavior from your
        # current project.
        #
        # Your model.joblib can be connected separately
        # once its input/output format is confirmed.
        # -------------------------------------------------

        disease = random.choice(
            diseases
        )


        confidence = random.randint(
            85,
            96
        )


        pesticide = pesticides.get(
            disease,
            "Follow local agricultural guidance."
        )


        remedy_name, remedy_process = home_remedies.get(
            disease,
            (
                "General plant care",
                "Remove affected leaves and monitor the plant."
            )
        )


        # Simple moisture estimate
        soil_moisture = int(
            np.mean(
                image_array[:, :, 2]
            ) / 255 * 100
        )


        return {

            "result": disease,

            "confidence": confidence,

            "soil_moisture": soil_moisture,

            "pesticide": pesticide,

            "remedy_name": remedy_name,

            "remedy_process": remedy_process

        }


    except Exception as error:

        raise Exception(
            f"Image processing failed: {error}"
        )


# =========================================================
# CAMERA DETECTION
# =========================================================

@app.route(
    "/camera-detect",
    methods=["POST"]
)
def camera_detect():

    file = request.files.get(
        "image"
    )


    if not file:

        return jsonify({
            "error": "No camera frame received."
        }), 400


    try:

        image_bytes = file.read()

        result = process_image(
            image_bytes
        )


        # Save latest detection in session
        session["detection"] = result


        return jsonify(
            result
        )


    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 400


# =========================================================
# HOME PAGE
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def home():

    result = None

    confidence = 0

    pesticide = None

    soil_moisture = 0

    img_data = None

    remedy_name = None

    remedy_process = None


    if request.method == "POST":

        file = request.files.get(
            "image"
        )


        if file and file.filename:

            try:

                image_bytes = file.read()


                # Convert uploaded image to Base64
                img_data = base64.b64encode(
                    image_bytes
                ).decode("utf-8")


                detection = process_image(
                    image_bytes
                )


                result = detection["result"]

                confidence = detection["confidence"]

                pesticide = detection["pesticide"]

                soil_moisture = detection["soil_moisture"]

                remedy_name = detection["remedy_name"]

                remedy_process = detection["remedy_process"]


                # Save latest detection
                session["detection"] = detection


            except Exception as error:

                result = (
                    "Image processing error"
                )

                print(
                    "Image processing error:",
                    error
                )


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
# AI SYSTEM INSTRUCTIONS
# =========================================================

AGRICULTURE_SYSTEM_PROMPT = """

You are Smart Agriculture AI, an intelligent agricultural
assistant integrated into a plant disease detection application.

Your job is to help farmers, students, gardeners and agricultural
users understand plant health and farming questions.

You should behave like a natural conversational AI assistant.

IMPORTANT BEHAVIOR:

1. Understand the user's actual question.

2. Do NOT repeat the same answer for every question.

3. Answer follow-up questions using the conversation context.

4. If a plant detection result is provided, use it as context.

5. If the user asks about the detected disease, explain it clearly.

6. If the user asks for treatment, give practical and safe
   agricultural guidance.

7. Do not pretend that a prediction is 100% certain.

8. Explain that image-based disease detection can make mistakes
   when appropriate.

9. Do not recommend unsafe chemical mixing.

10. For pesticides or agricultural chemicals, tell users to follow
    the product label and local agricultural guidance.

11. If you do not know something, say so instead of inventing
    information.

12. Keep answers understandable for ordinary farmers.

13. You can answer in English, Hindi, Telugu, Tamil or Kannada.

14. Reply in the language requested by the user.

15. If the user asks a general question unrelated to agriculture,
    you may still answer normally, but keep the assistant's
    agricultural purpose in mind.

16. You are a conversational assistant, not merely a fixed
    question-and-answer system.

"""



# =========================================================
# AI CHAT ENDPOINT
# =========================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    try:

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({
                "error": "No message received."
            }), 400


        user_message = str(
            data.get(
                "message",
                ""
            )
        ).strip()


        if not user_message:

            return jsonify({
                "error": "Please enter a message."
            }), 400


        # -------------------------------------------------
        # GET PREVIOUS CONVERSATION
        # -------------------------------------------------

        conversation = session.get(
            "conversation",
            []
        )


        # Keep the session reasonably small
        conversation = conversation[-12:]


        # -------------------------------------------------
        # CURRENT PLANT DETECTION
        # -------------------------------------------------

        detection = session.get(
            "detection"
        )


        detection_context = ""


        if detection:

            detection_context = f"""

CURRENT PLANT DETECTION:

Disease/result:
{detection.get("result")}

Confidence:
{detection.get("confidence")}%

Estimated soil moisture:
{detection.get("soil_moisture")}%

Pesticide information:
{detection.get("pesticide")}

Home remedy:
{detection.get("remedy_name")}

Remedy process:
{detection.get("remedy_process")}

Use this information only as supporting context.
Do not claim that the detection is perfectly accurate.

"""


        # -------------------------------------------------
        # BUILD INPUT
        # -------------------------------------------------

        input_messages = []


        for message in conversation:

            input_messages.append(
                {
                    "role": message["role"],
                    "content": message["content"]
                }
            )


        input_messages.append(

            {
                "role": "user",

                "content":
                    detection_context +
                    "\n\nUSER QUESTION:\n" +
                    user_message
            }

        )


        # -------------------------------------------------
        # CALL OPENAI
        # -------------------------------------------------

        response = client.responses.create(

            model="gpt-5-mini",

            instructions=AGRICULTURE_SYSTEM_PROMPT,

            input=input_messages

        )


        assistant_message = (
            response.output_text
            if response.output_text
            else "I couldn't generate a response."
        )


        # -------------------------------------------------
        # SAVE CONVERSATION
        # -------------------------------------------------

        conversation.append(

            {
                "role": "user",
                "content": user_message
            }

        )


        conversation.append(

            {
                "role": "assistant",
                "content": assistant_message
            }

        )


        session["conversation"] = (
            conversation[-12:]
        )


        # -------------------------------------------------
        # RETURN ANSWER
        # -------------------------------------------------

        return jsonify({

            "answer": assistant_message

        })


    except Exception as error:

        print(
            "OpenAI error:",
            error
        )


        return jsonify({

            "error":
                "The AI assistant could not respond. "
                "Please check your OpenAI API configuration."

        }), 500


# =========================================================
# CLEAR CHAT
# =========================================================

@app.route(
    "/clear-chat",
    methods=["POST"]
)
def clear_chat():

    session.pop(
        "conversation",
        None
    )


    return jsonify({
        "success": True
    })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "Smart Agriculture AI is running"
    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),

        debug=True

    )
