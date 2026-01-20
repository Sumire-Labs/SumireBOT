# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SumireBot v2 is a multi-functional Discord bot written in Python using discord.py 2.6.4. Primary language is Japanese.

## Commands

### Running the Bot
```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Run the bot
python bot.py
```

### Starting Lavalink (required for music)
```bash
cd lavalink
java -jar Lavalink.jar
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Singleton Pattern
`Config` and `Database` classes use singleton pattern. Access the same instance from anywhere:
```python
config = Config()
db = Database()
```

### Cog Structure
All features are implemented as discord.py Cogs in `cogs/`:
- Cogs are loaded in `bot.py` `setup_hook()`
- Each cog uses `@app_commands.command` for slash commands
- Error handling via `cog_app_command_error()` method

### UI Components
Two UI approaches are used:
- **Components V2 (LayoutView)**: Used for interactive panels (tickets, music). Cannot use Embeds within LayoutView.
- **Traditional Embed + View**: Used for logs and info displays where Components V2 restrictions don't apply.

Music views (`views/music_views.py`) demonstrate Components V2 pattern with `ui.Container`, `ui.Section`, `ui.TextDisplay`, etc.

### Persistent Views
Views that need to survive bot restarts are managed by `PersistentViewManager`:
1. Views register themselves via `bot.add_view()` with `custom_id`
2. State is stored in `persistent_views` table
3. Restored on startup in `setup_hook()`

### Multi-server Support
All data uses `guild_id` as primary key. Server data is isolated.

## Configuration

- Copy `config.yaml.example` to `config.yaml`
- Copy `lavalink/application.yml.example` to `lavalink/application.yml`
- Set Discord bot token, Lavalink password, and Spotify credentials

## Music System

Uses Wavelink 3.4.x + Lavalink 4.x:
- Supports YouTube, Spotify, SoundCloud URLs and text search
- Spotify metadata is resolved via LavaSrc plugin to playable sources
- YouTube playback uses youtube-plugin
- Loop modes: off, track, queue (stored in `Music.loop_mode` dict)
- Auto-leave after 3 minutes of inactivity

## Database

SQLite via aiosqlite. Tables are auto-created on first run in `Database._init_tables()`.

Key tables:
- `guild_settings`: Server language/preferences
- `ticket_settings`, `tickets`: Ticket system
- `logger_settings`: Server log configuration
- `music_settings`: Per-server music settings
- `user_levels`: XP/level tracking
- `persistent_views`: View state persistence
