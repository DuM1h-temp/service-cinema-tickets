from flask import Flask, render_template, request, session, abort, redirect, url_for
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


@app.route("/book", methods=["POST"])
def book():
    show_id = int(request.form["show_id"])
    seat_value = request.form.get("seat")
    name = request.form.get("name")
    surname = request.form.get("surname")
    if not seat_value or not name or not surname:
        abort(400, "Всі поля мають бути заповнені.")

    try:
        row_str, seat_str = seat_value.split('-')
        row = int(row_str)
        seat = int(seat_str)
    except Exception:
        abort(400, "Некоректний формат вибору місця.")

    data = load_data()
    show = next((s for s in data["shows"] if s["id"] == show_id), None)
    if not show or "seats" not in show:
        abort(404, "Показ не знайдено або немає даних про місця.")

    seat_obj = show["seats"][row][seat]
    if seat_obj["status"] == 0:
        seat_obj["status"] = 1
        seat_obj["booked_by"] = f"{name} {surname}"
        save_data(data)
        films = load_films()
        film = next((f for f in films if f["id"] == show["film_id"]), None)
        return render_template("confirm.html", film=film, row=row+1, seat=seat+1, booked_by=seat_obj["booked_by"], time=show["time"])
    else:
        abort(400, "Це місце вже зайняте. Повернись назад і вибери інше.")

@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    if not session.get("admin"):
        abort(403)
    films = load_films()
    data = load_data()
    if request.method == "POST":
        film_id = int(request.form["film_id"])
        date = request.form["date"]
        time = request.form["time"]
        new_id = max((s["id"] for s in data["shows"]), default=0) + 1
        new_show = {
            "id": new_id,
            "film_id": film_id,
            "date": date,
            "time": time,
            "seats": [
                [{"status": 0, "booked_by": None} for _ in range(5)] for _ in range(3)
            ]
        }
        data["shows"].append(new_show)
        save_data(data)
        return redirect(url_for("admin_panel"))
    return render_template("admin.html", films=films, shows=data["shows"])

@app.route("/admin/edit_show/<int:show_id>", methods=["POST"])
def edit_show(show_id):
    if not session.get("admin"):
        abort(403)
    data = load_data()
    show = next((s for s in data["shows"] if s["id"] == show_id), None)
    if not show:
        abort(404, "Показ не знайдено.")

    show["film_id"] = int(request.form["film_id"])
    show["date"] = request.form["date"]
    show["time"] = request.form["time"]
    save_data(data)

    return redirect(url_for("admin_panel"))

@app.route("/admin/delete/<int:show_id>", methods=["POST"])
def delete_show(show_id):
    if not session.get("admin"):
        abort(403)
    data = load_data()
    original_len = len(data["shows"])
    data["shows"] = [s for s in data["shows"] if s["id"] != show_id]
    if len(data["shows"]) < original_len:
        save_data(data)
    return redirect(url_for("admin_panel"))

@app.route("/add_film", methods=["POST"])
def add_film():
    if not session.get("admin"):
        abort(403)

    title = request.form.get("title")
    poster_url = request.form.get("poster_url")

    if not title or not poster_url:
        abort(400, "Назва і постер обов'язкові")

    films = load_films()
    new_id = max((f["id"] for f in films), default=0) + 1

    new_film = {
        "id": new_id,
        "title": title,
        "poster_url": poster_url
    }

    films.append(new_film)

    with open("films.json", "w", encoding="utf-8") as f:
        json.dump(films, f, indent=4, ensure_ascii=False)

    return redirect(url_for("admin_panel"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        data = load_data()
        admin = data.get("admin", {})
        if username == admin.get("username") and password == admin.get("password"):
            session["admin"] = True
            return redirect(url_for("admin_panel"))
        else:
            return render_template("login.html", error="Невірний логін або пароль")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

@app.context_processor
def inject_user():
    return dict(is_admin=session.get("admin", False))