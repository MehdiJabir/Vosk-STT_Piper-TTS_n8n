import sys
import os
import json
import threading
import time
import queue
import sounddevice as sd 
import pyttsx3
import requests
from flask import Flask, request, jsonify


# Import Vosk components, suppressing logs
from vosk import Model, KaldiRecognizer, SetLogLevel
SetLogLevel(0)

# --- Configuration ---
# Set the path to your working Vosk model.
VOSK_MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models', 'vosk-model-small-en-us-0.15')

# IMPORTANT: Replace with the actual URL from your n8n Webhook node.
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")

if not N8N_WEBHOOK_URL:
    print("ERROR: Environment variable N8N_WEBHOOK_URL is not set.")
    sys.exit(1)
# --- Audio Configuration ---
# We will now use your headset's detected sample rate from the logs.
SAMPLERATE = 44100
CHANNELS = 1
BLOCKSIZE = 8192
INPUT_DEVICE = None # Use default input device

# --- Flask App Setup ---
app = Flask(__name__)
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- Global Queue for Audio Data ---
# We are going back to the callback and queue model since it works.
q = queue.Queue()

# --- Callback Function for Audio Stream (runs in a separate thread handled by sounddevice) ---
def callback(indata, frames, time, status):
    if status:
        print(f"Sounddevice status: {status}", file=sys.stderr)
    q.put(bytes(indata))

# --- Text-to-Speech Engine Initialization ---
tts_engine = None
try:
    tts_engine = pyttsx3.init()
    voices = tts_engine.getProperty('voices')
    if voices:
        tts_engine.setProperty('voice', voices[1].id)
    print("Pyttsx3 engine initialized successfully.")
except Exception as e:
    print(f"Error initializing Pyttsx3 engine: {e}", file=sys.stderr)
    print("Text-to-speech functionality will be unavailable.", file=sys.stderr)

# --- TTS speaking function ---
def speak(text):
    if tts_engine:
        # We no longer wait here. Just add the text to the speech queue.
        print(f"Assistant: {text}")
        tts_engine.say(text) 
    else:
        print(f"Assistant (TTS unavailable): {text}")

# --- Flask API Endpoint for TTS ---
@app.route('/speak', methods=['POST'])
def speak_endpoint():
    data = request.json
    text_to_speak = data.get('text')
    if text_to_speak:
        threading.Thread(target=speak, args=(text_to_speak,)).start()
        return jsonify({"status": "success", "message": "Speaking initiated"}), 200
    return jsonify({"status": "error", "message": "No text provided"}), 400

# --- Flask Server Function (runs in a separate thread) ---
def run_flask_app():
    """Starts the Flask web server."""
    print("Starting Flask web server on http://127.0.0.1:5000")
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error starting Flask app: {e}", file=sys.stderr)

# --- Main Entry Point (Runs the audio listener in the main thread) ---
if __name__ == "__main__":
    # Start the Flask web server in a separate daemon thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    flask_thread.start()

    # 1. Verify Vosk model exists
    if not os.path.exists(VOSK_MODEL_DIR):
        print(f"ERROR: Vosk model not found at {VOSK_MODEL_DIR}")
        print("Please download and extract the model to the specified path.")
        sys.exit(1)

    try:
        # 2. Determine default sample rate
        device_info = sd.query_devices(INPUT_DEVICE, "input")
        samplerate_detected = int(device_info["default_samplerate"])
        print(f"Using default input device: {device_info['name']}")
        print(f"Detected sample rate: {samplerate_detected} Hz")

        # 3. Load Vosk model
        model = Model(VOSK_MODEL_DIR)
        rec = KaldiRecognizer(model, samplerate_detected)

        # 4. Start the TTS engine's non-blocking loop
        if tts_engine:
            # This starts the background thread for speech processing
            tts_engine.startLoop(False)

        # 5. Start the audio stream using the callback
        with sd.RawInputStream(
            samplerate=samplerate_detected,
            blocksize=BLOCKSIZE,
            device=INPUT_DEVICE,
            dtype="int16",
            channels=CHANNELS,
            callback=callback
        ):
            print("-" * 80)
            print("Listening for speech (Press Ctrl+C to stop)")
            print("-" * 80)

            speak("I am ready to listen.")

            # 6. Process audio and TTS events in the main thread
            while True:
                # This call is essential. It processes any pending speech tasks.
                if tts_engine:
                    tts_engine.iterate()

                data = q.get()
                if rec.AcceptWaveform(data):
                    recognized_text = json.loads(rec.Result()).get("text", "").strip()
                    if recognized_text:
                        print(f"You: {recognized_text}")
                        # --- Send recognized text to n8n via webhook ---
                        print("Assistant: Thinking...") # Visual feedback
                        try:
                            response = requests.post(N8N_WEBHOOK_URL, json={"text": recognized_text}, timeout=10)
                            response.raise_for_status()
                            print(f"SUCCESS: Data sent to n8n. Status Code: {response.status_code}")
                        except requests.exceptions.RequestException as e:
                            print(f"ERROR: Failed to send data to n8n. Error: {e}", file=sys.stderr)
                            speak("I'm having trouble connecting to my brain. Please check the connection.")

    except (KeyboardInterrupt, SystemExit):
        print("\nCtrl+C detected. Shutting down application.")
    except Exception as e:
        print(f"\nAn error occurred in the main thread: {type(e).__name__}: {e}", file=sys.stderr)
    finally:
        # Cleanly stop all resources
        if tts_engine:
            # This ensures the background TTS thread is stopped properly
            tts_engine.endLoop()
        sd.stop()
        print("Application terminated and resources released.")