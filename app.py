import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

from services import db, question_service, scoring_service, vision_service

load_dotenv()

app = Flask(__name__)
db.init_db()

# In-memory tracker of which question IDs have been shown per session,
# so the same session doesn't repeat a question. Fine for a single-user
# local app; would move to the DB for a multi-user deployment.
SESSION_SEEN_QUESTIONS = {}
SESSION_USE_AI = {}
QUESTIONS_PER_SESSION = 5


@app.route("/")
def index():
    roles = question_service.get_roles()
    api_key_configured = bool(os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))
    return render_template("index.html", roles=roles, api_key_configured=api_key_configured)


@app.route("/start", methods=["POST"])
def start_session():
    role = request.form.get("role")
    use_ai = request.form.get("use_ai") == "on"
    session_id = db.create_session(role)
    SESSION_SEEN_QUESTIONS[session_id] = []
    SESSION_USE_AI[session_id] = use_ai
    return redirect(url_for("interview", session_id=session_id))


@app.route("/interview/<int:session_id>")
def interview(session_id):
    session = db.get_session(session_id)
    if not session:
        return redirect(url_for("index"))

    attempts_so_far = len(db.get_session_attempts(session_id))
    if attempts_so_far >= QUESTIONS_PER_SESSION:
        return redirect(url_for("results", session_id=session_id))

    seen_ids = SESSION_SEEN_QUESTIONS.get(session_id, [])

    # Try AI-generated question first if an API key is configured AND the
    # user opted in for this session, else fall back to the local bank
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    question = None
    if api_key and SESSION_USE_AI.get(session_id):
        question = question_service.generate_ai_question(session["role"], api_key)
    if question is None:
        question = question_service.get_random_question(session["role"], exclude_ids=seen_ids)

    if question is None:
        return redirect(url_for("results", session_id=session_id))

    SESSION_SEEN_QUESTIONS.setdefault(session_id, []).append(question["id"])

    return render_template(
        "interview.html",
        session_id=session_id,
        role=session["role"],
        question=question,
        question_number=attempts_so_far + 1,
        total_questions=QUESTIONS_PER_SESSION,
        has_ai_key=bool(api_key),
    )


@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    audio_file = request.files["audio"]
    try:
        transcript = whisper_transcribe(audio_file)
        return jsonify({"transcript": transcript})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def whisper_transcribe(audio_file):
    from services.whisper_service import transcribe_audio
    return transcribe_audio(audio_file)


@app.route("/api/analyze_frame", methods=["POST"])
def api_analyze_frame():
    data = request.get_json()
    image_b64 = data.get("image")
    if not image_b64:
        return jsonify({"error": "No image provided"}), 400
    result = vision_service.analyze_frame(image_b64)
    return jsonify(result)


@app.route("/api/submit_answer", methods=["POST"])
def api_submit_answer():
    data = request.get_json()
    session_id = data.get("session_id")
    question_id = data.get("question_id")
    question_text = data.get("question_text")
    transcript = data.get("transcript", "")
    ideal_keywords = data.get("ideal_keywords", [])
    frame_results = data.get("frame_results", [])

    vision_agg = vision_service.aggregate_frame_scores(frame_results)

    scores = scoring_service.score_answer(
        transcript,
        ideal_keywords,
        engagement_score=vision_agg["engagement_score"],
        smile_score=vision_agg["smile_score"],
    )

    db.save_attempt(session_id, question_id, question_text, transcript, scores)

    return jsonify(scores)


@app.route("/results/<int:session_id>")
def results(session_id):
    session = db.get_session(session_id)
    attempts = db.get_session_attempts(session_id)
    if not attempts:
        avg_score = 0
    else:
        avg_score = round(sum(a["overall_score"] for a in attempts) / len(attempts), 1)
    return render_template("results.html", session=session, attempts=attempts, avg_score=avg_score)


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/dashboard_data")
def api_dashboard_data():
    sessions = db.get_all_sessions_summary()
    return jsonify(sessions)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
