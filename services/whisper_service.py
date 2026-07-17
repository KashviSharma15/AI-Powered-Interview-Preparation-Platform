import whisper
import tempfile
import os

_model = None


def get_model():
    """
    Loads the Whisper model once and reuses it across requests.
    'base' is a good balance of speed and accuracy for interview-length
    answers on a laptop CPU. Swap to 'tiny' for faster (less accurate)
    results, or 'small'/'medium' if you have a GPU.
    """
    global _model
    if _model is None:
        _model = whisper.load_model("base")
    return _model


def transcribe_audio(audio_file_storage):
    """
    Accepts a Flask FileStorage object (the uploaded audio blob from the
    browser's MediaRecorder), saves it temporarily, and returns the
    transcribed text. Requires ffmpeg to be installed on the system.
    """
    model = get_model()

    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        audio_file_storage.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = model.transcribe(tmp_path, fp16=False)
        return result["text"].strip()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
