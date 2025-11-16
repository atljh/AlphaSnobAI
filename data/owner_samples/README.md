# Owner Style Learning - Message Samples

This directory contains samples of the owner's messages for learning their writing style.

## How to Export Your Messages from Telegram

### Method 1: Telegram Desktop (Recommended)

1. Open Telegram Desktop
2. Go to Settings → Advanced → Export Telegram data
3. Select:
   - ✅ Personal chats
   - ✅ Messages
   - Format: JSON
4. Export to a temporary folder
5. Find `result.json` in the export
6. Extract YOUR messages and paste them into `messages.txt` (one per line)

### Method 2: Manual Collection

Simply copy-paste 50-100 of your typical messages into `messages.txt`, one message per line:

```
Example message 1
Example message 2
...
```

## File Format

**messages.txt** - One message per line:
```
Привет, как дела?
Да, это круто!
Ну я не знаю, наверное стоит попробовать
```

**IMPORTANT:**
- Minimum 50 messages required for good learning
- 100+ messages recommended for best results
- Include variety: short/long, different topics, different moods
- Only YOUR messages (not other people's)

## Owner Learning Configuration

After adding messages, enable owner learning in `config/config.yaml`:

```yaml
owner_learning:
  enabled: true
  owner_user_ids: [YOUR_TELEGRAM_USER_ID]  # Your user ID
  manual_samples_path: data/owner_samples/messages.txt
  min_samples: 50
```

## What the Bot Learns

The bot analyzes your messages to match:
- Average message length
- Emoji usage frequency
- Punctuation style (!, ?, ...)
- Common phrases and words
- Sentence structure
- Topics you discuss
- Casual vs formal tone
- Language mixing (if any)

## Testing Owner Mode

After setup, test with:
```bash
python bin/alphasnob start --interactive
```

The bot will use your style when `persona.default_mode: owner` in config.
