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
    import librosa
    import numpy as np
    import tempfile
    import os
    
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
        
        # Return features for now - No image generation yet as of 4/13/2026
        return jsonify({
            'success': True,
            'features': {
                'tempo': round(tempo, 1),
                'centroid': round(avg_centroid, 0),
                'zcr': round(avg_zcr, 3),
                'volume': round(avg_volume, 3)
            },
            'message': f'Analyzed: {round(tempo, 1)} BPM, brightness: {round(avg_centroid, 0)}'
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