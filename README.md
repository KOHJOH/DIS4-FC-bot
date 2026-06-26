# DIS4 FC Simulator V5

Fresh rebuild of the DIS4 solo AI Fulfillment Center simulator.

## Important Railway Fix

This package avoids the Python 3.13 `audioop` crash by including:

- `.python-version` set to Python 3.12
- `nixpacks.toml` using python312
- `audioop-lts` in requirements as backup compatibility

## Setup

1. Upload this folder to a new GitHub repo.
2. Connect the repo to Railway.
3. Add Railway variables:
   - `DISCORD_TOKEN`
   - `BOT_OWNER_ID`
4. Deploy.
5. In Discord run:
   - `/v5_start`
   - `/v5_panel`

## Main Commands

- `/v5_start`
- `/v5_help`
- `/v5_panel`
- `/v5_dashboard`
- `/v5_foresight`
- `/v5_start_shift`
- `/v5_sim_hour`
- `/v5_sim_shift`
- `/v5_manager_request`
- `/v5_manager_messages`
- `/v5_manager_meeting`
- `/v5_approve`
- `/v5_deny`
- `/v5_staffing`
- `/v5_cpt`
- `/v5_depart`
- `/v5_ai_associate`
- `/v5_leadership`
- `/v5_equipment`
- `/v5_business_review`

## V5 Design

V5 is built around:
- AI associates
- AI managers
- interactive embeds/buttons
- chain-of-command logic
- Foresight-style inbound/outbound volume
- Ship Dock CPT board
- AI TOM/trailer handling
- persistent building state
- autonomous operational events
