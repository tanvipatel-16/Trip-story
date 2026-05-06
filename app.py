from flask import Flask, render_template, request, send_file
import os
from gtts import gTTS
from moviepy import *
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    files = request.files.getlist("images")
    vibe = request.form.get("vibe", "cinematic")
    language = request.form.get("language", "en")

    image_paths = []

    # Save uploaded images
    for file in files:
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        image_paths.append(path)

    if not image_paths:
        return {"error": "No images uploaded"}, 400

    # Story generation based on vibe
    stories = {
        "funny": "What a hilarious adventure! Every moment was packed with laughter, surprises, and unforgettable comedy. This trip was truly one for the books!",
        "emotional": "This journey touched the deepest corners of the heart. Every photo holds a memory, every smile tells a story of love, warmth and belonging.",
        "dramatic": "Against all odds, this journey unfolded like an epic tale. Every step was a battle, every moment a triumph. This was no ordinary trip — this was destiny.",
        "cinematic": "The world opened up in all its glory. Sweeping landscapes, golden light, and the quiet magic of travel wove together into a story worth telling forever."
    }

    story = stories.get(vibe, stories["cinematic"])

    # Generate voiceover
    lang_code = "hi" if language == "hi" else "en"
    tts = gTTS(story, lang=lang_code)
    audio_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")
    tts.save(audio_path)

    # Create video clips from images
    clips = []
    duration_per_image = 3

    for img in image_paths:
        clip = ImageClip(img).with_duration(duration_per_image).resized(height=720)
        clips.append(clip)

    # Concatenate all clips
    video = concatenate_videoclips(clips, method="compose")

    # Add audio
    audio = AudioFileClip(audio_path).with_duration(video.duration)
    final_video = video.with_audio(audio)

    # Write final video
    output_path = os.path.join(OUTPUT_FOLDER, "final.mp4")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    return send_file(output_path, mimetype="video/mp4")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
