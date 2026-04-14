import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flaskwebgui import FlaskUI
from werkzeug.utils import secure_filename

from audio_analysis import analyze_upload, write_temp_upload
from prompt_mapping import features_to_prompt

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_AUDIO_EXT = {".wav", ".webm", ".ogg", ".flac", ".mp3", ".m4a", ".opus"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running!"})


@app.route("/api/analyze", methods=["POST"])
def analyze_audio():
    """
    Accept raw audio upload, extract librosa features, apply rule-based prompt mapping.
    Weeks 2–3 pipeline (no external LLM / image API yet).
    """
    if "audio" not in request.files:
        return jsonify({"success": False, "message": "No audio file in request (expected field 'audio')."}), 400

    file = request.files["audio"]
    if not file or not file.filename:
        return jsonify({"success": False, "message": "Empty upload."}), 400

    raw_name = secure_filename(file.filename) or "clip"
    ext = Path(raw_name).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXT:
        ext = ".wav"

    tmp_path, _ = write_temp_upload(file, suffix=ext)
    try:
        features = analyze_upload(tmp_path)
        prompt_data = features_to_prompt(features)
    except Exception as exc:
        return jsonify({"success": False, "message": f"Analysis failed: {exc!s}"}), 400
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return jsonify(
        {
            "success": True,
            "features": features,
            "labels": prompt_data["labels"],
            "prompt_fragments": prompt_data["prompt_fragments"],
            "prompt_preview": prompt_data["prompt_preview"],
        }
    )


@app.route("/api/generate", methods=["POST"])
def generate_art():
    """Reserved for week 4+: LLM + Replicate image pipeline."""
    return jsonify(
        {
            "success": True,
            "message": "Image generation will be added when the API pipeline is wired.",
        }
    )


if __name__ == "__main__":
    if os.environ.get("FLASK_DEV") == "1":
        app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
    else:
        ui = FlaskUI(
            app=app,
            server="flask",
            width=1100,
            height=800,
        )
        ui.run()
