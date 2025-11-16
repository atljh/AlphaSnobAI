"""Database Viewer Widget - Browse and manage bot database.

Provides interface for viewing messages, user profiles, topics, and response history
with filtering, search, and export capabilities.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QMessageBox, QTableWidget,
    QTableWidgetItem, QLineEdit, QComboBox, QHeaderView,
    QGroupBox, QFormLayout, QTextEdit, QFileDialog,
    QProgressDialog, QDateEdit
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.db_manager import DatabaseManager
from utils.stats_collector import StatsCollector
from config.settings import get_settings


class DatabaseViewerWidget(QWidget):
    """Widget for viewing and managing database."""

    def __init__(self):
        super().__init__()

        # Initialize managers
        settings = get_settings()
        self.db_manager = DatabaseManager(db_path=settings.paths.database)
        self.stats_collector = StatsCollector(db_path=settings.paths.database)

        # Create UI
        self._create_ui()

        # Load initial data
        self._load_database_stats()

    def _create_ui(self):
        """Create user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header with DB stats
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget for different tables
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Create tabs
        self.tabs.addTab(self._create_messages_tab(), "Messages")
        self.tabs.addTab(self._create_profiles_tab(), "User Profiles")
        self.tabs.addTab(self._create_topics_tab(), "Conversation Topics")
        self.tabs.addTab(self._create_response_history_tab(), "Response History")
        self.tabs.addTab(self._create_tools_tab(), "Database Tools")

        layout.addWidget(self.tabs)

    def _create_header(self) -> QWidget:
        """Create header with database statistics."""
        header = QWidget()
        header.setObjectName("glassCard")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(12)

        # Title
        title = QLabel("Database Viewer")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #f1f5f9;
            }
        """)
        header_layout.addWidget(title)

        # Stats row
        stats_row = QWidget()
        stats_layout = QHBoxLayout(stats_row)
        stats_layout.setSpacing(24)

        self.total_messages_label = QLabel("Messages: --")
        self.total_messages_label.setStyleSheet("font-size: 14px; color: #cbd5e1; font-weight: 600;")
        stats_layout.addWidget(self.total_messages_label)

        self.total_profiles_label = QLabel("Profiles: --")
        self.total_profiles_label.setStyleSheet("font-size: 14px; color: #cbd5e1; font-weight: 600;")
        stats_layout.addWidget(self.total_profiles_label)

        self.total_topics_label = QLabel("Topics: --")
        self.total_topics_label.setStyleSheet("font-size: 14px; color: #cbd5e1; font-weight: 600;")
        stats_layout.addWidget(self.total_topics_label)

        self.db_size_label = QLabel("Size: --")
        self.db_size_label.setStyleSheet("font-size: 14px; color: #cbd5e1; font-weight: 600;")
        stats_layout.addWidget(self.db_size_label)

        stats_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setMinimumHeight(32)
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1,
                    stop:1 #8b5cf6
                );
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5,
                    stop:1 #7c3aed
                );
            }
        """)
        refresh_btn.clicked.connect(self._load_database_stats)
        stats_layout.addWidget(refresh_btn)

        header_layout.addWidget(stats_row)

        return header

    def _create_messages_tab(self) -> QWidget:
        """Create Messages table tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Filters
        filters = QWidget()
        filters.setObjectName("glassCard")
        filters.setStyleSheet("QWidget#glassCard { padding: 12px; }")
        filters_layout = QHBoxLayout(filters)
        filters_layout.setSpacing(12)

        # Chat ID filter
        filters_layout.addWidget(QLabel("Chat ID:"))
        self.msg_chat_filter = QLineEdit()
        self.msg_chat_filter.setPlaceholderText("Filter by chat ID...")
        self.msg_chat_filter.setMinimumWidth(150)
        filters_layout.addWidget(self.msg_chat_filter)

        # User ID filter
        filters_layout.addWidget(QLabel("User ID:"))
        self.msg_user_filter = QLineEdit()
        self.msg_user_filter.setPlaceholderText("Filter by user ID...")
        self.msg_user_filter.setMinimumWidth(150)
        filters_layout.addWidget(self.msg_user_filter)

        # Search text
        filters_layout.addWidget(QLabel("Search:"))
        self.msg_search = QLineEdit()
        self.msg_search.setPlaceholderText("Search in text...")
        self.msg_search.setMinimumWidth(200)
        filters_layout.addWidget(self.msg_search)

        filters_layout.addStretch()

        # Load button
        load_btn = QPushButton("Load Messages")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._load_messages)
        filters_layout.addWidget(load_btn)

        layout.addWidget(filters)

        # Table
        self.messages_table = QTableWidget()
        self.messages_table.setColumnCount(7)
        self.messages_table.setHorizontalHeaderLabels([
            "ID", "Chat ID", "User ID", "Username", "Text", "Timestamp", "Persona"
        ])
        self.messages_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.messages_table.horizontalHeader().setStretchLastSection(False)
        self.messages_table.verticalHeader().setVisible(False)
        self.messages_table.setAlternatingRowColors(True)
        self.messages_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.messages_table.setSortingEnabled(True)

        layout.addWidget(self.messages_table)

        return widget

    def _create_profiles_tab(self) -> QWidget:
        """Create User Profiles table tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Filters
        filters = QWidget()
        filters.setObjectName("glassCard")
        filters.setStyleSheet("QWidget#glassCard { padding: 12px; }")
        filters_layout = QHBoxLayout(filters)
        filters_layout.setSpacing(12)

        # Relationship filter
        filters_layout.addWidget(QLabel("Relationship:"))
        self.profile_relationship_filter = QComboBox()
        self.profile_relationship_filter.addItems([
            "All", "owner", "close_friend", "friend", "acquaintance", "stranger"
        ])
        filters_layout.addWidget(self.profile_relationship_filter)

        filters_layout.addStretch()

        # Load button
        load_btn = QPushButton("Load Profiles")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._load_profiles)
        filters_layout.addWidget(load_btn)

        layout.addWidget(filters)

        # Table
        self.profiles_table = QTableWidget()
        self.profiles_table.setColumnCount(7)
        self.profiles_table.setHorizontalHeaderLabels([
            "User ID", "Username", "Name", "Relationship", "Trust Score",
            "Interactions", "Last Interaction"
        ])
        self.profiles_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.profiles_table.verticalHeader().setVisible(False)
        self.profiles_table.setAlternatingRowColors(True)
        self.profiles_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.profiles_table.setSortingEnabled(True)

        layout.addWidget(self.profiles_table)

        return widget

    def _create_topics_tab(self) -> QWidget:
        """Create Conversation Topics table tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Table
        self.topics_table = QTableWidget()
        self.topics_table.setColumnCount(6)
        self.topics_table.setHorizontalHeaderLabels([
            "Chat ID", "Topic", "Confidence", "Persona", "Mentions", "Last Mentioned"
        ])
        self.topics_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.topics_table.verticalHeader().setVisible(False)
        self.topics_table.setAlternatingRowColors(True)
        self.topics_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.topics_table.setSortingEnabled(True)

        # Load button
        load_btn = QPushButton("Load Topics")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._load_topics)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(load_btn)

        layout.addLayout(btn_layout)
        layout.addWidget(self.topics_table)

        return widget

    def _create_response_history_tab(self) -> QWidget:
        """Create Response History table tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Table
        self.response_history_table = QTableWidget()
        self.response_history_table.setColumnCount(7)
        self.response_history_table.setHorizontalHeaderLabels([
            "Chat ID", "User ID", "Should Respond", "Reason", "Persona",
            "Total Delay (ms)", "Timestamp"
        ])
        self.response_history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.response_history_table.verticalHeader().setVisible(False)
        self.response_history_table.setAlternatingRowColors(True)
        self.response_history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.response_history_table.setSortingEnabled(True)

        # Load button
        load_btn = QPushButton("Load Response History")
        load_btn.setCursor(Qt.PointingHandCursor)
        load_btn.clicked.connect(self._load_response_history)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(load_btn)

        layout.addLayout(btn_layout)
        layout.addWidget(self.response_history_table)

        return widget

    def _create_tools_tab(self) -> QWidget:
        """Create Database Tools tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Tools group
        tools_group = QGroupBox("Database Maintenance")
        tools_group.setObjectName("glassCard")
        tools_layout = QVBoxLayout(tools_group)
        tools_layout.setSpacing(12)

        # Backup button
        backup_btn = self._create_tool_button(
            "Create Backup",
            "Create a backup of the database",
            "#6366f1",
            "#8b5cf6",
            self._on_backup_clicked
        )
        tools_layout.addWidget(backup_btn)

        # Restore button
        restore_btn = self._create_tool_button(
            "Restore from Backup",
            "Restore database from a backup file",
            "#f59e0b",
            "#f97316",
            self._on_restore_clicked
        )
        tools_layout.addWidget(restore_btn)

        # Vacuum button
        vacuum_btn = self._create_tool_button(
            "Optimize Database (Vacuum)",
            "Optimize database size and performance",
            "#10b981",
            "#06b6d4",
            self._on_vacuum_clicked
        )
        tools_layout.addWidget(vacuum_btn)

        # Integrity check button
        integrity_btn = self._create_tool_button(
            "Check Integrity",
            "Verify database integrity",
            "#8b5cf6",
            "#ec4899",
            self._on_integrity_check_clicked
        )
        tools_layout.addWidget(integrity_btn)

        # Clean old messages button
        clean_btn = self._create_tool_button(
            "Clean Old Messages",
            "Delete messages older than specified date",
            "#ef4444",
            "#f59e0b",
            self._on_clean_old_clicked
        )
        tools_layout.addWidget(clean_btn)

        layout.addWidget(tools_group)
        layout.addStretch()

        return widget

    def _create_tool_button(self, title: str, description: str,
                           color1: str, color2: str, callback) -> QWidget:
        """Create a styled tool button."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        button = QPushButton(title)
        button.setMinimumHeight(48)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color1},
                    stop:1 {color2}
                );
                color: white;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 12px;
                padding: 12px 24px;
                text-align: left;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        button.clicked.connect(callback)

        desc_label = QLabel(description)
        desc_label.setStyleSheet("color: #94a3b8; font-size: 12px; padding-left: 12px;")

        container_layout.addWidget(button)
        container_layout.addWidget(desc_label)

        return container

    def _load_database_stats(self):
        """Load and display database statistics."""
        try:
            stats = asyncio.run(self.db_manager.get_stats())
            general_stats = asyncio.run(self.stats_collector.get_general_stats())

            self.total_messages_label.setText(f"Messages: {general_stats.total_messages}")
            self.total_profiles_label.setText(f"Profiles: {general_stats.unique_users}")
            self.total_topics_label.setText(f"Topics: {stats.get('topic_count', 0)}")

            # Format file size
            size_bytes = stats.get('file_size', 0)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

            self.db_size_label.setText(f"Size: {size_str}")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load database stats:\n{e}")

    def _load_messages(self):
        """Load messages from database."""
        try:
            # Get filter values
            chat_id = self.msg_chat_filter.text().strip()
            user_id = self.msg_user_filter.text().strip()
            search_text = self.msg_search.text().strip()

            # Build query
            query = "SELECT id, chat_id, user_id, username, text, timestamp, persona_mode FROM messages"
            params = []
            conditions = []

            if chat_id:
                conditions.append("chat_id = ?")
                params.append(int(chat_id))

            if user_id:
                conditions.append("user_id = ?")
                params.append(int(user_id))

            if search_text:
                conditions.append("text LIKE ?")
                params.append(f"%{search_text}%")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY timestamp DESC LIMIT 500"

            # Execute query
            conn = self.db_manager.get_connection()
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            # Populate table
            self.messages_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    # Truncate text if too long
                    if j == 4 and value and len(str(value)) > 100:
                        value = str(value)[:100] + "..."

                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.messages_table.setItem(i, j, item)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load messages:\n{e}")

    def _load_profiles(self):
        """Load user profiles from database."""
        try:
            relationship_filter = self.profile_relationship_filter.currentText()

            query = """
                SELECT user_id, username, first_name, relationship_level,
                       trust_score, interaction_count, last_interaction
                FROM user_profiles
            """
            params = []

            if relationship_filter != "All":
                query += " WHERE relationship_level = ?"
                params.append(relationship_filter)

            query += " ORDER BY interaction_count DESC LIMIT 500"

            conn = self.db_manager.get_connection()
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

            self.profiles_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    # Format trust score
                    if j == 4 and value is not None:
                        value = f"{value:.2f}"

                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.profiles_table.setItem(i, j, item)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load profiles:\n{e}")

    def _load_topics(self):
        """Load conversation topics from database."""
        try:
            query = """
                SELECT chat_id, topic, confidence, persona_used,
                       mention_count, last_mentioned
                FROM conversation_topics
                ORDER BY last_mentioned DESC LIMIT 500
            """

            conn = self.db_manager.get_connection()
            cursor = conn.execute(query)
            rows = cursor.fetchall()

            self.topics_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    # Format confidence
                    if j == 2 and value is not None:
                        value = f"{value:.2f}"

                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.topics_table.setItem(i, j, item)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load topics:\n{e}")

    def _load_response_history(self):
        """Load response history from database."""
        try:
            query = """
                SELECT chat_id, user_id, should_respond, decision_reason,
                       persona_mode, total_delay_ms, timestamp
                FROM response_history
                ORDER BY timestamp DESC LIMIT 500
            """

            conn = self.db_manager.get_connection()
            cursor = conn.execute(query)
            rows = cursor.fetchall()

            self.response_history_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, value in enumerate(row):
                    # Format boolean
                    if j == 2:
                        value = "Yes" if value else "No"

                    # Truncate reason if too long
                    if j == 3 and value and len(str(value)) > 100:
                        value = str(value)[:100] + "..."

                    item = QTableWidgetItem(str(value) if value is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.response_history_table.setItem(i, j, item)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load response history:\n{e}")

    def _on_backup_clicked(self):
        """Handle backup button click."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Create Backup",
            f"alphasnob_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            "Database Files (*.db);;All Files (*)"
        )

        if filename:
            try:
                asyncio.run(self.db_manager.backup(filename))
                QMessageBox.information(
                    self,
                    "Success",
                    f"Database backup created successfully:\n{filename}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Backup failed:\n{e}")

    def _on_restore_clicked(self):
        """Handle restore button click."""
        reply = QMessageBox.warning(
            self,
            "Warning",
            "Restoring from backup will replace the current database.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Select Backup File",
                "",
                "Database Files (*.db);;All Files (*)"
            )

            if filename:
                try:
                    asyncio.run(self.db_manager.restore(filename))
                    QMessageBox.information(self, "Success", "Database restored successfully!")
                    self._load_database_stats()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Restore failed:\n{e}")

    def _on_vacuum_clicked(self):
        """Handle vacuum button click."""
        try:
            asyncio.run(self.db_manager.vacuum())
            QMessageBox.information(self, "Success", "Database optimized successfully!")
            self._load_database_stats()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Vacuum failed:\n{e}")

    def _on_integrity_check_clicked(self):
        """Handle integrity check button click."""
        try:
            result = asyncio.run(self.db_manager.check_integrity())
            if result:
                QMessageBox.information(
                    self,
                    "Integrity Check",
                    "Database integrity check passed!\n\nNo issues found."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Integrity Check",
                    "Database integrity check found issues!\n\nConsider restoring from backup."
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Integrity check failed:\n{e}")

    def _on_clean_old_clicked(self):
        """Handle clean old messages button click."""
        # TODO: Implement date picker dialog for selecting cutoff date
        QMessageBox.information(
            self,
            "Coming Soon",
            "Clean old messages functionality will be implemented soon."
        )
