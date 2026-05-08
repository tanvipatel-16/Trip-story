from flask import Flask, render_template, request, send_file
import os
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from werkzeug.utils import secure_filename
import urllib.request

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
MUSIC_FOLDER = "music"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(MUSIC_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

MUSIC_URLS = {
    "funny":     "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8f4e2d4f4.mp3",
    "emotional": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1bab.mp3",
    "dramatic":  "https://cdn.pixabay.com/download/audio/2021/11/25/audio_5b34d88b5b.mp3",
    "cinematic": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"
}

def download_music(vibe):
    music_path = os.path.join(MUSIC_FOLDER, f"{vibe}.mp3")
    if not os.path.exists(music_path):
        try:
            url = MUSIC_URLS.get(vibe, MUSIC_URLS["cinematic"])
            urllib.request.urlretrieve(url, music_path)
        except Exception as e:
            print(f"Music download failed: {e}")
            return None
    return music_path if os.path.exists(music_path) else None

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

    english_stories = {
        "funny": (
            "Oh my God, where do I even begin?! This trip was an absolute DISASTER — and I mean that in the best possible way! "
            "First, we got completely lost trying to find the hotel. GPS said turn left, we turned left, and ended up in someone's backyard. "
            "Then at the restaurant, I ordered something I couldn't even pronounce and ended up with a plate of... honestly, I still don't know what it was. "
            "But I ATE it. Every. Single. Bite. Because that's what travelers do! "
            "We missed buses, got rained on, sunburned in places that should NEVER be sunburned, "
            "and somehow, SOMEHOW — it became the greatest story I will ever tell. "
            "Every disaster, every wrong turn, every awkward moment — it all became pure gold. "
            "Because at the end of the day, the best memories aren't the perfect ones. They're the ones that make you laugh until you cry. "
            "And oh boy, did we laugh. We laughed so hard. This trip? Absolutely unhinged. Ten out of ten. Would do it again tomorrow."
        ),
        "emotional": (
            "There are places that change you. Not slowly, not quietly — but all at once, like a wave you never saw coming. "
            "This journey was one of those places. "
            "I remember standing there, looking out at the horizon, and feeling something I hadn't felt in a very long time — peace. "
            "Real, deep, soul-level peace. Like the world had pressed pause just for me. "
            "Every photograph here holds a story. A moment where laughter and tears lived in the same breath. "
            "Where strangers became family and home felt a thousand miles away — and yet, somehow, everywhere. "
            "I thought about everyone I love. Everyone who couldn't be there. And I wished so deeply that they could see what I was seeing. "
            "Because some things are too beautiful to keep to yourself. "
            "This trip reminded me why we travel. Not to escape life — but to find it. To feel it fully. "
            "I will carry these memories forever. Long after the photos fade. Long after the words run out. "
            "This journey lives in my heart now. And it always will."
        ),
        "dramatic": (
            "They said it couldn't be done. They said the roads were too rough, the weather too unpredictable, the journey too long. "
            "They were right. And we went anyway. "
            "Every mile was a battle. Every summit, a victory claimed with burning legs and trembling hands. "
            "The wind did not stop. The rain did not stop. And neither did we. "
            "There were moments — dark moments — where doubt crept in like fog over a mountain pass. "
            "Where every rational thought screamed: turn back. Go home. This is madness. "
            "But something deeper whispered: keep going. You did not come this far to only come this far. "
            "And so we pushed. Through exhaustion. Through uncertainty. Through every obstacle the universe threw at us. "
            "And then — the moment. THE moment. When everything else fell away and all that remained was raw, pure, unfiltered triumph. "
            "We stood there. Breathless. Changed forever. "
            "Because the greatest journeys are never comfortable. They are meant to break you open and rebuild you stronger. "
            "This was not just a trip. This was a reckoning. And we survived it. Every glorious, brutal, beautiful second of it."
        ),
        "cinematic": (
            "Roll camera. "
            "The light hits differently when you are somewhere new. Golden and heavy and full of promise. "
            "Every frame of this journey looked like something out of a film you have seen in a dream — "
            "wide open roads stretching toward nothing and everything, ancient streets alive with sound and color, "
            "skies so vast they made you feel small in the best possible way. "
            "We moved through this place like characters in a story we had not written yet. "
            "Every turn, a new scene. Every conversation, a new chapter. "
            "The locals who smiled and pointed us in the right direction. The hidden cafes with the best coffee on earth. "
            "The sunsets that made everyone go quiet because some things are beyond words. "
            "This is what travel does. It turns ordinary days into extraordinary cinema. "
            "Somewhere in these photographs — in the light, in the faces, in the quiet spaces between moments — "
            "a story was born. A real one. The kind that stays with you. "
            "Cut to black. Roll credits. But for us — the adventure never really ends."
        )
    }

    hindi_stories = {
        "funny": (
            "यार, कहाँ से शुरू करूँ?! यह ट्रिप एक पूरा तमाशा था — लेकिन सबसे बेस्ट तमाशा! "
            "पहले दिन ही हम होटल ढूंढते-ढूंढते किसी के घर के अंदर घुस गए। Google Maps ने धोखा दिया, बिल्कुल! "
            "खाना ऑर्डर किया तो कुछ ऐसा आया जिसे देखकर हम सब बस एक-दूसरे का मुँह देखते रह गए। "
            "खाया? हाँ खाया! क्योंकि हम traveler हैं और traveler डरते नहीं! "
            "बस छूटी, बारिश में भीगे, धूप में जले, रास्ता भटके — "
            "और इन सबके बीच जो हँसी आई, वो हँसी जिंदगी भर याद रहेगी। "
            "हर गलती एक किस्सा बन गई। हर मुसीबत एक याद बन गई। "
            "क्योंकि सच में — सबसे अच्छी यादें वो नहीं होतीं जो perfect होती हैं। "
            "सबसे अच्छी यादें वो होती हैं जिन पर बाद में पेट पकड़ के हँसते हैं। "
            "यह ट्रिप? बिल्कुल पागलपन। दस में से दस। कल फिर जाना है।"
        ),
        "emotional": (
            "कुछ जगहें होती हैं जो आपको बदल देती हैं। चुपके से नहीं — एक झटके में। "
            "यह सफर उन्हीं जगहों में से एक था। "
            "जब मैं वहाँ खड़ा था, दूर क्षितिज को देखते हुए, तो मन में एक अजीब सी शांति उतर आई। "
            "जैसे दुनिया ने एक पल के लिए रुककर सिर्फ मुझसे बात की हो। "
            "इन तस्वीरों में सिर्फ जगहें नहीं हैं — इनमें वो लम्हे हैं जब हँसी और आँसू एक साथ आए। "
            "जब अजनबी यार बन गए और घर बहुत दूर था — फिर भी हर जगह घर जैसा लगा। "
            "मैंने उन सबके बारे में सोचा जिन्हें मैं चाहता हूँ। जो वहाँ नहीं थे। "
            "काश वो भी देख पाते — क्योंकि कुछ खूबसूरतियाँ अकेले सहना बहुत मुश्किल होता है। "
            "यह सफर याद दिलाता है कि हम travel क्यों करते हैं। जिंदगी से भागने के लिए नहीं — बल्कि जिंदगी को पूरी तरह जीने के लिए। "
            "ये यादें हमेशा मेरे साथ रहेंगी। तस्वीरें फीकी पड़ जाएँ, शब्द खत्म हो जाएँ — "
            "लेकिन यह सफर मेरे दिल में हमेशा जिंदा रहेगा।"
        ),
        "dramatic": (
            "लोगों ने कहा — मत जाओ। रास्ता मुश्किल है। मौसम खराब है। यह संभव नहीं। "
            "हम फिर भी गए। "
            "हर कदम एक जंग था। हर चोटी एक जीत जो जलते पैरों और कांपते हाथों से छीनी। "
            "हवा नहीं रुकी। बारिश नहीं रुकी। और हम भी नहीं रुके। "
            "ऐसे पल आए जब मन ने कहा — वापस चलो। यह पागलपन है। यह नासमझी है। "
            "लेकिन दिल की किसी गहरी आवाज़ ने कहा — बस एक और कदम। "
            "तुम इतनी दूर आए हो — सिर्फ यहाँ रुकने के लिए नहीं। "
            "और हम बढ़ते रहे। थकान के बावजूद। अंधेरे के बावजूद। हर रुकावट के बावजूद। "
            "और फिर वो पल आया — वो एक पल — जब सब कुछ थम गया। "
            "सिर्फ हम थे। और वो अहसास था जो शब्दों में नहीं समाता। "
            "क्योंकि सबसे बड़े सफर आरामदायक नहीं होते। वो तोड़ते हैं — और फिर नए सिरे से जोड़ते हैं। "
            "यह सिर्फ एक यात्रा नहीं थी। यह एक परीक्षा थी। और हम पास हुए।"
        ),
        "cinematic": (
            "कैमरा चलाइए। "
            "रोशनी अलग होती है जब आप किसी नई जगह होते हैं। सुनहरी, भारी, उम्मीदों से भरी। "
            "इस सफर का हर फ्रेम किसी फिल्म के दृश्य जैसा था — "
            "खुली सड़कें जो अनंत की तरफ जाती हैं, पुरानी गलियाँ जो जीवन से भरी हैं, "
            "ऐसे आसमान जो इतने विशाल थे कि खुद छोटे लगने लगे — और यह अच्छा लगा। "
            "हम इस जगह में ऐसे चले जैसे किसी अनलिखी कहानी के किरदार। "
            "हर मोड़ एक नया दृश्य। हर बातचीत एक नया अध्याय। "
            "वो सूर्यास्त जिसे देखकर सब चुप हो गए — क्योंकि कुछ चीज़ें शब्दों से परे होती हैं। "
            "यही है travel का जादू। यह आपकी साधारण जिंदगी को असाधारण सिनेमा बना देता है। "
            "इन तस्वीरों में — रोशनी में, चेहरों में, लम्हों के बीच की खामोशी में — "
            "एक कहानी जन्म लेती है। असली कहानी। जो रहती है। "
            "कट टु ब्लैक। लेकिन हमारा सफर? वो कभी खत्म नहीं होता।"
        )
    }

    if language == "hi":
        story = hindi_stories.get(vibe, hindi_stories["cinematic"])
        lang_code = "hi"
    else:
        story = english_stories.get(vibe, english_stories["cinematic"])
        lang_code = "en"

    # Generate voiceover
    tts = gTTS(story, lang=lang_code, slow=False)
    audio_path = os.path.join(OUTPUT_FOLDER, "voice.mp3")
    tts.save(audio_path)

    # Build video — duration matches voice
    voice_audio = AudioFileClip(audio_path)
    total_duration = voice_audio.duration
    duration_per_image = max(3, total_duration / len(image_paths))

    clips = []
    for img in image_paths:
        clip = ImageClip(img).with_duration(duration_per_image).resized(height=720)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    # Mix background music + voice
    try:
        music_path = download_music(vibe)
        if music_path:
            bg_music = AudioFileClip(music_path).with_duration(video.duration).multiply_volume(0.15)
            voice_clip = voice_audio.with_duration(video.duration)
            final_audio = CompositeAudioClip([bg_music, voice_clip])
        else:
            final_audio = voice_audio.with_duration(video.duration)
    except Exception as e:
        print(f"Music mixing failed: {e}")
        final_audio = voice_audio.with_duration(video.duration)

    final_video = video.with_audio(final_audio)
    output_path = os.path.join(OUTPUT_FOLDER, "final.mp4")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    return send_file(output_path, mimetype="video/mp4")
