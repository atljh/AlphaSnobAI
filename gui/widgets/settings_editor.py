"""Settings Editor Widget - Visual YAML Configuration Editor.

Provides a comprehensive interface for editing all bot configuration settings
with validation, defaults, and preview functionality.
"""

import sys
from pathlib import Path
from typing import Any, Dict
import yaml

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QMessageBox, QScrollArea,
    QGroupBox, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QTextEdit, QSlider, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_settings, Settings


class SettingsEditorWidget(QWidget):
    """Widget for editing bot configuration settings."""

    settings_changed = Signal()

    def __init__(self):
        super().__init__()

        # Load current settings
        self.settings = get_settings()
        self.config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        self.original_config = self._load_yaml()
        self.current_config = self.original_config.copy()

        # Track changes
        self.has_unsaved_changes = False

        # Create UI
        self._create_ui()

    def _create_ui(self):
        """Create user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget for different settings sections
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Create tabs
        self.tabs.addTab(self._create_general_tab(), "General")
        self.tabs.addTab(self._create_llm_tab(), "LLM")
        self.tabs.addTab(self._create_bot_tab(), "Bot Behavior")
        self.tabs.addTab(self._create_persona_tab(), "Persona")
        self.tabs.addTab(self._create_typing_tab(), "Typing & Delays")
        self.tabs.addTab(self._create_decision_tab(), "Decision Engine")
        self.tabs.addTab(self._create_profiling_tab(), "Profiling")
        self.tabs.addTab(self._create_owner_learning_tab(), "Owner Learning")
        self.tabs.addTab(self._create_language_tab(), "Language")

        layout.addWidget(self.tabs)

        # Action buttons
        actions = self._create_actions()
        layout.addWidget(actions)

    def _create_header(self) -> QWidget:
        """Create header with title and status."""
        header = QWidget()
        header.setObjectName("glassCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)

        # Title
        title = QLabel("Configuration Editor")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: 700;
                color: #f1f5f9;
            }
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Status label
        self.status_label = QLabel("No unsaved changes")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #10b981;
                font-weight: 600;
            }
        """)
        header_layout.addWidget(self.status_label)

        return header

    def _create_general_tab(self) -> QWidget:
        """Create General settings tab (Telegram, Paths, Daemon)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        # Telegram section
        telegram_group = QGroupBox("Telegram")
        telegram_group.setObjectName("glassCard")
        telegram_layout = QFormLayout(telegram_group)

        self.session_name_input = QLineEdit(self.current_config.get("telegram", {}).get("session_name", ""))
        telegram_layout.addRow("Session Name:", self.session_name_input)

        content_layout.addWidget(telegram_group)

        # Paths section
        paths_group = QGroupBox("Paths")
        paths_group.setObjectName("glassCard")
        paths_layout = QFormLayout(paths_group)

        paths = self.current_config.get("paths", {})
        self.corpus_path_input = QLineEdit(paths.get("corpus", ""))
        self.database_path_input = QLineEdit(paths.get("database", ""))
        self.logs_path_input = QLineEdit(paths.get("logs", ""))

        paths_layout.addRow("Corpus:", self.corpus_path_input)
        paths_layout.addRow("Database:", self.database_path_input)
        paths_layout.addRow("Logs:", self.logs_path_input)

        content_layout.addWidget(paths_group)

        # Daemon section
        daemon_group = QGroupBox("Daemon")
        daemon_group.setObjectName("glassCard")
        daemon_layout = QFormLayout(daemon_group)

        daemon = self.current_config.get("daemon", {})
        self.pid_file_input = QLineEdit(daemon.get("pid_file", ""))
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentText(daemon.get("log_level", "INFO"))
        self.auto_restart_check = QCheckBox()
        self.auto_restart_check.setChecked(daemon.get("auto_restart", False))

        daemon_layout.addRow("PID File:", self.pid_file_input)
        daemon_layout.addRow("Log Level:", self.log_level_combo)
        daemon_layout.addRow("Auto Restart:", self.auto_restart_check)

        content_layout.addWidget(daemon_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_llm_tab(self) -> QWidget:
        """Create LLM settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        llm_group = QGroupBox("LLM Configuration")
        llm_group.setObjectName("glassCard")
        llm_layout = QFormLayout(llm_group)

        llm = self.current_config.get("llm", {})

        # Provider
        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItems(["openai", "claude"])
        self.llm_provider_combo.setCurrentText(llm.get("provider", "openai"))
        llm_layout.addRow("Provider:", self.llm_provider_combo)

        # Model
        self.llm_model_input = QLineEdit(llm.get("model", ""))
        llm_layout.addRow("Model:", self.llm_model_input)

        # Temperature
        temp_container = QWidget()
        temp_layout = QHBoxLayout(temp_container)
        temp_layout.setContentsMargins(0, 0, 0, 0)

        self.llm_temp_slider = QSlider(Qt.Horizontal)
        self.llm_temp_slider.setMinimum(0)
        self.llm_temp_slider.setMaximum(200)  # 0.0 to 2.0
        self.llm_temp_slider.setValue(int(llm.get("temperature", 0.9) * 100))
        self.llm_temp_label = QLabel(f"{llm.get('temperature', 0.9):.2f}")
        self.llm_temp_slider.valueChanged.connect(
            lambda v: self.llm_temp_label.setText(f"{v/100:.2f}")
        )

        temp_layout.addWidget(self.llm_temp_slider)
        temp_layout.addWidget(self.llm_temp_label)
        llm_layout.addRow("Temperature:", temp_container)

        # Max Tokens
        self.llm_max_tokens_spin = QSpinBox()
        self.llm_max_tokens_spin.setRange(1, 4096)
        self.llm_max_tokens_spin.setValue(llm.get("max_tokens", 500))
        llm_layout.addRow("Max Tokens:", self.llm_max_tokens_spin)

        content_layout.addWidget(llm_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_bot_tab(self) -> QWidget:
        """Create Bot Behavior settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        bot_group = QGroupBox("Bot Behavior")
        bot_group.setObjectName("glassCard")
        bot_layout = QFormLayout(bot_group)

        bot = self.current_config.get("bot", {})

        # Response Mode
        self.response_mode_combo = QComboBox()
        self.response_mode_combo.addItems(["all", "specific_users", "probability", "mentioned"])
        self.response_mode_combo.setCurrentText(bot.get("response_mode", "all"))
        bot_layout.addRow("Response Mode:", self.response_mode_combo)

        # Response Probability
        prob_container = QWidget()
        prob_layout = QHBoxLayout(prob_container)
        prob_layout.setContentsMargins(0, 0, 0, 0)

        self.response_prob_slider = QSlider(Qt.Horizontal)
        self.response_prob_slider.setMinimum(0)
        self.response_prob_slider.setMaximum(100)
        self.response_prob_slider.setValue(int(bot.get("response_probability", 0.3) * 100))
        self.response_prob_label = QLabel(f"{bot.get('response_probability', 0.3):.2f}")
        self.response_prob_slider.valueChanged.connect(
            lambda v: self.response_prob_label.setText(f"{v/100:.2f}")
        )

        prob_layout.addWidget(self.response_prob_slider)
        prob_layout.addWidget(self.response_prob_label)
        bot_layout.addRow("Response Probability:", prob_container)

        # Context Length
        self.context_length_spin = QSpinBox()
        self.context_length_spin.setRange(1, 200)
        self.context_length_spin.setValue(bot.get("context_length", 50))
        bot_layout.addRow("Context Length:", self.context_length_spin)

        # Allowed Users
        self.allowed_users_input = QTextEdit()
        self.allowed_users_input.setMaximumHeight(80)
        allowed_users = bot.get("allowed_users", [])
        self.allowed_users_input.setPlainText("\n".join(map(str, allowed_users)))
        bot_layout.addRow("Allowed Users (one per line):", self.allowed_users_input)

        content_layout.addWidget(bot_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_persona_tab(self) -> QWidget:
        """Create Persona settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Persona settings - Coming soon")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        return widget

    def _create_typing_tab(self) -> QWidget:
        """Create Typing & Delays settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Typing & Delays settings - Coming soon")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        return widget

    def _create_decision_tab(self) -> QWidget:
        """Create Decision Engine settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Decision Engine settings - Coming soon")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        return widget

    def _create_profiling_tab(self) -> QWidget:
        """Create Profiling settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        label = QLabel("Profiling settings - Coming soon")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        return widget

    def _create_owner_learning_tab(self) -> QWidget:
        """Create Owner Learning settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        ol_group = QGroupBox("Owner Learning")
        ol_group.setObjectName("glassCard")
        ol_layout = QFormLayout(ol_group)

        ol = self.current_config.get("owner_learning", {})

        # Enabled
        self.ol_enabled_check = QCheckBox()
        self.ol_enabled_check.setChecked(ol.get("enabled", True))
        ol_layout.addRow("Enabled:", self.ol_enabled_check)

        # Auto Collect
        self.ol_auto_collect_check = QCheckBox()
        self.ol_auto_collect_check.setChecked(ol.get("auto_collect", False))
        ol_layout.addRow("Auto Collect:", self.ol_auto_collect_check)

        # Min Samples
        self.ol_min_samples_spin = QSpinBox()
        self.ol_min_samples_spin.setRange(1, 1000)
        self.ol_min_samples_spin.setValue(ol.get("min_samples", 50))
        ol_layout.addRow("Min Samples:", self.ol_min_samples_spin)

        # Owner User IDs
        self.ol_owner_ids_input = QTextEdit()
        self.ol_owner_ids_input.setMaximumHeight(80)
        owner_ids = ol.get("owner_user_ids", [])
        self.ol_owner_ids_input.setPlainText("\n".join(map(str, owner_ids)))
        ol_layout.addRow("Owner User IDs (one per line):", self.ol_owner_ids_input)

        content_layout.addWidget(ol_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_language_tab(self) -> QWidget:
        """Create Language settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)

        lang_group = QGroupBox("Language")
        lang_group.setObjectName("glassCard")
        lang_layout = QFormLayout(lang_group)

        lang = self.current_config.get("language", {})

        # Auto Detect
        self.lang_auto_detect_check = QCheckBox()
        self.lang_auto_detect_check.setChecked(lang.get("auto_detect", True))
        lang_layout.addRow("Auto Detect:", self.lang_auto_detect_check)

        # Default Language
        self.lang_default_combo = QComboBox()
        self.lang_default_combo.addItems(["ru", "en"])
        self.lang_default_combo.setCurrentText(lang.get("default", "ru"))
        lang_layout.addRow("Default Language:", self.lang_default_combo)

        content_layout.addWidget(lang_group)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_actions(self) -> QWidget:
        """Create action buttons."""
        actions = QWidget()
        actions.setObjectName("glassCard")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(20, 16, 20, 16)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setMinimumHeight(44)
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: rgba(71, 85, 105, 0.5);
                color: white;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background: rgba(71, 85, 105, 0.7);
            }
        """)
        reset_btn.clicked.connect(self._on_reset_clicked)
        actions_layout.addWidget(reset_btn)

        actions_layout.addStretch()

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.setMinimumHeight(44)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet("""
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
                padding: 10px 28px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5,
                    stop:1 #7c3aed
                );
            }
        """)
        save_btn.clicked.connect(self._on_save_clicked)
        actions_layout.addWidget(save_btn)

        # Save & Apply button
        save_apply_btn = QPushButton("Save & Restart Bot")
        save_apply_btn.setMinimumHeight(44)
        save_apply_btn.setCursor(Qt.PointingHandCursor)
        save_apply_btn.setStyleSheet("""
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
        save_apply_btn.clicked.connect(self._on_save_apply_clicked)
        actions_layout.addWidget(save_apply_btn)

        return actions

    def _load_yaml(self) -> Dict[str, Any]:
        """Load current YAML configuration."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            QMessageBox.warning(
                self,
                "Load Error",
                f"Failed to load configuration:\n{e}"
            )
            return {}

    def _collect_current_values(self) -> Dict[str, Any]:
        """Collect current values from all inputs."""
        config = self.current_config.copy()

        # General tab
        config.setdefault("telegram", {})["session_name"] = self.session_name_input.text()

        config.setdefault("paths", {})["corpus"] = self.corpus_path_input.text()
        config["paths"]["database"] = self.database_path_input.text()
        config["paths"]["logs"] = self.logs_path_input.text()

        config.setdefault("daemon", {})["pid_file"] = self.pid_file_input.text()
        config["daemon"]["log_level"] = self.log_level_combo.currentText()
        config["daemon"]["auto_restart"] = self.auto_restart_check.isChecked()

        # LLM tab
        config.setdefault("llm", {})["provider"] = self.llm_provider_combo.currentText()
        config["llm"]["model"] = self.llm_model_input.text()
        config["llm"]["temperature"] = self.llm_temp_slider.value() / 100.0
        config["llm"]["max_tokens"] = self.llm_max_tokens_spin.value()

        # Bot tab
        config.setdefault("bot", {})["response_mode"] = self.response_mode_combo.currentText()
        config["bot"]["response_probability"] = self.response_prob_slider.value() / 100.0
        config["bot"]["context_length"] = self.context_length_spin.value()

        # Parse allowed users
        allowed_users_text = self.allowed_users_input.toPlainText().strip()
        if allowed_users_text:
            config["bot"]["allowed_users"] = [
                int(uid.strip()) for uid in allowed_users_text.split('\n') if uid.strip()
            ]
        else:
            config["bot"]["allowed_users"] = []

        # Owner Learning tab
        config.setdefault("owner_learning", {})["enabled"] = self.ol_enabled_check.isChecked()
        config["owner_learning"]["auto_collect"] = self.ol_auto_collect_check.isChecked()
        config["owner_learning"]["min_samples"] = self.ol_min_samples_spin.value()

        # Parse owner user IDs
        owner_ids_text = self.ol_owner_ids_input.toPlainText().strip()
        if owner_ids_text:
            config["owner_learning"]["owner_user_ids"] = [
                int(uid.strip()) for uid in owner_ids_text.split('\n') if uid.strip()
            ]
        else:
            config["owner_learning"]["owner_user_ids"] = []

        # Language tab
        config.setdefault("language", {})["auto_detect"] = self.lang_auto_detect_check.isChecked()
        config["language"]["default"] = self.lang_default_combo.currentText()

        return config

    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to YAML file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save configuration:\n{e}"
            )
            return False

    def _on_save_clicked(self):
        """Handle Save button click."""
        config = self._collect_current_values()

        if self._save_config(config):
            self.current_config = config
            self.original_config = config.copy()
            self.has_unsaved_changes = False
            self.status_label.setText("Settings saved successfully!")
            self.status_label.setStyleSheet("QLabel { color: #10b981; font-size: 13px; font-weight: 600; }")

            QMessageBox.information(
                self,
                "Success",
                "Settings saved successfully!\n\nRestart the bot for changes to take effect."
            )

            self.settings_changed.emit()

    def _on_save_apply_clicked(self):
        """Handle Save & Restart button click."""
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Save settings and restart the bot?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._on_save_clicked()
            # TODO: Signal main window to restart bot

    def _on_reset_clicked(self):
        """Handle Reset button click."""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Reset all settings to defaults?\n\nThis will discard unsaved changes.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Reload from file
            self.current_config = self._load_yaml()
            # TODO: Reload all input widgets
            QMessageBox.information(self, "Reset", "Settings reset to defaults.")
