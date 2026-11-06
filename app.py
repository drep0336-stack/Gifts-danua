app = Flask(__name__)      # сначала создаётся app
MAX_NUM, STOP_MISSES = 30000, 60
cache, jobs = {}, {}

# ... функции fetch, scan, и маршруты /search, /status ...

@app.get("/health")        # потом /health
def health():
    return "ok"

# ... PAGE и маршрут "/" ...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
