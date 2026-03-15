from flask import Flask
import database
import threading

app = Flask(__name__)

@app.route("/")
def home():
    return f"<h1>予約一覧</h1><pre>{database.get_all()}</pre>"

def start_web():
    def run():
        app.run(port=5000)
    threading.Thread(target=run).start()