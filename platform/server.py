"""HEART Platform — Unified shell that integrates HEART /ops (5560) + Luis dashboard (3000)."""
from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

OPS_BASE  = "http://localhost:5560"
LUIS_BASE = "http://localhost:3000"

MODULES = [
    {"id": "arrivals",   "label": "Today's Arrivals",  "group": "Front-of-house",  "src": f"{LUIS_BASE}/",                                "source": "luis"},
    {"id": "humanqueue", "label": "Human Queue",       "group": "Front-of-house",  "src": f"{OPS_BASE}/ops?view=humanqueue&chrome=0",      "source": "ops"},
    {"id": "agents",     "label": "Guest Agents",      "group": "Front-of-house",  "src": f"{OPS_BASE}/ops?view=agents&chrome=0",          "source": "ops"},
    {"id": "departing",  "label": "Departing Threads", "group": "Front-of-house",  "src": f"{OPS_BASE}/ops?view=departing&chrome=0",       "source": "ops"},
    {"id": "hapconsole", "label": "HAP Console",       "group": "Protocol",        "src": f"{LUIS_BASE}/hap-console",                      "source": "merged"},
    {"id": "reputation", "label": "Reputation Audit",  "group": "Protocol",        "src": f"{OPS_BASE}/ops?view=reputation&chrome=0",      "source": "ops"},
    {"id": "roigap",     "label": "Agent ROI",         "group": "Insights",        "src": f"{OPS_BASE}/ops?view=roigap&chrome=0",          "source": "ops"},
    {"id": "install",    "label": "HAP Installation",  "group": "Setup",           "src": f"{LUIS_BASE}/install",                          "source": "luis"},
]

@app.route("/")
def index():
    return render_template("platform.html", modules=MODULES, ops_base=OPS_BASE, luis_base=LUIS_BASE)

@app.route("/api/metrics")
def metrics():
    """Aggregate live metrics from /ops."""
    try:
        d = requests.get(f"{OPS_BASE}/api/heart/v1/metrics", timeout=2).json()
        return jsonify(d)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/health")
def health():
    out = {"platform": "ok"}
    for name, base in (("ops", OPS_BASE), ("luis", LUIS_BASE)):
        try:
            r = requests.get(base + ("/api/heart/v1/metrics" if name == "ops" else "/"), timeout=2)
            out[name] = "ok" if r.status_code < 500 else f"http {r.status_code}"
        except Exception as e:
            out[name] = f"down: {e.__class__.__name__}"
    return jsonify(out)

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════╗
║  HEART Platform — Unified Operations             ║
║  http://localhost:5570                           ║
║                                                  ║
║  Upstreams:                                      ║
║    HEART /ops   → http://localhost:5560          ║
║    Luis Dashboard → http://localhost:3000        ║
╚══════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=5570, debug=False, threaded=True)
