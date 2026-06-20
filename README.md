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


## Version 2.1 Department OM Authority

New commands:

- `/assign_department_om`
- `/my_authority`

Example setup:

1. Make yourself L6:
   `/appoint_rank user:@you rank:L6 Operations Manager`

2. Assign yourself over Ship Dock:
   `/assign_department_om user:@you department:Ship Dock Operations Manager`

This gives the L6 OM authority over Shipping Sorter, Transship, Ship Dock, Lower Mezzanine, Upper Mezzanine, Quality, VRETS, TDR Operator, and Flow Desk.


## Version 3.0 FC Operations Simulator

Major additions:

- FHN/BHN shift system
- Dynamic leadership directory
- `/who_is_my_manager`
- `/department_leadership`
- `/org_chart`
- `/manager_dashboard`
- ICQA department and ICQA tasks
- Expanded certifications
- Process Guide appointments
- Area Manager assignments
- PA assignments
- UPT/PTO/Vacation balances
- Recognition and Swag Points
- Dock doors 120-150 and 201-222
- TDR door controls
- Shift handoff
- Site status dashboard

Recommended setup:

1. `/appoint_rank user:@you rank:L6 Operations Manager`
2. `/assign_department_om user:@you department:Ship Dock Operations Manager`
3. `/assign_shift user:@you shift:Front Half Nights`
4. `/my_authority`
5. `/manager_dashboard`


## Version 3.1 PA Lookup Feature

New lookup commands:

- `/lookup_associate`
- `/set_station`
- `/mark_active`
- `/idle_report`
- `/lookup_help`

This lets PAs, PGs, Learning Ambassadors, AMs, OMs, Senior OMs, and GMs view associate details such as:

- Rank
- Department
- Area
- Shift
- Assignment
- Station
- Clock status
- Station status
- Idle time
- Productivity
- Quality
- Safety
- Attendance
- Write-ups
- Morale
- Certifications

Idle time updates when an associate clocks in, completes a task, is assigned a station, or is marked active by leadership.


## Version 3.1.1 Associate Assignment Hotfix

New commands:

- `/assign_associate`
- `/transfer_associate`
- `/remove_assignment`
- `/assignment_help`

Example:

`/assign_associate user:@associate area:Transship shift:Front Half Nights`

This assigns:

- Department: Ship Dock
- Area: Transship
- Shift: Front Half Nights
- Assignment: Transship Associate

This makes `/who_is_my_manager`, `/department_leadership`, `/lookup_associate`, and `/idle_report` work properly for regular associates.
