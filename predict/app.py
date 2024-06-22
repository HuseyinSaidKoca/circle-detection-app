from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import threading
import time
import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
CORS(app)

def load_image_from_base64(base64_string):
    image_data = base64.b64decode(base64_string)
    image = Image.open(BytesIO(image_data))
    return image

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def detect_circles_using_roboflow(base64_image, api_key):
    url = "https://detect.roboflow.com/circle-detection-k90sy/1"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, params={"api_key": api_key}, data=base64_image, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def draw_detections_on_image(image, detections):
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    for detection in detections:
        x = detection['x']
        y = detection['y']
        width = detection['width']
        height = detection['height']
        confidence = detection['confidence']

        left = x - width / 2
        top = y - height / 2
        right = x + width / 2
        bottom = y + height / 2

        # Draw rectangle
        draw.rectangle([left, top, right, bottom], outline="red", width=2)

        # Draw confidence
        draw.text((left, top - 10), f"{confidence:.2f}", fill="red", font=font)

    return image

@app.route('/detect', methods=['POST', 'OPTIONS'])
def detect_circles():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    data = request.get_json()
    image_base64_str = data.get('image')

    if not image_base64_str:
        return jsonify({"error": "No image provided"}), 400

    # Detect circles using Roboflow API
    api_key = "t8UnnWwTH4Pl7YCaDGQP"
    detection_result = detect_circles_using_roboflow(image_base64_str, api_key)

    if detection_result is None:
        return jsonify({"error": "Detection failed"}), 500

    predictions = detection_result.get("predictions", [])

    # Load the original image
    image = load_image_from_base64(image_base64_str)

    # Draw detections on the image
    image = draw_detections_on_image(image, predictions)

    # Convert the modified image to base64
    modified_image_base64 = image_to_base64(image)

    response = {
        "image": modified_image_base64,
        "circle_count": len(predictions)
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
