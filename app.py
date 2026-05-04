from flask import Flask, render_template, request, send_file, jsonify
import os
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips
)
from PIL import Image
import requests

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================
# AI STORY (SMART)
# =========================
def generate_story(vibe, language):
    try:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return f"A {vibe} journey full of memories and emotions."

        client = OpenAI(api_key=api_key)

        prompt = f"""
        Create a {vibe} travel story in {language}.
        Make it emotional, cinematic, and natural for voice narration.
        Keep it around 80-120 words.
        No headings. Only storytelling narration.
        """

        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return res.choices[0].message.content

    except Exception as e:
        print("OpenAI Error:", e)
        return f"A beautiful {vibe} journey."

# =========================
# HUMAN VOICE (ElevenLabs)
# =========================
def generate_voice(text, output_path):
    api_key = os.getenv("ELEVENLABS_API_KEY")

    if not api_key:
        # fallback to gTTS
        from gtts import gTTS
        tts = gTTS(text)
        tts.save(output_path)
        return

    url = "https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
    else:
        print("ElevenLabs failed, fallback to gTTS")
        from gtts import gTTS
        tts = gTTS(text)
        tts.save(output_path)

# =========================
# MUSIC
# =========================
def get_music(vibe):
    path = f"static/music/{vibe}.mp3"
    return path if os.path.exists(path) else None

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

        if not files or files[0].filename == "":
            return "No images uploaded", 400

        # =========================
        # IMAGE PROCESSING
        # =========================
        processed_images = []

        for i, file in enumerate(files):
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            img = Image.open(path).convert("RGB")
            img = img.resize((1280, 720))

            new_path = os.path.join(UPLOAD_FOLDER, f"img_{i}.jpg")
            img.save(new_path)

            processed_images.append(new_path)

        # =========================
        # STORY
        # =========================
        story = generate_story(vibe, language)

        # =========================
        # VOICE (REAL)
        # =========================
        voice_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")
        generate_voice(story, voice_path)

        voice_audio = AudioFileClip(voice_path).volumex(1.3)

        # =========================
        # VIDEO (CINEMATIC)
        # =========================
        duration = voice_audio.duration / len(processed_images)

        clips = []
        for img_path in processed_images:
            clip = (
                ImageClip(img_path)
                .set_duration(duration)
                .resize(lambda t: 1 + 0.04 * t)
                .fadein(0.5)
                .fadeout(0.5)
            )
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        # =========================
        # AUDIO MIX (SMART)
        # =========================
        music_path = get_music(vibe)

        if music_path:
            music = AudioFileClip(music_path).volumex(0.08)
            final_audio = CompositeAudioClip([voice_audio, music])
        else:
            final_audio = voice_audio

        final_audio = final_audio.set_duration(video.duration)
        video = video.set_audio(final_audio)

        # =========================
        # EXPORT
        # =========================
        output_path = os.path.join(OUTPUT_FOLDER, "final_video.mp4")

        video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500


# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
