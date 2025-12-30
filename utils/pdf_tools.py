# utils/pdf_tools.py
from fpdf import FPDF
from pathlib import Path
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter

VALID_PAGE_FILES = (".jpg", ".jpeg", ".png", ".webp", ".txt")

def generate_pdf(files, output_path):
    """
    Create a PDF file from a list of file paths.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)

    for f in files:
        f = Path(f)
        ext = f.suffix.lower()

        # Image pages
        # IMAGE PAGES (including WEBP)
        if ext in (".jpg", ".jpeg", ".png", ".webp"):
            pdf.add_page()

            img = Image.open(f).convert("RGB")  # Convert WEBP → RGB for PDF use
            temp_img = f.with_suffix(".jpg")    # Save temp jpeg if needed
            img.save(temp_img)

            w, h = img.size
            aspect = h / w
            pdf.image(str(temp_img), x=10, y=10, w=190, h=190 * aspect)


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