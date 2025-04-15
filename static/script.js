let mediaRecorder;
let audioChunks = [];

const recordBtn = document.getElementById("record-btn");
const stopBtn = document.getElementById("stop-btn");
const uploadForm = document.getElementById("upload-form");
const statusText = document.getElementById("status");
const resultBox = document.getElementById("result");
const audioPlayer = document.getElementById("audio-player");
const audioSource = document.getElementById("audio-source");

recordBtn.onclick = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];

    mediaRecorder.ondataavailable = e => {
        audioChunks.push(e.data);
    };

    mediaRecorder.start();
    statusText.textContent = "Recording...";

    recordBtn.disabled = true;
    stopBtn.disabled = false;
};

stopBtn.onclick = () => {
    mediaRecorder.stop();
    statusText.textContent = "Recording stopped. You can now submit.";
    recordBtn.disabled = false;
    stopBtn.disabled = true;
};

uploadForm.onsubmit = async (e) => {
    e.preventDefault();

    const pdfInput = document.getElementById("pdf");
    if (!pdfInput.files[0]) {
        alert("Please upload a PDF.");
        return;
    }

    const formData = new FormData();
    formData.append("pdf", pdfInput.files[0]);

    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
    const audioFile = new File([audioBlob], "question.webm", { type: "audio/webm" });
    formData.append("audio", audioFile);

    statusText.textContent = "Uploading and processing...";

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (result.error) {
            resultBox.textContent = `❌ Error: ${result.error}`;
        } else {
            resultBox.innerText = `🎤 Question: ${result.question}\n\n💬 Answer: ${result.answer}`;
            if (result.audio_file) {
                audioSource.src = result.audio_file;
                audioPlayer.load();
                audioPlayer.style.display = "block";
            }
        }

        statusText.textContent = "Done!";
    } catch (err) {
        console.error(err);
        resultBox.textContent = "❌ An unexpected error occurred.";
        statusText.textContent = "Failed.";
    }
};
