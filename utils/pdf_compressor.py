import subprocess
import os


def compress_pdf(input_path, output_path, compression_level="medium"):
    """
    Compress PDF using Ghostscript.
    
    compression_level options:
        - low
        - medium
        - high
    """

    # Map user-friendly level to Ghostscript settings
    level_map = {
        "low": "/screen",     # Maximum compression (lowest quality)
        "medium": "/ebook",   # Balanced
        "high": "/printer"    # Better quality (less compression)
    }

    gs_setting = level_map.get(compression_level, "/ebook")

    command = [
        "gs",  # Linux Ghostscript
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={gs_setting}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path,
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error during PDF compression: {e}")
    except FileNotFoundError:
        raise RuntimeError(
            "Ghostscript is not installed on the server. "
            "Make sure it is installed via apt-get install ghostscript."
        )
