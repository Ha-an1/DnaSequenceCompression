import os
import tempfile
from flask import Flask, request, send_file, render_template, jsonify
from werkzeug.utils import secure_filename
import logging
import io  # <-- Import the io module

# --- IMPORTANT ---
# This line imports the functions from your original script.
# It assumes 'dna_compressor.py' is in the same folder.
try:
    from dna_compressor import compress_file, decompress_file
except ImportError:
    print("="*80)
    print("ERROR: Could not find 'dna_compressor.py'.")
    print("Please make sure 'dna_compressor.py' is in the same directory as 'app.py'.")
    print("="*80)
    exit(1)

# Configure the Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB max upload
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def index():
    """Serves the main HTML page."""
    # Renders the index.html file
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def handle_compress():
    """Handles the file compression request."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.fasta'):
        # Use tempfile to securely handle file I/O
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # 1. Save the uploaded .fasta file temporarily
                original_filename = secure_filename(file.filename)
                input_path = os.path.join(temp_dir, original_filename)
                file.save(input_path)
                app.logger.debug(f"Saved uploaded file to: {input_path}")

                # 2. Define the output path for the compressed file
                compressed_filename = original_filename.replace('.fasta', '.bin')
                output_path = os.path.join(temp_dir, compressed_filename)
                
                # 3. Run your compression logic
                app.logger.debug(f"Running compress_file on: {input_path}")
                compress_file(input_path, output_path)
                app.logger.debug(f"Compression successful. Output: {output_path}")

                # 4. *** THE FIX ***
                # Read the compressed file into an in-memory buffer (BytesIO)
                # This releases the file lock on disk.
                file_buffer = io.BytesIO()
                with open(output_path, 'rb') as f:
                    file_buffer.write(f.read())
                file_buffer.seek(0) # Rewind the buffer to the beginning

                # 5. Send the in-memory buffer.
                # The 'with' block can now safely delete the temporary directory.
                return send_file(
                    file_buffer,
                    as_attachment=True,
                    download_name=compressed_filename,
                    mimetype='application/octet-stream'
                )
            except Exception as e:
                app.logger.error(f"Compression failed: {e}")
                return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Please upload a .fasta file."}), 400

@app.route('/decompress', methods=['POST'])
def handle_decompress():
    """Handles the file decompression request."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.bin'):
        # Use tempfile to securely handle file I/O
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # 1. Save the uploaded .bin file temporarily
                compressed_filename = secure_filename(file.filename)
                input_path = os.path.join(temp_dir, compressed_filename)
                file.save(input_path)
                app.logger.debug(f"Saved uploaded file to: {input_path}")

                # 2. Define the output path for the restored file
                restored_filename = compressed_filename.replace('.bin', '_restored.fasta')
                output_path = os.path.join(temp_dir, restored_filename)

                # 3. Run your decompression logic
                app.logger.debug(f"Running decompress_file on: {input_path}")
                decompress_file(input_path, output_path)
                app.logger.debug(f"Decompression successful. Output: {output_path}")

                # 4. *** THE FIX ***
                # Read the restored file into an in-memory buffer
                file_buffer = io.BytesIO()
                with open(output_path, 'rb') as f:
                    file_buffer.write(f.read())
                file_buffer.seek(0)

                # 5. Send the in-memory buffer
                return send_file(
                    file_buffer,
                    as_attachment=True,
                    download_name=restored_filename,
                    mimetype='text/plain' # Changed mimetype for .fasta
                )
            except Exception as e:
                app.logger.error(f"Decompression failed: {e}")
                return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file type. Please upload a .bin file."}), 400

# This makes the app runnable with `python app.py`
if __name__ == '__main__':
    # Create a 'templates' folder if it doesn't exist for index.html
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Check if index.html is in the templates folder, if not, move it
    if os.path.exists('index.html') and not os.path.exists('templates/index.html'):
        os.rename('index.html', 'templates/index.html')
        
    print("Flask server running. Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True, port=5000)

