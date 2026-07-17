/**
 * Handles microphone recording using the browser's MediaRecorder API.
 * On stop, the recorded audio blob is sent to /api/transcribe for
 * Whisper-based transcription.
 */

let mediaRecorder = null;
let audioChunks = [];
let audioStream = null;

async function startRecording() {
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(audioStream);
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) audioChunks.push(event.data);
    };

    mediaRecorder.start();
}

function stopRecording() {
    return new Promise((resolve) => {
        if (!mediaRecorder) {
            resolve(null);
            return;
        }
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
            audioStream.getTracks().forEach((track) => track.stop());
            resolve(audioBlob);
        };
        mediaRecorder.stop();
    });
}

async function transcribeBlob(audioBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob, "answer.webm");

    const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData,
    });
    const data = await response.json();
    if (data.error) throw new Error(data.error);
    return data.transcript;
}
