# Rehearsal — AI Interview Preparation Platform

A local, full-stack mock interview tool that listens to your spoken answers,
watches your webcam for a light engagement/expression read, and scores each
answer on content relevance, keyword coverage, and delivery — then tracks
your progress across sessions.

Built with **Flask, OpenAI Whisper, OpenCV, and scikit-learn**. Runs entirely
on your own machine — no cloud services required (an LLM API key is optional,
only needed if you want AI-generated questions instead of the local bank).

---

## Features

- **Role-based mock interviews** — Software Engineer, Data Analyst, and
  HR/Behavioral tracks, five questions per session, pulled from a local
  question bank (or generated fresh via an LLM if you provide an API key).
- **Speech-to-text answers** — record your spoken answer in the browser;
  Whisper transcribes it locally, and you can edit the transcript before
  submitting.
- **Webcam engagement read** — lightweight OpenCV face/smile detection runs
  on periodic frames while you speak, giving a rough engagement and
  expression score. Nothing is stored as video or images.
- **NLP-based scoring** — each answer is scored on:
  - Content relevance (TF-IDF similarity to expected answer concepts)
  - Keyword coverage (how many key concepts you touched on)
  - Answer length and filler-word usage
  - Engagement and expression (from the webcam read)
- **Progress dashboard** — every session is saved to a local SQLite database,
  with a score-trend chart across all your past sessions.

---

## Project structure

```
interview-prep-platform/
├── app.py                     # Flask app and routes
├── requirements.txt
├── .env.example                # Copy to .env if using AI question generation
├── data/
│   └── questions.json          # Local question bank
├── services/
│   ├── db.py                   # SQLite session/attempt storage
│   ├── question_service.py     # Question bank + optional AI generation
│   ├── scoring_service.py      # NLP-based answer scoring
│   ├── vision_service.py       # OpenCV webcam frame analysis
│   └── whisper_service.py      # Whisper speech-to-text
├── static/
│   ├── css/style.css
│   └── js/
│       ├── recorder.js         # Mic recording (MediaRecorder API)
│       ├── webcam.js           # Webcam preview + frame capture
│       ├── interview.js        # Orchestrates the record/score flow
│       └── dashboard.js        # Chart.js progress chart
└── templates/
    ├── base.html, index.html, interview.html, results.html, dashboard.html
```

---

## Setup

### 1. Prerequisites

- **Python 3.10 or 3.11** recommended (Whisper/torch have the smoothest
  install experience on these versions).
- **ffmpeg** installed on your system — Whisper needs this to decode audio.
  - macOS: `brew install ffmpeg`
  - Windows: download from https://ffmpeg.org/download.html and add to PATH
  - Linux: `sudo apt install ffmpeg`

### 2. Create a virtual environment and install dependencies

```bash
cd interview-prep-platform
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> Note: `openai-whisper` will also pull in `torch`, which is a large
> download (a few hundred MB). This is expected and only happens once.

### 3. (Optional) Enable AI-generated questions

If you want fresh, AI-generated questions instead of only the local bank:

```bash
cp .env.example .env
```

Then open `.env` and add your Anthropic API key:
```
ANTHROPIC_API_KEY=your_key_here
```

If you skip this step, the app works fully offline using the local
question bank in `data/questions.json` — no functionality is lost, you
just get the same curated question set instead of freshly generated ones.

### 4. Run the app

```bash
python app.py
```

Open **http://localhost:5000** in your browser. Grant microphone and
webcam permissions when prompted.

---

## How scoring works

Each answer produces five component scores that combine into an overall
score out of 100:

| Component | What it measures | How |
|---|---|---|
| Content relevance | Does the answer touch the right concepts? | TF-IDF cosine similarity between your transcript and the question's expected-concept keywords |
| Keyword coverage | % of expected keywords mentioned | Simple keyword matching against the question's `ideal_keywords` |
| Filler words | Use of "um", "like", "actually", etc. | Regex count, penalizes overall score above a threshold |
| Engagement | Rough proxy for looking at the camera / being present | Face detection + how centered/prominent the face is in-frame |
| Expression | Rough proxy for positive expression | Smile detection within the face region |

This uses classical, lightweight models (TF-IDF, Haar cascades) rather than
large deep-learning models, so it runs instantly on a normal laptop CPU with
no GPU or extra downloads beyond Whisper itself. It's a directional signal
for practice purposes — not a clinical or definitive read on your interview
performance.

---

## Troubleshooting

- **"No module named whisper"** — make sure your virtual environment is
  activated and `pip install -r requirements.txt` completed without errors.
- **Transcription fails / hangs** — confirm `ffmpeg` is installed and on
  your PATH (`ffmpeg -version` in your terminal should work).
- **Webcam/mic permission denied** — check your browser's site settings for
  `localhost:5000` and allow camera/microphone access.
- **First transcription is slow** — Whisper downloads its model weights
  (~150MB for the "base" model) the first time it runs. Subsequent runs are
  fast since the model is cached locally.
- **Want faster transcription?** — open `services/whisper_service.py` and
  change `whisper.load_model("base")` to `whisper.load_model("tiny")`
  (faster, slightly less accurate).

---

## Tech stack

Python, Flask, OpenAI Whisper, OpenCV, scikit-learn (TF-IDF), SQLite,
vanilla JavaScript (MediaRecorder API, Canvas API), Chart.js.

## Suggested CV line

> Built and ran locally a full-stack AI mock-interview platform (Flask,
> Whisper, OpenCV, scikit-learn) that transcribes spoken answers, scores
> content relevance and keyword coverage via NLP, reads webcam engagement
> via computer vision, and tracks performance trends across sessions.
