from flask import Flask, request, jsonify, render_template
import g4f
from gtts import gTTS
import pygame
import os

app = Flask(__name__)

def get_career_advice(user_input):
    response = g4f.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a career guidance counselor. Provide advice based on the user's input."},
            {"role": "user", "content": user_input}
        ]
    )
    return response

def text_to_speech(text):
    tts = gTTS(text=text, lang="en")
    audio_file = "response.mp3"
    tts.save(audio_file)
    return audio_file

def play_audio(audio_file):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_advice", methods=["POST"])
def get_advice():
    user_input = request.json.get("message")
    advice = get_career_advice(user_input)
    
    # Convert GPT response to speech
    audio_file = text_to_speech(advice)
    
    # Play the audio file
    play_audio(audio_file)
    
    return jsonify({"response": advice, "audio_file": audio_file})

if __name__ == "__main__":
    app.run(debug=True)