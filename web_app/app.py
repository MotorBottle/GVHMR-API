import os
import sys
import subprocess
import shutil
import traceback
import logging
import zipfile
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = '/app/uploads'
RESULTS_FOLDER = '/app/results'
GVHMR_PATH = '/app/gvhmr'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'm4v'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_models_installed():
    """Check if required model checkpoints are installed"""
    required_models = {
        'GVHMR': '/app/gvhmr/inputs/checkpoints/gvhmr/gvhmr_siga24_release.ckpt',
        'HMR2': '/app/gvhmr/inputs/checkpoints/hmr2/epoch=10-step=25000.ckpt',
        'ViTPose': '/app/gvhmr/inputs/checkpoints/vitpose/vitpose-h-multi-coco.pth',
        'YOLO': '/app/gvhmr/inputs/checkpoints/yolo/yolov8x.pt',
        'DPVO (optional)': '/app/gvhmr/inputs/checkpoints/dpvo/dpvo.pth',
    }

    status = {}
    for name, path in required_models.items():
        status[name] = os.path.exists(path)

    return status

@app.route('/')
def index():
    model_status = check_models_installed()
    return render_template('index.html', model_status=model_status)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        return jsonify({
            'success': True,
            'filename': filename,
            'message': 'File uploaded successfully'
        })

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.json
        filename = data.get('filename')
        use_static_camera = data.get('static_camera', True)

        logger.info(f"Processing request for file: {filename}, static_camera: {use_static_camera}")

        if not filename:
            logger.error("No filename provided")
            return jsonify({'error': 'No filename provided'}), 400

        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(input_path):
            logger.error(f"File not found: {input_path}")
            return jsonify({'error': 'File not found'}), 404

        # Check if models are installed
        model_status = check_models_installed()
        logger.info(f"Model status: {model_status}")

        # Check required models (DPVO is optional, only needed for moving camera)
        required_models = ['GVHMR', 'HMR2', 'ViTPose', 'YOLO']
        missing_required = [k for k in required_models if not model_status.get(k, False)]

        # Check DPVO only if moving camera mode
        if not use_static_camera and not model_status.get('DPVO (optional)', False):
            missing_required.append('DPVO (optional)')

        if missing_required:
            logger.error(f"Missing models: {missing_required}")
            return jsonify({
                'error': 'Missing model checkpoints',
                'missing_models': missing_required,
                'message': 'Please download the required model checkpoints. See documentation.'
            }), 500

        # Prepare output directory
        output_name = Path(filename).stem
        output_path = os.path.join(RESULTS_FOLDER, output_name)
        os.makedirs(output_path, exist_ok=True)
        logger.info(f"Output directory: {output_path}")
        # Build command
        cmd = [
            'python',
            '/app/gvhmr/tools/demo/demo.py',
            f'--video={input_path}',
            f'--output_root={output_path}'
        ]

        if use_static_camera:
            cmd.append('-s')

        # Run GVHMR
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=GVHMR_PATH,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )

        logger.info(f"Command completed with return code: {result.returncode}")
        if result.stdout:
            logger.info(f"STDOUT: {result.stdout[:500]}")
        if result.stderr:
            logger.error(f"STDERR: {result.stderr[:500]}")

        if result.returncode != 0:
            logger.error(f"Processing failed with return code {result.returncode}")
            return jsonify({
                'error': 'Processing failed',
                'stderr': result.stderr,
                'stdout': result.stdout
            }), 500

        # Check for output files
        output_files = list(Path(output_path).rglob('*'))
        logger.info(f"Found {len(output_files)} output files")

        return jsonify({
            'success': True,
            'output_path': output_name,
            'message': 'Video processed successfully',
            'stdout': result.stdout,
            'file_count': len(output_files)
        })

    except subprocess.TimeoutExpired as e:
        logger.error(f"Processing timeout: {e}")
        return jsonify({'error': 'Processing timeout (10 minutes exceeded)'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/results/<path:output_name>')
def get_results(output_name):
    output_path = os.path.join(RESULTS_FOLDER, output_name)
    if not os.path.exists(output_path):
        return jsonify({'error': 'Results not found'}), 404

    # List all files in the output directory
    files = []
    for root, dirs, filenames in os.walk(output_path):
        for f in filenames:
            rel_path = os.path.relpath(os.path.join(root, f), output_path)
            files.append(rel_path)

    return jsonify({
        'output_name': output_name,
        'files': files
    })

@app.route('/download/<path:output_name>/<path:filename>')
def download_file(output_name, filename):
    file_path = os.path.join(RESULTS_FOLDER, output_name, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_path, as_attachment=True)

@app.route('/download_zip/<path:output_name>')
def download_zip(output_name):
    """Download all results as a zip file"""
    output_path = os.path.join(RESULTS_FOLDER, output_name)

    if not os.path.exists(output_path):
        return jsonify({'error': 'Results not found'}), 404

    # Create a temporary zip file
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    temp_zip.close()

    try:
        # Create zip file with all results
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_path)
                    zipf.write(file_path, arcname)

        logger.info(f"Created zip file for {output_name}: {temp_zip.name}")

        # Send the zip file and delete after sending
        return send_file(
            temp_zip.name,
            as_attachment=True,
            download_name=f"{output_name}_results.zip",
            mimetype='application/zip'
        )
    except Exception as e:
        logger.error(f"Error creating zip: {e}")
        logger.error(traceback.format_exc())
        if os.path.exists(temp_zip.name):
            os.unlink(temp_zip.name)
        return jsonify({'error': f'Failed to create zip: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'models': check_models_installed()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
