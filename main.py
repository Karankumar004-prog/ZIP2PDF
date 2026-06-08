# main.py
import sys
import tempfile
import webbrowser
from pathlib import Path
from natsort import natsorted
import os
import shutil

# Wayland compatibility
os.environ["QT_QPA_PLATFORM"] = "wayland"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget,
    QFileDialog, QListWidgetItem, QComboBox, QLabel,
    QHBoxLayout, QDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# ==========================================
# STARTUP ERROR HANDLING
# ==========================================
try:
    from utils.extractor import extract_archive, SUPPORTED_ARCHIVES
    from utils.pdf_tools import generate_pdf, merge_pdfs, VALID_PAGE_FILES
except ImportError as e:
    from PyQt5.QtWidgets import QMessageBox
    app = QApplication(sys.argv)
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Critical)
    error_box.setWindowTitle("Critical Error - ZIP2PDF")
    error_box.setText(f"Missing essential components. Please ensure the 'utils' folder is next to the executable.\n\nDetails: {e}")
    error_box.exec_()
    sys.exit(1)


# ==========================================
# CUSTOM UI COMPONENTS
# ==========================================
class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(15, 0, 10, 0)
        self.setFixedHeight(40)
        self.setObjectName("CustomTitleBar")

        self.title = QLabel("📦 ZIP2PDF")
        self.title.setStyleSheet("font-weight: bold; color: #00ADB5; font-size: 14px;")
        
        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("◻")
        self.btn_close = QPushButton("✕")
        
        for btn in [self.btn_min, self.btn_max, self.btn_close]:
            btn.setFixedSize(30, 30)
            btn.setObjectName("WindowControlButton")
            
        self.btn_close.setObjectName("CloseButton")

        self.btn_min.clicked.connect(self.parent.showMinimized)
        self.btn_max.clicked.connect(self.toggle_max_restore)
        self.btn_close.clicked.connect(self.parent.close)

        self.layout.addWidget(self.title)
        self.layout.addStretch()
        self.layout.addWidget(self.btn_min)
        self.layout.addWidget(self.btn_max)
        self.layout.addWidget(self.btn_close)
        self.setLayout(self.layout)

    def toggle_max_restore(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    # Fixed Dragging Logic for Wayland/Modern OS
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            window = self.window().windowHandle()
            if window and hasattr(window, 'startSystemMove'):
                window.startSystemMove()
            else:
                self.startPos = event.globalPos() - self.parent.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'startPos') and self.startPos:
            self.parent.move(event.globalPos() - self.startPos)
            
    def mouseReleaseEvent(self, event):
        self.startPos = None


class ModernMessageBox(QDialog):
    """A custom, frameless replacement for standard popups."""
    def __init__(self, parent, title, text, msg_type="info"):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self)
        self.title_bar.title.setText(f" {title}")
        self.title_bar.btn_min.hide()
        self.title_bar.btn_max.hide()
        layout.addWidget(self.title_bar)
        
        content = QWidget()
        content.setObjectName("ContentContainer")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "question": "❓"}
        icon = icons.get(msg_type, "ℹ️")
        
        lbl_text = QLabel(f"{icon}   {text}")
        lbl_text.setWordWrap(True)
        lbl_text.setStyleSheet("font-size: 14px; color: #E0E0E0;")
        content_layout.addWidget(lbl_text)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        if msg_type == "question":
            self.btn_no = QPushButton("No")
            self.btn_no.clicked.connect(self.reject)
            self.btn_yes = QPushButton("Yes")
            self.btn_yes.setObjectName("PrimaryButton")
            self.btn_yes.clicked.connect(self.accept)
            btn_layout.addWidget(self.btn_no)
            btn_layout.addWidget(self.btn_yes)
        else:
            self.btn_ok = QPushButton("OK")
            self.btn_ok.setObjectName("PrimaryButton")
            self.btn_ok.clicked.connect(self.accept)
            btn_layout.addWidget(self.btn_ok)
            
        content_layout.addLayout(btn_layout)
        layout.addWidget(content)
        
    @staticmethod
    def ask(parent, title, text):
        dlg = ModernMessageBox(parent, title, text, "question")
        return dlg.exec_() == QDialog.Accepted
        
    @staticmethod
    def show_msg(parent, title, text, msg_type="info"):
        dlg = ModernMessageBox(parent, title, text, msg_type)
        dlg.exec_()


class ModernMergeDialog(QDialog):
    """A custom, frameless replacement for the Merge Tool."""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self)
        self.title_bar.title.setText("🧩 Merge PDFs Tool")
        self.title_bar.btn_min.hide()
        self.title_bar.btn_max.hide()
        layout.addWidget(self.title_bar)
        
        content = QWidget()
        content.setObjectName("ContentContainer")
        content_layout = QVBoxLayout(content)
        
        self.list_widget = QListWidget()
        self.pdfs_to_merge = []
        
        btn_add = QPushButton("➕ Add PDF", clicked=self.add_pdf)
        btn_run = QPushButton("💾 Merge & Save", clicked=self.execute_merge)
        btn_run.setObjectName("PrimaryButton")
        
        content_layout.addWidget(self.list_widget)
        
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_run)
        content_layout.addLayout(btn_row)
        layout.addWidget(content)
        
    def add_pdf(self, path=None):
        if not path:
            dlg = ModernFileDialog(self, "Add PDF", "open", "PDF (*.pdf)")
            if dlg.exec_() == QDialog.Accepted:
                path_str = dlg.get_selected_path()
                if path_str: path = Path(path_str)
        if path:
            self.pdfs_to_merge.append(path)
            self.list_widget.addItem(f"📎 {path.name}")

    def execute_merge(self):
        if len(self.pdfs_to_merge) < 2: 
            return ModernMessageBox.show_msg(self, "Error", "Select at least 2 PDFs to merge.", "warning")
            
        dlg = ModernFileDialog(self, "Save Merged PDF", "save", "PDF (*.pdf)")
        if dlg.exec_() == QDialog.Accepted:
            save_path = dlg.get_selected_path()
            if save_path:
                try:
                    merge_pdfs(self.pdfs_to_merge, save_path)
                    ModernMessageBox.show_msg(self, "Success", "PDFs Merged Successfully!", "info")
                    self.close()
                except Exception as e:
                    ModernMessageBox.show_msg(self, "Error", f"Merge failed:\n{e}", "error")


# ==========================================
# THREADING CLASSES
# ==========================================
class ExtractorThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, archive_path, temp_dir):
        super().__init__()
        self.archive_path = archive_path
        self.temp_dir = temp_dir

    def run(self):
        try:
            extract_archive(str(self.archive_path), self.temp_dir)
            found_files = []
            for item in self.temp_dir.rglob("*"):
                if item.suffix.lower() in VALID_PAGE_FILES:
                    found_files.append(item)
            found_files = natsorted(found_files, key=lambda x: x.name.lower())
            self.finished.emit(found_files)
        except Exception as e:
            self.error.emit(str(e))

class PdfGeneratorThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, files, output_path):
        super().__init__()
        self.files = files
        self.output_path = output_path

    def run(self):
        try:
            generate_pdf(self.files, self.output_path)
            self.finished.emit(str(self.output_path))
        except Exception as e:
            self.error.emit(str(e))


# ==========================================
# MAIN APPLICATION
# ==========================================
class Zip2PDF(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(700)
        self.setMinimumHeight(550)
        self.setAcceptDrops(True)

        self.temp = Path(tempfile.mkdtemp())
        self.files = []         
        self.undo_stack = []    
        self.redo_stack = []    

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0) 
        main_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        content_container = QWidget()
        content_container.setObjectName("ContentContainer")
        layout = QVBoxLayout(content_container)
        layout.setContentsMargins(20, 20, 20, 20)

        hint = QLabel("Drag & Drop Archives, Images, or Text files into the workspace below.")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Sort:"))
        self.sort_box = QComboBox()
        self.sort_box.addItems(["Natural", "A-Z", "Z-A"])
        self.sort_box.currentIndexChanged.connect(self.apply_sort)
        controls_layout.addWidget(self.sort_box)

        self.btn_undo = QPushButton("↩ Undo")
        self.btn_undo.clicked.connect(self.undo)
        self.btn_undo.setEnabled(False)
        
        self.btn_redo = QPushButton("↪ Redo")
        self.btn_redo.clicked.connect(self.redo)
        self.btn_redo.setEnabled(False)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #00ADB5; font-weight: bold;")
        
        controls_layout.addStretch()
        controls_layout.addWidget(self.status_label)
        controls_layout.addWidget(self.btn_undo)
        controls_layout.addWidget(self.btn_redo)
        layout.addLayout(controls_layout)

        self.listbox = QListWidget()
        self.listbox.setDragDropMode(QListWidget.InternalMove)
        self.listbox.setSelectionMode(QListWidget.ExtendedSelection)
        self.listbox.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listbox.customContextMenuRequested.connect(self.show_context_menu)
        self.listbox.itemDoubleClicked.connect(self.preview_item)
        layout.addWidget(self.listbox)

        buttons = QHBoxLayout()
        self.btn_import = QPushButton("📂 Import File", clicked=self.open_file_dialog)
        self.btn_merge = QPushButton("🧩 Merge PDFs", clicked=self.open_merge_tool)
        self.btn_preview = QPushButton("👁 Preview PDF", clicked=self.preview_pdf)
        self.btn_save = QPushButton("💾 Save PDF", clicked=self.save_pdf)
        self.btn_save.setObjectName("PrimaryButton") 
        
        buttons.addWidget(self.btn_import)
        buttons.addWidget(self.btn_merge)
        buttons.addWidget(self.btn_preview)
        buttons.addWidget(self.btn_save)
        layout.addLayout(buttons)

        main_layout.addWidget(content_container)
        self.setLayout(main_layout)

    def closeEvent(self, event):
        if self.temp.exists():
            shutil.rmtree(self.temp, ignore_errors=True)
        event.accept()

    def save_state(self):
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

    def set_loading_state(self, is_loading, message=""):
        self.listbox.setEnabled(not is_loading)
        self.btn_import.setEnabled(not is_loading)
        self.btn_save.setEnabled(not is_loading)
        self.btn_preview.setEnabled(not is_loading)
        self.status_label.setText(message if is_loading else "")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.listbox.setStyleSheet("border: 2px dashed #00ADB5; background-color: #1A1A1A;")
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.listbox.setStyleSheet("")

    def dropEvent(self, event):
        self.listbox.setStyleSheet("")
        paths = [Path(u.toLocalFile()) for u in event.mimeData().urls()]
        if paths:
            self.save_state()
            for p in paths:
                self.process_input(p)

    def open_file_dialog(self):
        dlg = ModernFileDialog(self, "Select File", "open", "All Files (*)")
        if dlg.exec_() == QDialog.Accepted:
            path = dlg.get_selected_path()
            if path:
                self.save_state()
                self.process_input(Path(path))

    def process_input(self, path: Path):
        name = path.name.lower()

        if path.suffix == "":
            if ModernMessageBox.ask(self, "Unknown File", f"'{path.name}' has no extension.\nTreat as ZIP?"):
                new_path = path.with_suffix(".zip")
                path.rename(new_path)
                self.start_extraction(new_path)
            return

        if path.suffix.lower() in SUPPORTED_ARCHIVES:
            self.start_extraction(path)
        elif name.endswith(".pdf"):
            if ModernMessageBox.ask(self, "PDF Detected", "Open in PDF Merger?"):
                self.open_merge_tool(initial_pdf=path)
        elif path.suffix.lower() in VALID_PAGE_FILES:
            if path not in self.files:
                self.files.append(path)
                self.refresh_list()
        else:
            ModernMessageBox.show_msg(self, "Unsupported", f"Skipping: {path.name}", "warning")

    def start_extraction(self, archive_path):
        self.set_loading_state(True, "⏳ Extracting archive...")
        self.extractor_thread = ExtractorThread(archive_path, self.temp)
        self.extractor_thread.finished.connect(self.on_extraction_finished)
        self.extractor_thread.error.connect(self.on_thread_error)
        self.extractor_thread.start()

    def on_extraction_finished(self, found_files):
        for f in found_files:
            if f not in self.files:
                self.files.append(f)
        self.refresh_list()
        self.set_loading_state(False)
        ModernMessageBox.show_msg(self, "Success", "Archive extracted successfully!")

    def on_thread_error(self, error_msg):
        self.set_loading_state(False)
        ModernMessageBox.show_msg(self, "Error", f"An operation failed:\n{error_msg}", "error")

    def preview_pdf(self):
        if not self.files:
            return ModernMessageBox.show_msg(self, "Empty", "No files to preview.", "warning")
        out_path = self.temp / "preview_temp.pdf"
        self.start_pdf_generation(out_path, is_preview=True)

    def save_pdf(self):
        if not self.files:
            return ModernMessageBox.show_msg(self, "Empty", "Add files before saving.", "warning")
            
        dlg = ModernFileDialog(self, "Save PDF", "save", "PDF (*.pdf)")
        if dlg.exec_() == QDialog.Accepted:
            out_path = dlg.get_selected_path()
            if out_path:
                self.start_pdf_generation(Path(out_path), is_preview=False)

    def start_pdf_generation(self, out_path, is_preview):
        self.set_loading_state(True, "⏳ Generating PDF...")
        self.generator_thread = PdfGeneratorThread(self.files, out_path)
        self.generator_thread.is_preview = is_preview 
        self.generator_thread.finished.connect(self.on_generation_finished)
        self.generator_thread.error.connect(self.on_thread_error)
        self.generator_thread.start()

    def on_generation_finished(self, out_path_str):
        self.set_loading_state(False)
        if hasattr(self.generator_thread, 'is_preview') and self.generator_thread.is_preview:
            webbrowser.open(out_path_str)
        else:
            ModernMessageBox.show_msg(self, "Success", "PDF Saved Successfully! 🎉", "info")

    def apply_sort(self):
        self.save_state()
        mode = self.sort_box.currentText()
        if mode == "A-Z": self.files.sort(key=lambda x: x.name.lower())
        elif mode == "Z-A": self.files.sort(key=lambda x: x.name.lower(), reverse=True)
        else: self.files = natsorted(self.files, key=lambda x: x.name.lower())
        self.refresh_list()

    def refresh_list(self):
        self.listbox.clear()
        for f in self.files:
            item = QListWidgetItem(f"📄 {f.name}")
            item.setData(Qt.UserRole, f)
            self.listbox.addItem(item)

    def preview_item(self, item):
        webbrowser.open(str(item.data(Qt.UserRole)))

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
                if row < len(self.files): self.files.pop(row)
            self.refresh_list()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.remove_selected()

    def open_merge_tool(self, initial_pdf=None):
        dlg = ModernMergeDialog(self)
        if initial_pdf:
            dlg.add_pdf(initial_pdf)
        dlg.exec_()

class ModernFileDialog(QDialog):
    """A custom, frameless wrapper for the file explorer to match the dark theme."""
    def __init__(self, parent, title, mode="open", file_filter="All Files (*)"):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self)
        self.title_bar.title.setText(f" 📂 {title}")
        layout.addWidget(self.title_bar)
        
        content = QWidget()
        content.setObjectName("ContentContainer")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Embed the standard file dialog as a flat widget!
        self.file_dialog = QFileDialog(content, title, "", file_filter)
        self.file_dialog.setWindowFlags(Qt.Widget) # Strips the native OS frame
        self.file_dialog.setOptions(QFileDialog.DontUseNativeDialog)
        
        if mode == "save":
            self.file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        else:
            self.file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
            
        content_layout.addWidget(self.file_dialog)
        layout.addWidget(content)
        
        # Connect signals so clicking Open/Cancel closes the wrapper
        self.file_dialog.accepted.connect(self.accept)
        self.file_dialog.rejected.connect(self.reject)
        
    def get_selected_path(self):
        files = self.file_dialog.selectedFiles()
        return files[0] if files else None

# ==========================================
# MODERN OBSIDIAN & TEAL STYLESHEET
# ==========================================
MODERN_STYLE = """
QWidget {
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #E0E0E0;
}

Zip2PDF, ModernMessageBox, ModernMergeDialog {
    background-color: transparent;
}

QWidget#ContentContainer {
    background-color: #121212;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
    border: 1px solid #2D2D2D;
    border-top: none;
}

QWidget#CustomTitleBar {
    background-color: #1A1A1A;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border: 1px solid #2D2D2D;
    border-bottom: 1px solid #000000;
}

QPushButton#WindowControlButton {
    background-color: transparent;
    border: none;
    color: #888888;
    font-weight: bold;
    border-radius: 4px;
}

QPushButton#WindowControlButton:hover {
    background-color: #333333;
    color: #FFFFFF;
}

QPushButton#CloseButton:hover {
    background-color: #E81123;
    color: white;
}

QLabel#HintLabel {
    color: #888888;
    font-style: italic;
    margin-bottom: 10px;
}

QPushButton {
    background-color: #1E1E1E;
    color: #E0E0E0;
    border: 1px solid #333333;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2D2D2D;
    border: 1px solid #00ADB5;
}

QPushButton:pressed {
    background-color: #00ADB5;
    color: #121212;
}

QPushButton:disabled {
    background-color: #121212;
    color: #4A4A4A;
    border: 1px solid #1E1E1E;
}

QPushButton#PrimaryButton {
    background-color: #00ADB5;
    color: #121212;
    border: none;
}

QPushButton#PrimaryButton:hover {
    background-color: #00D2DD;
}

QListWidget {
    background-color: #1A1A1A;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 10px;
    outline: none;
}

QListWidget::item {
    background-color: #242424;
    border-radius: 5px;
    padding: 8px;
    margin-bottom: 4px;
    border: 1px solid transparent;
}

QListWidget::item:hover {
    background-color: #2D2D2D;
    border: 1px solid #444444;
}

QListWidget::item:selected {
    background-color: #00ADB5;
    color: #121212;
    font-weight: bold;
}

QComboBox {
    background-color: #1E1E1E;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 4px 10px;
    color: #E0E0E0;
}
QComboBox::drop-down { border: none; }

/* Fix for built-in Qt File Dialogs to keep the dark theme consistent */
QTreeView, QListView, QTableView, QLineEdit {
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: 1px solid #333333;
    border-radius: 4px;
}
QHeaderView::section {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #1A1A1A;
    padding: 4px;
}

/* Tool Buttons for File Dialog */
QFileDialog {
    background-color: transparent;
}
QToolButton {
    background-color: transparent;
    color: #E0E0E0;
    border: none;
    border-radius: 4px;
    padding: 4px;
}
QToolButton:hover {
    background-color: #2D2D2D;
    border: 1px solid #444444;
}
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE)
    window = Zip2PDF()
    window.show()
    sys.exit(app.exec())