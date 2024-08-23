from flask import Flask, request, jsonify, send_file
import os
import subprocess
import boto3
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Initialize the S3 client
s3 = boto3.client('s3')

# Replace with your S3 bucket name
BUCKET_NAME = 'demucss'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/separate', methods=['POST'])
def separate_audio():
    try:
        if 'file' not in request.files:
            return "No file part", 400

        file = request.files['file']
        if file.filename == '':
            return "No selected file", 400

        filename = secure_filename(file.filename)
        base_filename = os.path.splitext(filename)[0]

        # Upload the input file to S3
        s3.upload_fileobj(file, BUCKET_NAME, filename)
        logger.info(f'File {filename} uploaded successfully to S3')

        # Download the file from S3 to local storage
        local_input_path = os.path.join('/tmp', filename)
        s3.download_file(BUCKET_NAME, filename, local_input_path)
        logger.info(f'File {filename} downloaded successfully from S3')

        # Create local output path
        local_output_dir = os.path.join('/tmp', 'outputs')
        os.makedirs(local_output_dir, exist_ok=True)

        # Separate the audio using Demucs
        command = f"demucs {local_input_path} -o {local_output_dir}"
        subprocess.run(command, shell=True)

        # Upload the separated files to S3 in a new folder
        separated_dir = os.path.join(local_output_dir, base_filename)
        uploaded_files = []
        for root, dirs, files in os.walk(separated_dir):
            for file in files:
                local_file_path = os.path.join(root, file)
                s3_key = os.path.join('outputs', base_filename, file)
                with open(local_file_path, 'rb') as f:
                    s3.upload_fileobj(f, BUCKET_NAME, s3_key)
                logger.info(f'File {s3_key} uploaded successfully to S3')
                uploaded_files.append(s3_key)

        return jsonify({'message': 'Files processed and uploaded to S3', 'output_files': uploaded_files})
    except Exception as e:
        logger.error(f'Error processing file: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    try:
        # Use /tmp directory for temporary storage
        download_path = os.path.join('/tmp', filename)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        
        # Download the file from S3
        s3.download_file(BUCKET_NAME, filename, download_path)
        logger.info(f'File {filename} downloaded successfully to {download_path}')
        
        # Send the file to the client
        return send_file(download_path, as_attachment=True)
    except Exception as e:
        logger.error(f'Error downloading file: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
