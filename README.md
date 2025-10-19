
# Voice Assistant with Vosk-STT and n8n

This project is a Python-based voice assistant that listens for commands, converts them to text using the offline Vosk STT engine, and sends the text to an n8n workflow via a webhook. It uses `pyttsx3` for text-to-speech feedback and `Flask` to receive commands (like speaking) from n8n.

## Features

* **Offline Speech-to-Text:** Uses Vosk for fast, local STT.
* **Webhook Integration:** Sends recognized text to any n8n workflow.
* **Text-to-Speech Feedback:** Provides spoken responses from the assistant.
* **API Server:** Includes a simple Flask server on `http://127.0.0.1:5000` with a `/speak` endpoint so n8n can send text back to be spoken by the assistant.
* **Secure:** Uses a `.env` file to keep your webhook URL private.

---

## Setup and Installation

Follow these steps to get the project running on your local machine.

### 1. Clone the Repository (Optional)

If you're setting this up on a new machine, clone the repo first:

git clone [https://github.com/MehdiJabir/Vosk-STT_Piper-TTS_n8n.git](https://github.com/MehdiJabir/Vosk-STT_Piper-TTS_n8n.git)
cd Vosk-STT_Piper-TTS_n8n


### 2\. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment.


# Create the venv
python -m venv venv

# Activate it (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate it (macOS/Linux)
# source venv/bin/activate


### 3\. Install Dependencies

Install all the required Python packages from the `requirements.txt` file.


pip install -r requirements.txt


### 4\. Download the Vosk Model

This script is configured to use the small English model.

1.  Download the model (`vosk-model-small-en-us-0.15`) from the [Vosk website](https://alphacephei.com/vosk/models).
2.  Create a folder named `models` in the project directory.
3.  Extract the contents of the downloaded ZIP file into the `models` folder.




### 5\. Configure Your Environment File

This project uses a `.env` file to securely manage your n8n webhook URL.

1.  Create a file named `.env` in the root of the project directory.

2.  Add your n8n webhook URL to this file:

    ```
    # .env file
    N8N_WEBHOOK_URL="http://your-n8n-webhook-url-goes-here"
    ```

-----

## Usage

With your virtual environment activated and your `.env` file created, you can now run the assistant:


python voice_assistant_api.py


The script will initialize, and you will see "I am ready to listen." in your terminal and hear it spoken. You can now speak your commands.



