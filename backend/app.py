from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flaskwebgui import FlaskUI
import os
import tempfile
import urllib.parse
import requests
import random
import librosa
import numpy as np
import syncedlyrics
from mutagen import File as MutagenFile

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

def extract_metadata_and_lyrics(audio_path, user_title=None, user_artist=None):
    """Extract artist and title from audio file metadata or use user input, then fetch lyrics"""
    try:
        artist = user_artist
        title = user_title
        
        # If user didn't provide info, try to extract from metadata
        if not artist or not title:
            # Extract metadata using mutagen
            audio = MutagenFile(audio_path)
            
            # Try standard tag formats
            if hasattr(audio, 'get'):
                if not artist:
                    artist = audio.get('artist', [None])[0]
                if not title:
                    title = audio.get('title', [None])[0]
            
            # Handle MP4/M4A tags
            if not artist and '©ART' in audio:
                artist = str(audio['©ART'][0])
            if not title and '©nam' in audio:
                title = str(audio['©nam'][0])
            
            # Handle ID3 tags (MP3 format)
            if not artist and 'TPE1' in audio:
                artist = str(audio['TPE1'].text[0])
            if not title and 'TIT2' in audio:
                title = str(audio['TIT2'].text[0])
        
        # If we have either title or artist, try to fetch lyrics
        if title or artist:
            print(f"Searching lyrics - Artist: {artist}, Title: {title}")
            return fetch_lyrics_from_title_artist(title, artist)
        else:
            print("No title or artist found for lyrics search")
            return ""
            
    except Exception as e:
        print(f"Metadata extraction failed: {e}")
        return ""


def extract_keywords_from_lyrics(lyrics):
    """Extract key themes, emotions, and imagery from lyrics using keyword extraction"""
    if not lyrics or len(lyrics.strip()) < 20:
        return ""
    
    try:
        # Common words to ignore (stopwords)
        stopwords = {'the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'you', 'that', 
                     'was', 'for', 'on', 'are', 'with', 'as', 'i', 'be', 'this', 'have',
                     'from', 'at', 'by', 'not', 'but', 'what', 'all', 'were', 'when',
                     'your', 'can', 'said', 'there', 'use', 'an', 'each', 'which', 'she',
                     'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out',
                     'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make',
                     'like', 'him', 'into', 'time', 'has', 'look', 'two', 'more', 'write',
                     'go', 'see', 'number', 'no', 'way', 'could', 'people', 'than', 'first',
                     'water', 'been', 'call', 'who', 'oil', 'its', 'now', 'find', 'long',
                     'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part'}
        
        # Convert to lowercase and split into words
        words = lyrics.lower().split()
        
        # Filter out stopwords and short words, count frequencies
        word_freq = {}
        for word in words:
            # Remove punctuation
            clean_word = word.strip('.,!?;:()[]\'"')
            if len(clean_word) > 3 and clean_word not in stopwords:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # Get top 8-10 keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        top_keywords = [word for word, count in sorted_words[:10] if len(word) > 3]
        
        # Also look for emotional indicator words
        emotion_words = {
            'love', 'happy', 'sad', 'cry', 'pain', 'joy', 'heart', 'broken', 
            'dream', 'night', 'light', 'dark', 'fire', 'rain', 'sun', 'moon',
            'star', 'angel', 'demon', 'heaven', 'hell', 'free', 'lost', 'found'
        }
        
        emotions_found = [word for word in words if word in emotion_words]
        
        # Combine keywords and unique emotions
        all_keywords = list(set(top_keywords + emotions_found[:3]))
        
        if all_keywords:
            keyword_string = ", ".join(all_keywords[:8])
            print(f"Extracted keywords: {keyword_string}")
            return keyword_string
        else:
            return ""
            
    except Exception as e:
        print(f"Keyword extraction failed: {e}")
        return ""

def fetch_lyrics_from_title_artist(title, artist):
    """Fetch lyrics using song title and artist name with syncedlyrics"""
    if not title and not artist:
        return ""
    
    try:
        # Build search query
        if title and artist:
            search_query = f"{title} {artist}"
        elif title:
            search_query = title
        else:
            search_query = artist
        
        print(f"Searching syncedlyrics with query: {search_query}")
        lyrics = syncedlyrics.search(search_query)
        
        if lyrics:
            print(f"Successfully fetched lyrics ({len(lyrics)} characters)")
            # Clean LRC timestamps if present
            import re
            plain_lyrics = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', lyrics)
            plain_lyrics = re.sub(r'\n\s*\n', '\n', plain_lyrics).strip()
            return plain_lyrics
        else:
            print("No lyrics found for this query")
            return ""
            
    except Exception as e:
        print(f"Lyrics fetch failed: {e}")
        return ""

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
    # Receive audio file from frontend
    if 'audio' not in request.files:
        return jsonify({'success': False, 'message': 'No audio file provided'})
    
    audio_file = request.files['audio']

    # Get optional user inputs
    user_title = request.form.get('song_title', '')
    user_artist = request.form.get('song_artist', '')
    
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

        # Spectral rolloff
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
        avg_rolloff = float(np.mean(rolloff))

        # Spectral bandwidth
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        avg_bandwidth = float(np.mean(bandwidth))

        # Spectral flatness - noise vs tone (0 = pure tone, 1 = white noise)
        flatness = librosa.feature.spectral_flatness(y=y)
        avg_flatness = float(np.mean(flatness))

        # First 3 MFCCs - Timbre features
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc1 = float(np.mean(mfccs[0]))  # Overall spectral shape
        mfcc2 = float(np.mean(mfccs[1]))  # Spectral detail
        mfcc3 = float(np.mean(mfccs[2]))  # Fine spectral structure

        # Chroma features - Pitch class, maps to colors
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        dominant_chroma = np.argmax(np.mean(chroma, axis=1))  # Which note is strongest

        # =============================================

        print("Attempting to extract lyrics from audio file...")
        lyrics_text = ""
        keywords = ""
        lyrics_source = None

        # Get lyrics using user input (if provided) or file metadata
        print("Attempting to extract lyrics...")
        lyrics_text = extract_metadata_and_lyrics(temp_path, user_title, user_artist)
        if lyrics_text:
            lyrics_source = "user_input" if (user_title or user_artist) else "metadata"
            print(f"Lyrics found via {lyrics_source}")
            keywords = extract_keywords_from_lyrics(lyrics_text)
            if keywords:
                print(f"Extracted keywords: {keywords}")
        else:
            print("No lyrics found for this audio file")

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

        # Spectral rolloff mapping
        if avg_rolloff > 5000:
            rolloff_desc = "bright airy sparkling"
        elif avg_rolloff > 3000:
            rolloff_desc = "clear present"
        else:
            rolloff_desc = "bassy heavy warm"

        # Spectral bandwidth mapping
        if avg_bandwidth > 3000:
            bandwidth_desc = "complex layered rich"
        elif avg_bandwidth > 1500:
            bandwidth_desc = "balanced full"
        else:
            bandwidth_desc = "pure focused simple"

        # Spectral flatness mapping
        if avg_flatness > 0.5:
            flatness_desc = "noisy textured static"
        elif avg_flatness > 0.2:
            flatness_desc = "mixed harmonic"
        else:
            flatness_desc = "tonal melodic clear"

        # Chroma to color mapping (musical note to visual color)
        chroma_colors = ["red", "orange", "yellow", "yellow-green", "green", 
                        "teal", "cyan", "blue", "indigo", "purple", "magenta", "pink"]
        chroma_color = chroma_colors[dominant_chroma % 12]

        # MFCC-based texture mapping
        if mfcc1 > 0:
            texture_detail = "smooth refined"
        else:
            texture_detail = "crisp defined"
        
        # =============================================

        # Build the prompt
        if keywords:
            prompt = f"Abstract album art, evoking feelings and themes of {keywords}, {mood}, {colors}, {texture}, {intensity}, {rolloff_desc}, {bandwidth_desc}, {flatness_desc}, {chroma_color} tones, {texture_detail}, digital art, masterpiece, absurdres, high quality"
            print(f"Keywords: {keywords}")
        else:
            prompt = f"Abstract album art, {mood}, {colors}, {texture}, {intensity}, {rolloff_desc}, {bandwidth_desc}, {flatness_desc}, {chroma_color} tones, {texture_detail}, digital art, masterpiece, absurdres, high quality"
        print(f"Features - Tempo: {tempo:.1f}, Centroid: {avg_centroid:.0f}, ZCR: {avg_zcr:.3f}, Volume: {avg_volume:.3f}")

        # Generate image
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
            'has_lyrics': bool(lyrics_text),
            'keywords': keywords if keywords else None,
            'lyrics_source': lyrics_source,
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