from flask import Flask, render_template, request, send_file, jsonify
import os
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from gtts import gTTS

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================
# SAFE OPENAI STORY FUNCTION
# =========================
def generate_story(vibe, language):
    try:
        from openai import OpenAI

        api_key = os.environ.get("OPENAI_API_KEY")

        # Debug print (shows in Render logs)
        print("API KEY LOADED:", "YES" if api_key else "NO")

        if not api_key:
            # Instead of crashing → fallback story
            return f"This is a {vibe} journey full of beautiful memories."

        client = OpenAI(api_key=api_key)

        prompt = f"Create a {vibe} travel story in {language}. Only narration, no text labels."

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("OpenAI ERROR:", str(e))
        # Fallback story (prevents crash)
        return f"A wonderful {vibe} trip filled with unforgettable moments."


# =========================
# MUSIC FUNCTION
# =========================
def get_music(vibe):
    path = f"static/music/{vibe}.mp3"

    if not os.path.exists(path):
        print("Music file missing:", path)
        return None

    return path


# =========================
# ROUTES
# =========================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create", methods=["POST"])
def create():
    try:
        files = request.files.getlist("photos")
        vibe = request.form.get("vibe")
        language = request.form.get("language")

        if not files or len(files) < 1:
            return jsonify({"error": "No images uploaded"}), 400

        image_paths = []

        for file in files:
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            image_paths.append(path)

        # ✅ Generate story safely
        story = generate_story(vibe, language)

        # ✅ Voice generation
        lang_code = "hi" if language == "Hindi" else "en"
        voice_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")

        tts = gTTS(story, lang=lang_code)
        tts.save(voice_path)

        # ✅ Create slideshow
        clip = ImageSequenceClip(image_paths, fps=1).resize(height=720)

        # ✅ Load audio
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

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


# =========================
# RUN FOR RENDER
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
