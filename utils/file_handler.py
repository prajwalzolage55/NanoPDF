import os
from werkzeug.utils import secure_filename


# ---------------- File Validation ----------------
def allowed_file(filename, allowed_extensions):
    """
    Check if uploaded file has allowed extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


# ---------------- Secure Filename ----------------
def get_secure_filename(filename):
    """
    Return a secure version of the filename.
    """
    return secure_filename(filename)


# ---------------- Save File ----------------
def save_file(file, upload_folder):
    """
    Save uploaded file to specified folder.
    Returns full file path.
    """
    os.makedirs(upload_folder, exist_ok=True)

    filename = get_secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)

    file.save(file_path)
    return file_path


# ---------------- File Size ----------------
def get_file_size(file_path):
    """
    Return file size in KB.
    """
    if os.path.exists(file_path):
        size_bytes = os.path.getsize(file_path)
        size_kb = round(size_bytes / 1024, 2)
        return size_kb
    return 0


# ---------------- Delete File ----------------
def delete_file(file_path):
    """
    Safely delete a file if it exists.
    """
    if os.path.exists(file_path):
        os.remove(file_path)


# ---------------- Generate Output Path ----------------
def generate_output_path(input_filename, output_folder):
    """
    Create output path for compressed file.
    """
    os.makedirs(output_folder, exist_ok=True)

    name, ext = os.path.splitext(input_filename)
    compressed_filename = f"{name}_compressed{ext}"

    return os.path.join(output_folder, compressed_filename)
