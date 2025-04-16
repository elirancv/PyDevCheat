import sys
import re
import logging
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLineEdit, QTreeWidget, QTreeWidgetItem,
                            QTextEdit, QSplitter, QLabel, QPushButton, QMessageBox,
                            QProgressBar, QStatusBar, QToolBar, QMenu, QStyledItemDelegate,
                            QFrame)
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QRunnable, QThreadPool, QObject, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import (QFont, QSyntaxHighlighter, QTextCharFormat, QColor,
                        QAction, QIcon, QPainter, QPainterPath, QLinearGradient, QKeySequence,
                        QShortcut)
from qt_material import apply_stylesheet
import json
import os
from pathlib import Path
from .sources.tldr import TLDRSource
from .sources.cheatsh import CheatShSource
from .sources.devhints import DevhintsSource
import pyperclip

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Modern color scheme inspired by popular IDEs and tools
COLORS = {
    'background': '#1a1f2e',     # Richer dark blue background
    'sidebar': '#212739',        # Lighter blue-gray
    'text': '#c4d0ff',          # Bright blue-white
    'text_muted': '#8b9ccc',    # Soft periwinkle
    'accent': '#7aa2f7',        # Vibrant blue
    'accent_secondary': '#bb9af7',  # Soft purple
    'border': '#151926',        # Darker border
    'hover': '#3b4366',         # Rich navy hover
    'selection': '#2d3452',     # Deep navy selection
    'code_bg': '#2a304a',       # Navy code background
    'link': '#7dcfff',          # Bright blue for links
    'heading': '#c4d0ff',       # Bright white-blue for headings
    'success': '#9ece6a',       # Soft green
    'warning': '#e0af68',       # Soft orange
    'error': '#f7768e',         # Soft red
    'gradient_start': '#7aa2f7', # Start of gradients
    'gradient_end': '#bb9af7',   # End of gradients
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
    """Syntax highlighter for the content view."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Main title format (h1)
        main_title_format = QTextCharFormat()
        main_title_format.setForeground(QColor(COLORS['heading']))
        main_title_format.setFontWeight(QFont.Weight.Bold)
        font = QFont("Inter", 20)  # Using Inter font for modern look
        main_title_format.setFont(font)
        self.highlighting_rules.append((r'^\# .*$', main_title_format))

        # Section title format (h2)
        section_title_format = QTextCharFormat()
        section_title_format.setForeground(QColor(COLORS['heading']))
        section_title_format.setFontWeight(QFont.Weight.Bold)
        font = QFont("Inter", 16)
        section_title_format.setFont(font)
        self.highlighting_rules.append((r'^\#\# .*$', section_title_format))

        # Separator line format
        separator_format = QTextCharFormat()
        separator_format.setForeground(QColor(COLORS['border']))
        self.highlighting_rules.append((r'^─+$', separator_format))

        # Command format (monospace bold)
        command_format = QTextCharFormat()
        command_format.setForeground(QColor(COLORS['text']))
        command_format.setFontWeight(QFont.Weight.Bold)
        font = QFont("JetBrains Mono", 12)  # Modern monospace font
        command_format.setFont(font)
        self.highlighting_rules.append((r'^[^#].*?(?=\s+#|$)', command_format))

        # Comment format (description)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(COLORS['text_muted']))
        font = QFont("Inter", 12)
        comment_format.setFont(font)
        self.highlighting_rules.append((r'#.*$', comment_format))

        # URL format
        url_format = QTextCharFormat()
        url_format.setForeground(QColor(COLORS['link']))
        url_format.setFontUnderline(True)
        self.highlighting_rules.append((r'https?://\S+', url_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

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
    def __init__(self, text, parent=None, icon=None):
        super().__init__(text, parent)
        if icon:
            self.setIcon(icon)
        self.setStyleSheet(f"""
            ModernButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['background']};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-family: 'Inter';
                font-weight: 600;
                font-size: 13px;
            }}
            ModernButton:hover {{
                background-color: {COLORS['accent_secondary']};
            }}
            ModernButton:pressed {{
                background-color: {COLORS['selection']};
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
        
        # Store references to loading widgets
        self.loading_widgets = {}
        
        # Initialize sources
        self.tldr_source = TLDRSource()
        self.cheatsh_source = CheatShSource()
        self.devhints_source = DevhintsSource()
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "logo-64.png")
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
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
        # Increase minimum and default window size
        self.setMinimumSize(1000, 800)
        # Set a reasonable starting size that shows all welcome content
        self.resize(1200, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create modern toolbar
        self.create_toolbar()

        # Create search section
        search_container = QWidget()
        search_container.setFixedHeight(48)
        search_container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['sidebar']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(8, 4, 8, 4)

        # Create search box with clear button
        search_wrapper = QWidget()
        search_wrapper.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        search_wrapper_layout = QHBoxLayout(search_wrapper)
        search_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        search_wrapper_layout.setSpacing(0)

        # Add clear button first (on the left)
        self.clear_button = QPushButton("⨉")  # Using mathematical x symbol
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.setFixedSize(22, 22)
        self.clear_button.clicked.connect(self.clear_search)
        self.clear_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 3px;
                font-family: 'Inter';
                font-size: 16px;
                font-weight: normal;
                margin: 5px 6px 5px 0px;
                padding: 0;
                text-align: center;
                line-height: 22px;
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
        self.clear_button.hide()

        self.search_box = SearchBox()
        self.search_box.setFixedHeight(32)
        self.search_box.setPlaceholderText("Search commands (e.g., 'git commit', 'python list')...")
        self.search_box.textChanged.connect(self.on_search)
        self.search_box.setStyleSheet(f"""
            SearchBox {{
                background-color: {COLORS['background']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Inter';
                font-size: 12px;
            }}
            SearchBox:focus {{
                border: 1px solid {COLORS['accent']};
            }}
        """)

        search_wrapper_layout.addWidget(self.clear_button)
        search_wrapper_layout.addWidget(self.search_box)
        search_layout.addWidget(search_wrapper)
        layout.addWidget(search_container)

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
        sidebar.setMinimumWidth(250)
        sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['sidebar']};
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
        self.tree.setIndentation(12)  # Even smaller indentation
        self.tree.setItemsExpandable(True)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {COLORS['sidebar']};
                border: none;
                font-family: 'Inter';
                font-size: 12px;
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
            QTreeWidget::branch {{
                background: transparent;
                border: none;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: none;
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: none;
            }}
        """)
        sidebar_layout.addWidget(self.tree)

        # Initialize root items with minimal styling
        def create_root_item(name):
            item = QTreeWidgetItem(self.tree)
            item.setText(0, name)
            item.setForeground(0, QColor(COLORS['text']))
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            return item

        # Create root items without icons
        self.tldr_root = create_root_item("TLDR Pages")
        self.cheatsh_root = create_root_item("Cheat.sh")
        self.devhints_root = create_root_item("DevHints")

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
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        # Add title
        self.content_title = QLabel("Welcome to PyDevCheat")
        self.content_title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['heading']};
                font-family: 'Inter';
                font-size: 20px;
                font-weight: bold;
            }}
        """)
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

        # Set up initial welcome content with proper styling
        welcome_content = """# 🎯 Welcome to PyDevCheat

Your ultimate programming companion for instant command lookups and code snippets.

## 🚀 Quick Start
• Type in the search box above to find commands
  Example: `git commit` or `docker run`
• Browse categories in the sidebar
• Click any command to view details

## 📚 Available Sources
• TLDR Pages
  Simplified and practical command examples
• Cheat.sh
  Community-driven cheat sheets and snippets
• DevHints
  Quick reference guides for developers

## ⌨️ Keyboard Shortcuts
• Ctrl/Cmd + F: Focus search
• Esc: Clear search
• Up/Down: Navigate results
• Ctrl/Cmd + C: Copy content

## 💡 Pro Tips
• Use specific terms for better results
  Example: `python list comprehension`
• Select text to copy specific parts
• Right-click items for more options
• Check the status bar for updates

──────────────────────────────────

💻 Ready with {total_commands} commands at your fingertips!"""

        # Update initial content with total command count
        self.content.setPlainText(welcome_content.format(
            total_commands=self.get_total_commands()
        ))
        self.content_title.setText("Welcome to PyDevCheat")

    def create_toolbar(self):
        """Create a premium modern toolbar."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFixedHeight(44)
        
        # Create main container with enhanced styling
        container = QWidget()
        container.setFixedHeight(44)
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(4)
        
        # Enhanced button style with new colors
        button_style = f"""
            QPushButton {{
                background-color: {COLORS['code_bg']};
                color: {COLORS['text_muted']};
                border: none;
                border-radius: 5px;
                padding: 0px;
                font-family: 'Inter';
                font-weight: 600;
                font-size: 15px;
                min-width: 34px;
                max-width: 34px;
                min-height: 34px;
                max-height: 34px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['hover']};
                color: {COLORS['text']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['selection']};
                color: {COLORS['accent']};
            }}
        """
        
        # Create button group container with new styling
        button_group = QWidget()
        button_group.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['sidebar']};
                border-radius: 6px;
                padding: 3px;
            }}
        """)
        group_layout = QHBoxLayout(button_group)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(2)
        
        # Helper function to create modern action buttons
        def create_action_button(text, tooltip, callback):
            btn = QPushButton(text)
            btn.setFixedSize(34, 34)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            btn.setStyleSheet(button_style)
            return btn
        
        # Create and add buttons with modern icons
        home_btn = create_action_button("⌂", "Go to Welcome Screen (Home)", self.show_welcome)
        group_layout.addWidget(home_btn)
        
        refresh_btn = create_action_button("⟳", "Reload All Commands (Refresh)", self.load_sources)
        group_layout.addWidget(refresh_btn)
        
        sync_btn = create_action_button("↻", "Synchronize All Sources (Sync)", self.sync_all_sources)
        group_layout.addWidget(sync_btn)

        copy_btn = create_action_button("⎘", "Copy Content (Ctrl+C)", self.copy_content)
        group_layout.addWidget(copy_btn)
        
        # Add the button group to main layout
        layout.addWidget(button_group)
        
        # Add stretch to push everything to the left
        layout.addStretch()
        
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

    def show_welcome(self):
        """Show the welcome screen."""
        self.content_title.setText("Welcome to PyDevCheat")
        welcome_content = """# 🎯 Welcome to PyDevCheat

Your ultimate programming companion for instant command lookups and code snippets.

## 🚀 Quick Start
• Type in the search box above to find commands
  Example: `git commit` or `docker run`
• Browse categories in the sidebar
• Click any command to view details

## 📚 Available Sources
• TLDR Pages
  Simplified and practical command examples
• Cheat.sh
  Community-driven cheat sheets and snippets
• DevHints
  Quick reference guides for developers

## ⌨️ Keyboard Shortcuts
• Ctrl/Cmd + F: Focus search
• Esc: Clear search
• Up/Down: Navigate results
• Ctrl/Cmd + C: Copy content

## 💡 Pro Tips
• Use specific terms for better results
  Example: `python list comprehension`
• Select text to copy specific parts
• Right-click items for more options
• Check the status bar for updates

──────────────────────────────────

💻 Ready with {total_commands} commands at your fingertips!"""

        # Update initial content with total command count
        self.content.setPlainText(welcome_content.format(
            total_commands=self.get_total_commands()
        ))

    def load_sources(self):
        """Load command sources in background threads."""
        logger.debug("Loading sources...")
        
        # Reset loading state
        self.sources_loaded = False
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.statusBar().showMessage("Loading sources...")

        # Clear existing items
        self.tldr_root.takeChildren()
        self.cheatsh_root.takeChildren()
        self.devhints_root.takeChildren()

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

    def on_tldr_loaded(self, commands):
        """Handle loaded TLDR commands."""
        try:
            logger.debug(f"TLDR commands loaded: {len(commands)} commands")
            
            # Stop loading animation and remove loading item
            self.cleanup_loading_widget("TLDR Pages")
            
            # Update root text
            self.tldr_root.setText(0, f"TLDR Pages ({len(commands)})")
            
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
            
            self.tldr_root.setExpanded(True)
            self.check_loading_complete()
            self.update_status_message()
            
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
            
            # Update root text with count
            self.cheatsh_root.setText(0, f"Cheat.sh ({len(topic_list)})")
            
            # Sort topics alphabetically
            topic_list.sort(key=str.lower)
            
            # Add topics directly under root
            for topic in topic_list:
                topic_item = QTreeWidgetItem(self.cheatsh_root)
                topic_item.setText(0, topic)
            
            self.cheatsh_root.setExpanded(True)
            self.check_loading_complete()
            self.update_status_message()
            
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
            
            # Update root text with count
            self.devhints_root.setText(0, f"DevHints ({len(topic_list)})")
            
            # Sort topics alphabetically
            topic_list.sort(key=lambda x: x[0].lower())
            
            # Add topics directly under root
            for display_topic, original_topic in topic_list:
                topic_item = QTreeWidgetItem(self.devhints_root)
                topic_item.setText(0, display_topic)
                topic_item.setData(0, Qt.ItemDataRole.UserRole, original_topic)
            
            self.devhints_root.setExpanded(True)
            self.check_loading_complete()
            
        except Exception as e:
            logger.error(f"Error processing DevHints topics: {e}")
            self.on_load_error((str(e), "DevHints"))

    def check_loading_complete(self):
        """Check if all sources are loaded."""
        all_loaded = True
        total_items = 0
        
        # Count items and check loading state
        for root in [self.tldr_root, self.cheatsh_root, self.devhints_root]:
            count = root.childCount()
            if count == 0 and not root.text(0).endswith("(0)") and not "Error" in root.text(0):
                all_loaded = False
            total_items += count
        
        if all_loaded:
            self.progress.setVisible(False)
            self.sources_loaded = True
            if total_items > 0:
                self.statusBar().showMessage(f"Ready - {total_items:,} commands available")
            else:
                self.statusBar().showMessage("No commands loaded. Try syncing sources.")

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

    def on_search(self, text):
        """Filter tree items based on search text."""
        try:
            # Show/hide clear button based on search text
            self.clear_button.setVisible(bool(text))
            
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

    def clear_search(self):
        """Clear the search box and reset tree view."""
        self.search_box.clear()
        self.clear_button.hide()
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
        count = 0
        for i in range(root_item.childCount()):
            child = root_item.child(i)
            if not isinstance(child, LoadingLabel):
                count += 1
        return count

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

        self.content_title = QLabel("Welcome to PyDevCheat")
        self.content_title.setStyleSheet(f"""
            QLabel {{
                color: {COLORS['text']};
                font-family: 'Inter';
                font-size: 14px;
                font-weight: 600;
            }}
        """)
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
                font-size: 13px;
                selection-background-color: {COLORS['selection']};
                selection-color: {COLORS['text']};
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
        self.content_title.setText(command)
        
        worker = Worker(self._load_content_worker, source, command)
        worker.signals.result.connect(self.display_content)
        worker.signals.error.connect(lambda err: self.on_content_error(err, command))
        self.threadpool.start(worker)

    def _load_content_worker(self, source: str, command: str) -> str:
        """Worker function to load content."""
        try:
            if source == "tldr":
                content = self.tldr_source.search(command)
            elif source == "cheatsh":
                content = self.cheatsh_source.search(command)
            elif source == "devhints":
                content = self.devhints_source.search(command)
            else:
                raise ValueError(f"Unknown source: {source}")
            
            if not content:
                raise ValueError(f"No content found for {command}")
            
            return self.format_content(content)
        except Exception as e:
            logger.error(f"Error loading content for {source}:{command}: {e}")
            raise

    def display_content(self, content: str):
        """Display the content in the text view."""
        self.content.setPlainText(content)
        self.update_status_message()

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
                expand_source = menu.addAction(f"▾ Expand {source_name}")
                collapse_source = menu.addAction(f"▸ Collapse {source_name}")
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
            total = 0
            # Only count non-loading items
            for root in [self.tldr_root, self.cheatsh_root, self.devhints_root]:
                for i in range(root.childCount()):
                    child = root.child(i)
                    # Skip loading items
                    if not self.tree.itemWidget(child, 0):
                        total += 1
            return f"{total:,}"  # Format with commas for readability
        except Exception as e:
            logger.error(f"Error counting commands: {e}")
            return "thousands of"  # Fallback if counting fails

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