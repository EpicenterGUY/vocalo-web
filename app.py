from flask import Flask, render_template, request
import json
import random
from datetime import date

app = Flask(__name__)

def load_songs():
    with open("songs.json", "r", encoding="utf-8") as f:
        return json.load(f)

def random_recommend(songs, limit=10):
    copied = songs[:]
    random.shuffle(copied)
    return copied[:limit]

def hidden_gems(songs, limit=10):
    filtered = [
        song for song in songs
        if 10000 <= song.get("views", 0) <= 500000
    ]

    random.shuffle(filtered)
    return filtered[:limit]

def today_vocalo(songs, limit=10):
    today = date.today().isoformat()
    random.seed(today)

    copied = songs[:]
    random.shuffle(copied)

    return copied[:limit]

def keyword_recommend(songs, query, limit=10):
    query_words = query.lower().split()
    scored = []

    for song in songs:
        text = " ".join([
            song.get("title", ""),
            song.get("artist", ""),
            song.get("vocal", ""),
            song.get("description", ""),
            " ".join(song.get("keywords", []))
        ]).lower()

        score = 0

        for word in query_words:
            if word in text:
                score += 1

        if score > 0:
            scored.append((score, song))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [song for score, song in scored[:limit]]

@app.route("/", methods=["GET", "POST"])
def index():
    songs = load_songs()
    results = []
    query = ""

    if request.method == "POST":
        mode = request.form.get("mode")
        query = request.form.get("query", "")

        if mode == "keyword":
            results = keyword_recommend(songs, query)

        elif mode == "today":
            results = today_vocalo(songs)

        elif mode == "hidden":
            results = hidden_gems(songs)

        elif mode == "random":
            results = random_recommend(songs)

    return render_template("index.html", results=results, query=query)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)