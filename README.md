# ZIP2PDF
A simple and stable desktop tool to convert ZIP archives (and their contents) to PDF files. Supports images, text files, manual sorting, undo/redo, PDF merging, and WEBP conversion. Built with Python &amp; PyQt5.
# 📦 ZIP2PDF — Desktop Converter (Final Edition)

ZIP2PDF is a fast, stable and user-friendly desktop application to convert archive files into formatted PDF documents.  
Designed for convenience, productivity and cross-platform usage.

---

## ✨ Features

| Feature | Status |
|---------|--------|
| Convert `.zip` → PDF | ✔️ |
| Import archives **without extension** | ✔️ Ask & auto-rename |
| Supports `.jpg .jpeg .png .webp .txt` | ✔️ |
| Image → PDF with auto resize | ✔️ |
| Drag & Drop support | ✔️ |
| Manual sorting (Natural, A-Z, Z-A) | ✔️ Toggle to avoid Wayland spam |
| Undo / Redo | ✔️ |
| Delete pages (Delete / Backspace) | ✔️ |
| PDF Merge Tool | ✔️ |
| Folder & subfolder import (recursive) | ✔️ |
| Wayland compatible (Fedora Linux) | ✔️ |
| 7z Support (Optional, via `py7zr`) | ⚙️ |

---


## 🖥️ Screenshots

> *UI is simple and clean — no unnecessary complexity.*

<p align="center">
  <img src="https://github.com/user-attachments/assets/e98e360c-fb36-49a0-9000-5672d3a20491" width="700" alt="Home Screen"/>
  <br><sub><b>📌 Home Screen — ZIP2PDF Main Interface</b></sub>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/1021124c-6587-4c1f-9804-fdeda054882f" width="700" alt="Sorting Pages"/>
  <br><sub><b>🔁 Sort, reorder & manage document pages</b></sub>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/137286f8-251c-476a-86b9-c9bb9833b446" width="700" alt="PDF Preview"/>
  <br><sub><b>👁 PDF Preview before saving or merging</b></sub>
</p>


---

## 📁 Supported File Types

| Category | Extensions |
|----------|-------------|
| Images | `.jpg`, `.jpeg`, `.png`, `.webp` |
| Text documents | `.txt` |
| Archives | `.zip` |
| No-extension archives | Ask → convert `.zip` |
| PDFs for merge | `.pdf` |

---

## 📥 Installation & Setup

### 1️⃣ Clone the Repository
```sh
git clone https://github.com/Karankumar004-prog/ZIP2PDF.git
cd ZIP2PDF
```

### 2️⃣ Install Dependencies
```pip install -r requirements.txt```

### 3️⃣ Run the Application
```python3 main.py```

---

### ⚙️ Requirements

- Component	Version
- Python	3.8+
- OS	Linux / Windows
- Dependencies	See requirements.txt

## 📂 Project Structure
```
ZIP2PDF/
│
├── main.py                # Main UI & program
├── utils/
│   ├── extractor.py       # ZIP/7z extraction handler
│   └── pdf_tools.py       # PDF generation & merge
├── requirements.txt
└── README.md
```

## 🎯 How to Use

- Launch the app
- Import a ZIP archive or drag & drop it
- Sort / reorder pages as needed
- Delete unwanted pages (Delete/Backspace)
- Preview output
- Save as PDF

## ⚡ Keyboard Shortcuts
**Action	Shortcut**
- Remove page	= Delete / Backspace
- Undo	= Ctrl + Z
- Redo	= Ctrl + Y
- Close App	= Alt + F4

## ❓ Why This Tool Exists

**Because:**
- Online converters are slow or insecure
- PDF editors are expensive
- Normal users need a simple drag-and-convert app
- Local tools respect privacy & speed
- This project solves that. 🚀

## 🌱 Roadmap

 - PDF Thumbnails Preview
 - OCR Support (Image → Text)
 - Password-protected ZIP Support
 - AppImage + EXE Releases
 - UI Themes / Light & Dark Mode

## 🧑‍💻 Built With
```
Python
PyQt5
FPDF
Pillow (PIL)
PyPDF2
natsort
py7zr (optional)
```

## 🤝 Contributing

PRs and suggestions are welcome!
Open issues for bugs, improvements, and features.

## 📜 License

**This project is licensed under the MIT License — free to use, modify, and distribute.**

## 💬 Author

ZIP2PDF
Created by Mr. White
For personal usage, productivity & privacy.

# 🎉 Your README is Ready
It’s professional, structured, clear, and future-proof.  
This is how real open-source projects present themselves.

### If you want, I can **also write a GitHub Release page** or help you package into an **EXE / AppImage** next.

**Just say:** ```"We need some sweets & Some Coffee too."```

---
