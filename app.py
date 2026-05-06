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

    for file in files:
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        image_paths.append(path)

    if not image_paths:
        return {"error": "No images uploaded"}, 400

    # English stories
    english_stories = {
        "funny": "What a hilarious adventure! Every moment was packed with laughter, surprises, and unforgettable comedy. From getting lost to finding the best food, this trip was truly one for the books!",
        "emotional": "This journey touched the deepest corners of the heart. Every photo holds a memory, every smile tells a story of love, warmth and belonging. These moments will stay forever.",
        "dramatic": "Against all odds, this journey unfolded like an epic tale. Every step was a battle, every moment a triumph. This was no ordinary trip — this was destiny calling.",
        "cinematic": "The world opened up in all its glory. Sweeping landscapes, golden light, and the quiet magic of travel wove together into a story worth telling forever."
    }

    # Hindi stories
    hindi_stories = {
        "funny": "क्या मज़ेदार सफर था! हर पल हँसी और मस्ती से भरा हुआ था। रास्ता भटकना, अजीब खाना खाना, और नई जगहें खोजना — यह यात्रा सच में यादगार रही।",
        "emotional": "यह सफर दिल की गहराइयों को छू गया। हर तस्वीर में एक याद है, हर मुस्कान में एक कहानी है। प्यार, अपनापन और खूबसूरत पलों से भरी यह यात्रा हमेशा याद रहेगी।",
        "dramatic": "हर मुश्किल को पार करते हुए यह यात्रा एक महाकाव्य की तरह सामने आई। हर कदम एक संघर्ष था, हर पल एक जीत थी। यह कोई साधारण यात्रा नहीं थी — यह नियति का बुलावा था।",
        "cinematic": "दुनिया अपनी पूरी भव्यता के साथ सामने आई। विशाल परिदृश्य, सुनहरी रोशनी, और यात्रा का जादू मिलकर एक ऐसी कहानी बन गए जो हमेशा याद रहेगी।"
    }

    # Select story based on language
    if language == "hi":
        story = hindi_stories.get(vibe, hindi_stories["cinematic"])
        lang_code = "hi"
    else:
        story = english_stories.get(vibe, english_stories["cinematic"])
        lang_code = "en"

    # Generate voiceover
    tts = gTTS(story, lang=lang_code)
    audio_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")
    tts.save(audio_path)

    # Create video clips
    clips = []
    for img in image_paths:
        clip = ImageClip(img).with_duration(3).resized(height=720)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_path).with_duration(video.duration)
    final_video = video.with_audio(audio)

    output_path = os.path.join(OUTPUT_FOLDER, "final.mp4")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    return send_file(output_path, mimetype="video/mp4")
