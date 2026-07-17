/**
 * Handles webcam preview and periodic frame capture for engagement/expression
 * analysis. Frames are sent to the backend every 2.5s while recording is
 * active; results are accumulated and averaged when the answer is submitted.
 */

let webcamStream = null;
let frameCaptureInterval = null;
let collectedFrameResults = [];

async function startWebcam() {
    const video = document.getElementById("webcam-video");
    try {
        webcamStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = webcamStream;
    } catch (err) {
        console.warn("Webcam unavailable:", err);
        document.querySelector(".interview-side").innerHTML =
            '<p class="webcam-note">Webcam not available — engagement scoring will be skipped for this session.</p>';
    }
}

function captureFrameBase64() {
    const video = document.getElementById("webcam-video");
    const canvas = document.getElementById("webcam-canvas");
    if (!video || !video.videoWidth) return null;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.7);
}

async function analyzeCurrentFrame() {
    const imageData = captureFrameBase64();
    if (!imageData) return;

    try {
        const response = await fetch("/api/analyze_frame", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: imageData }),
        });
        const result = await response.json();
        collectedFrameResults.push(result);
    } catch (err) {
        console.warn("Frame analysis failed:", err);
    }
}

function startFrameCapture() {
    collectedFrameResults = [];
    frameCaptureInterval = setInterval(analyzeCurrentFrame, 2500);
}

function stopFrameCapture() {
    if (frameCaptureInterval) {
        clearInterval(frameCaptureInterval);
        frameCaptureInterval = null;
    }
}

document.addEventListener("DOMContentLoaded", startWebcam);
