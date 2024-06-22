import numpy as np
from PIL import Image, ImageDraw, ImageFont
import hashlib
import time
import random
import math
import base64
from io import BytesIO
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading

app = Flask(__name__)
CORS(app)

def get_background_color(serial_number):
    hash_object = hashlib.sha256(str(serial_number).encode())
    hex_dig = hash_object.hexdigest()
    r = int(hex_dig[:2], 16)
    g = int(hex_dig[2:4], 16)
    b = int(hex_dig[4:6], 16)
    return (r, g, b)

def calculate_grid_intersections(width, height, grid_size):
    intersections = []
    for x in range(0, width, grid_size):
        for y in range(0, height, grid_size):
            intersections.append((x, y))
    return intersections

def create_image_with_grid_and_circles(serial_number, circle_count):
    width, height = 1024, 512
    background_color = get_background_color(serial_number)
    original_background_color = background_color
    
    image = Image.new('RGB', (width, height), background_color)
    draw = ImageDraw.Draw(image)
    
    grid_color = tuple(min(c + 25, 255) for c in background_color)
    for x in range(0, width, 50):
        for y in range(0, height, 50):
            draw.rectangle([x, y, x + 49, y + 49], outline=grid_color)
    
    intersections = calculate_grid_intersections(width, height, 50)
    
    circles = []
    min_distance = 100
    
    for _ in range(circle_count):
        attempts = 0
        max_attempts = 1000
        while attempts < max_attempts:
            intersection = random.choice(intersections)
            grid_x, grid_y = intersection
            radius = random.randint(40, 50)
            circle_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            
            intersects = False
            for (existing_x, existing_y, existing_radius, _) in circles:
                distance = math.sqrt((grid_x - existing_x) ** 2 + (grid_y - existing_y) ** 2)
                if distance < radius + existing_radius + min_distance:
                    intersects = True
                    break
            
            if not intersects:
                draw.ellipse([grid_x - radius, grid_y - radius, grid_x + radius, grid_y + radius], fill=circle_color)
                circles.append((grid_x, grid_y, radius, circle_color))
                break
            
            attempts += 1
        
        if attempts == max_attempts:
            print("Warning: Max attempts reached, unable to place circle without intersection.")
    
    return image, circles, original_background_color

def update_image(image, circles, original_background_color):
    draw = ImageDraw.Draw(image)
    width, height = image.size
    
    image.paste(original_background_color, [0, 0, width, height])
    
    grid_color = tuple(min(c + 25, 255) for c in original_background_color)
    for x in range(0, width, 50):
        for y in range(0, height, 50):
            draw.rectangle([x, y, x + 49, y + 49], outline=grid_color)
    
    new_circles = []
    min_distance = 100
    
    for (grid_x, grid_y, radius, circle_color) in circles:
        grid_x += 50
        grid_y -= 50
        
        if grid_x >= width or grid_y < 0:
            grid_x = (grid_x % width) - (grid_y % height)
            grid_y = height - 25
        
        new_position = (grid_x, grid_y)
        for (existing_x, existing_y, existing_radius, _) in new_circles:
            distance = math.sqrt((new_position[0] - existing_x) ** 2 + (new_position[1] - existing_y) ** 2)
            if distance < radius + existing_radius + min_distance:
                dx = new_position[0] - existing_x
                dy = new_position[1] - existing_y
                direction = math.atan2(dy, dx)
                new_position = (
                    existing_x + int((radius + existing_radius + min_distance) * math.cos(direction)),
                    existing_y + int((radius + existing_radius + min_distance) * math.sin(direction))
                )
        
        draw.ellipse([new_position[0] - radius, new_position[1] - radius, new_position[0] + radius, new_position[1] + radius], fill=circle_color)
        new_circles.append((new_position[0], new_position[1], radius, circle_color))
    
    return image, new_circles

def add_timestamp(image):
    draw = ImageDraw.Draw(image)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    
    text_position = (10, image.height - 30)
    text_color = (255, 255, 255)
    draw.text(text_position, timestamp, fill=text_color, font=font)

    return image

serial_number = "A12345"
circle_count = 5
image, circles, original_background_color = create_image_with_grid_and_circles(serial_number, circle_count)
image = add_timestamp(image)

def update_image_periodically():
    global image, circles, original_background_color
    while True:
        time.sleep(10)
        image, circles = update_image(image, circles, original_background_color)
        image = add_timestamp(image)

thread = threading.Thread(target=update_image_periodically)
thread.start()


@app.route('/image', methods=['GET', 'OPTIONS'])
def get_image():
    global image
    if request.method == 'OPTIONS':
        response = app.response_class()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    response = jsonify({"image": img_str})
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
