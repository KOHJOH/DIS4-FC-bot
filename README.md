# DIS4 Solo FC Simulator V4.0

A separate solo Discord bot where you are the only real person and the entire fulfillment center is AI.

## Features
- 220+ persistent AI associates
- AI departments, PAs, AMs, OMs, Ship Clerks, TOM, Safety, Learning, ICQA
- Inbound and outbound Foresight-style volume
- Ship Dock CPT board
- AI TOM/trailer departures
- AI staffing and call-offs
- Building health, safety, quality, missorts, and CPT compliance
- AI recommendations
- Simulate hours or full shifts
- Rotate yourself between departments as OM, Senior OM, or GM

## Setup
1. Upload this folder to a new GitHub repo.
2. Deploy to Railway.
3. Add variables:
   - DISCORD_TOKEN
   - BOT_OWNER_ID
4. Start command:
   - python main.py

## First commands
- /solo_start
- /solo_help
- /solo_dashboard


## V4.1 Interactive AI Control Panel

New interactive features:

- Button-based control panel
- AI manager requests
- Approve/Deny/Escalate buttons
- Metrics buttons
- AI manager meetings
- Request memory
- Chain-of-command logic

New commands:

- `/solo_control_panel`
- `/solo_manager_request`
- `/solo_manager_messages`
- `/solo_manager_meeting`
- `/solo_approve_request`
- `/solo_deny_request`
- `/solo_interactive_help`
