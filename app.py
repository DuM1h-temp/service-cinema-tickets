from flask import Flask, render_template, request, session
import json
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"

def load_films():
    with open("films.json", "r", encoding="utf-8") as f:
        return json.load(f)

def load_data():
    with open("data.json", "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route("/")
def index():
    films = load_films()
    data = load_data()

    filter_date = request.args.get("date")
    if not filter_date:
        filter_date = datetime.now().strftime("%Y-%m-%d")

    shows_sorted = sorted(data["shows"], key=lambda s: (s["date"], s["time"]))
    shows_by_date = defaultdict(list)

    for show in shows_sorted:
        if show["date"] != filter_date:
            continue
        film = next((f for f in films if f["id"] == show["film_id"]), None)
        if film:
            show_info = show.copy()
            show_info["film"] = film
            shows_by_date[show["date"]].append(show_info)

    is_admin = session.get("admin", False)

    return render_template("index.html", shows_by_date=shows_by_date, is_admin=is_admin, filter_date=filter_date)