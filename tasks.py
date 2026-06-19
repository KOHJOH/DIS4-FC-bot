TASKS = {
    "Pick": [
        {
            "scenario": "You arrive at a bin, but the item is not there. What do you do?",
            "choices": ["Mark the item missing properly", "Pick a similar item", "Skip the scan"],
            "answer": 0,
            "reward": {"productivity": 4, "quality": 3},
            "area_effect": {"health": 1, "quality": 2, "missing_items": -1}
        }
    ],
    "Stow": [
        {
            "scenario": "A pod arrives with limited space. What should you do?",
            "choices": ["Stow neatly in the correct bin", "Force item anywhere", "Place item on floor"],
            "answer": 0,
            "reward": {"productivity": 4, "quality": 3},
            "area_effect": {"health": 1, "quality": 2, "overstuffed_bins": -1}
        }
    ],
    "Tote Runner": [
        {
            "scenario": "Pick stations are running low on empty totes. What do you do?",
            "choices": ["Refill priority stations first", "Only help friends", "Ignore shortage"],
            "answer": 0,
            "reward": {"productivity": 4, "leadership": 2},
            "area_effect": {"health": 2, "rate": 3, "backlog": -1}
        }
    ],
    "Amnesty": [
        {
            "scenario": "A product has fallen onto the AR floor and is causing pod gaps. What do you do?",
            "choices": ["Recover it safely using Amnesty process", "Leave it", "Ignore the alert"],
            "answer": 0,
            "reward": {"productivity": 4, "safety": 4},
            "area_effect": {"health": 2, "pod_gaps": -2}
        }
    ],
    "Pack Singles": [
        {
            "scenario": "The suggested box is too small. What do you do?",
            "choices": ["Choose the correct box size", "Force it in", "Ship without box"],
            "answer": 0,
            "reward": {"productivity": 5, "quality": 3},
            "area_effect": {"health": 2, "quality": 2, "slam_errors": -1}
        }
    ],
    "AFE Pack": [
        {
            "scenario": "AFE wall has orders waiting. What do you do?",
            "choices": ["Pack accurately and clear the wall", "Mix items", "Skip scans"],
            "answer": 0,
            "reward": {"productivity": 5, "quality": 3},
            "area_effect": {"health": 2, "quality": 2, "wip": -1}
        }
    ],
    "Receive Dock": [
        {
            "scenario": "A trailer arrives with mixed freight. What do you do?",
            "choices": ["Scan and organize freight correctly", "Unload randomly", "Block the dock"],
            "answer": 0,
            "reward": {"productivity": 5, "quality": 3},
            "area_effect": {"health": 2, "receive_rate": 3, "trailer_backlog": -1}
        }
    ],
    "Decant": [
        {
            "scenario": "Cartons are backing up on the line. What do you do?",
            "choices": ["Open, scan, and tote accurately", "Throw items randomly", "Ignore damage"],
            "answer": 0,
            "reward": {"productivity": 5, "quality": 3},
            "area_effect": {"health": 2, "line_rate": 3, "carton_backlog": -1}
        }
    ],
    "Learning": [
        {
            "scenario": "New hires need training before working. What do you do?",
            "choices": ["Assign ambassadors and track certs", "Send them untrained", "Ignore backlog"],
            "answer": 0,
            "reward": {"leadership": 6, "quality": 4},
            "area_effect": {"health": 3, "training_backlog": -1, "certifications_completed": 1}
        }
    ],
    "Non-Inventory": [
        {
            "scenario": "Pack is low on boxes and tape. What do you do?",
            "choices": ["Restock correct supplies", "Deliver random supplies", "Ignore request"],
            "answer": 0,
            "reward": {"productivity": 4, "leadership": 3},
            "area_effect": {"health": 3, "box_supply": 5, "tape_supply": 5, "supply_requests": -1}
        }
    ],
    "Safety": [
        {
            "scenario": "A blocked emergency exit is reported. What do you do?",
            "choices": ["Clear it, document it, coach area", "Ignore it", "Move blockage elsewhere"],
            "answer": 0,
            "reward": {"safety": 7, "leadership": 4},
            "area_effect": {"health": 4, "safety_audits": 1, "incident_risk": -2}
        }
    ],
    "PXT / HR": [
        {
            "scenario": "An associate needs attendance policy help. What do you do?",
            "choices": ["Explain policy and document support", "Guess", "Ignore associate"],
            "answer": 0,
            "reward": {"leadership": 4, "quality": 4},
            "area_effect": {"health": 3, "cases_open": -1, "associate_support": 3}
        }
    ],
    "Shipping Sorter": [
        {
            "scenario": "Sorter lanes are overflowing. What do you do?",
            "choices": ["Check lane health and move labor", "Ignore sorter", "Send all packages one lane"],
            "answer": 0,
            "reward": {"leadership": 4, "productivity": 6},
            "area_effect": {"health": 3, "backlog": -1, "lane_capacity": -3}
        }
    ],
    "Transship": [
        {
            "scenario": "Yellow totes are building up. What do you do?",
            "choices": ["Scan, sort, and stage by destination", "Mix with regular packages", "Ignore"],
            "answer": 0,
            "reward": {"productivity": 5, "quality": 5},
            "area_effect": {"health": 3, "yellow_tote_backlog": -1}
        }
    ],
    "Quality": [
        {
            "scenario": "Packages are found in the wrong lane. What do you do?",
            "choices": ["Audit lane and find root cause", "Move and ignore", "Tell people work faster"],
            "answer": 0,
            "reward": {"quality": 6, "leadership": 4},
            "area_effect": {"health": 3, "audits": 1, "defects": -1}
        }
    ],
    "PIT Operator": [
        {
            "scenario": "A pallet needs to be moved safely. What do you do first?",
            "choices": ["Safety check and clear path", "Drive fast", "Move without looking"],
            "answer": 0,
            "reward": {"productivity": 5, "safety": 5}
        }
    ],
    "TDR Operator": [
        {
            "scenario": "A trailer is ready to open. What do you do first?",
            "choices": ["Follow TDR safety checks", "Open immediately", "Let anyone open it"],
            "answer": 0,
            "reward": {"safety": 6, "quality": 4}
        }
    ]
}
