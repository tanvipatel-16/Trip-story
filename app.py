from flask import Flask, render_template, request, send_file
import os
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeAudioClip
from gtts import gTTS
from openai import OpenAI

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🔑 Add your OpenAI key in Render ENV
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# AI STORY GENERATOR
# =========================
def generate_story(vibe, language):
    prompt = f"Create a {vibe} travel story in {language} based on a photo journey. No text labels, only narration."

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# =========================
# MUSIC SELECTOR
# =========================
def get_music(vibe):
    return f"static/music/{vibe}.mp3"

# =========================
# ROUTES
# =========================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods=['POST'])
def create():
    files = request.files.getlist('photos')
    vibe = request.form['vibe']
    language = request.form['language']

    image_paths = []

    for file in files:
        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)
        image_paths.append(path)

    # 🔥 AI Story
    story = generate_story(vibe, language)

    # 🔊 Voice
    lang_code = 'hi' if language == 'Hindi' else 'en'
    voice_path = os.path.join(OUTPUT_FOLDER, 'voice.mp3')
    tts = gTTS(story, lang=lang_code)
    tts.save(voice_path)

    # 🎬 Slideshow
    clip = ImageSequenceClip(image_paths, fps=1)

    # 🎵 Audio
    voice_audio = AudioFileClip(voice_path)
    music_audio = AudioFileClip(get_music(vibe)).volumex(0.2)

    final_audio = CompositeAudioClip([voice_audio, music_audio])
    final_audio = final_audio.set_duration(clip.duration)

    video = clip.set_audio(final_audio)

    output_path = os.path.join(OUTPUT_FOLDER, 'final_video.mp4')
    video.write_videofile(output_path, codec='libx264', audio_codec='aac')

    return send_file(output_path, as_attachment=True)

# =========================
# RUN (Render compatible)
# =========================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)



