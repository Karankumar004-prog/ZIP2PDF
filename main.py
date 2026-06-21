# main.py
import sys
import tempfile
import webbrowser
from pathlib import Path
from natsort import natsorted
import os
import shutil

# Force X11/XWayland to fix Gnome frameless resizing and Wayland warnings
os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--no-sandbox"
os.environ["QT_QPA_PLATFORMTHEME"] = "gtk3"
os.environ["GTK_THEME"] = "Adwaita:dark"

from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QSize, QDir, QSortFilterProxyModel, QModelIndex, QUrl, QTimer
)
from PyQt6.QtGui import (
    QColor, QIcon, QPixmap, QImageReader, QKeySequence, QFont, QDesktopServices,
    QCursor, QDrag, QPainter, QPen, QAction, QShortcut, QFileSystemModel
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget,
    QFileDialog, QListWidgetItem, QComboBox, QLabel,
    QHBoxLayout, QDialog, QMenu, QGraphicsDropShadowEffect, QSizeGrip,
    QLineEdit, QTreeView, QSplitter, QAbstractItemView,
    QStackedWidget, QToolBar, QFrame, QInputDialog, QMessageBox, QHeaderView
)

# ==========================================
# STARTUP ERROR HANDLING
# ==========================================
try:
    from utils.extractor import extract_archive as utils_extract, SUPPORTED_ARCHIVES
    from utils.pdf_tools import generate_pdf, merge_pdfs, VALID_PAGE_FILES
except ImportError as e:
    app = QApplication(sys.argv)
    error_box = QMessageBox()
    error_box.setIcon(QMessageBox.Icon.Critical)
    error_box.setWindowTitle("Critical Error - ZIP2PDF")
    error_box.setText(f"Missing essential components. Please ensure the 'utils' folder is next to the executable.\n\nDetails: {e}")
    error_box.exec()
    sys.exit(1)

# Fallback extractor just in case utils/extractor.py hasn't been updated to accept passwords
def safe_extract_archive(archive_path, temp_dir, password=None):
    try:
        import zipfile
        utils_extract(archive_path, temp_dir, password)
    except TypeError:
        import zipfile
        with zipfile.ZipFile(archive_path, 'r') as zf:
            if password:
                zf.setpassword(password.encode('utf-8'))
            zf.extractall(temp_dir)

# ==========================================
# CUSTOM UI COMPONENTS
# ==========================================
class CustomItemWidget(QWidget):
    """A custom visual card for each list item containing thumbnails and controls."""
    def __init__(self, main_app, item, display_name, icon):
        super().__init__()
        self.main_app = main_app
        self.item = item
        self._display_name = display_name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        # 1. Thumbnail
        lbl_icon = QLabel()
        if not icon.isNull():
            lbl_icon.setPixmap(icon.pixmap(64, 64))
        else:
            lbl_icon.setFixedSize(64, 64)
        layout.addWidget(lbl_icon)

        # 2. File Name (editable inline via double-click or F2)
        self.lbl_name = QLabel(display_name)
        self.lbl_name.setStyleSheet("font-size: 14px; color: #E0E0E0; background: transparent;")
        layout.addWidget(self.lbl_name)

        layout.addStretch()

        # 3. Up / Down Adjuster Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)
        self.btn_up = QPushButton("▲")
        self.btn_down = QPushButton("▼")

        btn_style = """
            QPushButton { background-color: #2D2D2D; border: 1px solid #444444; border-radius: 4px; padding: 2px; font-size: 10px; min-width: 24px; min-height: 20px; color: #E0E0E0; }
            QPushButton:hover { background-color: #00ADB5; color: #121212; border: 1px solid #00ADB5; }
        """
        self.btn_up.setStyleSheet(btn_style)
        self.btn_down.setStyleSheet(btn_style)

        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)

        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        layout.addLayout(btn_layout)

    def move_up(self):
        self.main_app.move_item_manual(-1, self.item)

    def move_down(self):
        self.main_app.move_item_manual(1, self.item)

    def set_display_name(self, name):
        """Update the visible label after rename."""
        self._display_name = name
        self.lbl_name.setText(name)


class CustomTitleBar(QWidget):
    """
    Title bar: drag-to-move (manual delta, works on main window AND dialogs).
    Resize lives in Zip2PDF.mouseMoveEvent — not here.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self._win_parent = parent
        self._drag_start_pos = None

        self.setFixedHeight(40)
        self.setObjectName("CustomTitleBar")

        _hbox = QHBoxLayout()
        # Set right margin and spacing to 0 so buttons are flush against the right edge
        _hbox.setContentsMargins(15, 0, 0, 0)
        _hbox.setSpacing(0)

        self.title = QLabel("📦 ZIP2PDF")
        self.title.setStyleSheet("font-weight: bold; color: #00ADB5; font-size: 14px;")

        self.btn_min   = QPushButton("—")
        self.btn_max   = QPushButton("◻")
        self.btn_close = QPushButton("✕")

        # Assign unique IDs so they perfectly catch the CSS rules without inheritance conflicts
        self.btn_min.setObjectName("MinButton")
        self.btn_max.setObjectName("MaxButton")
        self.btn_close.setObjectName("CloseButton")

        for btn in [self.btn_min, self.btn_max, self.btn_close]:
            btn.setFixedSize(40, 40)

        self.btn_min.clicked.connect(self._win_parent.showMinimized)
        self.btn_max.clicked.connect(self.toggle_max_restore)
        self.btn_close.clicked.connect(self._win_parent.close)

        _hbox.addWidget(self.title)
        _hbox.addStretch()
        _hbox.addWidget(self.btn_min)
        _hbox.addWidget(self.btn_max)
        _hbox.addWidget(self.btn_close)
        self.setLayout(_hbox)

    def toggle_max_restore(self):
        if self._win_parent.isMaximized():
            self._win_parent.showNormal()
            self.btn_max.setText("◻")
        else:
            self._win_parent.showMaximized()
            self.btn_max.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._win_parent.isMaximized():
            self._drag_start_pos = (
                event.globalPosition().toPoint() - self._win_parent.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_start_pos is not None:
            self._win_parent.move(event.globalPosition().toPoint() - self._drag_start_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_max_restore()


class ModernMessageBox(QDialog):
    def __init__(self, parent, title, text, msg_type="info"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(400)
        
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(10, 10, 10, 10)
        
        main_wrapper = QWidget()
        main_wrapper.setObjectName("MainWrapper")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        main_wrapper.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(main_wrapper)
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
        base_layout.addWidget(main_wrapper)
        
    @staticmethod
    def ask(parent, title, text):
        dlg = ModernMessageBox(parent, title, text, "question")
        return dlg.exec() == int(QDialog.DialogCode.Accepted)
        
    @staticmethod
    def show_msg(parent, title, text, msg_type="info"):
        dlg = ModernMessageBox(parent, title, text, msg_type)
        dlg.exec()


class RenameDialog(QDialog):
    """Inline rename dialog — shown centered over the app."""
    def __init__(self, parent, current_name):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(380)

        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(10, 10, 10, 10)

        main_wrapper = QWidget()
        main_wrapper.setObjectName("MainWrapper")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        main_wrapper.setGraphicsEffect(shadow)

        layout = QVBoxLayout(main_wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        self.title_bar.title.setText("✏️ Rename File")
        self.title_bar.btn_min.hide()
        self.title_bar.btn_max.hide()
        layout.addWidget(self.title_bar)

        content = QWidget()
        content.setObjectName("ContentContainer")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(10)

        lbl = QLabel("Enter new name (stem only — extension is preserved):")
        lbl.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        content_layout.addWidget(lbl)

        # Split stem / suffix so user only edits the stem
        p = Path(current_name)
        self._suffix = p.suffix  # preserve original extension

        self.edit = QLineEdit(p.stem)
        self.edit.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                border: 1px solid #00ADB5;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 14px;
                color: #E0E0E0;
            }
        """)
        self.edit.selectAll()
        content_layout.addWidget(self.edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Rename")
        btn_ok.setObjectName("PrimaryButton")
        btn_ok.clicked.connect(self._commit)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        content_layout.addLayout(btn_row)

        layout.addWidget(content)
        base_layout.addWidget(main_wrapper)

        # Enter key confirms
        self.edit.returnPressed.connect(self._commit)

    def _commit(self):
        stem = self.edit.text().strip()
        if stem:
            self.accept()

    def new_filename(self):
        return self.edit.text().strip() + self._suffix


class ModernMergeDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(450)
        
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(10, 10, 10, 10)
        
        main_wrapper = QWidget()
        main_wrapper.setObjectName("MainWrapper")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        main_wrapper.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout(main_wrapper)
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
        self.list_widget.setStyleSheet("QListWidget::item { padding: 8px; margin-bottom: 4px; }")
        self.pdfs_to_merge = []
        
        btn_add = QPushButton("➕ Add PDF")
        btn_add.clicked.connect(lambda: self.add_pdf())
        btn_run = QPushButton("💾 Save As")
        btn_run.setObjectName("PrimaryButton")
        btn_run.clicked.connect(self.execute_merge)
        
        content_layout.addWidget(self.list_widget)
        
        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_run)
        content_layout.addLayout(btn_row)
        layout.addWidget(content)
        base_layout.addWidget(main_wrapper)
        
    def add_pdf(self, path=None):
        if path is None:
            options = QFileDialog.Option.DontUseNativeDialog
            path_str, _ = QFileDialog.getOpenFileName(self, "Add PDF", str(Path.home()), "PDF Files (*.pdf)", options=options)
            if path_str:
                path = Path(path_str)
            else:
                return  # user cancelled
        self.pdfs_to_merge.append(Path(path))
        self.list_widget.addItem(f"📎 {Path(path).name}")

    def execute_merge(self):
        if len(self.pdfs_to_merge) < 2: 
            return ModernMessageBox.show_msg(self, "Error", "Select at least 2 PDFs to merge.", "warning")
            
        options = QFileDialog.Option.DontUseNativeDialog
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", str(Path.home() / "merged.pdf"), "PDF Files (*.pdf)", options=options)
        if save_path:
            try:
                merge_pdfs(self.pdfs_to_merge, save_path)
                ModernMessageBox.show_msg(self, "Success", "PDFs Merged Successfully!", "info")
                self.close()
            except Exception as e:
                ModernMessageBox.show_msg(self, "Error", f"Merge failed:\n{e}", "error")


class FramelessFileDialog(QDialog):
    """Wraps the built-in Qt File Picker inside our sleek custom frameless window."""
    def __init__(self, parent, title, start_dir, name_filter, mode="open", multi=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(500, 350)
        self.resize(600, 400)

        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(10, 10, 10, 10)

        main_wrapper = QWidget()
        main_wrapper.setObjectName("MainWrapper")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 0)
        main_wrapper.setGraphicsEffect(shadow)

        layout = QVBoxLayout(main_wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Attach our custom dark title bar
        self.title_bar = CustomTitleBar(self)
        self.title_bar.title.setText(f" 📂 {title}")
        self.title_bar.btn_min.hide()
        self.title_bar.btn_max.hide()
        layout.addWidget(self.title_bar)

        # Embed the actual Qt File Dialog as a widget inside our layout
        self.picker = QFileDialog(self, title, start_dir, name_filter)
        self.picker.setWindowFlags(Qt.WindowType.Widget) # Forces it to be embedded, hiding OS borders
        self.picker.setOption(QFileDialog.Option.DontUseNativeDialog)
        
        if mode == "save":
            self.picker.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        else:
            self.picker.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            if multi:
                self.picker.setFileMode(QFileDialog.FileMode.ExistingFiles)

        # Link the picker's buttons to close our custom window
        self.picker.accepted.connect(self.accept)
        self.picker.rejected.connect(self.reject)

        layout.addWidget(self.picker)
        base_layout.addWidget(main_wrapper)

    def get_selected_paths(self):
        return self.picker.selectedFiles()
    

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
            safe_extract_archive(str(self.archive_path), self.temp_dir)
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
# SMOOTH LIST WIDGET  (single, correct __init__)
# ==========================================
class SmoothListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIconSize(QSize(64, 64))
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setUniformItemSizes(True)
        self.setAutoScroll(False)          # We use our own smooth scroll

        # Custom high-speed scroll timer
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self.force_auto_scroll)

    def dragMoveEvent(self, event):
        super().dragMoveEvent(event)
        if not self.scroll_timer.isActive():
            self.scroll_timer.start(16)   # 60 FPS

    def dropEvent(self, event):
        super().dropEvent(event)
        self.scroll_timer.stop()

    def force_auto_scroll(self):
        """Dynamically tracks physical mouse position so dragging outside still works."""
        local_pos = self.mapFromGlobal(QCursor.pos())
        local_y = local_pos.y()
        local_x = local_pos.x()
        margin = 40

        if local_x < -100 or local_x > self.width() + 100:
            self.scroll_timer.stop()
            return

        if local_y < margin:
            scroll_dir = -1
        elif local_y > self.height() - margin:
            scroll_dir = 1
        else:
            self.scroll_timer.stop()
            return

        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() + (scroll_dir * 15))

    def startDrag(self, supportedActions):
        """Dark-themed drag ghost; kills scroll loop on release."""
        item = self.currentItem()
        widget = self.itemWidget(item)

        if widget:
            pixmap = QPixmap(widget.size())
            pixmap.fill(QColor("#1A2B2C"))
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#00ADB5"), 2))
            painter.drawRoundedRect(1, 1, widget.width() - 2, widget.height() - 2, 6, 6)
            widget.render(painter, flags=QWidget.RenderFlag.DrawChildren)
            painter.end()

            drag = QDrag(self)
            drag.setMimeData(self.mimeData(self.selectedItems()))
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())
            drag.exec(supportedActions, Qt.DropAction.MoveAction)
        else:
            super().startDrag(supportedActions)

        # CRITICAL: kill auto-scroll the instant the drag ends
        self.scroll_timer.stop()


# ==========================================
# MAIN APPLICATION
# ==========================================
class Zip2PDF(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumWidth(740)
        self.setMinimumHeight(600)
        self.setAcceptDrops(True)

        # One persistent temp dir for the session
        self.temp = Path(tempfile.mkdtemp())
        self.files = []
        self.undo_stack = []
        self.redo_stack = []
        self.icon_cache = {}   # keyed by Path; cleared on clear-all / rename

        self._build_ui()

    def _build_ui(self):
        base_layout = QVBoxLayout(self)
        base_layout.setContentsMargins(15, 15, 15, 15)

        self.main_wrapper = QWidget()
        self.main_wrapper.setObjectName("MainWrapper")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        self.main_wrapper.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self.main_wrapper)
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

        # --- Sort controls row ---
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Sort:"))
        self.sort_box = QComboBox()
        self.sort_box.blockSignals(True)
        self.sort_box.addItems([
            "Natural / Num Sort", "Alphabetical (A-Z)", "Alphabetical (Z-A)",
            "By Extension / Type", "By File Size", "Custom (Manual Drag)"
        ])
        self.sort_box.blockSignals(False)
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

        # --- List widget ---
        self.listbox = SmoothListWidget(self)
        self.listbox.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.listbox.customContextMenuRequested.connect(self.show_context_menu)
        self.listbox.itemDoubleClicked.connect(self.preview_item)
        # Sync backend order when user drags in the list
        self.listbox.model().rowsMoved.connect(
            lambda: self.sort_box.blockSignals(True) or
                    self.sort_box.setCurrentText("Custom (Manual Drag)") or
                    self.sort_box.blockSignals(False)
        )
        layout.addWidget(self.listbox)

        # --- Trash / Clear row ---
        trash_layout = QHBoxLayout()
        trash_layout.addStretch()
        self.btn_clear_all = QPushButton("🧹 Clear All")
        self.btn_clear_all.setObjectName("TrashButton")
        self.btn_clear_all.clicked.connect(self.clear_all)
        self.btn_trash = QPushButton("🗑️ Remove Selected")
        self.btn_trash.setObjectName("TrashButton")
        self.btn_trash.clicked.connect(self.remove_selected)
        trash_layout.addWidget(self.btn_clear_all)
        trash_layout.addWidget(self.btn_trash)
        layout.addLayout(trash_layout)

        # --- Action buttons ---
        buttons = QHBoxLayout()
        self.btn_import = QPushButton("📂 Import File", clicked=self.open_file_dialog)
        self.btn_merge  = QPushButton("🧩 Merge PDFs",  clicked=self.open_merge_tool)
        self.btn_preview = QPushButton("👁 Preview PDF", clicked=self.preview_pdf)
        self.btn_save   = QPushButton("💾 Save PDF",    clicked=self.save_pdf)
        self.btn_save.setObjectName("PrimaryButton")

        buttons.addWidget(self.btn_import)
        buttons.addWidget(self.btn_merge)
        buttons.addWidget(self.btn_preview)
        buttons.addWidget(self.btn_save)
        layout.addLayout(buttons)

        main_layout.addWidget(content_container)
        base_layout.addWidget(self.main_wrapper)
        self.setLayout(base_layout)

    def closeEvent(self, event):
        if self.temp.exists():
            shutil.rmtree(self.temp, ignore_errors=True)

    # ── Edge-resize for frameless window ──────────────────────────────────────
    RESIZE_MARGIN = 8

    def _resize_edge(self, pos):
        x, y, m = pos.x(), pos.y(), self.RESIZE_MARGIN
        w, h = self.width(), self.height()
        edge = 0
        if x <= m:      edge |= Qt.Edge.LeftEdge.value
        if x >= w - m:  edge |= Qt.Edge.RightEdge.value
        if y <= m:      edge |= Qt.Edge.TopEdge.value
        if y >= h - m:  edge |= Qt.Edge.BottomEdge.value
        return edge

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.isMaximized():
            edge = self._resize_edge(event.position().toPoint())
            if edge:
                self.__resize_edge = edge
                self.__resize_start_geo = self.geometry()
                self.__resize_start_mouse = event.globalPosition().toPoint()
                event.accept()
                return
        self.__resize_edge = 0
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            edge = self._resize_edge(event.position().toPoint())
            cursors = {
                Qt.Edge.LeftEdge.value | Qt.Edge.TopEdge.value:     Qt.CursorShape.SizeFDiagCursor,
                Qt.Edge.RightEdge.value | Qt.Edge.BottomEdge.value: Qt.CursorShape.SizeFDiagCursor,
                Qt.Edge.RightEdge.value | Qt.Edge.TopEdge.value:    Qt.CursorShape.SizeBDiagCursor,
                Qt.Edge.LeftEdge.value | Qt.Edge.BottomEdge.value:  Qt.CursorShape.SizeBDiagCursor,
                Qt.Edge.TopEdge.value:                              Qt.CursorShape.SizeVerCursor,
                Qt.Edge.BottomEdge.value:                           Qt.CursorShape.SizeVerCursor,
                Qt.Edge.LeftEdge.value:                             Qt.CursorShape.SizeHorCursor,
                Qt.Edge.RightEdge.value:                            Qt.CursorShape.SizeHorCursor,
            }
            cursor = cursors.get(edge)
            self.setCursor(cursor) if cursor else self.unsetCursor()
            super().mouseMoveEvent(event)
            return

        edge = getattr(self, '_Zip2PDF__resize_edge', 0)
        if edge and not self.isMaximized():
            delta = event.globalPosition().toPoint() - self.__resize_start_mouse
            geo   = self.__resize_start_geo
            x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
            min_w, min_h = self.minimumWidth(), self.minimumHeight()

            if edge & Qt.Edge.RightEdge.value:  w = max(min_w, geo.width() + delta.x())
            if edge & Qt.Edge.BottomEdge.value: h = max(min_h, geo.height() + delta.y())
            if edge & Qt.Edge.LeftEdge.value:
                new_w = max(min_w, geo.width() - delta.x())
                x = geo.x() + geo.width() - new_w; w = new_w
            if edge & Qt.Edge.TopEdge.value:
                new_h = max(min_h, geo.height() - delta.y())
                y = geo.y() + geo.height() - new_h; h = new_h

            self.setGeometry(x, y, w, h)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.__resize_edge = 0
        self.unsetCursor()
        super().mouseReleaseEvent(event)
        event.accept()

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def save_state(self):
        self.sync_files_order()
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

    def sync_files_order(self):
        """Syncs backend list with visual drag-and-drop order."""
        self.files = [
            self.listbox.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.listbox.count())
        ]

    # ── Loading state ─────────────────────────────────────────────────────────

    def set_loading_state(self, is_loading, message=""):
        self.listbox.setEnabled(not is_loading)
        self.btn_import.setEnabled(not is_loading)
        self.btn_save.setEnabled(not is_loading)
        self.btn_preview.setEnabled(not is_loading)
        self.btn_trash.setEnabled(not is_loading)
        self.btn_clear_all.setEnabled(not is_loading)
        self.status_label.setText(message if is_loading else "")

    # ── Drag-and-drop into app ────────────────────────────────────────────────

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

    # ── File import ───────────────────────────────────────────────────────────

    def open_file_dialog(self):
        dlg = FramelessFileDialog(
            self, 
            "Select Files to Import", 
            str(Path.home()), 
            "Supported Files (*.zip *.7z *.jpg *.jpeg *.png *.webp *.txt *.pdf);;All Files (*)",
            mode="open",
            multi=True
        )
        
        if dlg.exec() == int(QDialog.DialogCode.Accepted):
            paths = dlg.get_selected_paths()
            if paths:
                self.save_state()
                for p in paths:
                    self.process_input(Path(p))

    def process_input(self, path: Path):
        if path.suffix == "":
            if ModernMessageBox.ask(self, "Unknown File", f"'{path.name}' has no extension.\nTreat as ZIP?"):
                temp_copy = self.temp / (path.stem + ".zip")
                shutil.copy2(path, temp_copy)
                self.start_extraction(temp_copy)
            return

        if path.suffix.lower() in SUPPORTED_ARCHIVES:
            self.start_extraction(path)
        elif path.suffix.lower() == ".pdf":
            if ModernMessageBox.ask(self, "PDF Detected", "Open in PDF Merger?"):
                self.open_merge_tool(initial_pdf=path)
        elif path.suffix.lower() in VALID_PAGE_FILES:
            if path not in self.files:
                self.files.append(path)
                self.refresh_list()
        else:
            ModernMessageBox.show_msg(self, "Unsupported", f"Skipping: {path.name}", "warning")

    # ── Archive extraction ─────────────────────────────────────────────────────
    # FIX #1: Each archive gets its own sub-temp dir so files from the previous
    # archive don't bleed into the next load.

    def start_extraction(self, archive_path):
        # Create a fresh sub-directory just for this archive
        archive_temp = Path(tempfile.mkdtemp(dir=self.temp))
        self.set_loading_state(True, "⏳ Extracting archive...")
        self.extractor_thread = ExtractorThread(archive_path, archive_temp)
        self.extractor_thread.finished.connect(self.on_extraction_finished)
        self.extractor_thread.error.connect(self.on_thread_error)
        self.extractor_thread.start()

    def on_extraction_finished(self, found_files):
        self.save_state()               # push undo snapshot BEFORE adding
        for f in found_files:
            if f not in self.files:
                self.files.append(f)
        self.refresh_list()
        self.set_loading_state(False)
        ModernMessageBox.show_msg(self, "Success", "Archive extracted successfully!")

    def on_thread_error(self, error_msg):
        self.set_loading_state(False)
        ModernMessageBox.show_msg(self, "Error", f"An operation failed:\n{error_msg}", "error")

    # ── List management ───────────────────────────────────────────────────────

    def refresh_list(self):
        self.listbox.clear()
        for f in self.files:
            display_name = f.name
            if len(display_name) > 28:
                display_name = display_name[:15] + "..." + display_name[-10:]

            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 80))
            item.setData(Qt.ItemDataRole.UserRole, f)

            ext = f.suffix.lower()
            if f not in self.icon_cache:
                if ext in (".jpg", ".jpeg", ".png", ".webp"):
                    reader = QImageReader(str(f))
                    reader.setAutoTransform(True)
                    reader.setScaledSize(QSize(64, 64))
                    img = reader.read()
                    self.icon_cache[f] = QIcon(QPixmap.fromImage(img)) if not img.isNull() else QIcon()
                else:
                    self.icon_cache[f] = QIcon()

            self.listbox.addItem(item)
            custom_widget = CustomItemWidget(self, item, display_name, self.icon_cache[f])
            self.listbox.setItemWidget(item, custom_widget)

    def preview_item(self, item):
        webbrowser.open(str(item.data(Qt.ItemDataRole.UserRole)))

    def apply_sort(self):
        self.save_state()
        mode = self.sort_box.currentText()
        if mode == "Alphabetical (A-Z)":
            self.files.sort(key=lambda x: x.name.lower())
        elif mode == "Alphabetical (Z-A)":
            self.files.sort(key=lambda x: x.name.lower(), reverse=True)
        elif mode == "By Extension / Type":
            self.files.sort(key=lambda x: (x.suffix.lower(), x.name.lower()))
        elif mode == "By File Size":
            self.files.sort(key=lambda x: x.stat().st_size if x.exists() else 0, reverse=True)
        elif mode == "Natural / Num Sort":
            self.files = natsorted(self.files, key=lambda x: x.name.lower())
        self.refresh_list()

    def move_item_manual(self, direction, item):
        self.save_state()
        row = self.listbox.row(item)
        new_row = row + direction
        if 0 <= new_row < len(self.files):
            self.files[row], self.files[new_row] = self.files[new_row], self.files[row]
            self.sort_box.setCurrentText("Custom (Manual Drag)")
            self.refresh_list()
            self.listbox.setCurrentRow(new_row)

    def show_context_menu(self, pos):
        menu = QMenu()
        rename_action = QAction("✏️ Rename (F2)", self)
        rename_action.triggered.connect(self.rename_selected)
        delete_action = QAction("❌ Remove Selected", self)
        delete_action.triggered.connect(self.remove_selected)
        menu.addAction(rename_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        menu.exec(self.listbox.mapToGlobal(pos))

    def remove_selected(self):
        rows = sorted(
            [index.row() for index in self.listbox.selectedIndexes()],
            reverse=True
        )
        if rows:
            self.save_state()
            for row in rows:
                self.listbox.takeItem(row)
            self.sync_files_order()

    def clear_all(self):
        """Remove ALL files, clear temp data, and reset undo/redo history."""
        if not self.files:
            return
        if ModernMessageBox.ask(self, "Clear All", "Remove all files from the workspace?"):
            # 1. Clear current files and UI
            self.files.clear()
            self.icon_cache.clear()
            self.listbox.clear()
            
            # 2. Hard reset the Undo and Redo stacks & buttons
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.update_undo_redo_buttons()
            
            # 3. Clean out and recreate a fresh temp directory
            shutil.rmtree(self.temp, ignore_errors=True)
            self.temp = Path(tempfile.mkdtemp())

    # ── FIX #2: Rename via F2 ─────────────────────────────────────────────────

    def rename_selected(self):
        """Rename the currently selected file (display name + actual file if in temp)."""
        item = self.listbox.currentItem()
        if not item:
            return
        old_path = item.data(Qt.ItemDataRole.UserRole)
        dlg = RenameDialog(self, old_path.name)
        if dlg.exec() != int(QDialog.DialogCode.Accepted):
            return

        new_name = dlg.new_filename()
        if new_name == old_path.name:
            return  # no change

        new_path = old_path.parent / new_name

        # Only physically rename if the file lives inside our temp dir
        # (never touch user originals that were added by reference)
        if self.temp in old_path.parents:
            try:
                old_path.rename(new_path)
            except Exception as e:
                ModernMessageBox.show_msg(self, "Rename Error", str(e), "error")
                return
        else:
            # For originals: we can't rename them, so just update the display alias
            # by copying them into temp under the new name
            try:
                shutil.copy2(old_path, new_path)
                # Replace in file list
                idx = self.files.index(old_path)
                self.files[idx] = new_path
            except Exception as e:
                ModernMessageBox.show_msg(self, "Rename Error", str(e), "error")
                return

        # Update icon cache: move old key to new key
        if old_path in self.icon_cache:
            self.icon_cache[new_path] = self.icon_cache.pop(old_path)

        # Update the in-memory file list
        idx = self.listbox.row(item)
        if idx < len(self.files) and self.files[idx] == old_path:
            self.files[idx] = new_path

        # Update the list item in-place (no full refresh needed)
        item.setData(Qt.ItemDataRole.UserRole, new_path)
        display = new_name if len(new_name) <= 28 else new_name[:15] + "..." + new_name[-10:]
        widget = self.listbox.itemWidget(item)
        if widget:
            widget.set_display_name(display)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F2:
            self.rename_selected()
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.remove_selected()

    # ── PDF generation ────────────────────────────────────────────────────────

    def preview_pdf(self):
        self.sync_files_order()
        if not self.files:
            return ModernMessageBox.show_msg(self, "Empty", "No files to preview.", "warning")
        out_path = self.temp / "preview_temp.pdf"
        self.start_pdf_generation(out_path, is_preview=True)

    def save_pdf(self):
        self.sync_files_order()
        if not self.files:
            return ModernMessageBox.show_msg(self, "Empty", "Add files before saving.", "warning")
            
        dlg = FramelessFileDialog(
            self, 
            "Save Merged PDF", 
            str(Path.home() / "output.pdf"), 
            "PDF (*.pdf)", 
            mode="save"
        )
        
        if dlg.exec() == int(QDialog.DialogCode.Accepted):
            paths = dlg.get_selected_paths()
            if paths:
                out_path = Path(paths[0])
                self.start_pdf_generation(out_path, is_preview=False)

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

    def open_merge_tool(self, initial_pdf=None):
        dlg = ModernMergeDialog(self)
        if initial_pdf:
            dlg.add_pdf(initial_pdf)
        dlg.exec()


# ==========================================
# MODERN OBSIDIAN & TEAL STYLESHEET
# ==========================================
MODERN_STYLE = """
QWidget {
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #E0E0E0;
}

QFileDialog QWidget {
    background-color: transparent;
}

QFileDialog QFrame {
    border: none;
}

QFileDialog QListView, QFileDialog QTreeView, QFileDialog QTableView {
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: 1px solid #2D2D2D;
    border-radius: 6px;
    selection-background-color: #1A2B2C;
    selection-color: #00D2DD;
    outline: none;
}

QFileDialog QListView::item:hover, QFileDialog QTreeView::item:hover {
    background-color: #2D2D2D;
}

QFileDialog QLabel {
    color: #E0E0E0;
}

QFileDialog QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #E0E0E0;
}

QFileDialog QToolButton:hover {
    background-color: #2D2D2D;
    border: 1px solid #00ADB5;
}

Zip2PDF, ModernMessageBox, ModernMergeDialog, FramelessFileDialog, RenameDialog {
    background-color: transparent;
}

QWidget#MainWrapper {
    background-color: #1A1A1A;
    border-radius: 10px;
}

QWidget#ContentContainer {
    background-color: transparent;
    border-bottom-left-radius: 10px;
    border-bottom-right-radius: 10px;
    border: 1px solid #2D2D2D;
    border-top: none;
}

QWidget#CustomTitleBar {
    background-color: #121212;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    border-left: 1px solid #2D2D2D;
    border-right: 1px solid #2D2D2D;
    border-top: 1px solid #2D2D2D;
    border-bottom: 2px solid #00ADB5;
}

/* Explicit Title Bar Button CSS - Targets specific object names */
QPushButton#MinButton, QPushButton#MaxButton, QPushButton#CloseButton {
    background-color: transparent;
    border: none;
    border-radius: 0px;
    color: #AAAAAA;
    font-weight: normal;
    font-size: 16px;
    padding: 0px;
    min-width: 40px;
    min-height: 40px;
}

QPushButton#MinButton:hover, QPushButton#MaxButton:hover {
    background-color: #333333;
    color: #FFFFFF;
}

/* Perfect native red hover for the close button matching the window's rounded edge */
QPushButton#CloseButton:hover {
    background-color: #E81123;
    color: #FFFFFF;
    border-top-right-radius: 10px;
}
QPushButton#CloseButton:pressed {
    background-color: #F1707A;
    color: #FFFFFF;
    border-top-right-radius: 10px;
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

QPushButton#TrashButton {
    background-color: #1A1212;
    color: #FF5555;
    border: 1px solid #331A1A;
    padding: 6px 12px;
}
QPushButton#TrashButton:hover {
    background-color: #2A1212;
    border: 1px solid #FF5555;
}

QListWidget {
    background-color: #121212;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 10px;
    outline: none;
}
QListWidget::item {
    background-color: #1E1E1E;
    border-radius: 6px;
    padding: 10px;
    margin-bottom: 6px;
    border: 1px solid #2D2D2D;
}
QListWidget::item:hover {
    background-color: #2A2A2A;
    border: 1px solid #00ADB5;
}
QListWidget::item:selected {
    background-color: #1A2B2C;
    border: 1px solid #00ADB5;
    color: #00D2DD;
    font-weight: bold;
}

/* 1. Base ComboBox - combobox-popup: 0 stops the jumping! */
QComboBox {
    background-color: #1E1E1E;
    color: #E0E0E0;
    selection-background-color: #1E1E1E; 
    selection-color: #E0E0E0;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 6px 12px;
    combobox-popup: 0; /* CRITICAL: Forces standard dropdown instead of jumping menu */
}

QComboBox:hover {
    border: 1px solid #00ADB5;
    background-color: #2D2D2D;
}

QComboBox:on {
    border: 1px solid #00ADB5;
}

QComboBox::drop-down { 
    border: none; 
}

/* 2. Dropdown List Container */
QComboBox QAbstractItemView {
    background-color: #1E1E1E;
    color: #E0E0E0;
    selection-background-color: #1A2B2C;
    selection-color: #00D2DD;
    border: 1px solid #333333;
    outline: none;
}

/* 3. Hover and sizing for the actual items inside the dropdown */
QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 4px 8px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #2D2D2D;
    color: #00D2DD;
}

/* File browser tree / list */
QFrame#Sidebar {
    background-color: #161616;
    border-right: 1px solid #2D2D2D;
}

QTreeView#FileTree, QTreeView#FileList {
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: none;
    border-radius: 0px;
    selection-background-color: #1A2B2C;
    selection-color: #00D2DD;
    outline: none;
}
QTreeView#FileTree::item:hover, QTreeView#FileList::item:hover {
    background-color: #2D2D2D;
}
QTreeView#FileTree::item:selected, QTreeView#FileList::item:selected {
    background-color: #1A2B2C;
    color: #00D2DD;
}

QHeaderView::section {
    background-color: #2D2D2D;
    color: #E0E0E0;
    border: 1px solid #1A1A1A;
    padding: 4px;
}

QSplitter::handle {
    background-color: #2D2D2D;
}

QLineEdit {
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 4px 8px;
}
QLineEdit:focus {
    border: 1px solid #00ADB5;
}

QScrollBar:vertical {
    background: #1A1A1A;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3A3A3A;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #00ADB5;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

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

QFileDialog {
    background-color: #121212;
    color: #E0E0E0;
}

QFileDialog QListView, QFileDialog QTreeView, QFileDialog QTableView {
    background-color: #1A1A1A;
    color: #E0E0E0;
    border: 1px solid #2D2D2D;
    border-radius: 6px;
    selection-background-color: #1A2B2C;
    selection-color: #00D2DD;
    outline: none;
}

QFileDialog QListView::item:hover, QFileDialog QTreeView::item:hover {
    background-color: #2D2D2D;
}

QFileDialog QLabel {
    color: #AAAAAA;
}
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(MODERN_STYLE)
    window = Zip2PDF()
    window.show()
    sys.exit(app.exec())