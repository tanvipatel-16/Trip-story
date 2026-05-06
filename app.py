```python
from flask import Flask, render_template, request, send_file
import os
from gtts import gTTS
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
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

    if not files:
        return "No files uploaded", 400

    image_paths = []

    # Save images
    for file in files:
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        image_paths.append(path)

    # Story
    story = "This was a beautiful journey full of memories, emotions and unforgettable moments."

    # Voice
    audio_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")
    tts = gTTS(story, lang="en")
    tts.save(audio_path)

    # Create video
    clips = []
    for img in image_paths:
        clip = ImageClip(img).set_duration(3).resize(height=720)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    audio = AudioFileClip(audio_path)
    final_video = video.set_audio(audio)

    output_path = os.path.join(OUTPUT_FOLDER, "final.mp4")
    final_video.write_videofile(output_path, fps=24)

    return send_file(output_path, mimetype="video/mp4", as_attachment=False)


# ✅ IMPORTANT FOR RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
```
