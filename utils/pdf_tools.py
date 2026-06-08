# utils/pdf_tools.py
import os
import tempfile
from fpdf import FPDF
from pathlib import Path
from PIL import Image

# Use pypdf instead of the deprecated PyPDF2
from pypdf import PdfReader, PdfWriter

# This is the constant that was missing!
VALID_PAGE_FILES = (".jpg", ".jpeg", ".png", ".webp", ".txt")


def generate_pdf(files, output_path):
    """
    Create a PDF file from a list of file paths.
    Includes A4 boundary limits and safe temporary file handling.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)

    for f in files:
        f = Path(f)
        ext = f.suffix.lower()

        # Image pages (including WEBP)
        if ext in (".jpg", ".jpeg", ".png", ".webp"):
            pdf.add_page()
            img = Image.open(f).convert("RGB")
            
            # Create a safe, temporary file that won't overwrite user data
            fd, temp_img_path = tempfile.mkstemp(suffix=".jpg")
            os.close(fd) # Close file descriptor so PIL can write to it
            img.save(temp_img_path, format="JPEG")

            w, h = img.size
            aspect = h / w
            
            # Prevent images from overflowing A4 dimensions (210x297mm)
            calc_w = 190 # Max width with 10mm margins
            calc_h = 190 * aspect
            
            if calc_h > 277: # 297mm total height - 20mm margins
                calc_h = 277
                calc_w = 277 / aspect
            
            # Center the image horizontally
            x_pos = (210 - calc_w) / 2
            pdf.image(temp_img_path, x=x_pos, y=10, w=calc_w, h=calc_h)
            
            # Clean up the temporary image immediately
            os.remove(temp_img_path)

        # Text pages
        elif ext == ".txt":
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            with open(f, "r", encoding="utf-8") as text:
                content = text.read()
                pdf.multi_cell(0, 10, content)

    pdf.output(output_path)


def merge_pdfs(input_pdfs, output_path):
    """
    Merge multiple PDF files into one.
    """
    writer = PdfWriter()

    for pdf in input_pdfs:
        reader = PdfReader(str(pdf))
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)