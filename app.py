import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Dashboard is working!"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Flask starting on port {port}", flush=True)
    app.run(host="0.0.0.0", port=port)
