
import json
import os
from typing import Any, Dict

STATE_FILE = "v5_state.json"

def save_state(state: Dict[str, Any]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def load_raw_state():
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def delete_state() -> None:
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
