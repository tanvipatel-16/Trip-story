from flask import Flask, render_template, request, send_file, jsonify
import os
import base64
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from gtts import gTTS
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# 🧠 STEP 1: Describe images using AI
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
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Describe this travel photo in one short sentence."},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            )

            descriptions.append(response.choices[0].message.content)

        return " ".join(descriptions)

    except Exception as e:
        print("Image AI ERROR:", str(e))
        return "A journey with beautiful places and memories."


# 🧠 STEP 2: Generate story from descriptions
def generate_story(vibe, language, image_text):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        prompt = f"""
        Based on these travel photo descriptions:
        {image_text}

        Create a {vibe} travel story in {language}.
        Make it emotional and engaging.
        Minimum 120 words.
        Only narration.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Story ERROR:", str(e))
        return "A journey full of memories and emotions."


# 🎵 Music
def get_music(vibe):
    path = f"static/music/{vibe}.mp3"
    return path if os.path.exists(path) else None


@app.route("/")
def index():
    return render_template("index.html")


# 🎬 MAIN ROUTE
@app.route("/create", methods=["POST"])
def create():
    try:
        files = request.files.getlist("photos")
        vibe = request.form.get("vibe")
        language = request.form.get("language")

        if not files or files[0].filename == "":
            return "No images uploaded", 400

        processed_images = []

        # 🖼 Resize images
        for i, file in enumerate(files):
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)

            img = Image.open(path).convert("RGB").resize((1280, 720))
            new_path = os.path.join(UPLOAD_FOLDER, f"resized_{i}.jpg")
            img.save(new_path, "JPEG")

            processed_images.append(new_path)

        # 🧠 AI understands images
        image_text = describe_images(processed_images)

        # ✍️ AI creates story
        story = generate_story(vibe, language, image_text)

        # 🗣 Voice
        lang_code = "hi" if language == "Hindi" else "en"
        voice_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")

        tts = gTTS(story, lang=lang_code)
        tts.save(voice_path)

        voice_audio = AudioFileClip(voice_path)
        voice_duration = voice_audio.duration

        # 🎬 VIDEO = MATCH VOICE (NO CRASH)
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

        video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac"
        )

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        print("FULL ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
