# ZIP2PDF

A sleek, lightweight Linux desktop utility designed to effortlessly extract ZIP archives and convert their contents into cleanly formatted PDF documents. 

## ✨ Key Features
* **Seamless Extraction:** Instantly unpacks standard archive formats.
* **Smart PDF Conversion:** Merges extracted images and text files into a single, cohesive PDF.
* **Native Linux Feel:** Built with a modern, dark-themed UI (Obsidian and Cyan) that looks right at home on Fedora, GNOME, and KDE.

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

### ⚙️ Requirements

- Component	Version
- Python	3.8+
- OS	Linux / Windows
- Dependencies	See requirements.txt

---

## 🚀 Installation & Setup
### Option 1: Run from Source

### 1️⃣ Clone the Repository
```sh
git clone [https://github.com/Karankumar004-prog/ZIP2PDF.git](https://github.com/Karankumar004-prog/ZIP2PDF.git)
cd ZIP2PDF
```

### 2️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```

### 3️⃣ Run the Application
```sh
python3 main.py
```

### Option 2: Build an Executable (PyInstaller)
To package this application into a standalone .exe (Windows) or binary (Linux) so users do not need to install Python or run terminal commands:

```sh
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --add-data "utils:utils" main.py
```
---

## ⚡ Keyboard Shortcuts
**Action	Shortcut**
- Remove page	= Delete / Backspace
- Undo	= Ctrl + Z
- Redo	= Ctrl + Y
- Minimize & Maximize Application = Double Tap Title bar
- Close App	= Alt + F4
- Rename File = F2

## ❓ Why This Tool Exists

**Because:**
- Online PDF converters are slow, riddled with ads, and compromise your privacy by uploading your sensitive documents to third-party servers.

- Premium PDF editors are unnecessarily expensive for basic document compiling.

- ZIP2PDF processes everything 100% locally on your machine, ensuring maximum speed and total data privacy. 🚀

### Prerequisites
Make sure you have Python 3 installed on your system along with the following dependencies:
* `PyQt6` (For the graphical interface)
* `Pillow` (For image processing)
* `PyCryptodome` (For secure extraction)
* `FPDF` (for PDF Generation)
* `PyPDF2` (for PDF merging)


### Running Locally
To run the application directly from the source code:
1. Clone the repository.
2. Navigate to the project folder: `cd ZIP2PDF`
3. Install requirements: `pip install -r requirements.txt`
4. Run the app: `python3 main.py`

## 📦 Building the Executable
If you want to compile ZIP2PDF into a single, standalone Linux executable, we use PyInstaller. 

Run the following command in the project root:
```bash
pyinstaller --onefile --windowed --name ZIP2PDF main.py
```
## 🖥️ Desktop Integration (Linux)
To add ZIP2PDF to your GNOME or KDE application menu:

### 1️⃣ Move the compiled ZIP2PDF executable to your desired permanent folder.

### 2️⃣ Create a desktop entry:
```bash
nano ~/.local/share/applications/zip2pdf.desktop
```
### 3️⃣ Paste the following configuration (update paths accordingly):
```Ini,TOML
[Desktop Entry]
Version=1.0
Type=Application
Name=ZIP2PDF
Comment=Extract archives and merge PDFs seamlessly
Exec="/path/to/your/ZIP2PDF"
Icon=/path/to/your/icons/image.png
Terminal=false
Categories=Utility;Office;
```
### 4️⃣ Update the desktop database:
```bash
update-desktop-database ~/.local/share/applications/
```
## Making an Excectuable permanent application

### 1️⃣ Move the Executable to a Permanent Home
In Linux, user-specific applications belong in ~/.local/bin/. Run this command to move your newly built app there:
```bash
mkdir -p ~/.local/bin
mv "/path/to/your/ZIP2PDF/dist/ZIP2PDF" ~/.local/bin/zip2pdf
```
### 2️⃣ Update the Desktop Shortcut
Now, you just need to tell your Fedora menu where the app moved to. Open your ~/.local/share/applications/zip2pdf.desktop file and update the Exec line to point to the new location:
```Ini,TOML
Exec=/home/mrwhite/.local/bin/zip2pdf
```
### 3️⃣ Clean Up Your Project
Now you are completely safe to run your cleanup command in your project folder:
```bash
rm -rf dist/ build/ __pycache__/ *.spec
```

---

## 🤝 Contributing

PRs and suggestions are welcome!
Open issues for bugs, improvements, and features.

---

## 📄 License
This project is licensed under standard open-source terms. See the LICENSE file for details.

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
