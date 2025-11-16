# AlphaSnobAI - Quick Start Guide

## Installation

```bash
# Clone and setup
cd AlphaSnobAI
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp config/config.yaml.example config/config.yaml
nano config/config.yaml  # Edit configuration
```

## Basic Configuration

### 1. Telegram Credentials

Get from https://my.telegram.org:

```yaml
telegram:
  api_id: YOUR_API_ID
  api_hash: "YOUR_API_HASH"
  phone: "+38094342123"
```

### 2. LLM Provider

Choose Claude or OpenAI:

```yaml
llm:
  provider: "claude"  # or "openai"
  anthropic_api_key: "sk-ant-..."  # For Claude
  # openai_api_key: "sk-..."      # For OpenAI
```

### 3. Choose Default Persona

```yaml
persona:
  default_mode: "owner"  # alphasnob | normal | owner
```

**Personas:**
- **alphasnob** - Troll mode (rude, direct, internet culture)
- **normal** - Friendly regular user
- **owner** - Mimics your writing style (requires samples)

## Running the Bot

### Interactive Mode (Recommended for testing)

```bash
python bot/runner.py
```

Shows real-time dashboard with messages and responses.

### Daemon Mode (Background)

```bash
python main.py
```

Runs in background. Check logs at `data/logs/bot.log`

## Using Owner Mode (Recommended)

Owner mode makes the bot write EXACTLY like you. Setup:

### 1. Export Your Messages

**Option A: Manual Collection**
1. Copy 50-100 of your recent messages
2. Paste into `data/owner_samples/messages.txt` (one per line)

**Option B: Telegram Desktop Export**
1. Open chat → Settings → Export
2. Format: Plain text, Messages only
3. Copy messages to `data/owner_samples/messages.txt`

### 2. Analyze Your Style

```bash
python cli.py owner analyze
```

You'll see:
- Average message length
- Emoji frequency and common emojis
- Formality score (casual vs formal)
- Common words and phrases
- Language distribution

### 3. Enable Owner Learning

```yaml
owner_learning:
  enabled: true
  min_samples: 50
```

### 4. Test It

Send a message to your bot account. It should respond in YOUR style!

## CLI Usage

```bash
# View available personas
python cli.py persona list

# Show all user profiles
python cli.py profile list

# View specific user
python cli.py profile show 123456789

# Update user relationship
python cli.py profile update 123456789 --relationship friend --trust 0.8

# Analyze owner writing style
python cli.py owner analyze

# Show random owner samples
python cli.py owner samples 20

# View configuration
python cli.py config
```

## Configuration Tips

### Response Behavior

```yaml
bot:
  response_mode: "probability"  # all | probability | specific_users | mentioned
  response_probability: 0.8     # 80% chance to respond
```

### Typing Simulation

Make responses feel human:

```yaml
typing:
  enabled: true
  read_delay: {min_ms: 500, max_ms: 3000, per_word_ms: 150}
  typing_action: {base_delay_ms: 1000, per_character_ms: 50}
```

**Delays:**
- Read: 0.5-3s + 150ms per word
- Think: 0.5-2.5s random
- Type: 1s + 50ms per character

To make faster (less realistic):
```yaml
typing:
  enabled: false
```

### Decision Engine

Control when bot responds:

```yaml
decision:
  base_probability: 0.8
  
  # Relationship affects probability
  relationship_multipliers:
    owner: 1.0          # Always respond to owner
    close_friend: 0.9   # 90% of base
    friend: 0.7         # 70% of base
    acquaintance: 0.5   # 50% of base
    stranger: 0.3       # 30% of base
  
  # Time-based behavior
  time_based:
    quiet_hours_start: 23  # 11 PM
    quiet_hours_end: 8     # 8 AM
    quiet_hours_multiplier: 0.2  # 20% of base during quiet hours
  
  # Cooldown to prevent spam
  cooldown:
    enabled: true
    min_seconds_between_responses: 30
    max_consecutive_responses: 3
```

### Per-User/Chat Personas

Override persona for specific users or chats:

```yaml
persona:
  user_overrides:
    123456789: "alphasnob"  # Always troll this user
    987654321: "normal"     # Always be nice to this user
  
  chat_overrides:
    -1001234567890: "normal"  # Be normal in this group
```

## Troubleshooting

### Bot doesn't respond

1. Check `response_mode` in config
2. Check `decision.base_probability` (try 1.0)
3. Check user's relationship level:
   ```bash
   python cli.py profile show <user_id>
   ```
4. Disable cooldown temporarily:
   ```yaml
   decision:
     cooldown:
       enabled: false
   ```

### Responses don't match my style

1. Check owner samples count:
   ```bash
   python cli.py owner samples
   ```
   Need 50+ samples for good results.

2. Analyze your style:
   ```bash
   python cli.py owner analyze
   ```

3. Make sure `owner_learning.enabled: true`

### API errors

1. Check API key is correct
2. Check you have credits/balance
3. Try switching provider:
   ```yaml
   llm:
     provider: "openai"  # Switch from claude
   ```

## Advanced Usage

### Setting Preferred Persona Per User

```bash
python cli.py profile update <user_id> --persona alphasnob
```

Now bot will always use alphasnob persona with this user.

### Adjusting Trust Score

```bash
python cli.py profile update <user_id> --trust 0.9
```

Trust affects nothing currently, but reserved for future features.

### Custom Notes

```bash
python cli.py profile update <user_id> --notes "Важный клиент, быть вежливым"
```

## What's Next?

1. **Export your messages** for owner mode
2. **Test in private chat** first
3. **Adjust decision.base_probability** to control response rate
4. **Monitor logs** at `data/logs/bot.log`
5. **Check user profiles** regularly with `python cli.py profile list`

## Support

- Check `ARCHITECTURE.md` for technical details
- Check `README.md` for general information
- Report issues on GitHub

---

Enjoy your AI-powered user replacement! 🤖

