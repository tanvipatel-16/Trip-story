from flask import Flask, render_template, request, send_file, jsonify
import os
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from gtts import gTTS
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def generate_story(vibe, language):
    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return f"This is a {vibe} journey full of beautiful memories."
        client = OpenAI(api_key=api_key)
        prompt = f"Create a detailed {vibe} travel story in {language} with at least 5 sentences. Only narration, no labels."
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("OpenAI ERROR:", str(e))
        return f"A beautiful {vibe} journey full of wonderful memories and amazing experiences."

def get_music(vibe):
    path = f"static/music/{vibe}.mp3"
    if os.path.exists(path):
        return path
    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create", methods=["POST"])
def create():
    try:
        files = request.files.getlist("photos")
        vibe = request.form.get("vibe")
        language = request.form.get("language")

        if not files or files[0].filename == "":
            return "No images uploaded", 400

        processed_images = []
        for i, file in enumerate(files):
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            img = Image.open(path).convert("RGB").resize((1280, 720))
            new_path = os.path.join(UPLOAD_FOLDER, f"resized_{i}.jpg")
            img.save(new_path, "JPEG")
            processed_images.append(new_path)

        story = generate_story(vibe, language)

        lang_code = "hi" if language == "Hindi" else "en"
        voice_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")
        tts = gTTS(story, lang=lang_code)
        tts.save(voice_path)

        voice_audio = AudioFileClip(voice_path)
        voice_duration = voice_audio.duration

        # Each photo shows for equal time based on voice duration
        duration_per_image = voice_duration / len(processed_images)
        clip = ImageSequenceClip(processed_images, durations=[duration_per_image] * len(processed_images))

        music_path = get_music(vibe)
        if music_path:
            music_audio = AudioFileClip(music_path).volumex(0.2).set_duration(voice_duration)
            final_audio = CompositeAudioClip([voice_audio, music_audio])
        else:
            final_audio = voice_audio

        video = clip.set_audio(final_audio)
        output_path = os.path.join(OUTPUT_FOLDER, "final_video.mp4")
        video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("FULL ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
