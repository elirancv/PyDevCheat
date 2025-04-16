import sys
import re
import logging
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem,
                            QTextEdit, QSplitter, QLabel, QPushButton, QMessageBox,
                            QProgressBar, QStatusBar, QToolBar, QMenu, QStyledItemDelegate,
                            QFrame, QComboBox, QTabWidget, QTabBar, QGroupBox, QFormLayout,
                            QSpinBox, QDialogButtonBox, QDialog)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QRunnable, QThreadPool, QObject, QTimer, QPropertyAnimation, QEasingCurve, QRect, pyqtProperty
from PyQt6.QtGui import (QFont, QSyntaxHighlighter, QTextCharFormat, QColor,
                        QAction, QIcon, QPainter, QPainterPath, QLinearGradient, QKeySequence,
                        QShortcut, QPixmap)
import json
import os
from pathlib import Path
from .sources.tldr import TLDRSource
from .sources.cheatsh import CheatShSource
from .sources.devhints import DevhintsSource
import pyperclip
from .config import UI_CONFIG, DEFAULT_FONT, MONOSPACE_FONT, TREE_VIEW_CONFIG, CONTENT_VIEW_CONFIG
from .settings import settings_manager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Modern color scheme inspired by popular IDEs and tools
COLORS = {
    'background': '#0d1117',     # GitHub Dark theme background
    'sidebar': '#161b22',        # Slightly lighter background for sidebar
    'text': '#e6edf3',          # Bright text color
    'text_muted': '#8b949e',    # Muted text for secondary information
    'accent': '#58a6ff',        # Bright blue accent
    'accent_secondary': '#bc8cff',  # Purple accent for variety
    'border': '#30363d',        # Subtle border color
    'hover': '#1f2937',         # Hover state background
    'selection': '#2d3847',     # Selection background
    'code_bg': '#1f2428',       # Code block background
    'link': '#58a6ff',          # Link color
    'heading': '#e6edf3',       # Heading color
    'success': '#3fb950',       # Success green
    'warning': '#d29922',       # Warning orange
    'error': '#f85149',         # Error red
    'gradient_start': '#58a6ff', # Start of gradients
    'gradient_end': '#bc8cff',   # End of gradients
    'accent-hover': '#75a9ff',   # Hover state for accent button
    'accent-pressed': '#3f86e0', # Pressed state for accent button
    'background-light': '#242933', # Light background for search box
    'background-lighter': '#2d333e', # Even lighter background for search box
    'text-light': '#94a0b4',    # Light text color for search box
}

class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(str)  # Added progress signal for status updates

class Worker(QRunnable):
    """Worker thread for handling background tasks."""
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            logger.error(f"Error in worker thread: {str(e)}")
            self.signals.error.emit((str(e), ""))
        finally:
            self.signals.finished.emit()

    def update_progress(self, message):
        """Safely emit progress signal."""
        self.signals.progress.emit(message)

class SyncWorker(Worker):
    """Specialized worker for sync operations."""
    def run(self):
        try:
            results = {
                'tldr': False,
                'cheatsh': False,
                'devhints': False
            }
            
            # TLDR Pages sync
            try:
                self.update_progress("Downloading TLDR Pages repository...")
                results['tldr'] = self.fn.tldr_source.sync()
                self.update_progress("TLDR Pages synchronized successfully")
            except Exception as e:
                logger.error(f"Error syncing TLDR: {e}")
                self.update_progress(f"Error syncing TLDR: {str(e)}")
            
            # Cheat.sh sync
            try:
                self.update_progress("Updating Cheat.sh cache...")
                results['cheatsh'] = self.fn.cheatsh_source.sync() if hasattr(self.fn.cheatsh_source, 'sync') else True
                self.update_progress("Cheat.sh cache updated")
            except Exception as e:
                logger.error(f"Error syncing Cheat.sh: {e}")
                self.update_progress(f"Error syncing Cheat.sh: {str(e)}")
            
            # DevHints sync
            try:
                self.update_progress("Refreshing DevHints content...")
                results['devhints'] = self.fn.devhints_source.sync() if hasattr(self.fn.devhints_source, 'sync') else True
                self.update_progress("DevHints content refreshed")
            except Exception as e:
                logger.error(f"Error syncing DevHints: {e}")
                self.update_progress(f"Error syncing DevHints: {str(e)}")
            
            self.signals.result.emit(results)
        except Exception as e:
            logger.error(f"Error in sync worker: {str(e)}")
            self.signals.error.emit((str(e), ""))
        finally:
            self.signals.finished.emit()

    def sync_all_sources(self):
        """Synchronize all available sources."""
        try:
            self.statusBar().showMessage("Starting synchronization...")
            self.progress.setVisible(True)
            self.progress.setRange(0, 6)  # 2 steps per source
            self.progress.setValue(0)
            
            # Create and start sync worker
            worker = SyncWorker(self)
            worker.signals.progress.connect(self.on_sync_progress)
            worker.signals.result.connect(self.on_sync_complete)
            worker.signals.error.connect(self.on_sync_error)
            
            self.threadpool.start(worker)
            
        except Exception as e:
            logger.error(f"Error starting sync: {e}")
            self.statusBar().showMessage(f"Error starting sync: {str(e)}")
            self.progress.setVisible(False)
            QMessageBox.warning(self, "Sync Error",
                              f"Failed to start sync: {str(e)}")

    def on_sync_progress(self, message):
        """Handle sync progress updates."""
        self.statusBar().showMessage(message)
        current = self.progress.value()
        self.progress.setValue(current + 1)

    def on_sync_complete(self, results):
        """Handle successful sync of all sources."""
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        if success_count == total_count:
            self.statusBar().showMessage("✓ All sources synchronized successfully")
        else:
            failed_sources = [source for source, result in results.items() if not result]
            self.statusBar().showMessage(f"⚠ Sync completed with errors ({success_count}/{total_count} sources)")
            
            # Show detailed message if there were any failures
            if success_count < total_count:
                QMessageBox.warning(self, "Sync Warning",
                                  f"Failed to sync: {', '.join(failed_sources)}\nCheck the logs for details.")
        
        self.progress.setVisible(False)
        
        # Reload sources after successful sync
        if success_count > 0:
            self.statusBar().showMessage("Reloading sources after sync...")
            QTimer.singleShot(1000, self.load_sources)  # Give UI time to update

    def on_sync_error(self, error_info):
        """Handle sync errors."""
        error_msg = error_info[0]
        logger.error(f"Error during sync: {error_msg}")
        self.statusBar().showMessage(f"✕ Sync failed: {error_msg}")
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Sync Error",
                           f"Sync failed: {error_msg}\nCheck the logs for details.")

class SyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create formats with the correct font size
        self.formats = {
            'command': self._create_format(UI_CONFIG["colors"]["highlight"], True),
            'description': self._create_format(UI_CONFIG["colors"]["text"]),
            'example': self._create_format(UI_CONFIG["colors"]["accent"]),
            'comment': self._create_format('#7c7f93', italic=True),  # Muted color for comments
            'section': self._create_format(UI_CONFIG["colors"]["highlight"], True, size_adjust=1)  # Slightly larger
        }
        
    def _create_format(self, color, bold=False, italic=False, size_adjust=0):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        # Use the content font size as base and adjust if needed
        font_size = UI_CONFIG["font_sizes"]["content"] + size_adjust
        fmt.setFontPointSize(font_size)
        return fmt
        
    def highlightBlock(self, text):
        # Highlight section headers
        if text.startswith('#'):
            self.setFormat(0, len(text), self.formats['section'])
            return
            
        # Highlight commands and descriptions
        if '#' in text:
            command, description = text.split('#', 1)
            # Highlight command
            self.setFormat(0, len(command), self.formats['command'])
            # Highlight description
            self.setFormat(len(command) + 1, len(description), self.formats['description'])
        else:
            # If no #, treat as example or regular text
            if text.strip().startswith('$') or text.strip().startswith('>'):
                self.setFormat(0, len(text), self.formats['example'])
            else:
                self.setFormat(0, len(text), self.formats['description'])

class ModernProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(2)
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        self.animation.setDuration(1000)
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLORS['code_bg']};
                border: none;
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background-color: {COLORS['accent']};
                border-radius: 1px;
            }}
        """)

    def setProgress(self, value):
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.start()

class LoadingLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.dots = 0
        self.base_text = text
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dots)
        self.timer.start(500)
        self.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-family: 'Inter';
                font-size: 12px;
                padding: 4px 8px;
            }}
        """)

    def update_dots(self):
        self.dots = (self.dots + 1) % 4
        self.setText(f"{self.base_text}{'.' * self.dots}")

    def set_text(self, text):
        self.base_text = text
        self.update_dots()

    def stop(self):
        self.timer.stop()

class ModernButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['text']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent-hover']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent-pressed']};
            }}
        """)

class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search commands (e.g., 'git commit', 'python list')...")
        self.setStyleSheet(f"""
            SearchBox {{
                background-color: {COLORS['code_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 10px 36px;
                font-family: 'Inter';
                font-size: 14px;
                selection-background-color: {COLORS['selection']};
            }}
            SearchBox:focus {{
                border: 1px solid {COLORS['accent']};
                background-color: {COLORS['background']};
            }}
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.threadpool = QThreadPool()
        logger.debug(f"Multithreading with maximum {self.threadpool.maxThreadCount()} threads")
        
        # Initialize state
        self.sources_loaded = False
        self.loading_complete_count = 0
        
        # Load settings
        self.font_sizes = settings_manager.get_font_sizes()
        
        # Update default fonts with loaded settings
        DEFAULT_FONT.setPointSize(self.font_sizes["content"])
        MONOSPACE_FONT.setPointSize(self.font_sizes["content"])
        
        # Store references to loading widgets
        self.loading_widgets = {}
        
        # Initialize sources
        self.tldr_source = TLDRSource()
        self.cheatsh_source = CheatShSource()
        self.devhints_source = DevhintsSource()
        
        # Set window icon and logo path
        self.logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "logo-64.png")
        if os.path.exists(self.logo_path):
            app_icon = QIcon(self.logo_path)
            self.setWindowIcon(app_icon)
            if sys.platform == 'win32':
                import ctypes
                myappid = 'elirancv.pydevcheat.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
        
        self.init_ui()
        self.load_sources()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Search focus shortcut (Ctrl+F or Cmd+F)
        self.search_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        self.search_shortcut.activated.connect(self.focus_search)
        
        # Clear search shortcut (Esc)
        self.clear_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.clear_shortcut.activated.connect(self.clear_search)
        
        # Copy shortcut (Ctrl+C or Cmd+C)
        self.copy_shortcut = QShortcut(QKeySequence.StandardKey.Copy, self)
        self.copy_shortcut.activated.connect(self.copy_content)

    def focus_search(self):
        """Focus the search box."""
        self.search_box.setFocus()
        self.search_box.selectAll()

    def copy_content(self):
        """Copy selected content to clipboard."""
        cursor = self.content.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
        else:
            text = self.content.toPlainText()
        
        if text:
            pyperclip.copy(text)
            self.statusBar().showMessage("Content copied to clipboard!", 2000)

    def keyPressEvent(self, event):
        """Handle keyboard events."""
        if event.key() == Qt.Key.Key_Up:
            # Navigate up in tree
            current = self.tree.currentItem()
            if current:
                index = self.tree.indexAbove(self.tree.currentIndex())
                if index.isValid():
                    self.tree.setCurrentIndex(index)
                    self.on_item_clicked(self.tree.itemFromIndex(index), 0)
        elif event.key() == Qt.Key.Key_Down:
            # Navigate down in tree
            current = self.tree.currentItem()
            if current:
                index = self.tree.indexBelow(self.tree.currentIndex())
                if index.isValid():
                    self.tree.setCurrentIndex(index)
                    self.on_item_clicked(self.tree.itemFromIndex(index), 0)
        else:
            super().keyPressEvent(event)

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("PyDevCheat - Your Programming Companion")
        self.setMinimumSize(800, 600)
        
        # Set application-wide font
        app_font = QFont("Inter", self.font_sizes["content"])
        QApplication.setFont(app_font)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create modern toolbar
        self.create_toolbar()

        # Create main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
            }}
            QSplitter::handle:hover {{
                background-color: {COLORS['accent']};
            }}
        """)

        # Create sidebar
        sidebar = QWidget()
        sidebar.setMinimumWidth(280)
        sidebar.setMaximumWidth(320)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['sidebar']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Add progress bar
        self.progress = ModernProgressBar()
        self.progress.setVisible(False)
        sidebar_layout.addWidget(self.progress)

        # Create tree widget with improved styling
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setIndentation(16)
        self.tree.setItemsExpandable(True)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setVerticalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tree.setFrameShape(QFrame.Shape.NoFrame)
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS['sidebar']};
                border: none;
                font-family: 'Inter';
                font-size: {self.font_sizes["source_list"]}pt;
                padding: 8px 4px;
            }}
            QTreeWidget::item {{
                color: {COLORS['text']};
                padding: 8px;
                margin: 2px 4px;
                border-radius: 6px;
            }}
            QTreeWidget::item:hover {{
                background-color: {COLORS['hover']};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS['selection']};
                color: {COLORS['accent']};
            }}
            QTreeWidget::branch {{
                background: transparent;
                border: none;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: url(assets/icons/chevron-right.png);
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: url(assets/icons/chevron-down.png);
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 16px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                min-height: 30px;
                border-radius: 7px;
                margin: 2px 4px 2px 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['accent']};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
                height: 0px;
            }}
        """)
        sidebar_layout.addWidget(self.tree)

        # Initialize root items with minimal styling
        def create_root_item(name):
            """Create a root item with proper styling."""
            item = QTreeWidgetItem(self.tree)
            item.setData(0, Qt.ItemDataRole.UserRole, name)  # Store original name
            font = QFont("Inter", self.font_sizes["source_header"])  # Use loaded font size
            font.setBold(True)
            item.setFont(0, font)
            return item

        # Create root items without icons
        self.tldr_root = create_root_item("TLDR Pages")
        self.cheatsh_root = create_root_item("Cheat.sh")
        self.devhints_root = create_root_item("DevHints")

        # Update initial counts
        self.update_root_item_count(self.tldr_root, 0)
        self.update_root_item_count(self.cheatsh_root, 0)
        self.update_root_item_count(self.devhints_root, 0)

        # Create loading widgets
        def create_loading_item(parent, source_name):
            loading_label = LoadingLabel(f"Loading {source_name}...")
            loading_item = QTreeWidgetItem(parent)
            self.tree.setItemWidget(loading_item, 0, loading_label)
            self.loading_widgets[source_name] = {
                'label': loading_label,
                'item': loading_item,
                'parent': parent
            }
            return loading_item

        create_loading_item(self.tldr_root, "TLDR Pages")
        create_loading_item(self.cheatsh_root, "Cheat.sh")
        create_loading_item(self.devhints_root, "DevHints")

        # Create content area
        content_area = QWidget()
        content_area.setMinimumWidth(400)
        content_area.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
            }}
        """)
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(16, 0, 16, 16)  # Removed top margin
        content_layout.setSpacing(8)  # Reduced spacing between elements

        # Add title
        self.content_title = QLabel("")
        self.content_title.setStyleSheet("QLabel { color: " + COLORS['text'] + "; font-family: Inter; font-size: 14px; font-weight: bold; }")
        content_layout.addWidget(self.content_title)
        
        # Add content display
        content_display = self.setup_content_display()
        content_layout.addWidget(content_display)
        
        # Add panels to splitter
        splitter.addWidget(sidebar)
        splitter.addWidget(content_area)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)

        # Create status bar
        self.statusBar().showMessage("Loading sources...")
        self.statusBar().setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['sidebar']};
                color: {COLORS['text_muted']};
                border-top: 1px solid {COLORS['border']};
                padding: 2px 8px;
                font-family: 'Inter';
                font-size: 12px;
            }}
        """)

        # Show welcome screen
        self.show_home_screen()

    def create_toolbar(self):
        """Create a premium modern toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFixedHeight(48)
         
        # Create main container with gradient background
        container = QWidget()
        container.setFixedHeight(48)
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
         
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)
         
        # Create logo section
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setSpacing(8)

        # Add app icon/logo
        logo_label = QLabel()
        logo_pixmap = QPixmap(self.logo_path)
        logo_label.setPixmap(logo_pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setStyleSheet("QLabel { padding: 0; background: transparent; }")
        logo_layout.addWidget(logo_label)

        # Add app name
        app_name = QLabel("PyDevCheat")
        app_name.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']};
                font-family: 'Inter';
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }}
        """)
        logo_layout.addWidget(app_name)
        layout.addWidget(logo_container)

        # Create button container with subtle background
        button_container = QWidget()
        button_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['sidebar']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(4, 0, 4, 0)
        button_layout.setSpacing(4)
        
        # Create and add buttons with modern icons
        class ModernToolButton(QPushButton):
            def __init__(self, icon, tooltip, parent=None):
                super().__init__(parent)
                self.setFixedSize(32, 32)
                self.setText(icon)
                self.setToolTip(tooltip)
                self.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS['text_muted']};
                        border: none;
                        border-radius: 6px;
                        font-size: 18px;  /* Increased font size */
                        padding: 0;
                        font-family: 'Segoe UI Symbol', 'Apple Symbols', sans-serif;  /* Better icon fonts */
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['hover']};
                        color: {COLORS['text']};
                    }}
                    QPushButton:pressed {{
                        background-color: {COLORS['selection']};
                        color: {COLORS['accent']};
                    }}
                """)
        
        # Add left side buttons
        home_btn = ModernToolButton("⌂", "Home (Welcome Screen)")
        home_btn.clicked.connect(self.show_home_screen)
        button_layout.addWidget(home_btn)
        
        refresh_btn = ModernToolButton("↻", "Refresh (Reload Commands)")
        refresh_btn.clicked.connect(self.load_sources)
        button_layout.addWidget(refresh_btn)
        
        sync_btn = ModernToolButton("⟳", "Sync (Update Sources)")
        sync_btn.clicked.connect(self.sync_all_sources)
        button_layout.addWidget(sync_btn)

        copy_btn = ModernToolButton("⎘", "Copy (Ctrl+C)")
        copy_btn.clicked.connect(self.copy_content)
        button_layout.addWidget(copy_btn)
        
        # Add the button container to main layout
        layout.addWidget(button_container)

        # Add stretching space before search
        layout.addStretch()

        # Add search box in the middle
        search_container = QWidget()
        search_container.setFixedWidth(400)  # Increased width
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        search_wrapper = QWidget()
        search_wrapper.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['sidebar']};
                border-radius: 6px;
            }}
        """)
        search_wrapper_layout = QHBoxLayout(search_wrapper)
        search_wrapper_layout.setContentsMargins(12, 6, 12, 6)  # Increased padding
        search_wrapper_layout.setSpacing(8)  # Increased spacing

        self.search_icon = QLabel("🔍")
        self.search_icon.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-size: 16px;
                background: transparent;
            }}
            QLabel:hover {{
                color: {COLORS['text']};
            }}
        """)
        self.search_icon.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_icon.mousePressEvent = self.clear_search
        search_wrapper_layout.addWidget(self.search_icon)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search commands...")
        self.search_box.textChanged.connect(self.on_search)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                border: none;
                color: {COLORS['text']};
                font-family: 'Inter';
                font-size: 14px;
                padding: 4px;
                min-width: 300px;  /* Ensure minimum width */
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_muted']};
            }}
        """)
        search_wrapper_layout.addWidget(self.search_box)

        search_layout.addWidget(search_wrapper)
        layout.addWidget(search_container)

        # Add stretching space after search
        layout.addStretch()

        # Create right-side button container
        right_button_container = QWidget()
        right_button_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['sidebar']};
                border-radius: 8px;
                padding: 4px;
            }}
        """)
        right_button_layout = QHBoxLayout(right_button_container)
        right_button_layout.setContentsMargins(4, 0, 4, 0)
        right_button_layout.setSpacing(4)

        settings_btn = ModernToolButton("⚙", "Settings")
        settings_btn.clicked.connect(self.show_settings)
        right_button_layout.addWidget(settings_btn)
        
        # Add the right button container to main layout
        layout.addWidget(right_button_container)
        
        # Add version label
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text_muted']};
                font-family: 'Inter';
                font-size: 12px;
                background: transparent;
                margin-left: 8px;
            }}
        """)
        layout.addWidget(version_label)
        
        # Set the container as the toolbar widget
        toolbar.setStyleSheet("""
            QToolBar {
                border: none;
                spacing: 0px;
                padding: 0px;
            }
        """)
        toolbar.addWidget(container)
        self.addToolBar(toolbar)

    def show_home_screen(self):
        """Show the home screen with welcome message."""
        self.content_title.setText("Welcome to PyDevCheat")
        
        # Get command counts
        counts = self.get_total_commands()
        is_loading = counts['status'] == 'loading'
        count_data = counts['counts']
        
        # Create welcome screen HTML with modern styling
        welcome_html = f"""<html><style>
            body {{
                color: {COLORS['text']};
                font-family: 'Inter', sans-serif;
                line-height: 1.6;
                padding: 16px 24px;
                margin: 0;
                background: {COLORS['background']};
            }}
            .section {{
                background: {COLORS['sidebar']};
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 16px;
            }}
            .section-title {{
                color: {COLORS['accent']};
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                white-space: nowrap;
            }}
            .section-title .emoji {{
                margin-right: 8px;
                font-size: 18px;
            }}
            .content {{
                margin-left: 24px;
            }}
            .stats-table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                margin: 12px 0;
                background: {COLORS['background']};
                border-radius: 6px;
                overflow: hidden;
            }}
            .stats-table td {{
                padding: 10px 12px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            .stats-table tr:last-child td {{
                border-bottom: none;
            }}
            .stats-table .source {{
                color: {COLORS['text']};
                font-weight: 500;
                white-space: nowrap;
            }}
            .stats-table .count {{
                color: {COLORS['accent']};
                font-family: 'JetBrains Mono', monospace;
                text-align: right;
                padding: 4px 8px;
                background: {COLORS['code_bg']};
                border-radius: 4px;
                min-width: 60px;
                display: inline-block;
            }}
            .stats-table .description {{
                color: {COLORS['text_muted']};
                padding-left: 16px;
                width: 100%;
            }}
            .stats-table .total-row {{
                font-weight: bold;
                background: {COLORS['code_bg']};
            }}
            .stats-table .total-row .count {{
                color: {COLORS['accent_secondary']};
                background: {COLORS['selection']};
            }}
            .stats-table .loading {{
                color: {COLORS['text_muted']};
                font-style: italic;
            }}
            ul {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            li {{
                margin: 6px 0;
                padding-left: 16px;
                position: relative;
                line-height: 1.5;
            }}
            li::before {{
                content: "•";
                color: {COLORS['accent']};
                position: absolute;
                left: 0;
            }}
            .code {{
                color: {COLORS['accent']};
                background: {COLORS['code_bg']};
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.9em;
                white-space: nowrap;
            }}
            .indent {{
                margin-left: 16px;
                color: {COLORS['text_muted']};
                font-size: 0.95em;
            }}
        </style>
        <body>
            <div class="section">
                <div class="section-title"><span class="emoji">📊</span> Command Sources</div>
                <div class="content">
                    <table class="stats-table">
                        <tr>
                            <td class="source">TLDR Pages</td>
                            <td class="count">{count_data['tldr']}</td>
                            <td class="description">Simplified and practical command examples</td>
                        </tr>
                        <tr>
                            <td class="source">Cheat.sh</td>
                            <td class="count">{count_data['cheatsh']}</td>
                            <td class="description">Community-driven cheat sheets and snippets</td>
                        </tr>
                        <tr>
                            <td class="source">DevHints</td>
                            <td class="count">{count_data['devhints']}</td>
                            <td class="description">Quick reference guides for developers</td>
                        </tr>
                        <tr class="total-row">
                            <td class="source">Total Commands</td>
                            <td class="count">{count_data['total']}</td>
                            <td class="description">{'Loading sources...' if is_loading else 'Ready to use'}</td>
                        </tr>
                    </table>
                </div>
            </div>

            <div class="section">
                <div class="section-title"><span class="emoji">🚀</span> Quick Start</div>
                <div class="content">
                    <ul>
                        <li>Type in the search box above to find commands<div class="indent">Example: <span class="code">git commit</span> or <span class="code">docker run</span></div></li>
                        <li>Browse categories in the sidebar</li>
                        <li>Right-click items to expand/collapse sections</li>
                    </ul>
                </div>
            </div>

            <div class="section">
                <div class="section-title"><span class="emoji">💡</span> Pro Tips</div>
                <div class="content">
                    <ul>
                        <li>Use specific terms for better results<div class="indent">Example: <span class="code">python list comprehension</span></div></li>
                        <li>Press Enter to search across all sources</li>
                        <li>Click any command for detailed usage</li>
                    </ul>
                </div>
            </div>

            <div class="section">
                <div class="section-title"><span class="emoji">⌨️</span> Shortcuts</div>
                <div class="content">
                    <ul>
                        <li><span class="code">Ctrl/Cmd + F</span>: Focus search</li>
                        <li><span class="code">Esc</span>: Clear search</li>
                        <li><span class="code">Up/Down</span>: Navigate results</li>
                    </ul>
                </div>
            </div>
        </body></html>"""
        
        self.content.setHtml(welcome_html)
        self.statusBar().showMessage("Ready" if not is_loading else "Loading sources...")

    def load_sources(self):
        """Load command sources in background threads."""
        logger.debug("Loading sources...")
        
        # Reset loading state
        self.sources_loaded = False
        self.loading_complete_count = 0
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.statusBar().showMessage("Loading sources...")

        # Clear existing items
        self.tldr_root.takeChildren()
        self.cheatsh_root.takeChildren()
        self.devhints_root.takeChildren()

        # Reset counts
        self.update_root_item_count(self.tldr_root, 0)
        self.update_root_item_count(self.cheatsh_root, 0)
        self.update_root_item_count(self.devhints_root, 0)

        # Start workers
        worker = Worker(self.load_tldr_commands)
        worker.signals.result.connect(self.on_tldr_loaded)
        worker.signals.error.connect(lambda err: self.on_load_error((str(err[0]), "TLDR")))
        self.threadpool.start(worker)
        
        worker = Worker(self.load_cheatsh_commands)
        worker.signals.result.connect(self.on_cheatsh_loaded)
        worker.signals.error.connect(lambda err: self.on_load_error((str(err[0]), "Cheat.sh")))
        self.threadpool.start(worker)
        
        worker = Worker(self.load_devhints_commands)
        worker.signals.result.connect(self.on_devhints_loaded)
        worker.signals.error.connect(lambda err: self.on_load_error((str(err[0]), "DevHints")))
        self.threadpool.start(worker)

    def load_tldr_commands(self) -> Dict[str, List[str]]:
        """Load TLDR commands."""
        logger.debug("Loading TLDR commands...")
        try:
            commands = self.tldr_source.list_all_commands()
            if not commands:
                raise Exception("No TLDR commands found. Try syncing the repository first.")
            return commands
        except Exception as e:
            logger.error(f"Error loading TLDR commands: {e}")
            raise

    def load_cheatsh_commands(self) -> Dict[str, str]:
        """Load Cheat.sh commands in a worker thread."""
        try:
            return self.cheatsh_source.list_all_topics()
        except Exception as e:
            logger.error(f"Error loading Cheat.sh topics: {e}")
            raise

    def load_devhints_commands(self) -> Dict[str, List[str]]:
        """Load DevHints commands in a worker thread."""
        try:
            logger.debug("Initializing DevhintsSource...")
            topics = self.devhints_source.list_all_topics()
            logger.debug(f"Got {len(topics)} topics from DevhintsSource")
            return topics
        except Exception as e:
            logger.error(f"Error loading DevHints topics: {e}")
            raise

    def cleanup_loading_widget(self, source_name):
        """Safely cleanup loading widget for a source."""
        if source_name in self.loading_widgets:
            try:
                widgets = self.loading_widgets[source_name]
                if widgets['label']:
                    widgets['label'].stop()
                if widgets['item'] and widgets['parent']:
                    idx = widgets['parent'].indexOfChild(widgets['item'])
                    if idx >= 0:
                        widgets['parent'].takeChild(idx)
                self.loading_widgets[source_name] = {'label': None, 'item': None, 'parent': None}
            except Exception as e:
                logger.error(f"Error cleaning up loading widget for {source_name}: {e}")

    def update_root_item_count(self, item, count):
        """Update root item text with properly formatted count."""
        original_name = item.data(0, Qt.ItemDataRole.UserRole)
        formatted_count = f"{count:,}" if count > 0 else "0"  # Add commas for thousands
        # Use a more subtle formatting for the count
        item.setText(0, f"{original_name}  {formatted_count}")
        item.setForeground(0, QColor(COLORS['text_muted']))

    def on_tldr_loaded(self, commands):
        """Handle loaded TLDR commands."""
        try:
            logger.debug(f"TLDR commands loaded: {len(commands)} commands")
            
            # Stop loading animation and remove loading item
            self.cleanup_loading_widget("TLDR Pages")
            
            # Create a flat list of all commands with their platforms
            command_list = []
            for command, platforms in commands.items():
                if isinstance(platforms, list):
                    platform_str = ", ".join(sorted(platforms))
                else:
                    platform_str = str(platforms)
                command_list.append((command, platform_str))
            
            # Sort commands alphabetically
            command_list.sort(key=lambda x: x[0].lower())
            
            # Add commands directly under root
            for command, platforms in command_list:
                cmd_item = QTreeWidgetItem(self.tldr_root)
                cmd_item.setText(0, command)
                cmd_item.setToolTip(0, f"Platforms: {platforms}")
            
            # Update root text with count
            self.update_root_item_count(self.tldr_root, len(command_list))
            
            self.tldr_root.setExpanded(True)
            self.loading_complete_count += 1
            self.check_loading_complete()
            
        except Exception as e:
            logger.error(f"Error processing TLDR commands: {e}")
            self.on_load_error((str(e), "TLDR"))

    def on_cheatsh_loaded(self, topics):
        """Handle Cheat.sh topics loaded."""
        try:
            # Stop loading animation and remove loading item
            self.cleanup_loading_widget("Cheat.sh")
            
            # Create a flat list of topics
            topic_list = []
            if isinstance(topics, dict):
                for topic, desc in topics.items():
                    topic_list.append(topic)
            else:
                topic_list = list(topics)
            
            # Sort topics alphabetically
            topic_list.sort(key=str.lower)
            
            # Add topics directly under root
            for topic in topic_list:
                topic_item = QTreeWidgetItem(self.cheatsh_root)
                topic_item.setText(0, topic)
            
            # Update root text with count
            self.update_root_item_count(self.cheatsh_root, len(topic_list))
            
            self.cheatsh_root.setExpanded(True)
            self.loading_complete_count += 1
            self.check_loading_complete()
            
        except Exception as e:
            logger.error(f"Error processing Cheat.sh topics: {e}")
            self.on_load_error((str(e), "Cheat.sh"))

    def on_devhints_loaded(self, topics):
        """Handle DevHints topics loaded."""
        try:
            # Create a flat list of topics
            topic_list = []
            if isinstance(topics, dict):
                for topic, desc in topics.items():
                    # Clean up topic name
                    clean_topic = topic.split('/')[-1] if '/' in topic else topic
                    clean_topic = clean_topic.replace('-', ' ').replace('_', ' ').strip()
                    topic_list.append((clean_topic, topic))  # Store original topic for lookup
            else:
                topic_list = [(topic, topic) for topic in topics]
            
            # Sort topics alphabetically
            topic_list.sort(key=lambda x: x[0].lower())
            
            # Add topics directly under root
            for display_topic, original_topic in topic_list:
                topic_item = QTreeWidgetItem(self.devhints_root)
                topic_item.setText(0, display_topic)
                topic_item.setData(0, Qt.ItemDataRole.UserRole, original_topic)
            
            # Update root text with count
            self.update_root_item_count(self.devhints_root, len(topic_list))
            
            # Stop loading animation and remove loading item
            self.cleanup_loading_widget("DevHints")
            
            self.devhints_root.setExpanded(True)
            self.loading_complete_count += 1
            self.check_loading_complete()
            
        except Exception as e:
            logger.error(f"Error processing DevHints topics: {e}")
            self.on_load_error((str(e), "DevHints"))

    def check_loading_complete(self):
        """Check if all sources are loaded."""
        try:
            # Get counts for each source
            tldr_count = self.count_items(self.tldr_root)
            cheatsh_count = self.count_items(self.cheatsh_root)
            devhints_count = self.count_items(self.devhints_root)
            total = tldr_count + cheatsh_count + devhints_count

            # Check if all three sources have completed loading
            if self.loading_complete_count >= 3:
                self.sources_loaded = True
                self.progress.setVisible(False)
                
                if total > 0:
                    self.statusBar().showMessage(f"Ready - {total:,} commands available")
                else:
                    self.statusBar().showMessage("No commands loaded. Try syncing sources.")
                
                # Update the welcome screen to reflect current counts
                self.show_home_screen()
            
        except Exception as e:
            logger.error(f"Error checking loading complete: {e}")
            self.statusBar().showMessage("Error checking loading status")

    def on_load_error(self, error_info):
        """Handle loading errors."""
        error_msg, source = error_info
        logger.error(f"Error loading {source}: {error_msg}")
        
        # Map source to root item
        source_map = {
            "TLDR": self.tldr_root,
            "Cheat.sh": self.cheatsh_root,
            "DevHints": self.devhints_root
        }
        
        if source in source_map:
            root_item = source_map[source]
            root_item.setText(0, f"{source} (Error: {error_msg})")
        
        self.statusBar().showMessage(f"Error loading {source}")
        self.check_loading_complete()

    def on_search_text_changed(self, text):
        """Handle search text changes."""
        # Update search icon
        self.search_icon.setText("✕" if text else "🔍")
        # Call the original search function
        self.on_search(text)

    def on_search(self, text):
        """Filter tree items based on search text."""
        try:
            # Update search icon
            self.search_icon.setText("✕" if text else "🔍")
            self.search_icon.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text_muted' if not text else 'text']};
                    font-size: 16px;
                    background: transparent;
                }}
                QLabel:hover {{
                    color: {COLORS['text']};
                }}
            """)
            
            text = text.lower()
            # Create variations of the search term
            search_variations = {text}  # Original search
            if '-' in text:
                # Add space version of hyphenated search
                search_variations.add(text.replace('-', ' '))
            elif ' ' in text:
                # Add hyphenated version of space-separated search
                search_variations.add(text.replace(' ', '-'))

            matches = 0
            total_items = 0
            
            def filter_item(item):
                nonlocal matches, total_items
                # Check if this item matches any variation of the search term
                item_text = item.text(0).lower()
                matches_self = any(variation in item_text for variation in search_variations)
                
                # Don't count root items in total
                if item.parent():
                    total_items += 1
                    if matches_self:
                        matches += 1
                
                # Check children
                matches_children = False
                for i in range(item.childCount()):
                    if filter_item(item.child(i)):
                        matches_children = True
                
                # Show/hide based on matches
                should_show = matches_self or matches_children
                item.setHidden(not should_show)
                
                # Expand if there are matches
                if should_show:
                    # Expand this item if it has matching children
                    if matches_children:
                        item.setExpanded(True)
                    # Also expand all parents
                    parent = item.parent()
                    while parent:
                        parent.setExpanded(True)
                        parent = parent.parent()
                else:
                    # Collapse if no matches
                    item.setExpanded(False)
                
                return should_show
            
            # Process all top-level items
            for i in range(self.tree.topLevelItemCount()):
                filter_item(self.tree.topLevelItem(i))
            
            # Update status bar with search results
            if text:
                if matches == 0:
                    self.statusBar().showMessage(f"No matches found for '{text}'")
                else:
                    self.statusBar().showMessage(f"Found {matches} matches for '{text}'")
            else:
                self.update_status_message()
                
        except Exception as e:
            logger.error(f"Error in search: {e}")
            self.statusBar().showMessage(f"Search error: {str(e)}")

    def clear_search(self, event=None):
        """Clear the search box and reset tree view."""
        if self.search_box.text():  # Only clear if there's text
            self.search_box.clear()
            self.search_icon.setText("🔍")
            self.search_icon.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['text_muted']};
                    font-size: 16px;
                    background: transparent;
                }}
                QLabel:hover {{
                    color: {COLORS['text']};
                }}
            """)
            self.reset_tree_visibility()
            self.update_status_message()

    def update_status_message(self):
        """Update status bar with current state."""
        try:
            if not self.sources_loaded:
                self.statusBar().showMessage("Loading sources...")
                return
                
            # Count total items per source
            tldr_count = self.count_items(self.tldr_root)
            cheatsh_count = self.count_items(self.cheatsh_root)
            devhints_count = self.count_items(self.devhints_root)
            
            total_count = tldr_count + cheatsh_count + devhints_count
            
            if total_count == 0:
                self.statusBar().showMessage("No commands loaded. Try syncing sources.")
            else:
                self.statusBar().showMessage(
                    f"Ready - {total_count} commands available "
                    f"(TLDR: {tldr_count}, Cheat.sh: {cheatsh_count}, DevHints: {devhints_count})"
                )
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            self.statusBar().showMessage("Ready")

    def count_items(self, root_item):
        """Count non-root items under a root item."""
        try:
            if not root_item:
                return 0
                
            count = 0
            for i in range(root_item.childCount()):
                child = root_item.child(i)
                # Skip loading widgets and hidden items
                if not self.tree.itemWidget(child, 0) and not child.isHidden():
                    # Only count leaf nodes (actual commands)
                    if child.childCount() == 0:
                        count += 1
                    else:
                        # For non-leaf nodes, recursively count their children
                        count += self.count_items(child)
            return count
        except Exception as e:
            logger.error(f"Error counting items: {e}")
            return 0

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle tree item click."""
        try:
            # Get the root item
            root = item
            while root.parent():
                root = root.parent()

            # Get the source and command
            source = root.text(0).split(" (")[0].lower()
            command = item.text(0)
            
            # For DevHints, use the stored original topic
            if source == "devhints":
                command = item.data(0, Qt.ItemDataRole.UserRole) or command
            
            # Only load content if this is a leaf item (not a root)
            if item != root:
                self.statusBar().showMessage(f"Loading '{command}'...")
                if source.startswith("tldr"):
                    self.load_content("tldr", command)
                elif source.startswith("cheat.sh"):
                    self.load_content("cheatsh", command)
                elif source.startswith("devhints"):
                    self.load_content("devhints", command)
            
        except Exception as e:
            logger.error(f"Error in on_item_clicked: {e}")
            self.statusBar().showMessage(f"Error loading content: {str(e)}")

    def setup_content_display(self):
        """Set up the content display area."""
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Add title bar
        title_container = QWidget()
        title_container.setFixedHeight(44)
        title_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(16, 0, 16, 0)

        self.content_title = QLabel("")
        self.content_title.setStyleSheet("QLabel { color: " + COLORS['text'] + "; font-family: Inter; font-size: 14px; font-weight: bold; }")
        title_layout.addWidget(self.content_title)
        title_layout.addStretch()

        content_layout.addWidget(title_container)

        # Create content text edit with syntax highlighting
        self.content = QTextEdit()
        self.content.setReadOnly(True)
        self.highlighter = SyntaxHighlighter(self.content.document())
        self.content.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: none;
                font-family: 'JetBrains Mono';
                font-size: {self.font_sizes["content"]}pt;
                selection-background-color: {COLORS['selection']};
                selection-color: {COLORS['text']};
                padding: 0;
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 16px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                min-height: 30px;
                border-radius: 7px;
                margin: 2px 4px 2px 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {COLORS['accent']};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background-color: transparent;
                height: 16px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {COLORS['border']};
                min-width: 30px;
                border-radius: 7px;
                margin: 4px 2px 4px 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {COLORS['accent']};
            }}
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {{
                background: none;
                width: 0px;
            }}
        """)

        content_layout.addWidget(self.content)
        return content_container

    def format_content(self, content: str) -> str:
        """Format the content for better display."""
        if not content:
            return ""
            
        lines = content.split('\n')
        formatted_lines = []
        current_section = None
        in_table = False
        
        for line in lines:
            line = line.strip()
            if not line:
                if formatted_lines and not formatted_lines[-1] == "":
                    formatted_lines.append("")
                continue
            
            # Handle markdown table (usually in header)
            if line.startswith('|'):
                if not in_table:
                    in_table = True
                    # Extract title and intro if this is the header table
                    parts = line.split('|')
                    if len(parts) >= 3:
                        title = parts[1].strip()
                        intro = parts[2].strip()
                        if title and intro:
                            formatted_lines.append(f"# {title}")
                            formatted_lines.append("─" * 50)
                            formatted_lines.append(f"{intro}")
                            formatted_lines.append("")
                continue
            elif in_table:
                in_table = False
                continue
                
            # Handle section headers (> text)
            if line.startswith('>'):
                if formatted_lines:
                    formatted_lines.append("")
                section_name = line[1:].strip()
                formatted_lines.append(f"## {section_name}")
                formatted_lines.append("─" * 30)
                current_section = section_name
                continue
            
            # Handle regular command lines
            if line.startswith('`'):
                # Clean up command line
                cmd = line.strip('`')
                # Extract command and description
                parts = cmd.split('#', 1)
                command = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
                
                # Format command with description
                if description:
                    formatted_lines.append(f"{command}  # {description}")
                else:
                    formatted_lines.append(command)
            elif line.startswith('#'):
                # Handle markdown headers
                if formatted_lines:
                    formatted_lines.append("")
                formatted_lines.append(line)
                formatted_lines.append("─" * 50)
            else:
                # Regular text (probably description)
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)

    def load_content(self, source: str, command: str) -> Optional[str]:
        """Load content for a command."""
        logger.debug(f"Loading content for {source}:{command}")
        self.statusBar().showMessage(f"Loading {command}...")
        
        # Clear previous content
        self.content.clear()
        self.content_title.setText(command)
        
        worker = Worker(self._load_content_worker, source, command)
        worker.signals.result.connect(self._handle_content_result)
        worker.signals.error.connect(lambda err: self.on_content_error(err, command))
        self.threadpool.start(worker)

    def _handle_content_result(self, result):
        """Handle the content loading result."""
        if isinstance(result, tuple):
            source, content = result
            if source == "tldr":
                self.display_tldr_content(content)
            elif source == "cheatsh":
                self.display_cheatsh_content(content)
            elif source == "devhints":
                self.display_devhints_content(content)
        else:
            self.display_content(result)
        self.update_status_message()  # Update status after content is displayed

    def _load_content_worker(self, source: str, command: str) -> tuple:
        """Worker function to load content."""
        try:
            if source == "tldr":
                content = self.tldr_source.search(command)
                return ("tldr", content)
            elif source == "cheatsh":
                content = self.cheatsh_source.search(command)
                return ("cheatsh", content)
            elif source == "devhints":
                content = self.devhints_source.search(command)
                return ("devhints", content)
            else:
                raise ValueError(f"Unknown source: {source}")
        except Exception as e:
            logger.error(f"Error loading content for {source}:{command}: {e}")
            raise

    def display_tldr_content(self, content):
        """Display TLDR content with proper formatting."""
        if not content:
            self.display_error("No TLDR content available")
            return
            
        self.content_title.setText("TLDR Pages")
        formatted_content = self.format_content(content)
        self.content.clear()
        self.content.setPlainText(formatted_content.lstrip())  # Remove leading whitespace
        self.statusBar().showMessage("Ready")
        
    def display_cheatsh_content(self, content):
        """Display Cheat.sh content with proper formatting."""
        if not content:
            self.display_error("No Cheat.sh content available")
            return
            
        self.content_title.setText("Cheat.sh")
        formatted_content = self.format_content(content)
        self.content.clear()
        self.content.setPlainText(formatted_content.lstrip())  # Remove leading whitespace
        self.statusBar().showMessage("Ready")
        
    def display_devhints_content(self, content):
        """Display DevHints content with proper formatting."""
        if not content:
            self.display_error("No DevHints content available")
            return
            
        self.content_title.setText("DevHints")
        formatted_content = self.format_content(content)
        self.content.clear()
        self.content.setPlainText(formatted_content.lstrip())  # Remove leading whitespace
        self.statusBar().showMessage("Ready")
        
    def display_search_results(self, results):
        """Display search results with proper formatting."""
        if not results:
            self.display_error("No search results found")
            return
            
        self.content_title.setText("Search Results")
        self.content.clear()
        self.content.setPlainText(results)
        self.statusBar().showMessage("Search completed")
        
    def display_error(self, error_message):
        """Display error message with proper formatting."""
        self.content_title.setText("Error")
        self.content.clear()
        error_html = f"""
        <html>
        <body style="color: {COLORS['error']}; font-family: 'Inter'; padding: 20px;">
            <h3 style="margin: 0;">❌ Error</h3>
            <p style="margin: 10px 0;">{error_message}</p>
        </body>
        </html>
        """
        self.content.setHtml(error_html)
        self.statusBar().showMessage(f"Error: {error_message}")

    def on_content_error(self, error_info: tuple, command: str):
        """Handle content loading error."""
        error_msg = error_info[0]
        self.statusBar().showMessage(f"Error loading '{command}': {error_msg}")
        self.content.setPlainText(f"Error loading content:\n{error_msg}")

    def sync_all_sources(self):
        """Synchronize all available sources."""
        try:
            self.statusBar().showMessage("Starting synchronization...")
            self.progress.setVisible(True)
            self.progress.setRange(0, 6)  # 2 steps per source
            self.progress.setValue(0)
            
            # Create and start sync worker
            worker = SyncWorker(self)
            worker.signals.progress.connect(self.on_sync_progress)
            worker.signals.result.connect(self.on_sync_complete)
            worker.signals.error.connect(self.on_sync_error)
            
            self.threadpool.start(worker)
            
        except Exception as e:
            logger.error(f"Error starting sync: {e}")
            self.statusBar().showMessage(f"Error starting sync: {str(e)}")
            self.progress.setVisible(False)
            QMessageBox.warning(self, "Sync Error",
                              f"Failed to start sync: {str(e)}")

    def on_sync_progress(self, message):
        """Handle sync progress updates."""
        self.statusBar().showMessage(message)
        current = self.progress.value()
        self.progress.setValue(current + 1)

    def on_sync_complete(self, results):
        """Handle successful sync of all sources."""
        success_count = sum(1 for result in results.values() if result)
        total_count = len(results)
        
        if success_count == total_count:
            self.statusBar().showMessage("✓ All sources synchronized successfully")
        else:
            failed_sources = [source for source, result in results.items() if not result]
            self.statusBar().showMessage(f"⚠ Sync completed with errors ({success_count}/{total_count} sources)")
            
            # Show detailed message if there were any failures
            if success_count < total_count:
                QMessageBox.warning(self, "Sync Warning",
                                  f"Failed to sync: {', '.join(failed_sources)}\nCheck the logs for details.")
        
        self.progress.setVisible(False)
        
        # Reload sources after successful sync
        if success_count > 0:
            self.statusBar().showMessage("Reloading sources after sync...")
            QTimer.singleShot(1000, self.load_sources)  # Give UI time to update

    def on_sync_error(self, error_info):
        """Handle sync errors."""
        error_msg = error_info[0]
        logger.error(f"Error during sync: {error_msg}")
        self.statusBar().showMessage(f"✕ Sync failed: {error_msg}")
        self.progress.setVisible(False)
        QMessageBox.critical(self, "Sync Error",
                           f"Sync failed: {error_msg}\nCheck the logs for details.")

    def reset_tree_visibility(self):
        """Reset visibility of all tree items and restore default expansion."""
        def reset_item(item):
            item.setHidden(False)
            # Expand only top-level items by default
            item.setExpanded(item.parent() is None)
            for i in range(item.childCount()):
                reset_item(item.child(i))
        
        for i in range(self.tree.topLevelItemCount()):
            reset_item(self.tree.topLevelItem(i))
    
    def show_tree_context_menu(self, position):
        """Show a modern context menu for the tree widget."""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['sidebar']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 8px 0;
            }}
            QMenu::item {{
                color: {COLORS['text']};
                padding: 8px 24px;
                font-family: 'Inter';
                font-size: 13px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['hover']};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {COLORS['border']};
                margin: 4px 0;
            }}
        """)

        # Get the item that was clicked
        item = self.tree.itemAt(position)
        
        if item:
            if item.parent() is None:
                source_name = item.text(0).split(" (")[0]
                expand_action = menu.addAction(f"▾ Expand {source_name}")
                collapse_action = menu.addAction(f"▸ Collapse {source_name}")
                menu.addSeparator()
        
        expand_all = menu.addAction("▾ Expand All")
        collapse_all = menu.addAction("▸ Collapse All")
        
        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        
        if action:
            if action == expand_all:
                self.tree.expandAll()
            elif action == collapse_all:
                self.tree.collapseAll()
            elif item and item.parent() is None:
                if "Expand" in action.text():
                    self._expand_tree_section(item)
                elif "Collapse" in action.text():
                    self._collapse_tree_section(item)

    def _expand_tree_section(self, item):
        """Expand a tree section with animation."""
        def expand_children(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                child.setExpanded(True)
                expand_children(child)
        
        item.setExpanded(True)
        expand_children(item)

    def _collapse_tree_section(self, item):
        """Collapse a tree section with animation."""
        def collapse_children(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                child.setExpanded(False)
                collapse_children(child)
        
        item.setExpanded(False)
        collapse_children(item)

    def get_total_commands(self):
        """Get total number of commands available."""
        try:
            # Get counts for each source
            tldr_count = self.count_items(self.tldr_root)
            cheatsh_count = self.count_items(self.cheatsh_root)
            devhints_count = self.count_items(self.devhints_root)
            total = tldr_count + cheatsh_count + devhints_count

            # Check if we're still loading
            loading = not self.sources_loaded

            # Format counts with commas
            def format_count(count):
                return f"{count:,}" if count > 0 else "0"

            return {
                'status': 'loading' if loading else 'ready',
                'counts': {
                    'tldr': format_count(tldr_count),
                    'cheatsh': format_count(cheatsh_count),
                    'devhints': format_count(devhints_count),
                    'total': format_count(total)
                }
            }
        except Exception as e:
            logger.error(f"Error counting commands: {e}")
            return {
                'status': 'error',
                'counts': {
                    'tldr': '0',
                    'cheatsh': '0',
                    'devhints': '0',
                    'total': '0'
                }
            }

    def display_content(self, content: str):
        """Display the content in the text view."""
        if content.startswith('<html>'):
            self.content.setHtml(content)
        else:
            self.content.setPlainText(content)
        self.update_status_message()

    def show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
            }}
        """)
        dialog.exec()

    def expand_all(self):
        """Expand all items in the tree."""
        self.tree.expandAll()
        self.statusBar().showMessage("Expanded all items", 2000)

    def collapse_all(self):
        """Collapse all items in the tree."""
        self.tree.collapseAll()
        # Keep root items expanded
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setExpanded(True)
        self.statusBar().showMessage("Collapsed all items", 2000)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Create tabs
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['background']};
                padding: 10px;
            }}
            QTabWidget::tab-bar {{
                alignment: left;
            }}
            QTabBar::tab {{
                background: {COLORS['sidebar']};
                color: {COLORS['text']};
                padding: 8px 16px;
                border: 1px solid {COLORS['border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['background']};
                border-bottom: none;
            }}
            QTabBar::tab:!selected {{
                margin-top: 2px;
            }}
        """)
        
        # Appearance tab
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        # Font sizes group
        font_group = QGroupBox("Font Sizes")
        font_group.setStyleSheet(f"""
            QGroupBox {{
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 1em;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
            }}
        """)
        font_layout = QFormLayout(font_group)
        font_layout.setSpacing(10)
        
        # Create spin boxes for font sizes
        self.source_list_size = QSpinBox()
        self.source_header_size = QSpinBox()  # New spinbox for source headers
        self.content_size = QSpinBox()
        self.search_size = QSpinBox()
        self.title_size = QSpinBox()
        
        for spinbox in [self.source_list_size, self.source_header_size, self.content_size, self.search_size, self.title_size]:
            spinbox.setRange(6, 24)
            spinbox.setStyleSheet(f"""
                QSpinBox {{
                    background-color: {COLORS['code_bg']};
                    color: {COLORS['text']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 4px;
                    min-width: 60px;
                }}
                QSpinBox::up-button, QSpinBox::down-button {{
                    background: {COLORS['sidebar']};
                    border: none;
                    border-radius: 2px;
                    margin: 1px;
                }}
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                    background: {COLORS['hover']};
                }}
            """)
        
        # Set current values from settings manager
        font_sizes = settings_manager.get_font_sizes()
        self.source_list_size.setValue(font_sizes["source_list"])
        self.source_header_size.setValue(font_sizes["source_header"])
        self.content_size.setValue(font_sizes["content"])
        self.search_size.setValue(font_sizes["search"])
        self.title_size.setValue(font_sizes["title"])
        
        # Add to layout with labels
        font_layout.addRow("Source Headers:", self.source_header_size)  # Add source headers control
        font_layout.addRow("Source Items:", self.source_list_size)
        font_layout.addRow("Content:", self.content_size)
        font_layout.addRow("Search Box:", self.search_size)
        font_layout.addRow("Titles:", self.title_size)
        
        appearance_layout.addWidget(font_group)
        appearance_layout.addStretch()
        
        # Add tabs
        tabs.addTab(appearance_tab, "Appearance")
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['code_bg']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['hover']};
                border-color: {COLORS['accent']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['selection']};
            }}
        """)
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply_settings)
        
        layout.addWidget(button_box)
    
    def apply_settings(self):
        """Apply the current settings."""
        # Update font sizes in settings manager
        new_sizes = {
            "source_list": self.source_list_size.value(),
            "source_header": self.source_header_size.value(),
            "content": self.content_size.value(),
            "search": self.search_size.value(),
            "title": self.title_size.value()
        }
        settings_manager.update_font_sizes(new_sizes)
        
        # Update fonts
        DEFAULT_FONT.setPointSize(new_sizes["content"])
        MONOSPACE_FONT.setPointSize(new_sizes["content"])
        
        # Apply changes to parent window
        if self.parent:
            # Update root items font size
            for root_item in [self.parent.tldr_root, self.parent.cheatsh_root, self.parent.devhints_root]:
                font = QFont("Inter", new_sizes["source_header"])
                font.setBold(True)
                root_item.setFont(0, font)
            
            # Update tree font
            self.parent.tree.setStyleSheet(f"""
                QTreeWidget {{
                    background-color: {COLORS['sidebar']};
                    border: none;
                    font-family: 'Inter';
                    font-size: {new_sizes["source_list"]}pt;
                }}
                QTreeWidget::item {{
                    color: {COLORS['text']};
                    padding: 2px 4px;
                    margin: 0px;
                }}
                QTreeWidget::item:hover {{
                    background-color: {COLORS['hover']};
                }}
                QTreeWidget::item:selected {{
                    background-color: {COLORS['selection']};
                    color: {COLORS['heading']};
                }}
            """)
            
            # Update search box font
            self.parent.search_box.setStyleSheet(f"""
                SearchBox {{
                    background-color: {COLORS['background']};
                    color: {COLORS['text']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-family: 'Inter';
                    font-size: {new_sizes["search"]}pt;
                }}
                SearchBox:focus {{
                    border: 1px solid {COLORS['accent']};
                }}
            """)
            
            # Update content title font
            self.parent.content_title.setStyleSheet(f"""
                QLabel {{
                    color: {COLORS['heading']};
                    font-family: 'Inter';
                    font-size: {new_sizes["title"]}pt;
                    font-weight: bold;
                    padding: 8px 0;
                }}
            """)
            
            # Update content view font
            self.parent.content.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {COLORS['background']};
                    color: {COLORS['text']};
                    border: none;
                    font-family: 'JetBrains Mono';
                    font-size: {new_sizes["content"]}pt;
                    selection-background-color: {COLORS['selection']};
                    selection-color: {COLORS['text']};
                    padding: 0;
                }}
            """)
            
            # Refresh the content to apply new styles
            current_content = self.parent.content.toHtml()
            self.parent.content.clear()
            self.parent.content.setHtml(current_content)
    
    def accept(self):
        """Handle OK button click."""
        self.apply_settings()
        super().accept()

def run_gui():
    """Run the GUI application."""
    try:
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle("Fusion")
        
        # Set application icon for taskbar
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "logo-64.png")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
        
        # Set dark theme colors
        palette = app.palette()
        palette.setColor(palette.ColorRole.Window, QColor(COLORS['background']))
        palette.setColor(palette.ColorRole.WindowText, QColor(COLORS['text']))
        palette.setColor(palette.ColorRole.Base, QColor(COLORS['background']))
        palette.setColor(palette.ColorRole.AlternateBase, QColor(COLORS['sidebar']))
        palette.setColor(palette.ColorRole.ToolTipBase, QColor(COLORS['code_bg']))
        palette.setColor(palette.ColorRole.ToolTipText, QColor(COLORS['text']))
        palette.setColor(palette.ColorRole.Text, QColor(COLORS['text']))
        palette.setColor(palette.ColorRole.Button, QColor(COLORS['sidebar']))
        palette.setColor(palette.ColorRole.ButtonText, QColor(COLORS['text']))
        palette.setColor(palette.ColorRole.Highlight, QColor(COLORS['accent']))
        palette.setColor(palette.ColorRole.HighlightedText, QColor(COLORS['text']))
        app.setPalette(palette)
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Fatal error in GUI: {e}")
        if 'app' in locals():
            QMessageBox.critical(None, "Fatal Error",
                               f"Application crashed: {str(e)}")
        sys.exit(1) 