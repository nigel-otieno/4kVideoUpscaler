from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import subprocess
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upscale_to_4k(input_path):
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    output_path = os.path.join(UPLOAD_FOLDER, f"{name}_4k{ext}")

    # FFmpeg command to upscale to 4K and force 60 FPS
    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-vf', 'scale=3840:2160',
        '-r', '60',
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '18',
        output_path
    ]

    subprocess.run(cmd, check=True)
    return output_path

@app.route('/')
def index():
    return '''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>4K Video Upscaler</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card shadow-sm rounded">
                        <div class="card-body">
                            <h1 class="card-title text-center mb-4">4K Video Upscaler</h1>
                            <form method="post" enctype="multipart/form-data" action="/upload">
                                <div class="mb-3">
                                    <input class="form-control" type="file" name="video" required>
                                </div>
                                <div class="d-grid">
                                    <button type="submit" class="btn btn-primary">Upload and Upscale</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return 'No file part', 400

    file = request.files['video']
    if file.filename == '':
        return 'No selected file', 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        try:
            output_path = upscale_to_4k(input_path)
            output_filename = os.path.basename(output_path)
            return f"""
            <!doctype html>
            <html lang='en'>
            <head>
                <meta charset='utf-8'>
                <meta name='viewport' content='width=device-width, initial-scale=1'>
                <link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css' rel='stylesheet'>
                <title>Download 4K Video</title>
            </head>
            <body class='bg-light'>
                <div class='container py-5'>
                    <div class='row justify-content-center'>
                        <div class='col-md-6'>
                            <div class='alert alert-success text-center'>
                                <h4 class='mb-3'>Video successfully upscaled to 4K at 60 FPS!</h4>
                                <a href='/download/{output_filename}' class='btn btn-success'>Download 4K Video</a>
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
        except subprocess.CalledProcessError:
            return 'Failed to upscale video', 500

    return 'Invalid file type', 400

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)