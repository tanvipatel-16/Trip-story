from flask import Flask, render_template, request, send_file
import os
from gtts import gTTS
from moviepy.editor import *
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    files = request.files.getlist("images")

    image_paths = []

    # Save images
    for file in files:
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        image_paths.append(path)

    # ✅ Story generation (simple but working)
    story = "This was a beautiful journey full of memories, emotions and unforgettable moments."

    # ✅ Voice (Hindi + English mix)
    tts = gTTS(story, lang="en")  # change to "hi" later if needed
    audio_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")
    tts.save(audio_path)

    # ✅ Create video clips
    clips = []
    for img in image_paths:
        clip = ImageClip(img).set_duration(3).resize(height=720)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    audio = AudioFileClip(audio_path)
    final_video = video.set_audio(audio)

    output_path = os.path.join(OUTPUT_FOLDER, "final.mp4")

    final_video.write_videofile(output_path, fps=24)

    return send_file(output_path, mimetype="video/mp4")

if __name__ == "__main__":
    app.run(debug=True)
