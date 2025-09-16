#!/usr/bin/env python3
"""
Qt Log Handler for WhisperEngine
Captures logging output and displays it in a Qt widget with copying capabilities.
"""

import logging
import threading
from datetime import datetime
from typing import List, Optional, Union
from collections import deque

try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QTextEdit,
        QPushButton,
        QComboBox,
        QLabel,
        QCheckBox,
        QSplitter,
        QGroupBox,
        QFormLayout,
        QSpinBox,
    )
    from PySide6.QtCore import Qt, QTimer, Signal, QObject
    from PySide6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


class LogEntry:
    """Represents a single log entry"""

    def __init__(self, record: logging.LogRecord):
        self.timestamp = datetime.fromtimestamp(record.created)
        self.level = record.levelname
        self.logger_name = record.name
        self.message = record.getMessage()
        self.pathname = record.pathname
        self.lineno = record.lineno
        self.funcName = record.funcName
        self.thread_name = getattr(record, "threadName", "MainThread")
        self.formatted = ""  # Will be set by formatter

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.level}: {self.logger_name}: {self.message}"


class LogSignals(QObject):
    """Signals for log updates"""

    new_log_entry = Signal(object)  # LogEntry
    logs_cleared = Signal()


class QtLogHandler(logging.Handler):
    """Custom logging handler that captures logs for Qt display"""

    def __init__(self, max_entries: int = 1000):
        super().__init__()
        self.max_entries = max_entries
        self.log_entries: deque = deque(maxlen=max_entries)
        self.signals = LogSignals()
        self.lock: Union[threading.Lock, threading.RLock] = threading.RLock()

        # Set default formatter
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord):
        """Handle a log record"""
        try:
            # Create log entry
            entry = LogEntry(record)
            entry.formatted = self.format(record)

            # Add to collection (thread-safe)
            with self.lock:
                self.log_entries.append(entry)

            # Emit signal for UI update
            self.signals.new_log_entry.emit(entry)

        except Exception:
            # Don't let logging errors crash the app
            pass

    def get_logs(self, level_filter: Optional[str] = None) -> List[LogEntry]:
        """Get all logs, optionally filtered by level"""
        with self.lock:
            if level_filter is None:
                return list(self.log_entries)
            else:
                return [entry for entry in self.log_entries if entry.level == level_filter]

    def clear_logs(self):
        """Clear all stored logs"""
        with self.lock:
            self.log_entries.clear()
        self.signals.logs_cleared.emit()


class SystemLogsWidget(QWidget):
    """Widget for displaying and managing system logs"""

    def __init__(self):
        super().__init__()
        self.log_handler: Optional[QtLogHandler] = None
        self.auto_scroll = True
        self.max_display_lines = 10000

        self.init_ui()
        self.setup_log_handler()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Header section
        header_layout = QHBoxLayout()

        # Log level filter
        header_layout.addWidget(QLabel("Filter:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.setCurrentText("All")
        self.level_filter.currentTextChanged.connect(self.refresh_logs)
        header_layout.addWidget(self.level_filter)

        header_layout.addStretch()

        # Auto-scroll checkbox
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.toggled.connect(self.toggle_auto_scroll)
        header_layout.addWidget(self.auto_scroll_cb)

        # Control buttons
        self.clear_button = QPushButton("Clear Logs")
        self.clear_button.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.clear_button)

        self.copy_button = QPushButton("Copy All")
        self.copy_button.clicked.connect(self.copy_all_logs)
        header_layout.addWidget(self.copy_button)

        self.copy_selected_button = QPushButton("Copy Selected")
        self.copy_selected_button.clicked.connect(self.copy_selected_logs)
        header_layout.addWidget(self.copy_selected_button)

        layout.addLayout(header_layout)

        # Log display area
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Monaco", 9) if self.is_macos() else QFont("Consolas", 9))

        # Set background and colors for better readability
        self.log_display.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
        """
        )

        layout.addWidget(self.log_display)

        # Stats section
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Logs: 0 entries")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()

        # Max lines setting
        stats_layout.addWidget(QLabel("Max lines:"))
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(100, 50000)
        self.max_lines_spin.setValue(self.max_display_lines)
        self.max_lines_spin.setSuffix(" lines")
        self.max_lines_spin.valueChanged.connect(self.update_max_lines)
        stats_layout.addWidget(self.max_lines_spin)

        layout.addLayout(stats_layout)

    def is_macos(self) -> bool:
        """Check if running on macOS"""
        import platform

        return platform.system() == "Darwin"

    def setup_log_handler(self):
        """Set up the log handler to capture application logs"""
        self.log_handler = QtLogHandler(max_entries=10000)

        # Connect signals
        self.log_handler.signals.new_log_entry.connect(self.add_log_entry)
        self.log_handler.signals.logs_cleared.connect(self.refresh_logs)

        # Add to root logger to capture all logs
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)

        # Set level to capture everything
        self.log_handler.setLevel(logging.DEBUG)

    def add_log_entry(self, entry: LogEntry):
        """Add a new log entry to the display"""
        if not self.should_display_entry(entry):
            return

        # Format the entry with colors
        formatted_text = self.format_log_entry(entry)

        # Add to display
        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Apply color formatting
        format = QTextCharFormat()
        format.setForeground(QColor(self.get_level_color(entry.level)))
        cursor.setCharFormat(format)

        cursor.insertText(formatted_text + "\n")

        # Limit display size
        self.limit_display_size()

        # Auto-scroll if enabled
        if self.auto_scroll:
            self.log_display.verticalScrollBar().setValue(
                self.log_display.verticalScrollBar().maximum()
            )

        # Update stats
        self.update_stats()

    def should_display_entry(self, entry: LogEntry) -> bool:
        """Check if entry should be displayed based on current filter"""
        filter_level = self.level_filter.currentText()
        return filter_level == "All" or entry.level == filter_level

    def format_log_entry(self, entry: LogEntry) -> str:
        """Format a log entry for display"""
        timestamp = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
        return f"[{timestamp}] {entry.level:8s} | {entry.logger_name:20s} | {entry.message}"

    def get_level_color(self, level: str) -> str:
        """Get color for log level"""
        colors = {
            "DEBUG": "#888888",
            "INFO": "#ffffff",
            "WARNING": "#ffaa00",
            "ERROR": "#ff6666",
            "CRITICAL": "#ff0000",
        }
        return colors.get(level, "#ffffff")

    def limit_display_size(self):
        """Limit the number of lines in the display"""
        document = self.log_display.document()
        if document.lineCount() > self.max_display_lines:
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.KeepAnchor,
                document.lineCount() - self.max_display_lines,
            )
            cursor.removeSelectedText()

    def refresh_logs(self):
        """Refresh the log display with current filter"""
        if not self.log_handler:
            return

        # Clear display
        self.log_display.clear()

        # Get filtered logs
        filter_level = self.level_filter.currentText()
        level_filter = None if filter_level == "All" else filter_level
        logs = self.log_handler.get_logs(level_filter)

        # Add all logs
        for entry in logs:
            self.add_log_entry(entry)

        self.update_stats()

    def clear_logs(self):
        """Clear all logs"""
        if self.log_handler:
            self.log_handler.clear_logs()
        self.log_display.clear()
        self.update_stats()

    def copy_all_logs(self):
        """Copy all visible logs to clipboard"""
        text = self.log_display.toPlainText()
        if text:
            from PySide6.QtWidgets import QApplication

            QApplication.clipboard().setText(text)

    def copy_selected_logs(self):
        """Copy selected logs to clipboard"""
        cursor = self.log_display.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            from PySide6.QtWidgets import QApplication

            QApplication.clipboard().setText(text)

    def toggle_auto_scroll(self, enabled: bool):
        """Toggle auto-scroll feature"""
        self.auto_scroll = enabled

    def update_max_lines(self, value: int):
        """Update maximum display lines"""
        self.max_display_lines = value
        self.limit_display_size()

    def update_stats(self):
        """Update statistics display"""
        if self.log_handler:
            total_logs = len(self.log_handler.log_entries)
            display_lines = self.log_display.document().lineCount()
            self.stats_label.setText(f"Logs: {total_logs} entries, {display_lines} displayed")
        else:
            self.stats_label.setText("Logs: 0 entries")

    def closeEvent(self, event):
        """Clean up when widget is closed"""
        if self.log_handler:
            # Remove handler from root logger
            root_logger = logging.getLogger()
            root_logger.removeHandler(self.log_handler)
        super().closeEvent(event)
