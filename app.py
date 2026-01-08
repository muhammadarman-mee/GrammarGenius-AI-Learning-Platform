import os
import json
import requests
from pathlib import Path
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# Removed lru_cache as it's not compatible with non-hashable arguments like lists
# from functools import lru_cache

# Optional: Google TTS
try:
    from google.cloud import texttospeech

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# ===== CONFIG =====
# Your Gemini API key has been added here.
GEMINI_API_KEY = "replace api"
GEMINI_MODEL = "gemini-2.5-flash-preview-05-20"
DEFAULT_LANG = "en-US"

# We define the JSON schema that the front-end expects and the API will generate.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "corrected_text": {"type": "string"},
        "explanation": {"type": "string"},
        "vocabulary_tips": {"type": "string"}
    },
    "required": ["corrected_text"]
}
# Schema for interactive exercises
EXERCISE_SCHEMA = {
    "type": "object",
    "properties": {
        "exercise_text": {"type": "string"},
        "correct_answer": {"type": "string"},
        "options": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["exercise_text", "correct_answer"]
}

VOICES = {
    "en-US": "en-US-Neural2-C",
    "es-ES": "es-ES-Neural2-B",
    "fr-FR": "fr-FR-Standard-A",
    "de-DE": "de-DE-Wavenet-F",
    "it-IT": "it-IT-Wavenet-D",
    "zh-CN": "cmn-CN-Wavenet-A",
    "ja-JP": "ja-JP-Standard-D",
    "ur-PK": "ur-PK-Standard-A"
}

BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "static" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# ===== INIT APP =====
app = Flask(__name__)
CORS(app)

_tts_client = None


def get_tts_client():
    global _tts_client
    if _tts_client is None and GOOGLE_AVAILABLE:
        try:
            _tts_client = texttospeech.TextToSpeechClient()
        except Exception as e:
            print("⚠ Google Cloud TTS not available:", e)
            return None
    return _tts_client


# We can't cache a function that takes a list as an argument
# because lists are not hashable.
# @lru_cache(maxsize=128)
def get_ai_response_from_gemini(user_text, chat_history, persona, lang):
    """
    Updated to handle chat history and AI persona for contextual conversations.
    """
    print(f"📩 Calling Gemini API for: {user_text} | lang: {lang} | persona: {persona}")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    # Build a context-aware prompt
    persona_prompt = f"You are a helpful language tutor with a {persona} personality. "
    history_prompt = "Here is the past conversation for context:\n" + "\n".join(
        [f"User: {h['user']}\nAI: {h['ai']}" for h in chat_history]
    ) if chat_history else ""

    main_prompt = f"""
    {persona_prompt}
    {history_prompt}
    The user is practicing {lang}. Analyze the following phrase: "{user_text}".
    Correct any grammatical mistakes, provide a brief explanation of the correction, and suggest a related vocabulary tip.
    The response should be in {lang} if possible.
    """

    payload = {
        "contents": [{"role": "user", "parts": [{"text": main_prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA
        }
    }
    try:
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        api_reply_json_string = result['candidates'][0]['content']['parts'][0]['text']
        api_reply_json = json.loads(api_reply_json_string)
        return api_reply_json
    except Exception as e:
        print("❌ AI request error:", e)
        return {
            "corrected_text": user_text,
            "explanation": f"AI request failed: {e}",
            "vocabulary_tips": ""
        }


def synthesize_speech(text, lang):
    """Function to synthesize speech, now with caching."""
    client = get_tts_client()
    if not client:
        return None
    filename = f"{abs(hash(text + lang))}.mp3"
    filepath = AUDIO_DIR / filename
    if filepath.exists():
        return f"/static/audio/{filename}"
    print(f"🔊 Calling TTS API for text: {text}")
    try:
        voice_name = VOICES.get(lang, VOICES.get(DEFAULT_LANG, "en-US-Neural2-C"))
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(language_code=lang, name=voice_name)
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        with open(filepath, "wb") as out:
            out.write(response.audio_content)
        return f"/static/audio/{filename}"
    except Exception as e:
        print("❌ TTS synthesis error:", e)
        return None


def generate_exercise(corrected_text, lang):
    """
    New function to generate an interactive exercise based on a corrected phrase.
    """
    print(f"📝 Generating exercise for: {corrected_text} | lang: {lang}")
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
    The following sentence has been corrected: "{corrected_text}".
    Create a multiple-choice grammar exercise in {lang} to test this concept.
    The exercise should have:
    - a key `exercise_text` with the sentence, but replace one word with a blank space (`___`).
    - a key `correct_answer` with the word that fits in the blank.
    - a key `options` with an array of at least 3 other plausible but incorrect options.
    For example:
    {{"exercise_text": "I ___ to the store.", "correct_answer": "went", "options": ["goes", "go", "going", "went"]}}
    Ensure the JSON is well-formed.
    """

    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": EXERCISE_SCHEMA
        }
    }

    try:
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        api_reply_json_string = result['candidates'][0]['content']['parts'][0]['text']
        api_reply_json = json.loads(api_reply_json_string)
        return api_reply_json
    except Exception as e:
        print("❌ Exercise generation error:", e)
        return {"error": "Failed to generate exercise."}


# ===== ROUTES =====
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/message", methods=["POST"])
def api_message():
    data = request.get_json(force=True)
    user_text = data.get("text", "").strip()
    lang = data.get("lang", DEFAULT_LANG)
    chat_history = data.get("chat_history", [])  # Get chat history from front-end
    persona = data.get("persona", "Friendly Tutor")  # Get persona from front-end

    if not user_text:
        return jsonify({"reply": {"corrected_text": "⚠ Empty message"}, "audio_url": None})

    print(f"📩 Received message: {user_text} | lang: {lang}")
    # FIX: Pass chat_history directly.
    api_reply_json = get_ai_response_from_gemini(user_text, chat_history, persona, lang)

    print(f"🤖 AI reply: {api_reply_json.get('corrected_text', 'No text found')}")

    return jsonify({
        "reply": api_reply_json,
        "audio_url": None
    })


@app.route("/api/tts", methods=["POST"])
def api_tts():
    """New endpoint to handle the TTS request separately."""
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    lang = data.get("lang", DEFAULT_LANG)
    if not text or not GOOGLE_AVAILABLE or not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        return jsonify({"audio_url": None})
    try:
        audio_url = synthesize_speech(text, lang)
        print("🔊 TTS audio generated.")
        return jsonify({"audio_url": audio_url})
    except Exception as e:
        print("⚠ TTS error in endpoint:", e)
        return jsonify({"audio_url": None})


@app.route("/api/exercise", methods=["POST"])
def api_exercise():
    """
    New endpoint to generate and return an interactive exercise.
    """
    data = request.get_json(force=True)
    corrected_text = data.get("corrected_text", "").strip()
    lang = data.get("lang", DEFAULT_LANG)
    if not corrected_text:
        return jsonify({"error": "No text provided for exercise."})
    exercise = generate_exercise(corrected_text, lang)
    return jsonify({"exercise": exercise})


if __name__ == "__main__":

    app.run(debug=True)
