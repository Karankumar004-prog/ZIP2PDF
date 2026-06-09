# 📦 ZIP2PDF — Professional Edition

ZIP2PDF is a fast, stable, and beautifully designed desktop application that converts archive files and images into formatted PDF documents. 

Built with Python and PyQt5, this tool features a custom frameless UI, background multi-threading for heavy processing, and an elegant **Obsidian & Teal** dark theme.

---

## ✨ Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Modern Frameless UI** | Custom title bar, rounded corners, and Obsidian & Teal theme. | ✔️ |
| **Multi-Threaded Engine** | UI never freezes. Heavy extractions and PDF generations run in the background. | ✔️ |
| **Smart Conversion** | Convert `.zip` files, `.jpg`, `.png`, `.webp`, and `.txt` directly to PDF. | ✔️ |
| **PDF Merge Tool** | Built-in utility to merge multiple existing PDFs into one. | ✔️ |
| **Drag & Drop** | Seamlessly drag files and archives directly into the workspace. | ✔️ |
| **Custom Dialogs** | 100% themed warning pop-ups and custom file explorers. | ✔️ |
| **Wayland Native** | Fully optimized for modern Linux/Fedora environments. | ✔️ |
| **Auto-Correction** | Detects extension-less archives and auto-renames them. | ✔️ |

---

## 🖥️ Screenshots

> *Add your application screenshots to the `assets` folder or directly via GitHub issues/PRs and replace the links below.*

<p align="center">
  <img src="https://github.com/user-attachments/assets/3877f0bf-5cb7-46bb-8d8c-cfbc1c1013ec" width="700" alt="Home Screen"/>
  <br><sub><b>📌 Clean, Frameless Workspace</b></sub>
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/c20e51e3-8e04-449a-91f0-021e872baaf3" width="700" alt="Merge Tool"/>
  <br><sub><b>🧩 Custom PDF Merge Tool</b></sub>
</p>

---

## 📥 Installation & Setup

### Option 1: Run from Source

**1. Clone the Repository**
```sh
git clone [https://github.com/Karankumar004-prog/ZIP2PDF.git](https://github.com/Karankumar004-prog/ZIP2PDF.git)
cd ZIP2PDF
```

### 2️⃣ Install Dependencies
```pip install -r requirements.txt```

### 3️⃣ Run the Application
```python3 main.py```

### Option 2: Build an Executable (PyInstaller)
To package this application into a standalone .exe (Windows) or binary (Linux) so users do not need to install Python or run terminal commands:

```sh
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --add-data "utils:utils" main.py
```
Your runnable application will be generated inside the dist/main folder. You can zip this folder and distribute it to your users.

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
├── main.py                # Main UI, Threading, and custom Window Logic
├── utils/
│   ├── extractor.py       # ZIP/7z background extraction handler
│   └── pdf_tools.py       # pypdf & FPDF generation logic
├── requirements.txt       # Dependencies
└── README.md              # Project Documentation
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
- Minimize & Maximize Application = Double Tap Title bar
- Close App	= Alt + F4

## ❓ Why This Tool Exists

**Because:**
- Online PDF converters are slow, riddled with ads, and compromise your privacy by uploading your sensitive documents to third-party servers.

- Premium PDF editors are unnecessarily expensive for basic document compiling.

- ZIP2PDF processes everything 100% locally on your machine, ensuring maximum speed and total data privacy. 🚀

## 🌱 Roadmap

 - PDF Thumbnails Preview
 - OCR Support (Image → Text)
 - Password-protected ZIP Support
 - AppImage + EXE Releases
 - UI Themes / Light & Dark Mode

## 🧑‍💻 Built With
```
Python 3.8+
PyQt5 - GUI Framework
FPDF - PDF Generation
Pillow (PIL) - Image processing
pypdf - PDF Merging (Modern replacement for PyPDF2)
natsort
py7zr (optional)
```

## 🤝 Contributing

PRs and suggestions are welcome!
Open issues for bugs, improvements, and features.

## 📜 License

**This project is licensed under the MIT License — free to use, modify, and distribute. See the LICENSE file for details.**

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
