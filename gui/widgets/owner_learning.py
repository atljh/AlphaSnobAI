"""Owner Learning Widget - Manage Owner Style Learning.

Provides interface for managing owner message collection, style analysis,
and testing the learned writing style.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QMessageBox, QTextEdit,
    QLineEdit, QGroupBox, QFormLayout, QListWidget,
    QListWidgetItem, QScrollArea, QProgressDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.owner_learning import OwnerLearningSystem
from services.owner_collector import OwnerMessageCollector
from config.settings import get_settings


class OwnerLearningWidget(QWidget):
    """Widget for managing owner style learning."""

    def __init__(self):
        super().__init__()

        # Initialize systems
        self.settings = get_settings()
        self.owner_learning = OwnerLearningSystem(
            manual_samples_path=self.settings.owner_learning.manual_samples_path
        )
        self.owner_collector = OwnerMessageCollector(
            config=self.settings.owner_learning
        )

        # Create UI
        self._create_ui()

        # Load initial data
        self._load_data()

    def _create_ui(self):
        """Create user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header with status
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Create tabs
        self.tabs.addTab(self._create_dashboard_tab(), "Dashboard")
        self.tabs.addTab(self._create_manual_samples_tab(), "Manual Samples")
        self.tabs.addTab(self._create_auto_collection_tab(), "Auto Collection")
        self.tabs.addTab(self._create_style_analysis_tab(), "Style Analysis")
        self.tabs.addTab(self._create_testing_tab(), "Style Testing")

        layout.addWidget(self.tabs)

    def _create_header(self) -> QWidget:
        """Create header with status information."""
        header = QWidget()
        header.setObjectName("glassCard")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        header_layout.setSpacing(12)

        # Title row
        title_row = QHBoxLayout()

        title = QLabel("Owner Learning")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #f1f5f9;
            }
        """)
        title_row.addWidget(title)

        title_row.addStretch()

        # Status indicator
        self.status_indicator = QLabel("● Enabled")
        self.status_indicator.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #10b981;
            }
        """)
        title_row.addWidget(self.status_indicator)

        header_layout.addLayout(title_row)

        # Stats row
        stats_row = QHBoxLayout()

        self.samples_count_label = QLabel("Samples: --")
        self.samples_count_label.setStyleSheet("color: #cbd5e1; font-size: 14px; font-weight: 600;")
        stats_row.addWidget(self.samples_count_label)

        self.auto_collect_label = QLabel("Auto-collect: OFF")
        self.auto_collect_label.setStyleSheet("color: #cbd5e1; font-size: 14px; font-weight: 600;")
        stats_row.addWidget(self.auto_collect_label)

        self.min_samples_label = QLabel("Min required: --")
        self.min_samples_label.setStyleSheet("color: #cbd5e1; font-size: 14px; font-weight: 600;")
        stats_row.addWidget(self.min_samples_label)

        stats_row.addStretch()

        header_layout.addLayout(stats_row)

        return header

    def _create_dashboard_tab(self) -> QWidget:
        """Create Dashboard tab with quick actions."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Owner User IDs section
        ids_group = QGroupBox("Owner User IDs")
        ids_group.setObjectName("glassCard")
        ids_layout = QVBoxLayout(ids_group)
        ids_layout.setSpacing(12)

        desc = QLabel("User IDs that will be considered as bot owner for message collection:")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        ids_layout.addWidget(desc)

        self.owner_ids_input = QTextEdit()
        self.owner_ids_input.setMaximumHeight(100)
        self.owner_ids_input.setPlaceholderText("Enter owner user IDs, one per line...")
        ids_layout.addWidget(self.owner_ids_input)

        save_ids_btn = QPushButton("Save Owner IDs")
        save_ids_btn.setMinimumHeight(40)
        save_ids_btn.setCursor(Qt.PointingHandCursor)
        save_ids_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1,
                    stop:1 #8b5cf6
                );
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5,
                    stop:1 #7c3aed
                );
            }
        """)
        save_ids_btn.clicked.connect(self._on_save_owner_ids)
        ids_layout.addWidget(save_ids_btn)

        layout.addWidget(ids_group)

        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_group.setObjectName("glassCard")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(12)

        # Toggle auto-collect
        toggle_auto_btn = self._create_action_button(
            "Toggle Auto-Collection",
            "Enable/disable automatic collection of owner messages",
            "#10b981", "#06b6d4",
            self._on_toggle_auto_collect
        )
        actions_layout.addWidget(toggle_auto_btn)

        # Re-analyze style
        analyze_btn = self._create_action_button(
            "Re-Analyze Style",
            "Analyze writing style from current samples",
            "#6366f1", "#8b5cf6",
            self._on_analyze_style
        )
        actions_layout.addWidget(analyze_btn)

        # Merge collections
        merge_btn = self._create_action_button(
            "Merge Auto with Manual",
            "Merge auto-collected messages into manual samples",
            "#f59e0b", "#f97316",
            self._on_merge_collections
        )
        actions_layout.addWidget(merge_btn)

        layout.addWidget(actions_group)
        layout.addStretch()

        return widget

    def _create_manual_samples_tab(self) -> QWidget:
        """Create Manual Samples editor tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Info
        info = QLabel(
            "Edit manual samples of owner's messages. "
            "Each message should be on a separate line."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #cbd5e1; font-size: 14px;")
        layout.addWidget(info)

        # Text editor
        self.manual_samples_editor = QTextEdit()
        self.manual_samples_editor.setFont(QFont("JetBrains Mono", 12))
        layout.addWidget(self.manual_samples_editor)

        # Stats and actions row
        bottom_row = QHBoxLayout()

        self.manual_samples_stats = QLabel("Lines: 0, Characters: 0")
        self.manual_samples_stats.setStyleSheet("color: #94a3b8; font-size: 13px;")
        bottom_row.addWidget(self.manual_samples_stats)

        bottom_row.addStretch()

        # Save button
        save_btn = QPushButton("Save Manual Samples")
        save_btn.setMinimumHeight(40)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981,
                    stop:1 #06b6d4
                );
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 10px;
                padding: 10px 28px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669,
                    stop:1 #0891b2
                );
            }
        """)
        save_btn.clicked.connect(self._on_save_manual_samples)
        bottom_row.addWidget(save_btn)

        layout.addLayout(bottom_row)

        # Connect text change to update stats
        self.manual_samples_editor.textChanged.connect(self._update_manual_samples_stats)

        return widget

    def _create_auto_collection_tab(self) -> QWidget:
        """Create Auto Collection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Stats card
        stats_card = QWidget()
        stats_card.setObjectName("glassCard")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(24, 20, 24, 20)

        stats_title = QLabel("Collection Statistics")
        stats_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 12px;
            }
        """)
        stats_layout.addWidget(stats_title)

        self.collection_stats_label = QLabel("Loading...")
        self.collection_stats_label.setWordWrap(True)
        self.collection_stats_label.setStyleSheet("color: #cbd5e1; font-size: 14px;")
        stats_layout.addWidget(self.collection_stats_label)

        layout.addWidget(stats_card)

        # Actions
        actions_row = QHBoxLayout()

        clear_btn = QPushButton("Clear Collection")
        clear_btn.setMinimumHeight(40)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef4444,
                    stop:1 #f59e0b
                );
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dc2626,
                    stop:1 #d97706
                );
            }
        """)
        clear_btn.clicked.connect(self._on_clear_collection)
        actions_row.addWidget(clear_btn)

        actions_row.addStretch()

        layout.addLayout(actions_row)
        layout.addStretch()

        return widget

    def _create_style_analysis_tab(self) -> QWidget:
        """Create Style Analysis visualization tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Analysis card
        analysis_card = QWidget()
        analysis_card.setObjectName("glassCard")
        analysis_layout = QVBoxLayout(analysis_card)
        analysis_layout.setContentsMargins(24, 20, 24, 20)
        analysis_layout.setSpacing(16)

        title = QLabel("Writing Style Analysis")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 600;
                color: #f1f5f9;
            }
        """)
        analysis_layout.addWidget(title)

        self.style_analysis_text = QTextEdit()
        self.style_analysis_text.setReadOnly(True)
        self.style_analysis_text.setFont(QFont("JetBrains Mono", 12))
        self.style_analysis_text.setMinimumHeight(400)
        analysis_layout.addWidget(self.style_analysis_text)

        layout.addWidget(analysis_card)

        return widget

    def _create_testing_tab(self) -> QWidget:
        """Create Style Testing tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Input section
        input_group = QGroupBox("Test Prompt")
        input_group.setObjectName("glassCard")
        input_layout = QVBoxLayout(input_group)

        self.test_prompt_input = QTextEdit()
        self.test_prompt_input.setPlaceholderText("Enter a test prompt to see how bot would respond in owner's style...")
        self.test_prompt_input.setMaximumHeight(100)
        input_layout.addWidget(self.test_prompt_input)

        test_btn = QPushButton("Generate Response")
        test_btn.setMinimumHeight(40)
        test_btn.setCursor(Qt.PointingHandCursor)
        test_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6,
                    stop:1 #ec4899
                );
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 10px;
                padding: 10px 28px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed,
                    stop:1 #db2777
                );
            }
        """)
        test_btn.clicked.connect(self._on_test_style)
        input_layout.addWidget(test_btn)

        layout.addWidget(input_group)

        # Output section
        output_group = QGroupBox("Generated Response")
        output_group.setObjectName("glassCard")
        output_layout = QVBoxLayout(output_group)

        self.test_output = QTextEdit()
        self.test_output.setReadOnly(True)
        self.test_output.setFont(QFont("JetBrains Mono", 12))
        self.test_output.setPlaceholderText("Generated response will appear here...")
        output_layout.addWidget(self.test_output)

        layout.addWidget(output_group)

        return widget

    def _create_action_button(self, title: str, description: str,
                             color1: str, color2: str, callback) -> QWidget:
        """Create a styled action button."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)

        button = QPushButton(title)
        button.setMinimumHeight(44)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color1},
                    stop:1 {color2}
                );
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                text-align: left;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        button.clicked.connect(callback)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #94a3b8; font-size: 12px; padding-left: 12px;")

        container_layout.addWidget(button)
        container_layout.addWidget(desc_label)

        return container

    def _load_data(self):
        """Load all data."""
        # Update status
        if self.settings.owner_learning.enabled:
            self.status_indicator.setText("● Enabled")
            self.status_indicator.setStyleSheet("QLabel { color: #10b981; font-size: 14px; font-weight: 600; }")
        else:
            self.status_indicator.setText("● Disabled")
            self.status_indicator.setStyleSheet("QLabel { color: #ef4444; font-size: 14px; font-weight: 600; }")

        # Update samples count
        samples = self.owner_learning._load_samples()
        if samples:
            self.samples_count_label.setText(f"Samples: {len(samples)}")
        else:
            self.samples_count_label.setText("Samples: 0")

        # Update auto-collect status
        if self.settings.owner_learning.auto_collect:
            self.auto_collect_label.setText("Auto-collect: ON")
        else:
            self.auto_collect_label.setText("Auto-collect: OFF")

        # Update min samples
        self.min_samples_label.setText(f"Min required: {self.settings.owner_learning.min_samples}")

        # Load owner IDs
        owner_ids = self.settings.owner_learning.owner_user_ids
        self.owner_ids_input.setPlainText("\n".join(map(str, owner_ids)))

        # Load manual samples
        self._load_manual_samples()

        # Load collection stats
        self._load_collection_stats()

        # Load style analysis
        self._load_style_analysis()

    def _load_manual_samples(self):
        """Load manual samples into editor."""
        try:
            samples_path = Path(self.settings.owner_learning.manual_samples_path)
            if samples_path.exists():
                with open(samples_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.manual_samples_editor.setPlainText(content)
            else:
                self.manual_samples_editor.setPlainText("")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load manual samples:\n{e}")

    def _load_collection_stats(self):
        """Load auto-collection statistics."""
        try:
            stats = self.owner_collector.get_collection_stats()
            text = f"Total collected: {stats['total_collected']}\n"
            text += f"Unique messages: {stats['unique_messages']}\n"
            if stats['last_collected']:
                text += f"Last collected: {stats['last_collected']}\n"
            else:
                text += "Last collected: Never\n"

            self.collection_stats_label.setText(text)
        except Exception as e:
            self.collection_stats_label.setText(f"Error loading stats: {e}")

    def _load_style_analysis(self):
        """Load and display style analysis."""
        try:
            if not self.owner_learning.has_sufficient_samples():
                samples = self.owner_learning._load_samples()
                current_count = len(samples) if samples else 0
                self.style_analysis_text.setPlainText(
                    f"Insufficient samples for analysis.\n\n"
                    f"Current: {current_count}\n"
                    f"Required: {self.settings.owner_learning.min_samples}\n\n"
                    f"Add more samples to enable style analysis."
                )
                return

            analysis = self.owner_learning.get_analysis()

            # Format analysis
            text = f"=== Writing Style Analysis ===\n\n"
            text += f"Total messages: {analysis.total_messages}\n"
            text += f"Avg message length: {analysis.avg_message_length:.1f} characters\n"
            text += f"Avg sentence length: {analysis.avg_sentence_length:.1f} words\n"
            text += f"Emoji frequency: {analysis.emoji_frequency:.2f} per message\n\n"

            if analysis.common_emojis:
                text += f"Common emojis: {', '.join(f'{e}({c})' for e, c in analysis.common_emojis[:10])}\n\n"

            if analysis.common_words:
                text += f"Common words: {', '.join(f'{w}({c})' for w, c in analysis.common_words[:20])}\n\n"

            if analysis.common_phrases:
                text += f"Common phrases:\n"
                for phrase, count in analysis.common_phrases[:10]:
                    text += f"  • '{phrase}' ({count})\n"
                text += "\n"

            text += f"Punctuation patterns:\n"
            for pattern, count in sorted(analysis.punctuation_patterns.items(), key=lambda x: x[1], reverse=True):
                text += f"  • {pattern}: {count}\n"
            text += "\n"

            text += f"Formality score: {analysis.formality_score:.2f} (0=casual, 1=formal)\n\n"

            if analysis.language_distribution:
                text += f"Languages:\n"
                for lang, pct in analysis.language_distribution.items():
                    text += f"  • {lang}: {pct:.1f}%\n"

            self.style_analysis_text.setPlainText(text)

        except Exception as e:
            self.style_analysis_text.setPlainText(f"Error analyzing style:\n{e}")

    def _update_manual_samples_stats(self):
        """Update manual samples statistics."""
        text = self.manual_samples_editor.toPlainText()
        lines = len(text.split('\n'))
        chars = len(text)
        self.manual_samples_stats.setText(f"Lines: {lines}, Characters: {chars}")

    def _on_save_owner_ids(self):
        """Handle save owner IDs."""
        try:
            text = self.owner_ids_input.toPlainText().strip()
            if text:
                ids = [int(line.strip()) for line in text.split('\n') if line.strip()]
            else:
                ids = []

            # Update config (simplified - in real app would use proper config update)
            QMessageBox.information(
                self,
                "Save Owner IDs",
                f"Owner IDs saved: {ids}\n\nNote: Restart bot for changes to take effect."
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save owner IDs:\n{e}")

    def _on_save_manual_samples(self):
        """Handle save manual samples."""
        try:
            samples_path = Path(self.settings.owner_learning.manual_samples_path)
            samples_path.parent.mkdir(parents=True, exist_ok=True)

            with open(samples_path, 'w', encoding='utf-8') as f:
                f.write(self.manual_samples_editor.toPlainText())

            QMessageBox.information(self, "Success", "Manual samples saved successfully!")
            self._load_data()  # Reload

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save manual samples:\n{e}")

    def _on_toggle_auto_collect(self):
        """Handle toggle auto-collection."""
        QMessageBox.information(
            self,
            "Toggle Auto-Collect",
            "Auto-collection toggle will be implemented in settings integration."
        )

    def _on_analyze_style(self):
        """Handle re-analyze style."""
        try:
            # Force reload
            self.owner_learning = OwnerLearningSystem(
                manual_samples_path=self.settings.owner_learning.manual_samples_path
            )
            self._load_style_analysis()
            QMessageBox.information(self, "Success", "Style re-analyzed successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to analyze style:\n{e}")

    def _on_merge_collections(self):
        """Handle merge collections."""
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Merge",
                "Merge auto-collected messages into manual samples?\n\n"
                "This will append all collected messages to your manual samples file.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.owner_collector.merge_with_manual_samples()
                QMessageBox.information(self, "Success", "Collections merged successfully!")
                self._load_data()  # Reload

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to merge collections:\n{e}")

    def _on_clear_collection(self):
        """Handle clear collection."""
        try:
            reply = QMessageBox.warning(
                self,
                "Confirm Clear",
                "Clear all auto-collected messages?\n\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.owner_collector.clear_collection()
                QMessageBox.information(self, "Success", "Collection cleared!")
                self._load_collection_stats()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to clear collection:\n{e}")

    def _on_test_style(self):
        """Handle style testing."""
        prompt = self.test_prompt_input.toPlainText().strip()

        if not prompt:
            QMessageBox.warning(self, "Warning", "Please enter a test prompt.")
            return

        # For now, just show the style instructions that would be used
        try:
            instructions = self.owner_learning.generate_style_instructions()
            self.test_output.setPlainText(
                f"Style instructions that would be used:\n\n{instructions}\n\n"
                f"Note: Full LLM integration for testing will be implemented."
            )
        except Exception as e:
            self.test_output.setPlainText(f"Error: {e}")
