# AlphaSnobAI - Technical Architecture

## Overview

AlphaSnobAI v2.0 is a sophisticated Telegram UserBot with a multi-persona system designed to fully replace a real user account. It combines AI-powered response generation, user profiling, intelligent decision-making, and human-like behavior simulation.

## System Components

### 1. **LanguageDetector** - Auto-detect message language (ru/en)
### 2. **UserProfiler** - Track relationships and auto-upgrade levels
### 3. **DecisionEngine** - Intelligent response probability calculation
### 4. **PersonaManager** - Manage multiple personalities (alphasnob/normal/owner)
### 5. **OwnerLearningSystem** - Analyze and mimic owner's writing style
### 6. **TypingSimulator** - Realistic human-like delays and typing action
### 7. **StyleEngine** - LLM API interface (Claude/OpenAI)
### 8. **Memory** - Conversation history storage

## Message Processing Flow

```
Message → Language Detection → User Profiling → Decision Engine
                                                      ↓ (respond?)
              Persona Selection → Typing Simulation → LLM Generation → Send
```

## Key Features

- **Multi-Persona System:** Switch between troll, normal, and owner modes
- **Relationship Tracking:** Automatically upgrade user levels (stranger→friend→close_friend)
- **Intelligent Decisions:** Consider relationship, time, topic, and cooldown
- **Owner Mimicry:** Learn from message samples to match owner's style
- **Human-Like Behavior:** Realistic reading/thinking/typing delays
- **Multi-Language:** Auto-detect and respond in Russian or English

## Database Schema

**user_profiles:**
- relationship_level, trust_score, interaction_count
- Auto-upgrade thresholds: 5/20/100 interactions

**messages:**
- Conversation history with metadata (persona, response_delay, decision_score)

## CLI Commands

```bash
python cli.py persona list
python cli.py profile list  
python cli.py owner analyze
python cli.py stats chat <chat_id>
```

See config.yaml for full configuration options.

