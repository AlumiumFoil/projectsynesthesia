# Project Synesthesia

Project Synesthesia is a Flask-based prototype that records a short audio clip and sends it to a backend endpoint intended to generate visual artwork from sound.

The current version includes a simple browser UI, microphone recording, backend health checking, and a placeholder audio-processing endpoint. The audio-to-art generation pipeline is planned but not fully implemented yet.

## Features

- Records 3 seconds of audio from the user's microphone.
- Sends recorded audio to the Flask backend using `FormData`.
- Provides a `/api/health` endpoint to confirm the backend is running.
- Provides a `/api/generate` endpoint as the future entry point for audio processing and image generation.
- Runs as a desktop-style app window through `flaskwebgui`.

## Project Structure

```text
projectsynesthesia/
├── backend/
│   ├── static
│       └── css/
│           └── styles.css
│   ├── templates/
│       └── index.html
│   ├── app.py
│   └── requirements.txt
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10 recommended
- Google Chrome or Chromium-based browser
- `pip` for installing Python dependencies

## Setup

From the project root, create and activate a virtual environment:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate.bat

OR

For MacOS/Linux:
source venv/bin/activate
```

Install the project dependencies:

```powershell
cd backend
pip install -r requirements.txt
```

## Run the App

Start the application from the `backend` folder while in the virtual environment:

```powershell
python app.py
```

The app opens a desktop-style window using `flaskwebgui`. From there, you an upload audio files for analysis.

## API Endpoints

### `GET /api/health`

Checks whether the backend is running.

Example response:

```json
{
  "status": "ok",
  "message": "Backend is running!"
}
```

### `POST /api/generate`

Receives uploaded audio from the frontend. Backend will analyze the audio features (tempo, texture, volume, brightness, etc.) and lyrics to send to an external image generation model

Example response:

```json
{
  "success": true,
  "image_url": image_url,
  "features": {
    "tempo": "152",
    "centroid": "870",
    "zcr": "0.046",
    "volume": "0.039"
  },
  "has_lyrics": true,
  "keywords": "never", "still", "know", "pain", "cannot", "love", "must"
  "lyrics_source": lyrics_source
  "prompt": "Abstract album art, evoking feelings and themes of {keywords}, {mood}, {colors}, {texture}, {intensity}, {rolloff_desc}, {bandwidth_desc}, {flatness_desc}, {chroma_color} tones, {texture_detail}, digital art, masterpiece, absurdres, high quality"
}
```

## Current Status

This project is a simple, but completed, tech demo. The frontend receives audio files and connects to the backend to analyze and send the data back to pollinations.ai. If lyrics are present, specific keywords will also be sent to affect the final image. The audio file can be played on the application as the image is being generated.


## Troubleshooting

- If dependencies fail to install, make sure the virtual environment is active and Python is available from the terminal.
- If the app does not open, try running `python app.py` from inside the `backend` folder.
- If any modules is missing or not found, make sure your Python version is lower than version 3.12
