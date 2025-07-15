from flask import Flask
import json

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
