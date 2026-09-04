from flask import Flask, render_template, request
import os
import base64
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import json
from PIL import Image

try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_PATH = "mood_history.db"

# Create DB table if not exists
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS mood_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            mood TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

import random

messages = {
    'happy': [
        "Enjoy it while it lasts… life’s got plot twists. 😈",
        "Wow, happy? Must be a glitch in the matrix. 🤖",
        "Careful, smiling too much might attract responsibilities. 😅"
    ],
    'sad': [
        "Cry all you want, the Wi-Fi still won’t fix itself. 😢📶",
        "Tears won't pay the bills, but hey—hydration. 💧",
        "Feeling sad? The universe says 'meh'. 🌌"
    ],
    'angry': [
        "Take a breath. Murder is illegal (for now). 🔪🙂",
        "You're not angry, just auditioning for a villain role. 😤🎭",
        "Channel that rage into... cleaning your room maybe? 🧹🔥"
    ],
    'surprise': [
        "Shocked? Wait till you check your bank balance. 😮💸",
        "Surprise! It’s still Monday. 🎉🔁",
        "Didn't see that coming? Plot twist: life doesn't care. 📚🌀"
    ],
    'fear': [
        "Scared? Don’t worry, the end is inevitable anyway. ☠️",
        "Monsters under the bed? Relax, they're unionized now. 👻🪦",
        "Fear is just excitement... with bad lighting. 🔦😨"
    ],
    'disgust': [
        "Some things just can’t be unseen. Welcome to life. 🤢",
        "Grossed out? That's just life saying hello. 👋😬",
        "Ew. You’ve officially leveled up in adulthood. 🧻🧼"
    ],
    'neutral': [
        "Flat as your phone battery. Do something. ⚡😐",
        "Neutral? So... basically a potato. 🥔",
        "Excitement called. You hit ‘Ignore’. 📴🤷"
    ]
}

# Usage example (select random quote based on mood):
# (Removed from production code. Move to tests or documentation if needed.)

# Spotify tracks per emotion: (track name, embed URL)
spotify_tracks = {
    "happy": [
        ("Happy - Pharrell Williams", "https://open.spotify.com/embed/track/60nZcImufyMA1MKQY3dcCH"),
        ("Blinding Lights - The Weeknd", "https://open.spotify.com/embed/track/0VjIjW4GlUZAMYd2vXMi3b"),
        ("Walking on Sunshine", "https://open.spotify.com/embed/track/3GZlhw7QeudRJgJo0yVHfM")
    ],
    "sad": [
        ("Someone Like You - Adele", "https://open.spotify.com/embed/track/7LVHVU3tWfcxj5aiPFEW4Q"),
        ("Let Her Go - Passenger", "https://open.spotify.com/embed/track/0B5ZCdP4He2x4TpoFhYxOJ"),
        ("All I Want - Kodaline", "https://open.spotify.com/embed/track/2X485T9Z5Ly0xyaghN73ed")
    ],
    "angry": [
        ("In the End - Linkin Park", "https://open.spotify.com/embed/track/60a0Rd6pjrkxjPbaKzXjfq"),
        ("Believer - Imagine Dragons", "https://open.spotify.com/embed/track/1G391cbiT3v3Cywg8T7DM1"),
        ("Demons - Imagine Dragons", "https://open.spotify.com/embed/track/5qaEfEh1AtSdrdrByCP7qR")
    ],
    "neutral": [
        ("Sunflower - Post Malone", "https://open.spotify.com/embed/track/3KkXRkHbMCARz0aVfEt68P"),
        ("Memories - Maroon 5", "https://open.spotify.com/embed/track/2b8fOow8UzyDFAE27YhOZM"),
        ("Perfect - Ed Sheeran", "https://open.spotify.com/embed/track/0tgVpDi06FyKpA1z0VMD4v")
    ],
    "surprise": [
        ("Wake Me Up - Avicii", "https://open.spotify.com/embed/track/6JV2JOEocMgcZxYSZelKcc"),
        ("Counting Stars - OneRepublic", "https://open.spotify.com/embed/track/2tpWsVSb9UEmDRxAl1zhX1")
    ],
    "disgust": [
        ("Thnks fr th Mmrs - Fall Out Boy", "https://open.spotify.com/embed/track/5Awg4zIK8OeKGHklDcVd3D"),
        ("Dark Horse - Katy Perry", "https://open.spotify.com/embed/track/4I3xSf2oN7r5lCzXKU0G5g")
    ],
    "fear": [
        ("Lovely - Billie Eilish", "https://open.spotify.com/embed/track/0k6rTg8zkhN5A56fpkU5v3"),
        ("Creep - Radiohead", "https://open.spotify.com/embed/track/3H7ihDc1dqLriiWXwsc2po")
    ]
}
def get_random_quote():
    quotes_path = os.path.join(os.path.dirname(__file__), 'data', 'quotes.json')
    if os.path.exists(quotes_path):
        with open(quotes_path, 'r', encoding='utf-8') as f:
            quotes = json.load(f)
        return random.choice(quotes)
    else:
        # Fallback quote if file does not exist
        return "Keep smiling! (No quotes file found.)"

@app.route('/')
def index():
    quote = get_random_quote()
    return render_template('index.html', quote=quote)

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('image')
    image_data = request.form.get('image_data')

    if file and file.filename != '':
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
    elif image_data:
        # Handle base64 image from camera
        encoded = image_data.split(',', 1)[1] if ',' in image_data else image_data
        img_bytes = base64.b64decode(encoded)
        filename = f"webcam_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(img_bytes)
    else:
        return "No image file or image data provided.", 400

    try:
        if DeepFace is None:
            raise RuntimeError("DeepFace is not installed")
        analysis = DeepFace.analyze(img_path=filepath, actions=['emotion'], enforce_detection=False)
        # DeepFace may return a dict with 'dominant_emotion' or a list of such dicts
        if isinstance(analysis, dict) and 'dominant_emotion' in analysis:
            emotion = analysis['dominant_emotion']
        elif isinstance(analysis, list) and len(analysis) > 0:
            # Each item should be a dict with 'dominant_emotion'
            if isinstance(analysis[0], dict) and 'dominant_emotion' in analysis[0]:
                emotion = analysis[0]['dominant_emotion']
            else:
                emotion = "neutral"
        else:
            emotion = "neutral"
    except Exception:
        emotion = "neutral"
    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO mood_history (timestamp, mood) VALUES (?, ?)", (datetime.now().isoformat(), emotion))
    conn.commit()
    conn.close()
    message = random.choice(messages.get(emotion, ["You’re feeling... something, I guess."]))

    # Pick random Spotify track
    tracks = spotify_tracks.get(emotion, [])
    if tracks:
        selected_track = random.choice(tracks)
        music_title = selected_track[0]
        spotify_embed_url = selected_track[1]
    else:
        music_title = "No track available"
        spotify_embed_url = ""

    # Resize image in-memory before encoding to base64
    from io import BytesIO
    with Image.open(filepath) as img:
        img.thumbnail((500, 500))
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        encoded_img = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return render_template('result.html', mood=emotion.capitalize(), message=message, music=music_title, spotify_embed_url=spotify_embed_url, image_data=encoded_img)

@app.route('/history')
def history():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM mood_history ORDER BY timestamp DESC")
        history = c.fetchall()
        conn.close()
    except Exception as e:
        history = []
        print(f"Database error: {e}")
    # Mood emoji mapping
    mood_emojis = {
        'happy': '😄',
        'sad': '😢',
        'angry': '😡',
        'surprise': '😮',
        'fear': '😨',
        'disgust': '🤢',
        'neutral': '😐'
    }
    from collections import Counter
    mood_stats = Counter(row[2] for row in history if len(row) > 2 and row[2])
    try:
        return render_template(
            'history.html',
            history=history,
            messages=messages,
            spotify_tracks=spotify_tracks,
            mood_emojis=mood_emojis,
            mood_stats=mood_stats
        )
    except Exception as e:
        return f"Template rendering error: {e}", 500


if __name__ == "__main__":
    app.run(debug=True)
