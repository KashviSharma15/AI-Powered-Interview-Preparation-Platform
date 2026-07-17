import cv2
import numpy as np
import base64

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_smile.xml")
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")


def _decode_base64_image(base64_string):
    """Converts a 'data:image/jpeg;base64,...' string from the browser into a cv2 frame."""
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    img_bytes = base64.b64decode(base64_string)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return frame


def analyze_frame(base64_image):
    """
    Runs lightweight face/smile/eye detection on a single webcam frame.
    Returns heuristic scores (0-100) for:
      - engagement: whether a face is present and roughly centered (proxy for
        looking at the camera, rather than looking away or leaving frame)
      - smile: whether a smile was detected within the face region

    This uses classical Haar cascades (bundled with opencv-python) rather
    than a deep model, so it runs instantly on any laptop CPU with no
    extra downloads. It's a proxy signal, not a clinical read on emotion —
    framed to the user as a rough confidence/engagement indicator only.
    """
    frame = _decode_base64_image(base64_image)
    if frame is None:
        return {"face_detected": False, "engagement_score": 0, "smile_score": 0}

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_h, frame_w = gray.shape

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(80, 80))

    if len(faces) == 0:
        return {"face_detected": False, "engagement_score": 0, "smile_score": 0}

    # Use the largest detected face (closest to camera)
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    face_center_x = x + w / 2
    face_center_y = y + h / 2

    # Engagement proxy: how close the face center is to the frame center,
    # plus how large the face is (closer/more present = more engaged)
    center_offset_x = abs(face_center_x - frame_w / 2) / (frame_w / 2)
    center_offset_y = abs(face_center_y - frame_h / 2) / (frame_h / 2)
    centeredness = max(0, 1 - (center_offset_x + center_offset_y) / 2)
    size_ratio = min(1.0, (w * h) / (frame_w * frame_h * 0.15))
    engagement_score = round((0.6 * centeredness + 0.4 * size_ratio) * 100, 1)

    # Smile detection within the face region only (reduces false positives)
    face_roi_gray = gray[y:y + h, x:x + w]
    smiles = smile_cascade.detectMultiScale(face_roi_gray, scaleFactor=1.7, minNeighbors=20)
    smile_score = 100.0 if len(smiles) > 0 else 30.0

    return {
        "face_detected": True,
        "engagement_score": engagement_score,
        "smile_score": smile_score,
    }


def aggregate_frame_scores(frame_results):
    """Averages engagement/smile scores across all frames captured during one answer."""
    valid = [f for f in frame_results if f.get("face_detected")]
    if not valid:
        return {"engagement_score": 0, "smile_score": 0}
    avg_engagement = round(sum(f["engagement_score"] for f in valid) / len(valid), 1)
    avg_smile = round(sum(f["smile_score"] for f in valid) / len(valid), 1)
    return {"engagement_score": avg_engagement, "smile_score": avg_smile}
