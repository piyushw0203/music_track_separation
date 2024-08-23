from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
import os
import shutil
import subprocess

app = Flask(__name__)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/separate', methods=['POST'])
def separate_audio():
    if 'file' not in request.files:
        return "No file part", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    filename = secure_filename(file.filename)
    upload_path = os.path.join(UPLOAD_DIR, filename)
    file.save(upload_path)

    output_path = os.path.join(OUTPUT_DIR, filename)
    command = f"demucs {upload_path} -o {OUTPUT_DIR}"
    subprocess.run(command, shell=True)

    separated_dir = os.path.join(OUTPUT_DIR, filename.split('.')[0])
    output_zip = shutil.make_archive(output_path, 'zip', separated_dir)

    return send_file(output_zip, as_attachment=True, download_name=f"{filename.split('.')[0]}.zip")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
