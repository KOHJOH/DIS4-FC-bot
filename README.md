# FC RP Discord Bot

A Discord roleplay bot for a fulfillment-center operations server.

## Features

- Rank system
- Owner-only T3+ rank appointment
- Assignments separate from rank
- Certifications and cross-training
- Pick, Stow, Pack, Inbound, Ship Dock, Learning, Non-Inventory, Safety, PXT/HR
- Department health metrics
- Task system with cooldowns
- Clock-in / clock-out
- CPT risk board
- Labor moves
- Recruiting postings
- Write-ups
- Performance reviews
- Flow dashboard

## Setup

### 1. Install Python

Install Python 3.11 or newer.

### 2. Install requirements

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

Copy `.env.example` and rename it to `.env`.

Add your Discord bot token and your Discord user ID.

```env
DISCORD_TOKEN=your_token_here
BOT_OWNER_ID=your_discord_user_id_here
```

### 4. Run the bot

```bash
python main.py
```

## GitHub Upload

Upload this whole folder to GitHub.

Do **not** upload your `.env` file.

## Role Sync

This version includes Discord role syncing.

Commands:

```text
/create_fc_roles
/sync_roles
/appoint_rank
/assign_position
/train
```

Important Discord setup:

- Give the bot **Manage Roles** permission.
- Move the bot's highest role above the FC roles it needs to manage.
- Role names must match the bot constants exactly unless you use `/create_fc_roles`.

`/create_fc_roles` creates all rank, assignment, and certificate roles automatically.

## Help Menu

Use `/help` in Discord to view all bot commands grouped by category with FC-style metric emojis.


## Version 2.0 Additions

New commands added:

- `/create_log_channels`
- `/setup_channels`
- `/hire`
- `/reject`
- `/interview_pass`
- `/interview_fail`
- `/activity`
- `/staffing`
- `/peak_event`
- `/health_decay`

Recommended first commands after inviting the bot:

1. `/create_fc_roles`
2. `/create_log_channels`
3. `/setup_channels`
4. `/help`

Make sure the bot has:
- Manage Roles
- Manage Channels
- Send Messages
- Embed Links
- Use Slash Commands
