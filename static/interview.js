document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("interview-root");
    const sessionId = root.dataset.sessionId;
    const questionId = root.dataset.questionId;
    const questionText = root.dataset.questionText;
    const idealKeywords = JSON.parse(root.dataset.idealKeywords || "[]");

    const recordBtn = document.getElementById("record-btn");
    const recordLabel = document.getElementById("record-label");
    const recordStatus = document.getElementById("record-status");
    const transcriptBox = document.getElementById("transcript-box");
    const transcriptText = document.getElementById("transcript-text");
    const submitBtn = document.getElementById("submit-answer-btn");
    const scoreBox = document.getElementById("score-box");

    let isRecording = false;

    recordBtn.addEventListener("click", async () => {
        if (!isRecording) {
            // Start
            isRecording = true;
            recordBtn.classList.add("recording");
            recordLabel.textContent = "Stop answer";
            recordStatus.textContent = "Recording... speak your answer, then click stop.";
            transcriptBox.style.display = "none";
            scoreBox.style.display = "none";

            await startRecording();
            startFrameCapture();
        } else {
            // Stop
            isRecording = false;
            recordBtn.classList.remove("recording");
            recordLabel.textContent = "Start answer";
            recordStatus.textContent = "Transcribing your answer...";
            stopFrameCapture();

            const audioBlob = await stopRecording();
            try {
                const transcript = await transcribeBlob(audioBlob);
                transcriptText.value = transcript;
                transcriptBox.style.display = "block";
                recordStatus.textContent = "Done. Review your transcript below, then submit.";
            } catch (err) {
                recordStatus.textContent = "Transcription failed — you can type your answer manually below.";
                transcriptBox.style.display = "block";
            }
        }
    });

    submitBtn.addEventListener("click", async () => {
        submitBtn.disabled = true;
        submitBtn.textContent = "Scoring...";

        const response = await fetch("/api/submit_answer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: sessionId,
                question_id: questionId,
                question_text: questionText,
                transcript: transcriptText.value,
                ideal_keywords: idealKeywords,
                frame_results: collectedFrameResults,
            }),
        });
        const scores = await response.json();

        document.getElementById("score-overall").textContent = scores.overall_score;
        document.getElementById("score-content").textContent = scores.content_score;
        document.getElementById("score-coverage").textContent = scores.keyword_coverage + "%";
        document.getElementById("score-engagement").textContent = scores.engagement_score;
        document.getElementById("score-smile").textContent = scores.smile_score;
        document.getElementById("score-filler").textContent = scores.filler_count;

        scoreBox.style.display = "block";
        transcriptBox.style.display = "none";
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit answer";
    });
});
