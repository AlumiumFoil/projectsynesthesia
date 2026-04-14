from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flaskwebgui import FlaskUI
import os
import tempfile
import urllib.parse

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Call to generative AI image API
def pollinations_gen_img(prompt):
    # Generate image using free Pollinations.ai API
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://pollinations.ai/p/{encoded_prompt}?width=512&height=512"
    return url  # Returns a URL to the generated image

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
    import librosa
    import numpy as np
    import tempfile
    import os
    import urllib.parse
    import requests
    import random
    
    # Receive audio file from frontend
    if 'audio' not in request.files:
        return jsonify({'success': False, 'message': 'No audio file provided'})
    
    audio_file = request.files['audio']
    
    # Save temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
        audio_file.save(tmp.name)
        temp_path = tmp.name
    
    try:
        # Load audio with Librosa
        y, sr = librosa.load(temp_path, duration=3.0)
        
        # Extract features
        # Tempo (speed/rhythm)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Spectral centroid (brightness)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        avg_centroid = float(np.mean(centroid))
        
        # Zero crossing rate (noisiness/percussion)
        zcr = librosa.feature.zero_crossing_rate(y)
        avg_zcr = float(np.mean(zcr))
        
        # RMS energy (volume)
        rms = librosa.feature.rms(y=y)
        avg_volume = float(np.mean(rms))

        # =============================================
        # Map audio features to visual descriptions
        # Tempo mapping
        if tempo > 120:
            mood = "energetic chaotic dynamic explosive"
        elif tempo > 80:
            mood = "moderate flowing steady balanced"
        else:
            mood = "calm peaceful slow meditative"

        # Spectral centroid mapping - Brightness & Colors
        if avg_centroid > 3000:
            colors = "bright neon electric hot pink cyan yellow"
        elif avg_centroid > 2000:
            colors = "warm vibrant orange red gold"
        elif avg_centroid > 1000:
            colors = "earthy green brown olive"
        else:
            colors = "deep dark purple navy blue black"

        # Zero crossing rate mapping - Texture
        if avg_zcr > 0.1:
            texture = "rough sharp angular fractured jagged"
        elif avg_zcr > 0.05:
            texture = "textured detailed patterned"
        else:
            texture = "smooth soft curved flowing liquid"

        # Volume mapping - Intensity
        if avg_volume > 0.5:
            intensity = "bold intense high contrast saturated"
        elif avg_volume > 0.2:
            intensity = "balanced moderate"
        else:
            intensity = "subtle gentle pastel transparent"
        
        # =============================================

        # Build the prompt
        prompt = f"Abstract album art, {mood}, {colors}, {texture}, {intensity}, digital art, trending on ArtStation, high quality"
        print(f"Generated prompt: {prompt}")  # DEBUGGING
        print(f"Features - Tempo: {tempo:.1f}, Centroid: {avg_centroid:.0f}, ZCR: {avg_zcr:.3f}, Volume: {avg_volume:.3f}")

        # Generate image
        import random

        encoded_prompt = urllib.parse.quote(prompt)

        # Generate random seed
        random_seed = random.randint(1, 999999)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={random_seed}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # DEBUGGING - Verify the URL works
        try:
            response = requests.get(image_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # The URL is valid
                pass
            else:
                print(f"Image generation returned status: {response.status_code}")
        except Exception as img_error:
            print(f"Image request error: {img_error}")

        # Return results to frontend
        return jsonify({
            'success': True,
            'image_url': image_url,
            'features': {
                'tempo': round(tempo, 1),
                'centroid': round(avg_centroid, 0),
                'zcr': round(avg_zcr, 3),
                'volume': round(avg_volume, 3)
            },
            'prompt': prompt
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

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