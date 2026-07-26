"""
Flask server exposing the agent pipeline over HTTP so the UI (ui/index.html)
can trigger it with a plain fetch() call.

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000 in a browser.
"""

from flask import Flask, request, jsonify, send_from_directory
from agents import AgentPipeline

app = Flask(__name__, static_folder="ui", static_url_path="")
pipeline = AgentPipeline()


@app.route("/")
def index():
    return send_from_directory("ui", "index.html")


@app.route("/api/run-pipeline", methods=["POST"])
def run_pipeline():
    data = request.get_json(force=True)
    grade = data.get("grade")
    topic = data.get("topic")

    if grade is None or not topic:
        return jsonify({"error": "Both 'grade' and 'topic' are required."}), 400

    try:
        result = pipeline.run(grade=grade, topic=topic)
        return jsonify(result)
    except Exception as exc:  # surface pipeline/agent errors to the UI
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
