from flask import Flask, render_template, request
import json
import random
from datetime import date
import requests
import os

app = Flask(__name__)


def load_songs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "songs.json")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def random_recommend(songs, limit=10):
    copied = songs[:]
    random.shuffle(copied)
    return copied[:limit]


def view_range_recommend(songs, min_views, max_views, limit=10):
    filtered = []

    for song in songs:
        views = song.get("views", 0)

        if min_views <= views <= max_views:
            filtered.append(song)

    random.shuffle(filtered)
    return filtered[:limit]


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

def nico_view_range_recommend(min_views, max_views, query="VOCALOID", limit=10):
    api_url = "https://snapshot.search.nicovideo.jp/api/v2/snapshot/video/contents/search"

    headers = {
        "User-Agent": "VocaPick/0.1"
    }

    params = {
        "q": query,
        "targets": "tagsExact",
        "fields": "contentId,title,description,tags,viewCounter,commentCounter,mylistCounter,likeCounter,thumbnailUrl,startTime",
        "filters[viewCounter][gte]": min_views,
        "filters[viewCounter][lte]": max_views,
        "_sort": "-viewCounter",
        "_offset": 0,
        "_limit": 50,
        "_context": "VocaPick"
    }

    try:
        response = requests.get(api_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        videos = data.get("data", [])
        songs = []

        for video in videos:
            content_id = video.get("contentId", "")

            songs.append({
                "title": video.get("title", "제목 없음"),
                "artist": "ニコニコ動画",
                "vocal": query,
                "views": video.get("viewCounter", 0),
                "description": video.get("description", ""),
                "keywords": video.get("tags", []),
                "url": f"https://www.nicovideo.jp/watch/{content_id}",
                "thumbnail": video.get("thumbnailUrl", "")
            })

        random.shuffle(songs)
        return songs[:limit]

    except Exception as e:
        print("니코동 API 오류:", e)
        return []


def keyword_recommend(songs, query, limit=10):
    query = query.strip().lower()

    if not query:
        return []

    query_words = query.split()
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
                score += 2

        if query in text:
            score += 3

        if score > 0:
            scored.append((score, song))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [song for score, song in scored[:limit]]


@app.route("/", methods=["GET", "POST"])
def index():
    songs = load_songs()
    results = []
    message = ""

    nico_query = ""
    keyword_query = ""
    min_views = "0"
    max_views = "50000"

    if request.method == "POST":
        mode = request.form.get("mode")

        nico_query = request.form.get("nico_query", "")
        keyword_query = request.form.get("keyword_query", "")

        min_views = request.form.get("min_views", "0")
        max_views = request.form.get("max_views", "50000")

        try:
            min_views_int = int(min_views)
            max_views_int = int(max_views)
        except ValueError:
            min_views_int = 0
            max_views_int = 50000

        if mode == "views":
            search_word = nico_query.strip() if nico_query.strip() else "VOCALOID"

            results = nico_view_range_recommend(
                min_views_int,
                max_views_int,
                query=search_word
            )

        elif mode == "keyword":
            results = keyword_recommend(songs, keyword_query)

        elif mode == "today":
            results = today_vocalo(songs)

        elif mode == "hidden":
            results = hidden_gems(songs)

        elif mode == "random":
            results = random_recommend(songs)

        if not results:
            message = "조건에 맞는 곡이 없어요. 태그, 키워드, 조회수 범위를 바꿔보세요."

    return render_template(
        "index.html",
        results=results,
        message=message,
        nico_query=nico_query,
        keyword_query=keyword_query,
        min_views=min_views,
        max_views=max_views
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)