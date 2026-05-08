from flask import Flask, render_template, request, send_file
import os
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
from werkzeug.utils import secure_filename
import urllib.request

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
MUSIC_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
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
            "This trip was literally just bad decisions and good outfits. "
            "We started the journey acting like main characters and ended it fighting for one power bank. "
            "Nobody knew the plan. Nobody booked properly. But the confidence? Astronomical. "
            "We spent more time taking aesthetic photos than actually enjoying the place. "
            "At one point we walked 20 minutes just to click one Instagram story and honestly… worth it. "
            "One friend kept saying 'trust the process' while actively making the situation worse. "
            "The hotel looked NOTHING like the pictures. Like actually nothing. "
            "Our budget disappeared on iced coffee and unnecessary snacks within the first two hours. "
            "Somehow we were tired, broke, dehydrated, slightly sunburnt, and still saying — "
            "'Wait wait, one more photo.' "
            "And despite the chaos, the confusion, and the almost criminal level of bad planning… "
            "this trip absolutely ate."
        ),
        "emotional": (
            "I didn’t expect this trip to heal something in me, but somehow it did. "
            "For a little while, life felt slower. Quieter. Easier to breathe in. "
            "No deadlines, no overthinking, no pretending everything was fine. "
            "Just sunsets, long conversations, random laughter, and moments I wish I could pause forever. "
            "It’s strange how people can go from strangers to feeling like home so quickly. "
            "Somewhere between the late-night talks, blurry photos, and tired walks back to the hotel… "
            "these memories became something bigger than just a trip. "
            "We were all dealing with our own things, even if nobody said it out loud. "
            "But for those few days, nothing really mattered except being there together. "
            "And honestly? I think that’s what made it special. "
            "Not the places. Not the pictures. "
            "Just the feeling of being alive at the right moment with the right people. "
            "Some memories don’t fade after a trip ends. "
            "They stay with you quietly, like a song you never stop replaying."
        ),
        "dramatic": (
            "This trip felt less like a vacation and more like a survival challenge with cinematic lighting. "
            "Every five minutes something went wrong, but somehow the chaos just kept getting funnier. "
            "We missed buses, lost directions, ignored warning signs, and still walked around like we owned the city. "
            "At one point our entire plan depended on one person saying, 'Bro trust me,' which is honestly terrifying. "
            "The weather switched moods faster than our group chat. "
            "One second we were taking aesthetic sunset photos, next second we were running for our lives in the rain. "
            "Nobody slept properly. Nobody drank enough water. But the confidence levels? Absolutely dangerous. "
            "We climbed things we probably shouldn’t have climbed, ate things we definitely couldn’t pronounce, "
            "and made memories that honestly sound fake when we retell them. "
            "Everything about this trip was loud, chaotic, dramatic, and completely unhinged. "
            "And somehow… that’s exactly what made it legendary."
        ),
        "cinematic": (
            "This trip genuinely felt like living inside a movie nobody wanted to end. "
            "The kind where the lighting is perfect for no reason and every random moment somehow becomes a core memory. "
            "Late-night drives, blurry city lights, overpriced coffee, sunsets that didn’t even look real — "
            "everything felt weirdly cinematic. "
            "We kept saying 'this feels fake' every five minutes because honestly… it did. "
            "There were moments where nobody spoke, and somehow those became the loudest memories. "
            "Just music playing, windows down, everyone tired but secretly not wanting the day to end. "
            "We took hundreds of photos trying to capture the vibe, but none of them fully explained how it actually felt to be there. "
            "And maybe that’s the beautiful part. "
            "Some memories aren’t meant to be perfectly captured. "
            "They’re meant to be felt. "
            "And this trip? "
            "Yeah… this one felt like cinema."
        ),
    }

    hindi_stories = {
        "funny": (
             "ये trip literally proof थी कि हम सब 'it is what it is' mentality पर survive कर रहे हैं। "
             "Planning zero थी, confidence unlimited था। "
             "हम घर से निकले थे Pinterest travel aesthetic बनकर… "
             "और वापस आए low battery, no money, emotionally unstable humans बनकर। "
             "एक दोस्त पूरे trip में बस यही बोल रहा था — "
             "'Guys trust me, I know a shortcut.' "
             "भाई उसके shortcut ने हमें Narnia पहुँचा दिया था। "
             "हमने इतनी photos लीं कि phone storage ने खुद give up कर दिया। "
             "और end में upload वही blurry dump हुई जिसमें कोई properly दिख भी नहीं रहा। "
             "Budget का तो पूरा 'womp womp' हो गया overpriced coffee और random snacks में। "
             "एक point पर हम सब इतने tired थे कि AC वाली जगह देखकर spiritual happiness मिल रही थी। "
             "लेकिन जैसे ही कहीं aesthetic lights दिखीं — "
             "suddenly everyone became a content creator again. "
             "कोई पानी नहीं पी रहा था, कोई map नहीं देख रहा था, "
             "लेकिन सब बोल रहे थे — "
             "'Wait wait candid ले.' "
            "Honestly पूरा trip chaotic था, unserious था, और borderline nonsense था… "
            "but lowkey? "
             "It absolutely slapped."
        ),
        "emotional": (
           "सच कहूँ तो मुझे नहीं लगा था कि ये trip मुझे अंदर से इतना change कर देगा। "
           "कुछ दिनों के लिए life थोड़ी slow लगने लगी थी। "
           "ना stress, ना overthinking, ना वो fake smile जो रोज़ पहननी पड़ती है। "
           "बस sunsets, late-night talks, random हँसी, और वो moments जिन्हें दिल हमेशा के लिए save कर लेना चाहता है। "
           "अजीब है ना… कैसे कुछ लोग इतनी जल्दी strangers से home जैसा feel होने लगते हैं। "
           "शायद इसी लिए ये सिर्फ एक trip नहीं लगा। "
           "ये उन rare moments में से था जहाँ सब कुछ सही feel हो रहा था। "
           "हम सब अपनी-अपनी problems लेकर आए थे, "
           "लेकिन उन कुछ दिनों के लिए ऐसा लगा जैसे दुनिया ने pause ले लिया हो। "
           "और honestly… शायद यही इस trip की सबसे खूबसूरत बात थी। "
           "ना जगहें special थीं, ना photos perfect थीं। "
           "Special था बस वो feeling… सही लोगों के साथ सही moment में होने की। "
           "कुछ memories trip खत्म होने के बाद भी खत्म नहीं होतीं। "
           "वो quietly हमेशा दिल में चलती रहती हैं… किसी favorite song की तरह।"
        ),
        "dramatic": (
            "यह ट्रिप vacation कम और full-on survival movie ज़्यादा लग रही थी। "
            "हर थोड़ी देर में कुछ ना कुछ गलत हो रहा था, लेकिन chaos इतना funny था कि हँसी रुक ही नहीं रही थी। "
            "कभी बस miss हुई, कभी रास्ता गलत निकला, कभी किसी ने confidence के साथ completely गलत direction दे दी। "
            "और सबसे dangerous line थी — 'भाई trust me.' "
            "मौसम भी हमारे group chat की तरह हर पाँच मिनट में mood बदल रहा था। "
            "एक moment हम aesthetic sunset photos ले रहे थे, अगले ही second बारिश से जान बचाकर भाग रहे थे। "
            "ना ठीक से नींद मिली, ना पानी पिया, लेकिन confidence level फिर भी peak पर था। "
            "हम ऐसी जगह चढ़ गए जहाँ शायद नहीं चढ़ना चाहिए था, "
            "ऐसी चीज़ें खा लीं जिनका नाम तक pronounce नहीं हो रहा था, "
            "और ऐसी memories बना लीं जो बाद में सुनाने पर fake लगती हैं। "
            "पूरा trip loud था, messy था, dramatic था, और honestly थोड़ा unhinged भी। "
            "लेकिन शायद यही reason है कि ये इतना legendary बन गया।"
        ),
        "cinematic": (
            "यह ट्रिप सच में किसी ऐसी फिल्म जैसा लगा जिसे कोई खत्म ही नहीं करना चाहता। "
            "वो वाली फिल्म जहाँ बिना वजह हर चीज़ cinematic लगती है और हर छोटा पल एक core memory बन जाता है। "
            "Late night drives, धुंधली city lights, overpriced coffee, और ऐसे sunsets जो unreal लग रहे थे — "
            "सब कुछ किसी movie scene जैसा feel हो रहा था। "
            "हर पाँच मिनट में हम बस यही बोल रहे थे — 'भाई ये सब इतना fake क्यों लग रहा है?' "
            "कुछ moments ऐसे भी थे जहाँ कोई कुछ बोल नहीं रहा था, "
            "लेकिन वही silence सबसे loud memory बन गई। "
            "बस music चल रहा था, windows नीचे थीं, सब थके हुए थे — "
            "लेकिन अंदर से कोई भी उस दिन को खत्म नहीं करना चाहता था। "
            "हमने vibe capture करने के लिए सैकड़ों photos लीं, "
            "लेकिन honestly कोई भी photo उस feeling को पूरी तरह explain नहीं कर पाई। "
            "और शायद यही सबसे खूबसूरत बात है। "
            "कुछ memories capture करने के लिए नहीं होतीं… बस feel करने के लिए होती हैं। "
            "और ये trip? "
            "हाँ… ये पूरी cinema थी।"
        ),
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
        clip = ImageClip(img).set_duration(duration_per_image).resize(height=720)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose")

    # Mix background music + voice
    try:
        music_path = download_music(vibe)
        if music_path:
           from moviepy.audio.fx.all import audio_loop

           bg_music = AudioFileClip(music_path).volumex(0.10)
           bg_music = audio_loop(bg_music, duration=video.duration)

           voice_clip = voice_audio.set_duration(video.duration)

           final_audio = CompositeAudioClip([
             bg_music,
             voice_clip
])
        else:
            final_audio = voice_audio.set_duration(video.duration)
    except Exception as e:
        print(f"Music mixing failed: {e}")
        final_audio = voice_audio.set_duration(video.duration)

    final_video = video.set_audio(final_audio)
    output_path = os.path.join(OUTPUT_FOLDER, "final.mp4")
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    return send_file(output_path, mimetype="video/mp4")
if __name__ == "__main__":
    app.run(debug=True)