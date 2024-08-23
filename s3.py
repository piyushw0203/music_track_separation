import boto3
from flask import Flask, request, jsonify, send_file
import os
import logging

app = Flask(__name__)

# Initialize the S3 client
s3 = boto3.client('s3')

# Replace with your S3 bucket name
BUCKET_NAME = 'demucss'

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        filename = file.filename
        s3.upload_fileobj(file, BUCKET_NAME, filename)
        logger.info(f'File {filename} uploaded successfully')
        return jsonify({'message': 'File uploaded successfully'})
    except Exception as e:
        logger.error(f'Error uploading file: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
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
    app.run(debug=True)
