"""Statistics Widget - Bot Activity Metrics and Charts.

Provides comprehensive visualization of bot activity including message stats,
response rates, persona usage, and decision engine metrics.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QMessageBox, QScrollArea,
    QGroupBox, QGridLayout, QDateEdit, QComboBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.stats_collector import StatsCollector
from config.settings import get_settings


class MetricCard(QWidget):
    """Glass-style metric display card."""

    def __init__(self, title: str, value: str, color: str = "#6366f1"):
        super().__init__()
        self.setObjectName("glassCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                font-weight: 700;
                color: {color};
            }}
        """)
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #cbd5e1;
                font-weight: 600;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)


class StatisticsWidget(QWidget):
    """Widget for displaying bot statistics and metrics."""

    def __init__(self):
        super().__init__()

        # Initialize stats collector
        settings = get_settings()
        self.stats_collector = StatsCollector(db_path=settings.paths.database)

        # Create UI
        self._create_ui()

        # Load initial stats
        self._load_stats()

    def _create_ui(self):
        """Create user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Overview dashboard with key metrics
        overview = self._create_overview()
        layout.addWidget(overview)

        # Tab widget for detailed stats
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Create tabs
        self.tabs.addTab(self._create_activity_tab(), "Activity")
        self.tabs.addTab(self._create_personas_tab(), "Personas")
        self.tabs.addTab(self._create_chats_tab(), "Top Chats")
        self.tabs.addTab(self._create_users_tab(), "Top Users")
        self.tabs.addTab(self._create_decisions_tab(), "Decisions")

        layout.addWidget(self.tabs)

    def _create_header(self) -> QWidget:
        """Create header with title and refresh button."""
        header = QWidget()
        header.setObjectName("glassCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)

        # Title
        title = QLabel("Statistics & Analytics")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #f1f5f9;
            }
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh Data")
        refresh_btn.setMinimumHeight(36)
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
                padding: 8px 24px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5,
                    stop:1 #7c3aed
                );
            }
        """)
        refresh_btn.clicked.connect(self._load_stats)
        header_layout.addWidget(refresh_btn)

        return header

    def _create_overview(self) -> QWidget:
        """Create overview dashboard with key metrics."""
        overview = QWidget()
        layout = QVBoxLayout(overview)
        layout.setSpacing(12)

        # Metric cards grid
        grid = QGridLayout()
        grid.setSpacing(12)

        self.total_messages_card = MetricCard("Total Messages", "--", "#6366f1")
        self.bot_messages_card = MetricCard("Bot Messages", "--", "#8b5cf6")
        self.response_rate_card = MetricCard("Response Rate", "--", "#10b981")
        self.unique_users_card = MetricCard("Unique Users", "--", "#06b6d4")

        grid.addWidget(self.total_messages_card, 0, 0)
        grid.addWidget(self.bot_messages_card, 0, 1)
        grid.addWidget(self.response_rate_card, 0, 2)
        grid.addWidget(self.unique_users_card, 0, 3)

        self.unique_chats_card = MetricCard("Unique Chats", "--", "#f59e0b")
        self.messages_today_card = MetricCard("Messages Today", "--", "#ec4899")
        self.avg_decision_score_card = MetricCard("Avg Decision Score", "--", "#a78bfa")
        self.responses_today_card = MetricCard("Responses Today", "--", "#14b8a6")

        grid.addWidget(self.unique_chats_card, 1, 0)
        grid.addWidget(self.messages_today_card, 1, 1)
        grid.addWidget(self.avg_decision_score_card, 1, 2)
        grid.addWidget(self.responses_today_card, 1, 3)

        layout.addLayout(grid)

        return overview

    def _create_activity_tab(self) -> QWidget:
        """Create Activity charts tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Info card
        info_card = QWidget()
        info_card.setObjectName("glassCard")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(24, 20, 24, 20)

        info_title = QLabel("Activity Charts")
        info_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #f1f5f9;
            }
        """)
        info_layout.addWidget(info_title)

        info_desc = QLabel(
            "Visualizations of bot activity over time will be available here.\n\n"
            "Charts will include:\n"
            "• Messages timeline (last 7/30 days)\n"
            "• Response rate over time\n"
            "• Messages by hour of day\n"
            "• Messages by day of week\n\n"
            "Note: Matplotlib integration for charts is coming soon."
        )
        info_desc.setWordWrap(True)
        info_desc.setStyleSheet("color: #cbd5e1; font-size: 14px; line-height: 1.6;")
        info_layout.addWidget(info_desc)

        layout.addWidget(info_card)
        layout.addStretch()

        return widget

    def _create_personas_tab(self) -> QWidget:
        """Create Personas usage tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Persona stats card
        stats_card = QWidget()
        stats_card.setObjectName("glassCard")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(24, 20, 24, 20)
        stats_layout.setSpacing(12)

        title = QLabel("Persona Usage Statistics")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 12px;
            }
        """)
        stats_layout.addWidget(title)

        self.persona_stats_label = QLabel("Loading...")
        self.persona_stats_label.setWordWrap(True)
        self.persona_stats_label.setStyleSheet("color: #cbd5e1; font-size: 14px;")
        stats_layout.addWidget(self.persona_stats_label)

        layout.addWidget(stats_card)

        # Note about charts
        note = QLabel("Pie chart visualization coming soon with matplotlib integration")
        note.setAlignment(Qt.AlignCenter)
        note.setStyleSheet("color: #94a3b8; font-size: 13px; font-style: italic;")
        layout.addWidget(note)

        layout.addStretch()

        return widget

    def _create_chats_tab(self) -> QWidget:
        """Create Top Chats tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Top chats card
        chats_card = QWidget()
        chats_card.setObjectName("glassCard")
        chats_layout = QVBoxLayout(chats_card)
        chats_layout.setContentsMargins(24, 20, 24, 20)
        chats_layout.setSpacing(12)

        title = QLabel("Top 10 Most Active Chats")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 12px;
            }
        """)
        chats_layout.addWidget(title)

        self.top_chats_label = QLabel("Loading...")
        self.top_chats_label.setWordWrap(True)
        self.top_chats_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 14px;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
        chats_layout.addWidget(self.top_chats_label)

        layout.addWidget(chats_card)
        layout.addStretch()

        return widget

    def _create_users_tab(self) -> QWidget:
        """Create Top Users tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Top users card
        users_card = QWidget()
        users_card.setObjectName("glassCard")
        users_layout = QVBoxLayout(users_card)
        users_layout.setContentsMargins(24, 20, 24, 20)
        users_layout.setSpacing(12)

        title = QLabel("Top 10 Most Active Users")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 12px;
            }
        """)
        users_layout.addWidget(title)

        self.top_users_label = QLabel("Loading...")
        self.top_users_label.setWordWrap(True)
        self.top_users_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 14px;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
        users_layout.addWidget(self.top_users_label)

        layout.addWidget(users_card)
        layout.addStretch()

        return widget

    def _create_decisions_tab(self) -> QWidget:
        """Create Decision Engine stats tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Decision stats card
        decisions_card = QWidget()
        decisions_card.setObjectName("glassCard")
        decisions_layout = QVBoxLayout(decisions_card)
        decisions_layout.setContentsMargins(24, 20, 24, 20)
        decisions_layout.setSpacing(12)

        title = QLabel("Decision Engine Statistics")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 12px;
            }
        """)
        decisions_layout.addWidget(title)

        self.decision_stats_label = QLabel("Loading...")
        self.decision_stats_label.setWordWrap(True)
        self.decision_stats_label.setStyleSheet("color: #cbd5e1; font-size: 14px;")
        decisions_layout.addWidget(self.decision_stats_label)

        layout.addWidget(decisions_card)
        layout.addStretch()

        return widget

    def _load_stats(self):
        """Load all statistics."""
        try:
            # Get general stats (async call wrapped in sync)
            stats = asyncio.run(self.stats_collector.get_general_stats())

            # Update overview cards
            self.total_messages_card.findChild(QLabel).setText(str(stats.total_messages))
            self.bot_messages_card.findChild(QLabel).setText(str(stats.bot_messages))

            # Calculate response rate
            if stats.user_messages > 0:
                response_rate = (stats.bot_messages / stats.user_messages) * 100
                self.response_rate_card.findChild(QLabel).setText(f"{response_rate:.1f}%")
            else:
                self.response_rate_card.findChild(QLabel).setText("0%")

            self.unique_users_card.findChild(QLabel).setText(str(stats.unique_users))
            self.unique_chats_card.findChild(QLabel).setText(str(stats.unique_chats))
            self.messages_today_card.findChild(QLabel).setText(str(stats.messages_today))

            if stats.avg_decision_score is not None:
                self.avg_decision_score_card.findChild(QLabel).setText(f"{stats.avg_decision_score:.2f}")
            else:
                self.avg_decision_score_card.findChild(QLabel).setText("--")

            self.responses_today_card.findChild(QLabel).setText(str(stats.responses_today))

            # Load persona stats
            self._load_persona_stats()

            # Load top chats
            self._load_top_chats()

            # Load top users
            self._load_top_users()

            # Load decision stats
            self._load_decision_stats()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load statistics:\n{e}")

    def _load_persona_stats(self):
        """Load persona usage statistics."""
        try:
            persona_stats = asyncio.run(self.stats_collector.get_persona_stats())

            if not persona_stats:
                self.persona_stats_label.setText("No persona data available yet.")
                return

            # Format persona stats
            text = ""
            for stat in persona_stats:
                text += f"{stat.persona_name}: {stat.usage_count} uses ({stat.percentage:.1f}%)\n"

            self.persona_stats_label.setText(text.strip())

        except Exception as e:
            self.persona_stats_label.setText(f"Error loading persona stats: {e}")

    def _load_top_chats(self):
        """Load top chats statistics."""
        try:
            top_chats = asyncio.run(self.stats_collector.get_top_chats(limit=10))

            if not top_chats:
                self.top_chats_label.setText("No chat data available yet.")
                return

            # Format top chats
            text = ""
            for i, chat in enumerate(top_chats, 1):
                text += f"{i}. Chat {chat.chat_id}\n"
                text += f"   Messages: {chat.total_messages}, "
                text += f"Users: {chat.unique_users}, "
                text += f"Bot: {chat.bot_messages}\n"
                if chat.last_message:
                    text += f"   Last: {chat.last_message}\n"
                text += "\n"

            self.top_chats_label.setText(text.strip())

        except Exception as e:
            self.top_chats_label.setText(f"Error loading top chats: {e}")

    def _load_top_users(self):
        """Load top users statistics."""
        try:
            top_users = asyncio.run(self.stats_collector.get_top_users(limit=10))

            if not top_users:
                self.top_users_label.setText("No user data available yet.")
                return

            # Format top users
            text = ""
            for i, user in enumerate(top_users, 1):
                username = user.username or f"User {user.user_id}"
                text += f"{i}. {username}\n"
                text += f"   Messages: {user.total_messages}, "
                text += f"Chats: {user.total_chats}\n"
                text += f"   Relationship: {user.relationship_level}, "
                text += f"Trust: {user.trust_score:.2f}\n"
                if user.last_interaction:
                    text += f"   Last seen: {user.last_interaction}\n"
                text += "\n"

            self.top_users_label.setText(text.strip())

        except Exception as e:
            self.top_users_label.setText(f"Error loading top users: {e}")

    def _load_decision_stats(self):
        """Load decision engine statistics."""
        try:
            decision_stats = asyncio.run(self.stats_collector.get_decision_stats())

            if not decision_stats:
                self.decision_stats_label.setText("No decision data available yet.")
                return

            # Format decision stats
            text = f"Average Score: {decision_stats.avg_score:.3f}\n"
            text += f"Min Score: {decision_stats.min_score:.3f}\n"
            text += f"Max Score: {decision_stats.max_score:.3f}\n\n"

            text += "Distribution:\n"
            text += f"  Low (<0.3):    {decision_stats.distribution['low']} decisions\n"
            text += f"  Medium (0.3-0.7): {decision_stats.distribution['medium']} decisions\n"
            text += f"  High (≥0.7):   {decision_stats.distribution['high']} decisions\n"

            self.decision_stats_label.setText(text)

        except Exception as e:
            self.decision_stats_label.setText(f"Error loading decision stats: {e}")
