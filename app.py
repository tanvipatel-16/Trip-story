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

# =========================
# SAFE STORY FUNCTION
# =========================
def generate_story(vibe, language):
    try:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")
        print("API KEY:", "FOUND" if api_key else "MISSING")

        if not api_key:
            return f"This is a {vibe} journey full of memories."

        client = OpenAI(api_key=api_key)

        prompt = f"Create a {vibe} travel story in {language}. Only narration."

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("OpenAI ERROR:", str(e))
        return f"A beautiful {vibe} journey."

# =========================
# MUSIC FUNCTION
# =========================
def get_music(vibe):
    path = f"static/music/{vibe}.mp3"
    if os.path.exists(path):
        return path
    else:
        print("Music not found:", path)
        return None

# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create", methods=["POST"])
def create():
    try:
        print("=== REQUEST START ===")

        files = request.files.getlist("photos")
        vibe = request.form.get("vibe")
        language = request.form.get("language")

        if not files or files[0].filename == "":
            return "No images uploaded", 400

        # =========================
        # RESIZE IMAGES (FIX)
        # =========================
        processed_images = []

        for i, file in enumerate(files):
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            img = Image.open(path)
            img = img.convert("RGB")

            # Resize all images to same size
            img = img.resize((1280, 720))

            new_path = os.path.join(UPLOAD_FOLDER, f"resized_{i}.jpg")
            img.save(new_path, "JPEG")

            processed_images.append(new_path)

        print("Images processed")

        # =========================
        # STORY
        # =========================
        story = generate_story(vibe, language)
        print("Story generated")

        # =========================
        # VOICE
        # =========================
        lang_code = "hi" if language == "Hindi" else "en"
        voice_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")

        tts = gTTS(story, lang=lang_code)
        tts.save(voice_path)

        print("Voice created")

        # =========================
        # VIDEO
        # =========================
        clip = ImageSequenceClip(processed_images, fps=1)

        # =========================
        # AUDIO
        # =========================
        voice_audio = AudioFileClip(voice_path)

        music_path = get_music(vibe)
        if music_path:
            music_audio = AudioFileClip(music_path).volumex(0.2)
            final_audio = CompositeAudioClip([voice_audio, music_audio])
        else:
            final_audio = voice_audio

        final_audio = final_audio.set_duration(clip.duration)

        video = clip.set_audio(final_audio)

        output_path = os.path.join(OUTPUT_FOLDER, "final_video.mp4")

        video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac"
        )

        print("Video created")

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("FULL ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


# =========================
# RUN FOR RENDER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
