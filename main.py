import os
import io
from flask import Flask, request, render_template, jsonify, send_file
from werkzeug.utils import secure_filename
import google.generativeai as google_ai
from google.cloud import texttospeech_v1
import speech_recognition as sr
from pydub import AudioSegment
import PyPDF2

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Set up Gemini
API_KEY = os.getenv('GOOGLE_AI_API_KEY')
if API_KEY:
    google_ai.configure(api_key=API_KEY)
    model = google_ai.GenerativeModel('gemini-1.5-flash')
else:
    raise Exception("GOOGLE_AI_API_KEY not set.")

# Set up Google Text-to-Speech
tts_client = texttospeech_v1.TextToSpeechClient()

# Allowed file types
ALLOWED_EXTENSIONS = {'pdf', 'wav', 'mp3', 'm4a', 'webm'}

def allowed_file(filename, types):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in types

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

def transcribe_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    wav_path = file_path.rsplit('.', 1)[0] + ".wav"
    audio.export(wav_path, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        return recognizer.recognize_google(audio_data)

def synthesize_speech(text):
    input = texttospeech_v1.SynthesisInput(text=text)
    voice = texttospeech_v1.VoiceSelectionParams(language_code="en-US")
    audio_config = texttospeech_v1.AudioConfig(audio_encoding="LINEAR16")
    request = texttospeech_v1.SynthesizeSpeechRequest(
        input=input,
        voice=voice,
        audio_config=audio_config
    )
    response = tts_client.synthesize_speech(request=request)
    return response.audio_content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf' not in request.files or 'audio' not in request.files:
        return jsonify({'error': 'PDF or Audio file missing'}), 400

    pdf = request.files['pdf']
    audio = request.files['audio']

    if not allowed_file(pdf.filename, {'pdf'}) or not allowed_file(audio.filename, ALLOWED_EXTENSIONS):
        return jsonify({'error': 'Invalid file format'}), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(pdf.filename))
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(audio.filename))

    pdf.save(pdf_path)
    audio.save(audio_path)

    try:
        pdf_text = extract_text_from_pdf(pdf_path)
        question_text = transcribe_audio(audio_path)

        prompt = f"""
        Given the following book content and a question, provide the answer.

        Book Content:
        {pdf_text}

        Question:
        {question_text}
        """

        response = model.generate_content(prompt)
        answer_text = response.text

        # Convert answer text to speech
        audio_output = synthesize_speech(answer_text)

        # Save the audio to a file
        audio_response_path = os.path.join(app.config['UPLOAD_FOLDER'], "response.wav")
        with open(audio_response_path, "wb") as out:
            out.write(audio_output)

        return jsonify({
            "question": question_text,
            "answer": answer_text,
            "audio_file": "/get_audio"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_audio')
def get_audio():
    path = os.path.join(app.config['UPLOAD_FOLDER'], "response.wav")
    return send_file(path, mimetype='audio/wav')

if __name__ == '__main__':
    app.run(debug=True, port=8081)