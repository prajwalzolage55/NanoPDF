import os
import time
import logging
from uuid import uuid4
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    send_file, flash, current_app
)

from config import Config
from utils.pdf_compressor import compress_pdf
from utils.file_handler import (
    allowed_file,
    get_secure_filename,
    get_file_size,
    delete_file,
    generate_output_path
)

# ---------------- App Setup ----------------
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config.get("SECRET_KEY", "supersecretkey")

# Make sure upload folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['COMPRESSED_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


# ---------------- Helpers ----------------
def cleanup_old_files(folder, hours=1):
    """
    Delete files older than 'hours' in the given folder.
    """
    now = time.time()
    cutoff = now - hours * 3600
    for fname in os.listdir(folder):
        fpath = os.path.join(folder, fname)
        if os.path.isfile(fpath):
            try:
                if os.path.getmtime(fpath) < cutoff:
                    delete_file(fpath)
                    logging.info("Deleted old file: %s", fpath)
            except Exception as e:
                logging.exception("Failed to delete old file %s: %s", fpath, str(e))


# ---------------- Routes ----------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/compress', methods=['POST'])
def compress():
    """
    Accepts uploaded file (supports input name 'file' or 'pdf_file'),
    validates it, compresses it and returns result.html on success.
    """
    # Accept either name used in different templates/versions
    file = None
    if 'file' in request.files:
        file = request.files.get('file')
    elif 'pdf_file' in request.files:
        file = request.files.get('pdf_file')

    if file is None:
        flash("No file uploaded. Please choose a PDF file.", "danger")
        logging.info("Compress called but no file found in request.files.")
        return redirect(url_for('index'))

    if file.filename == '':
        flash("No file selected. Please choose a PDF file.", "danger")
        logging.info("Compress called but empty filename.")
        return redirect(url_for('index'))

    # Allowed check using file_handler.allowed_file
    allowed_exts = app.config.get('ALLOWED_EXTENSIONS', {'pdf'})
    if not allowed_file(file.filename, allowed_exts):
        flash("Only PDF files are allowed.", "danger")
        logging.info("Rejected file with disallowed extension: %s", file.filename)
        return redirect(url_for('index'))

    try:
        # Secure the original filename for display & storage
        secure_name = get_secure_filename(file.filename)  # e.g. report.pdf

        # Give uploaded file a unique filename to avoid collisions
        unique_prefix = uuid4().hex
        unique_filename = f"{unique_prefix}_{secure_name}"

        upload_folder = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        input_path = os.path.join(upload_folder, unique_filename)

        # Save uploaded file
        file.save(input_path)
        logging.info("Saved uploaded file to %s", input_path)

        # Get compression level from form (default from config)
        compression_level = request.form.get(
            'compression_level',
            app.config.get('DEFAULT_COMPRESSION_LEVEL', 'medium')
        )

        # Prepare output file path (generate_output_path will add _compressed)
        output_path = generate_output_path(unique_filename, app.config['COMPRESSED_FOLDER'])

        # Sizes before compression
        original_size = get_file_size(input_path)

        # Compress PDF (may raise)
        compress_pdf(input_path, output_path, compression_level)
        logging.info("Compression finished: %s -> %s (level=%s)", input_path, output_path, compression_level)

        # Sizes after compression
        compressed_size = get_file_size(output_path)

        # Calculate reduction safely
        reduction = 0
        if original_size > 0:
            reduction = round(((original_size - compressed_size) / original_size) * 100, 2)

        # Optionally remove original uploaded file to save space
        try:
            delete_file(input_path)
            logging.info("Deleted original uploaded file: %s", input_path)
        except Exception:
            logging.exception("Failed to delete original file: %s", input_path)

        # Show result page using the original safe filename for clarity
        return render_template(
            'result.html',
            original_file=secure_name,
            compressed_file=os.path.basename(output_path),
            original_size=original_size,
            compressed_size=compressed_size,
            reduction=reduction
        )

    except Exception as e:
        logging.exception("Error while compressing file: %s", str(e))
        # Render friendly error page with message
        return render_template(
            'error.html',
            error_title="Compression Failed",
            error_message=str(e)
        ), 500


@app.route('/download/<path:filename>')
def download(filename):
    file_path = os.path.join(app.config['COMPRESSED_FOLDER'], filename)

    if os.path.exists(file_path):
        try:
            response = send_file(file_path, as_attachment=True)

            # Delete file after sending
            @response.call_on_close
            def remove_file():
                try:
                    delete_file(file_path)
                    logging.info("Deleted compressed file after download: %s", file_path)
                except Exception as e:
                    logging.exception("Failed to delete compressed file: %s", str(e))

            return response

        except Exception as e:
            logging.exception("Download failed: %s", str(e))
            flash("Download failed.", "danger")
            return redirect(url_for('index'))
    else:
        flash("File not found.", "danger")
        return redirect(url_for('index'))



# ---------------- Error Handlers ----------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "error.html",
        error_title="404 - Page Not Found",
        error_message="The page you are looking for does not exist."
    ), 404


@app.errorhandler(500)
def internal_server_error(e):
    # If e has description use it, else generic message
    message = getattr(e, "description", "Internal server error. Please try again later.")
    return render_template(
        "error.html",
        error_title="500 - Server Error",
        error_message=message
    ), 500


# ---------------- Run Server ----------------
if __name__ == '__main__':
    # Optional: clean old files on startup (older than 1 hour by default)
    try:
        cleanup_old_files(app.config['UPLOAD_FOLDER'], hours=1)
        cleanup_old_files(app.config['COMPRESSED_FOLDER'], hours=1)
    except Exception:
        logging.exception("Failed during initial cleanup.")

    # Enforce max upload size from config if present
    max_size = app.config.get('MAX_CONTENT_LENGTH')
    if max_size:
        app.config['MAX_CONTENT_LENGTH'] = max_size

    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
