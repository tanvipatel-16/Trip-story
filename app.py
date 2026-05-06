from flask import Flask, render_template, request, send_file, jsonify
import os
import base64
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from gtts import gTTS
from PIL import Image
import imageio_ffmpeg

# ✅ Force FFmpeg path
os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# 🧠 STEP 1: Describe images
def describe_images(image_paths):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        descriptions = []

        for path in image_paths:
            with open(path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this travel photo in a vivid, emotional sentence."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }]
            )

            text = response.choices[0].message.content
            if text:
                descriptions.append(text)

        return " ".join(descriptions) if descriptions else "A beautiful travel journey."

    except Exception as e:
        print("❌ Image AI ERROR:", str(e))
        return "A beautiful travel journey."


# 🧠 STEP 2: Story generation
def generate_story(vibe, language, image_text):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        prompt = f"""
        Create a {vibe} travel story in {language}.

        Based on:
        {image_text}

        Make it emotional, engaging, and cinematic.
        Minimum 120 words.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        story = response.choices[0].message.content
        return story if story else "A beautiful journey."

    except Exception as e:
        print("❌ Story ERROR:", str(e))
        return "A beautiful journey."


# 🎵 Music
def get_music(vibe):
    path = f"static/music/{vibe.lower()}.mp3"
    return path if os.path.exists(path) else None


@app.route("/")
def index():
    return render_template("index.html")


# 🎬 MAIN ROUTE
@app.route("/create", methods=["POST"])
def create():
    print("🔥 CREATE API HIT")

    try:
        files = request.files.getlist("photos")
        vibe = request.form.get("vibe", "cinematic")
        language = request.form.get("language", "English")

        print("FILES:", len(files))
        print("VIBE:", vibe)
        print("LANG:", language)

        if not files or files[0].filename == "":
            return "No images uploaded", 400

        processed_images = []

        # 🖼 Process images (NO stretching)
        for i, file in enumerate(files):
            path = os.path.join(UPLOAD_FOLDER, f"img_{i}.jpg")
            file.save(path)

            img = Image.open(path).convert("RGB")
            img.thumbnail((1280, 720))  # ✅ keeps aspect ratio

            new_path = os.path.join(UPLOAD_FOLDER, f"resized_{i}.jpg")
            img.save(new_path, "JPEG")

            processed_images.append(new_path)

        print("✅ Images processed")

        # 🧠 AI
        image_text = describe_images(processed_images)
        print("🧠 Image text:", image_text)

        story = generate_story(vibe, language, image_text)
        print("✍️ Story:", story[:100])

        # 🗣 Voice
        lang_code = "hi" if "Hindi" in language else "en"
        voice_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")

        tts = gTTS(story, lang=lang_code)
        tts.save(voice_path)

        voice_audio = AudioFileClip(voice_path)
        voice_duration = voice_audio.duration

        print("🎙 Voice duration:", voice_duration)

        # 🎬 Video
        duration_per_image = voice_duration / len(processed_images)

        clip = ImageSequenceClip(
            processed_images,
            durations=[duration_per_image] * len(processed_images)
        )

        # 🎵 Music
        music_path = get_music(vibe)

        if music_path:
            music_audio = AudioFileClip(music_path).volumex(0.2).set_duration(voice_duration)
            final_audio = CompositeAudioClip([voice_audio, music_audio])
        else:
            final_audio = voice_audio

        video = clip.set_audio(final_audio)

        output_path = os.path.join(OUTPUT_FOLDER, "final_video.mp4")

        print("🎬 Rendering video...")

        video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )

        print("✅ VIDEO CREATED:", output_path)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("❌ FULL ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
