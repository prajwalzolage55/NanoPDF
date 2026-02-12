import subprocess
import os


def compress_pdf(input_path, output_path, compression_level="medium"):
    """
    Compress PDF using Ghostscript (real compression).
    """

    # Ghostscript quality presets
    quality = {
        "low": "/printer",      # High quality, less compression
        "medium": "/ebook",     # Balanced
        "high": "/screen"       # Smallest size
    }

    if compression_level not in quality:
        compression_level = "medium"

    gs_quality = quality[compression_level]

    gs_path = r"C:\Program Files\gs\gs10.06.0\bin\gswin64c.exe"

    command = [
        gs_path,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={gs_quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise Exception("Ghostscript compression failed.")
