# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlphaSnobAI v2.0 is a Telegram UserBot with a sophisticated multi-persona system that can fully replace a real user account. The system combines AI-powered response generation, user profiling, intelligent decision-making, and human-like behavior simulation.

## Development Commands

### Running the Bot

```bash
# Interactive mode (with real-time dashboard)
python bot/runner.py

# Daemon mode (background)
python main.py

# CLI management
python cli.py persona list
python cli.py profile list
python cli.py owner analyze
```

### Testing

```bash
# Syntax validation
python -m py_compile <file.py>

# Test database migrations
python -c "import asyncio; from utils.db_migration import run_migration; from config.settings import get_settings; asyncio.run(run_migration(get_settings().paths.database))"
```

## Core Architecture

### Multi-Persona System

The bot switches between 3 personas dynamically based on context:

1. **AlphaSnob (Troll)** - Direct, rude responses using corpus examples
2. **Normal User** - Friendly conversational style
3. **Owner Mode** - Mimics the actual account owner's writing style

**Selection Priority:**
```
user_overrides (config) → chat_overrides (config) → user.preferred_persona (DB) → default_mode (config)
```

Managed by `services/persona_manager.py` using YAML prompts in `prompts/`.

### Message Processing Pipeline

```
1. MessageHandler receives Telegram event
2. LanguageDetector → detect ru/en
3. UserProfiler → get/create profile, update interaction count
4. DecisionEngine → calculate response probability
   - relationship_multiplier × time_multiplier × topic_multiplier
5. PersonaManager → select persona based on priority
6. TypingSimulator → simulate read delay
7. StyleEngine → generate LLM response (Claude/OpenAI)
8. TypingSimulator → show "typing..." action
9. Send response + save with metadata
```

**Key files:** `bot/handlers.py`, `services/*`, `main.py`

### Database Structure

SQLite with async operations (aiosqlite):

**Schema versioning:** `utils/db_migration.py` with incremental migrations
- `schema_version` table tracks current version
- Migrations run automatically on startup

**Tables:**
- `messages` - conversation history with persona_mode, response_delay_ms, decision_score
- `user_profiles` - relationship tracking, trust scores, interaction counts
- Auto-upgrade thresholds: 5 interactions → acquaintance, 20 → friend, 100 → close_friend

### Configuration System

Two-file YAML configuration:
- `config/config.yaml` - bot settings, persona config, decision rules
- `config/secrets.yaml` - API keys, Telegram credentials (gitignored)

**Loaded via:** `config/settings.py` with 13+ dataclass structures

**Critical sections:**
- `persona.default_mode` - which persona to use by default
- `decision.base_probability` - base response probability before multipliers
- `typing.enabled` - human-like typing simulation
- `owner_learning.enabled` - owner style mimicry

## Key Subsystems

### DecisionEngine (services/decision_engine.py)

Calculates whether to respond using probability formula:
```python
final_p = base_p × relationship_mult × time_mult × topic_mult
```

**Cooldown system:**
- Min 30s between responses
- Max 3 consecutive responses
- Reset after 5 minutes

Returns `DecisionResult` with reasoning for logging.

### OwnerLearningSystem (services/owner_learning.py)

Analyzes owner's message samples to generate style instructions:
- Message/sentence length patterns
- Emoji frequency and common emojis
- Word patterns (bigrams)
- Punctuation style (!, !!, ?, ...)
- Formality score (formal vs casual markers)
- Language distribution (ru/en ratio)

**Requires 50+ samples** in `data/owner_samples/messages.txt` for reliable analysis.

### TypingSimulator (services/typing_simulator.py)

Simulates realistic human behavior:
- **Read delay:** base + (words × 150ms), range 500-3000ms
- **Think delay:** random 500-2500ms
- **Type delay:** 1000ms + (chars × 50ms) ± 30%, max 20000ms

Shows Telegram "typing..." action during type phase.

### UserProfiler (services/user_profiler.py)

Tracks relationships with automatic upgrades:
- Stranger (default) → Acquaintance (5 interactions)
- Acquaintance → Friend (20 interactions)
- Friend → Close Friend (100 interactions)

**Trust score system:**
- Positive markers: "спасибо", "thanks", "круто" (+0.1 each)
- Negative markers: "тупой", "stupid", "идиот" (-0.1 each)
- Range: -1.0 to +1.0

## Code Patterns

### Adding New Components to MessageHandler

1. Initialize in `main.py::initialize_components()`
2. Pass to `MessageHandler.__init__()` in correct order
3. Update `bot/runner.py` similarly for interactive mode
4. Access via `self.<component_name>` in handler methods

### Creating New Personas

1. Create YAML file in `prompts/` with structure:
   ```yaml
   persona:
     name: my_persona
     display_name: "My Persona"
     description: "..."
   system_prompt: "..."
   response_guidelines: {}
   tone_mapping: {}
   ```
2. Add to `PersonaManager._load_all_personas()` in `persona_files` dict
3. Update `config.yaml` to use new persona

### Database Migrations

When adding fields/tables:
1. Create new migration in `utils/db_migration.py::_migrate_to_vX()`
2. Increment `LATEST_VERSION`
3. Migration runs automatically on next startup
4. No manual intervention needed

### LLM API Calls

Both Claude and OpenAI supported via `services/style.py`:
```python
# Access through StyleEngine
if self.provider == "claude":
    response = await self._generate_claude(system_prompt, user_prompt, ...)
else:
    response = await self._generate_openai(system_prompt, user_prompt, ...)
```

Provider selected via `config.yaml::llm.provider`

## Testing Owner Mode

1. Add 50+ message samples to `data/owner_samples/messages.txt`
2. Run `python cli.py owner analyze` to see style analysis
3. Set `owner_learning.enabled: true` in config
4. Set `persona.default_mode: owner` in config
5. Test with message to bot - should respond in owner's style

## Common Gotchas

- **MessageHandler initialization order matters** - components must be initialized before passing to handler
- **Typing delays are cumulative** - read + think + type can total 10-20 seconds for long messages
- **Decision probability is multiplicative** - stranger (0.3x) at night (0.2x) = only 6% base chance
- **Owner learning requires sufficient samples** - less than 50 samples falls back to conservative style
- **Database migrations are automatic** - don't manually alter schema, create migrations instead
- **Config changes require restart** - daemon mode doesn't hot-reload configuration

## File Organization

```
services/          # Core bot logic
├── persona_manager.py      # Persona selection and prompt generation
├── owner_learning.py       # Owner style analysis
├── user_profiler.py        # Relationship tracking
├── decision_engine.py      # Response decision logic
├── typing_simulator.py     # Human-like delays
├── style.py                # LLM API interface
└── memory.py               # Database operations

bot/               # Telegram integration
├── handlers.py             # Main message processing pipeline
├── client.py               # Telethon wrapper
├── runner.py               # Interactive mode
└── daemon.py               # Background process management

utils/             # Helper utilities
├── db_migration.py         # Database schema versioning
├── language_detector.py    # ru/en detection
└── corpus_loader.py        # Style examples loader

prompts/           # Persona definitions (YAML)
config/            # Configuration (YAML)
data/              # Runtime data (DB, logs, samples)
```

## CLI Structure

Main CLI: `cli.py` using Typer with sub-apps:
- `persona` - Manage personas (list, show, set-default)
- `profile` - User profiles (list, show, update)
- `owner` - Owner learning (analyze, samples)
- `stats` - Statistics (chat stats)

All CLI commands are async-wrapped where needed for database access.

