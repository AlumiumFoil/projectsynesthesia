from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flaskwebgui import FlaskUI
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Home page route
@app.route('/')
def index():
    return render_template('index.html')

# Backend check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Backend is running!'})

# Audio processing endpoint (placeholder for now)
@app.route('/api/generate', methods=['POST'])
def generate_art():
    # Librosa and image generation will go here
    return jsonify({
        'success': True,
        'message': 'Audio received! Processing will be added soon.'
    })

# Run the app
if __name__ == '__main__':
    # Use flaskwebgui to create desktop window
    # Setting close_server_on_exit=True ensures everything shuts down properly
    ui = FlaskUI(
        app=app,
        server="flask",
        width=1024,
        height=768
    )
    ui.run()