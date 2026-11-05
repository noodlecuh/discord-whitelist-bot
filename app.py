import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Dashboard is working!"

if __name__ == "__main__":
    print("Flask starting on port 8080", flush=True)
    app.run(host="0.0.0.0", port=8080)
