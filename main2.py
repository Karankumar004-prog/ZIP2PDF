# main.py
import sys
import tempfile
import webbrowser
from pathlib import Path
from natsort import natsorted

import os
os.environ["QT_QPA_PLATFORM"] = "wayland"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget,
    QFileDialog, QMessageBox, QListWidgetItem, QComboBox, QLabel,
    QHBoxLayout, QDialog, QMenu, QAction
)
from PyQt5.QtCore import QTimer

def sort_files(self):
    m = self.sort_box.currentText()

    if m == "A-Z":
        self.file_list.sort(key=lambda x: x.name.lower())
    elif m == "Z-A":
        self.file_list.sort(key=lambda x: x.name.lower(), reverse=True)
    else:
        self.file_list = natsorted(self.file_list, key=lambda x: x.name.lower())

    # Prevent Wayland activation warnings
    QTimer.singleShot(50, self.rebuild)

from PyQt5.QtCore import Qt

# Local utilities
try:
    from utils.extractor import extract_archive, SUPPORTED_ARCHIVES
    from utils.pdf_tools import generate_pdf, merge_pdfs, VALID_PAGE_FILES
except ImportError:
    print("Error: 'utils' folder missing. Please ensure directory structure is correct.")
    sys.exit(1)


class Zip2PDF(QWidget):
    """
    Main Application Window: Combines Drag-Drop, Import, Merge, and Undo/Redo.
    """

    def __init__(self):
        super().__init__()

        # ----- Window Setup -----
        self.setWindowTitle("ZIP2PDF — Professional Edition")
        self.setMinimumWidth(700)
        self.setMinimumHeight(550)
        self.setAcceptDrops(True)

        # State Management
        self.temp = Path(tempfile.mkdtemp())
        self.files = []         # Current list of pages (Path objects)
        self.undo_stack = []    # History for Undo
        self.redo_stack = []    # History for Redo

        # ----- Layout Start -----
        layout = QVBoxLayout()

        # Header
        title = QLabel("📦 ZIP/7Z → PDF Converter")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(title)

        hint = QLabel("Drag & Drop Archives, Images, or Text files here.")
        hint.setStyleSheet("color: gray; margin-bottom: 5px;")
        layout.addWidget(hint)

        # Controls Row
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Sort:"))
        self.sort_box = QComboBox()
        self.sort_box.addItems(["Natural", "A-Z", "Z-A"])
        self.sort_box.currentIndexChanged.connect(self.apply_sort)
        controls_layout.addWidget(self.sort_box)

        # Undo/Redo Buttons
        self.btn_undo = QPushButton("↩ Undo")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_undo.setEnabled(False)
        
        self.btn_redo = QPushButton("↪ Redo")
        self.btn_redo.clicked.connect(self.redo)
        self.btn_redo.setEnabled(False)

        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_undo)
        controls_layout.addWidget(self.btn_redo)
        
        layout.addLayout(controls_layout)

        # File List Area
        self.listbox = QListWidget()
        self.listbox.setDragDropMode(QListWidget.InternalMove)
        self.listbox.setSelectionMode(QListWidget.ExtendedSelection)
        self.listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listbox.customContextMenuRequested.connect(self.show_context_menu)
        self.listbox.itemDoubleClicked.connect(self.preview_item)
        layout.addWidget(self.listbox)

        # Action Buttons
        buttons = QHBoxLayout()
        buttons.addWidget(QPushButton("📂 Import File", clicked=self.open_file_dialog))
        buttons.addWidget(QPushButton("🧩 Merge PDFs", clicked=self.open_merge_tool))
        buttons.addWidget(QPushButton("👁 Preview PDF", clicked=self.preview_pdf))
        buttons.addWidget(QPushButton("💾 Save PDF", clicked=self.save_pdf))
        layout.addLayout(buttons)

        self.setLayout(layout)

    # ==============================================================
    #  STATE & UNDO/REDO
    # ==============================================================

    def save_state(self):
        """Pushes current file list to undo stack before a change."""
        self.undo_stack.append(self.files.copy())
        self.redo_stack.clear()
        self.update_undo_redo_buttons()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.files.copy())
            self.files = self.undo_stack.pop()
            self.refresh_list()
            self.update_undo_redo_buttons()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.files.copy())
            self.files = self.redo_stack.pop()
            self.refresh_list()
            self.update_undo_redo_buttons()

    def update_undo_redo_buttons(self):
        self.btn_undo.setEnabled(bool(self.undo_stack))
        self.btn_redo.setEnabled(bool(self.redo_stack))

    # ==============================================================
    #  DRAG & DROP
    # ==============================================================

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls()]
        if paths:
            self.save_state()
            for p in paths:
                self.process_input(p)
            self.refresh_list()

    # ==============================================================
    #  FILE HANDLING
    # ==============================================================

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*)")
        if path:
            self.save_state()
            self.process_input(Path(path))
            self.refresh_list()

    def process_input(self, path: Path):
        name = path.name.lower()

        # 🔹 1️⃣ FILE WITH NO EXTENSION → Ask user how to treat it
        if path.suffix == "":
            reply = QMessageBox.question(
                self,
                "Unknown File Type",
                f"'{path.name}' has no extension.\n\nTreat it as a ZIP file?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    new_path = path.with_suffix(".zip")
                    path.rename(new_path)
                    path = new_path
                    extract_archive(str(path), self.temp)
                    self.scan_temp_folder()
                    QMessageBox.information(self, "Imported", f"Renamed and extracted: {path.name}")
                    return
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to process file:\n{e}")
                    return
            else:
                QMessageBox.information(self, "Skipped", "File ignored.")
                return

        # 🔹 2️⃣ ARCHIVES WITH EXTENSION (.zip / .7z)
        if name.endswith(SUPPORTED_ARCHIVES):
            try:
                extract_archive(str(path), self.temp)
                self.scan_temp_folder()
                QMessageBox.information(self, "Imported", f"Extracted contents of {path.name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to extract {path.name}:\n{str(e)}")

        # 🔹 3️⃣ PDFs → Send to merge
        elif name.endswith(".pdf"):
            reply = QMessageBox.question(
                self, "PDF Detected", 
                "You dropped a PDF. Do you want to open the PDF Merger?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.open_merge_tool(initial_pdf=path)

        # 🔹 4️⃣ Images/Text (including WEBP)
        elif path.suffix.lower() in VALID_PAGE_FILES:
            self.files.append(path)

        else:
            QMessageBox.warning(self, "Unsupported", f"Skipping unsupported file: {path.name}")

    def scan_temp_folder(self):
        """Finds all valid images/text in the temp folder and adds them."""
        # Use natsorted instantly on import to prevent mess
        found_files = []
        for item in self.temp.rglob("*"):
            if item.suffix.lower() in VALID_PAGE_FILES:
                if item not in self.files:
                    found_files.append(item)
        
        # Sort natural order by default on import
        found_files = natsorted(found_files, key=lambda x: x.name.lower())
        self.files.extend(found_files)

    # ==============================================================
    #  LIST MANAGEMENT
    # ==============================================================

    def apply_sort(self):
        self.save_state()
        mode = self.sort_box.currentText()
        if mode == "A-Z":
            self.files.sort(key=lambda x: x.name.lower())
        elif mode == "Z-A":
            self.files.sort(key=lambda x: x.name.lower(), reverse=True)
        else:
            self.files = natsorted(self.files, key=lambda x: x.name.lower())
        self.refresh_list()

    def refresh_list(self):
        self.listbox.clear()
        for f in self.files:
            item = QListWidgetItem(f"📄 {f.name}")
            item.setData(Qt.UserRole, f)
            self.listbox.addItem(item)

    def preview_item(self, item):
        path = item.data(Qt.UserRole)
        webbrowser.open(str(path))

    # ==============================================================
    #  CONTEXT MENU & DELETION
    # ==============================================================

    def show_context_menu(self, pos):
        menu = QMenu()
        delete_action = QAction("❌ Remove Selected", self)
        delete_action.triggered.connect(self.remove_selected)
        menu.addAction(delete_action)
        menu.exec_(self.listbox.mapToGlobal(pos))

    def remove_selected(self):
        rows = sorted([index.row() for index in self.listbox.selectedIndexes()], reverse=True)
        if rows:
            self.save_state()
            for row in rows:
                if row < len(self.files):
                    self.files.pop(row)
            self.refresh_list()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.remove_selected()

    # ==============================================================
    #  PDF GENERATION
    # ==============================================================

    def preview_pdf(self):
        if not self.files:
            return QMessageBox.warning(self, "Empty", "No files to preview.")
        
        out_path = self.temp / "preview_temp.pdf"
        try:
            generate_pdf(self.files, out_path)
            webbrowser.open(str(out_path))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate preview:\n{e}")

    def save_pdf(self):
        if not self.files:
            return QMessageBox.warning(self, "Empty", "Add files before saving.")

        out_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", "", "PDF (*.pdf)")
        if out_path:
            try:
                generate_pdf(self.files, out_path)
                QMessageBox.information(self, "Success", "PDF Saved Successfully! 🎉")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save PDF:\n{e}")

    # ==============================================================
    #  MERGE TOOL
    # ==============================================================

    def open_merge_tool(self, initial_pdf=None):
        dlg = QDialog(self)
        dlg.setWindowTitle("Merge PDFs Tool")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout()

        list_widget = QListWidget()
        pdfs_to_merge = []

        def add_pdf(path=None):
            if not path:
                path_str, _ = QFileDialog.getOpenFileName(dlg, "Add PDF", "", "PDF (*.pdf)")
                if path_str: path = Path(path_str)
            
            if path:
                pdfs_to_merge.append(path)
                list_widget.addItem(f"📎 {path.name}")

        def execute_merge():
            if len(pdfs_to_merge) < 2:
                return QMessageBox.warning(dlg, "Error", "Select at least 2 PDFs to merge.")
            
            save_path, _ = QFileDialog.getSaveFileName(dlg, "Save Merged PDF", "", "PDF (*.pdf)")
            if save_path:
                try:
                    merge_pdfs(pdfs_to_merge, save_path)
                    QMessageBox.information(dlg, "Success", "PDFs Merged Successfully!")
                    dlg.close()
                except Exception as e:
                    QMessageBox.critical(dlg, "Error", f"Merge failed:\n{e}")

        # Add buttons
        btn_add = QPushButton("➕ Add PDF")
        btn_add.clicked.connect(lambda: add_pdf())
        
        btn_run = QPushButton("💾 Merge & Save")
        btn_run.clicked.connect(execute_merge)

        layout.addWidget(list_widget)
        layout.addWidget(btn_add)
        layout.addWidget(btn_run)
        dlg.setLayout(layout)

        # If a PDF was passed from drag-drop
        if initial_pdf:
            add_pdf(initial_pdf)

        dlg.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Zip2PDF()
    window.show()
    sys.exit(app.exec())