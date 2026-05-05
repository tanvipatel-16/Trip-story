from flask import Flask, render_template, request, send_file, jsonify
import os
import base64
from moviepy.editor import (
    ImageClip,
    concatenate_videoclips,
    AudioFileClip,
    CompositeAudioClip
)
from gtts import gTTS
from PIL import Image
from openai import OpenAI

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🔑 OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 🖼️ FIX IMAGE QUALITY
def resize_with_padding(img, target_size=(1280, 720)):
    img.thumbnail(target_size, Image.LANCZOS)

    new_img = Image.new("RGB", target_size, (0, 0, 0))
    new_img.paste(
        img,
        (
            (target_size[0] - img.width) // 2,
            (target_size[1] - img.height) // 2
        )
    )
    return new_img


# 🔍 SAFE TEXT EXTRACTION (VERY IMPORTANT)
def extract_text(response):
    text = ""

    try:
        if hasattr(response, "output_text") and response.output_text:
            return response.output_text

        if hasattr(response, "output"):
            for item in response.output:
                if hasattr(item, "content"):
                    for part in item.content:
                        if hasattr(part, "text"):
                            text += part.text

    except Exception as e:
        print("Extraction error:", str(e))

    return text.strip()


# 🧠 IMAGE UNDERSTANDING
def describe_images(image_paths):
    descriptions = []

    try:
        for i, path in enumerate(image_paths):
            with open(path, "rb") as img_file:
                base64_image = base64.b64encode(img_file.read()).decode("utf-8")

            response = client.responses.create(
                model="gpt-4o-mini",
                input=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Analyze this travel photo deeply. Describe place, mood, people, lighting, and emotions."
                        },
                        {
                            "type": "input_image",
                            "image_base64": base64_image
                        }
                    ]
                }]
            )

            text = extract_text(response)

            if not text:
                text = "A travel moment captured beautifully."

            descriptions.append(f"Image {i+1}: {text}")

        final_text = "\n".join(descriptions)
        print("IMAGE ANALYSIS:", final_text)

        return final_text

    except Exception as e:
        print("Image AI ERROR:", str(e))
        return "A beautiful journey with memorable moments."


# ✍️ STORY GENERATION
def generate_story(vibe, language, image_text):
    try:
        prompt = f"""
You are a cinematic storyteller.

Based on these travel moments:
{image_text}

Create a {vibe} travel story in {language}.

Make it:
- emotional
- vivid
- connected like a journey
- NOT generic

Minimum 120 words.
Only narration.
"""

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt
        )

        story = extract_text(response)

        if not story:
            story = "This journey was filled with unforgettable memories, emotions, and beautiful moments."

        print("STORY:", story)

        return story

    except Exception as e:
        print("Story ERROR:", str(e))
        return "A beautiful journey full of memories."


# 🎵 MUSIC
def get_music(vibe):
    path = f"static/music/{vibe.lower()}.mp3"
    return path if os.path.exists(path) else None


@app.route("/")
def index():
    return render_template("index.html")


# 🎬 MAIN ROUTE
@app.route("/create", methods=["POST"])
def create():
    try:
        print("API KEY:", os.environ.get("OPENAI_API_KEY"))

        files = request.files.getlist("photos")
        vibe = request.form.get("vibe", "cinematic").lower()
        language = request.form.get("language", "English")

        print("VIBE:", vibe)
        print("LANGUAGE:", language)

        if not files or files[0].filename == "":
            return "No images uploaded", 400

        processed_images = []

        # 🖼️ IMAGE PROCESSING
        for i, file in enumerate(files):
            path = os.path.join(UPLOAD_FOLDER, f"{i}.jpg")
            file.save(path)

            img = Image.open(path).convert("RGB")
            img = resize_with_padding(img)

            new_path = os.path.join(UPLOAD_FOLDER, f"resized_{i}.jpg")
            img.save(new_path, "JPEG", quality=95)

            processed_images.append(new_path)

        # 🧠 AI ANALYSIS
        image_text = describe_images(processed_images)

        # ✍️ STORY
        story = generate_story(vibe, language, image_text)

        # 🗣️ VOICE
        lang_code = "hi" if language.lower() == "hindi" else "en"
        voice_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")

        tts = gTTS(text=story, lang=lang_code, slow=False)
        tts.save(voice_path)

        voice_audio = AudioFileClip(voice_path)
        voice_duration = voice_audio.duration

        # 🎬 VIDEO
        duration_per_image = voice_duration / len(processed_images)

        clips = []
        for img_path in processed_images:
            clip = (
                ImageClip(img_path)
                .set_duration(duration_per_image)
                .resize(lambda t: 1 + 0.05 * t)  # zoom effect
                .set_position("center")
            )
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        # 🎵 AUDIO SYNC
        music_path = get_music(vibe)

        if music_path:
            music_audio = (
                AudioFileClip(music_path)
                .volumex(0.15)
                .audio_loop(duration=voice_duration)
            )
            final_audio = CompositeAudioClip([voice_audio, music_audio])
        else:
            final_audio = voice_audio

        video = video.set_audio(final_audio)

        output_path = os.path.join(OUTPUT_FOLDER, "final_video.mp4")

        video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast"
        )

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("FULL ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
