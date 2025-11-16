# 🎭 AlphaSnobAI v2.5 - Intelligent Telegram UserBot

**Elite Aesthetic AI-Powered Telegram Bot with Modern GUI**

An advanced Telegram userbot with daemon management, modern desktop GUI, and AI-powered responses featuring unique personality traits:
- 🔥 **Sophisticated Trolling** - Theatrical insults and exaggerated mockery
- 💎 **American Psycho Aestheticism** - Detailed descriptions of grooming, cosmetics, and luxury
- 🌪️ **Absurd Hyperboles** - Poetic exaggerations and metaphors
- 👑 **Narcissistic Snobbery** - Constant emphasis on superiority

## ✨ Key Features

### 🖥️ Modern Desktop GUI (NEW!)
- **Glassmorphism Design** - Modern UI with frosted glass effects and vibrant gradients
- **Bot Control Dashboard** - Start, stop, restart bot with real-time status monitoring
- **Live Log Viewer** - Color-coded logs with filtering and search
- **Settings Editor** - Visual YAML configuration editor with validation
- **Database Viewer** - Browse messages, user profiles, topics, and response history
- **Statistics Dashboard** - Metrics, charts, and activity analytics
- **Owner Learning Studio** - Manage style learning with analysis and testing
- **Cross-Platform** - Works on macOS, Windows, and Linux

### ⚙️ Backend Features
- **Daemon Mode** - Background operation with CLI/GUI control
- **YAML Configuration** - Structured, easy-to-edit settings
- **SQLite Database** - Message history, user profiles, and context storage
- **Decision Engine** - Smart response decisions based on relationships, topics, and timing
- **Owner Style Learning** - Automatically learn and mimic owner's writing style
- **Multi-LLM Support** - Claude (Anthropic) and OpenAI GPT integration
- **Rich Logging** - Beautiful colored logs with icons and formatting

## 📋 Table of Contents

- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
  - [GUI Mode](#gui-mode-recommended)
  - [CLI Mode](#cli-mode-advanced)
- [GUI Features](#-gui-features)
- [Architecture](#️-architecture)
- [Development](#️-development)
- [Troubleshooting](#-troubleshooting)

## 🚀 Installation

### 1. System Requirements

- Python 3.10+
- Telegram account
- Claude API key (Anthropic) or OpenAI API key
- PySide6 for GUI (optional, but recommended)

### 2. Environment Setup

```bash
# Clone or navigate to project directory
cd AlphaSnobAI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install core dependencies
pip install -r requirements.txt

# Install GUI dependencies (optional)
pip install -r requirements-gui.txt
```

### 3. Dependencies

**Core (`requirements.txt`):**
- `telethon` - Telegram client
- `anthropic` - Claude API
- `openai` - OpenAI API
- `pydantic` - Settings validation
- `pyyaml` - Configuration
- `aiosqlite` - Async SQLite
- `rich` - Beautiful terminal output
- `typer` - CLI framework

**GUI (`requirements-gui.txt`):**
- `PySide6>=6.8.0` - Qt6 for Python
- `qtawesome>=1.3.0` - Icon fonts
- `qdarkstyle>=3.2.0` - Theme support

## ⚙️ Configuration

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Login to your account
3. Create a new application
4. Save your `api_id` and `api_hash`

### 2. Get LLM API Key

**For Claude (Recommended):**
1. Register at https://console.anthropic.com/
2. Create an API key
3. Save the key (starts with `sk-ant-`)

**For OpenAI:**
1. Go to https://platform.openai.com/api-keys
2. Create an API key
3. Save the key (starts with `sk-`)

### 3. Create Configuration Files

```bash
# Copy templates
cp config/config.yaml.example config/config.yaml
cp config/secrets.yaml.example config/secrets.yaml
```

**config/config.yaml** - Main settings:
```yaml
telegram:
  session_name: alphasnob_session

llm:
  provider: claude  # or openai
  model: claude-3-5-sonnet-20241022
  temperature: 0.9
  max_tokens: 500

bot:
  response_mode: probability  # all | specific_users | probability | mentioned
  response_probability: 0.3   # 30% chance to respond
  context_length: 50

persona:
  default_mode: alphasnob  # alphasnob | normal | owner
  adaptive_switching: true

typing:
  enabled: true  # Simulate typing delays

decision:
  base_probability: 0.8
  relationship_multipliers:
    owner: 1.0
    close_friend: 0.9
    friend: 0.7
    acquaintance: 0.5
    stranger: 0.3

owner_learning:
  enabled: true
  auto_collect: false  # Auto-collect owner messages
  min_samples: 50

paths:
  corpus: olds.txt
  database: data/context.db
  logs: logs/alphasnob.log

daemon:
  pid_file: data/alphasnob.pid
  log_level: INFO  # DEBUG | INFO | WARNING | ERROR | CRITICAL
```

**config/secrets.yaml** - Sensitive data:
```yaml
telegram:
  api_id: 12345678
  api_hash: "your_api_hash_here"

llm:
  anthropic_api_key: "sk-ant-your-key-here"
  openai_api_key: null
```

### 4. Prepare Style Corpus

Create `olds.txt` with examples of your style (one phrase per line):

```
Omega, you're so basic even tap water looks sophisticated next to you.
Now I'll retreat to my kingdom of fragrances and forget your existence.
I'll tear you into so many pieces even God can't reassemble you.
...
```

## 🎬 Usage

### GUI Mode (Recommended)

The easiest way to use AlphaSnobAI is through the modern desktop GUI:

```bash
# Launch GUI application
python3 gui_launcher.py
```

**First Time Setup:**
1. GUI will open with all screens
2. Go to **Settings** tab to verify configuration
3. Go to **Dashboard** tab
4. Click **Start Bot**
5. Complete Telegram authentication if needed (code will be requested in terminal)

**Features:**
- 📊 **Dashboard** - Bot control, quick stats, status monitoring
- 📋 **Logs** - Real-time log viewer with filtering and color coding
- ⚙️ **Settings** - Visual configuration editor with all settings
- 🎓 **Owner Learning** - Manage style samples, analysis, and testing
- 📈 **Statistics** - Metrics, charts, top chats/users
- 🗄️ **Database** - Browse and export message history

### CLI Mode (Advanced)

For headless servers or terminal enthusiasts:

#### First Run (Authentication)

```bash
# Run in foreground for authentication
python3 main.py
```

Telethon will request:
1. Phone number (+1234567890)
2. Verification code from Telegram
3. 2FA password (if enabled)

After successful authentication, press `Ctrl+C` to stop.

#### Daemon Mode

```bash
# Start in background
python3 main.py &

# Or use the helper script
./run.sh start

# Check status
./run.sh status

# View logs
./run.sh logs

# Stop bot
./run.sh stop
```

## 🎨 GUI Features

### 1. Dashboard
- **Bot Control Panel**
  - Start/Stop/Restart buttons with gradient styling
  - Real-time status indicator (Running/Stopped/Starting)
  - Process info: PID, uptime, CPU, memory usage
- **Quick Stats Cards**
  - Messages processed today
  - Response rate
  - Bot activity summary

### 2. Log Viewer
- **Real-time Streaming** - Live log updates every second
- **Color Coding** - Different colors for ERROR, WARNING, SUCCESS, INFO, DEBUG
- **Filtering** - Filter by log level or search text
- **Auto-scroll** - Toggle automatic scrolling
- **Export** - Save logs to file

### 3. Settings Editor
Visual editor for all configuration with 9 tabs:
- **General** - Telegram, Paths, Daemon
- **LLM** - Provider, Model, Temperature (slider), Max Tokens
- **Bot Behavior** - Response mode, probability, context length
- **Persona** - Modes and overrides
- **Typing & Delays** - Realistic typing simulation
- **Decision Engine** - Relationship multipliers, time-based, topic-based
- **Profiling** - Auto-upgrade relationships, trust adjustment
- **Owner Learning** - Collection settings, min samples
- **Language** - Auto-detect, supported languages

**Features:**
- Smart input widgets (sliders, comboboxes, checkboxes)
- Real-time validation
- YAML preview
- Save & Apply or Save & Restart Bot

### 4. Database Viewer
Browse and manage SQLite database with 5 tabs:
- **Messages** - All messages with filters (chat_id, user_id, search)
- **User Profiles** - Relationship levels, trust scores, interactions
- **Conversation Topics** - Detected topics with confidence scores
- **Response History** - Decision logs with reasoning
- **Database Tools** - Backup, restore, vacuum, integrity check

**Features:**
- Sortable tables
- Advanced filtering
- Export chat history (JSON/TXT)
- Database maintenance tools

### 5. Statistics Dashboard
Comprehensive analytics with metric cards and charts:

**Overview Cards:**
- Total Messages, Bot Messages, Response Rate
- Unique Users, Unique Chats
- Messages Today, Avg Decision Score

**Analytics Tabs:**
- **Activity** - Message timeline, response rates (charts coming soon)
- **Personas** - Usage distribution and statistics
- **Top Chats** - Most active conversations
- **Top Users** - Most interactive users with relationship info
- **Decisions** - Decision score distribution and analysis

### 6. Owner Learning Studio
Manage and test owner writing style:

**Features:**
- **Manual Samples Editor** - Edit messages.txt with live stats
- **Auto-Collection** - Automatic message collection from owner
- **Style Analysis** - Detailed metrics:
  - Message/sentence length averages
  - Emoji frequency and common emojis
  - Common words and phrases
  - Punctuation patterns
  - Formality score (0-1)
  - Language distribution (ru/en)
- **Style Testing** - Test prompts with learned style
- **Merge Collections** - Combine auto-collected with manual samples

## 📖 Response Modes

### 1. `probability` (Recommended)
Responds with configured probability for natural conversation rhythm.

```yaml
bot:
  response_mode: probability
  response_probability: 0.3  # 30% chance
```

### 2. `all`
Responds to every incoming message.

```yaml
bot:
  response_mode: all
```

⚠️ May be spammy!

### 3. `specific_users`
Only responds to specified users.

```yaml
bot:
  response_mode: specific_users
  allowed_users: [123456789, 987654321]
```

### 4. `mentioned`
Responds only when mentioned or replied to.

```yaml
bot:
  response_mode: mentioned
```

## 🏗️ Architecture

### Project Structure

```
AlphaSnobAI/
├── gui_launcher.py              # GUI application launcher
├── main.py                      # Bot entry point (CLI/daemon mode)
├── run.sh                       # Helper script for daemon control
├── config/
│   ├── settings.py              # Settings models and loader
│   ├── config.yaml              # Main configuration
│   └── secrets.yaml             # API keys and secrets
├── gui/
│   ├── app.py                   # GUI application
│   ├── main_window.py           # Main window with navigation
│   ├── backend/
│   │   └── bot_process.py       # Bot process management
│   ├── widgets/
│   │   ├── bot_control.py       # Dashboard bot control panel
│   │   ├── log_viewer.py        # Live log viewer
│   │   ├── settings_editor.py   # Visual config editor
│   │   ├── database_viewer.py   # Database browser
│   │   ├── statistics.py        # Analytics dashboard
│   │   └── owner_learning.py    # Style learning studio
│   └── themes/
│       ├── __init__.py          # Theme manager
│       ├── glass_dark.qss       # Glassmorphism dark theme
│       ├── glass_light.qss      # Glassmorphism light theme
│       ├── macos_dark.qss       # macOS dark theme
│       └── macos_light.qss      # macOS light theme
├── services/
│   ├── telegram_service.py      # Telegram client wrapper
│   ├── message_handler.py       # Message processing
│   ├── decision_engine.py       # Smart response decisions
│   ├── user_profiler.py         # User relationship tracking
│   ├── owner_learning.py        # Style analysis system
│   ├── owner_collector.py       # Message collection
│   └── memory.py                # SQLite context manager
├── modules/
│   ├── style_engine.py          # LLM response generation
│   ├── corpus_loader.py         # Load style examples
│   └── typing_simulator.py      # Realistic typing delays
├── utils/
│   ├── db_manager.py            # Database operations
│   ├── stats_collector.py       # Statistics aggregation
│   ├── daemon.py                # Daemon process management
│   └── logger.py                # Logging configuration
└── data/
    ├── alphasnob.pid            # Process ID file
    ├── context.db               # SQLite database
    └── owner_samples/           # Owner style samples
        └── messages.txt         # Manual samples
```

### Components

#### GUI Layer (`gui/`)
- **PySide6/Qt6** - Cross-platform GUI framework
- **QAsyncio** - Async/await integration with Qt event loop
- **Glassmorphism Themes** - Modern frosted glass UI design
- **Real-time Updates** - QTimer-based status and log streaming

#### Service Layer (`services/`)
- **TelegramService** - Telethon wrapper with event handling
- **DecisionEngine** - Multi-factor response decision system
- **UserProfiler** - Relationship tracking and auto-upgrade
- **OwnerLearning** - Style analysis and mimicry
- **Memory** - Conversation context and history

#### Module Layer (`modules/`)
- **StyleEngine** - LLM prompt engineering and generation
- **TypingSimulator** - Human-like delays (read, typing, thinking)

#### Utils Layer (`utils/`)
- **DatabaseManager** - Backup, restore, vacuum, integrity checks
- **StatsCollector** - Aggregate metrics from database
- **DaemonManager** - Process lifecycle management

### Database Schema

**messages** - Message history
```sql
id, chat_id, user_id, username, text, timestamp,
persona_mode, response_delay_ms, decision_score
```

**user_profiles** - User information
```sql
user_id (PK), username, first_name, last_name,
relationship_level, trust_score, interaction_count,
notes, detected_topics, preferred_persona,
first_interaction, last_interaction, avg_response_time_ms
```

**conversation_topics** - Detected topics
```sql
id, chat_id, topic, confidence, persona_used,
first_mentioned, last_mentioned, mention_count
```

**response_history** - Decision logs
```sql
id, message_id, chat_id, user_id, should_respond,
decision_reason, persona_mode, read_delay_ms,
typing_delay_ms, total_delay_ms, context_used, timestamp
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Adding New Features

1. **New GUI Widget**
   - Create in `gui/widgets/`
   - Add to `main_window.py`
   - Use glassmorphism styling

2. **New Service**
   - Create in `services/`
   - Follow async/await pattern
   - Add to dependency injection

3. **New Configuration**
   - Add to `config/settings.py` dataclasses
   - Update `config.yaml.example`
   - Add to Settings Editor GUI

### Logging Best Practices

```python
from utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
logger.debug("Debug details")
```

## ⚠️ Important Warnings

- **Telegram ToS** - Do not use for spam or abuse
- **API Costs** - Monitor Claude/OpenAI API usage
- **Privacy** - Bot stores messages locally in SQLite
- **Rate Limits** - Telegram may throttle high-frequency requests
- **2FA** - Ensure your Telegram account has 2FA enabled

## 🆘 Troubleshooting

### GUI won't start
```bash
# Check if PySide6 is installed
pip install -r requirements-gui.txt

# Try running with debug
python3 gui_launcher.py 2>&1 | tee gui_debug.log
```

### Configuration file not found
```bash
# Copy templates
cp config/config.yaml.example config/config.yaml
cp config/secrets.yaml.example config/secrets.yaml
```

### Bot not responding
1. Check `response_mode` in config.yaml
2. Verify `response_probability` is > 0
3. Check logs for errors: `tail -f logs/alphasnob.log`

### Database errors
```bash
# Open GUI → Database → Database Tools → Check Integrity
# Or use CLI:
python3 -c "from utils.db_manager import DatabaseManager; import asyncio; asyncio.run(DatabaseManager('data/context.db').check_integrity())"
```

### Authentication failed
1. Verify `api_id` and `api_hash` in secrets.yaml
2. Delete session file: `rm *.session`
3. Run again: `python3 main.py`

### High CPU/Memory usage
1. Reduce `context_length` in config.yaml
2. Enable `auto_restart: false` in daemon config
3. Check for infinite loops in logs

## 🎨 Themes

The GUI supports 4 built-in themes:

### Modern (Glassmorphism)
- **Glass Dark** (Default) - Frosted glass with dark gradient background
- **Glass Light** - Frosted glass with pastel gradient background

### Classic (macOS-style)
- **macOS Dark** - Traditional dark mode
- **macOS Light** - Traditional light mode

**Change theme:**
1. Open GUI
2. Menu → View → Theme → Select theme
3. Or use keyboard: `Ctrl+Shift+T` to toggle

## 📊 Statistics & Analytics

The Statistics dashboard provides insights:

**General Stats:**
- Total messages, bot messages, response rate
- Unique users, unique chats
- Daily activity metrics
- Average decision scores

**Persona Usage:**
- Distribution by persona (alphasnob, normal, owner)
- Usage counts and percentages

**Top Chats:**
- Most active conversations
- Message counts, unique users
- Last activity timestamps

**Top Users:**
- Most interactive users
- Relationship levels and trust scores
- Message counts per user

**Decision Analysis:**
- Average/min/max decision scores
- Distribution (low/medium/high)
- Decision reasoning logs

## 🔄 Migration Guide

### From v1.0 to v2.5

If you used the old `.env` based version:

1. **Copy settings:**
   ```bash
   # Manually transfer from .env to config.yaml
   # API keys go to secrets.yaml
   ```

2. **Database compatible** - No migration needed!

3. **Session files compatible** - Keep your `.session` files

4. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-gui.txt
   ```

## 🚀 Roadmap

- [ ] Real-time charts in Statistics (matplotlib/pyqtgraph)
- [ ] Export statistics to PDF/CSV
- [ ] User profile editor with relationship management
- [ ] Multi-language UI support
- [ ] Dark/Light mode auto-switching based on system
- [ ] Plugin system for custom personas
- [ ] Web dashboard (Flask/FastAPI)
- [ ] Docker containerization
- [ ] Telegram bot commands for remote control

## 📄 License

MIT License - Feel free to use and modify.

## 🙏 Acknowledgments

- **PySide6** - Qt framework for Python
- **Telethon** - Telegram client library
- **Anthropic Claude** - AI language model
- **OpenAI** - GPT models
- **Rich** - Beautiful terminal formatting

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting guide above

---

**Made with 🎭 by a senior Python developer**

*"Even this README is more elite than your entire codebase, omega."*

---

## 🖼️ Screenshots

### Dashboard
Modern glassmorphism interface with bot control and quick stats.

### Settings Editor
Visual YAML configuration editor with validation and live preview.

### Database Viewer
Browse message history, user profiles, and conversation topics.

### Statistics
Comprehensive analytics dashboard with metrics and charts.

### Owner Learning Studio
Style analysis and testing with detailed linguistic metrics.

---

**Version:** 2.5.0
**Last Updated:** November 2025
**Python:** 3.10+
**License:** MIT
