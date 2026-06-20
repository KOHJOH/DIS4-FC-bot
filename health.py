PICK_FLOORS = {
    "Floor 1": {"health": 100, "rate": 100, "quality": 100, "backlog": 0, "pod_gaps": 0, "missing_items": 0, "tote_supply": 100},
    "Floor 2": {"health": 100, "rate": 100, "quality": 100, "backlog": 0, "pod_gaps": 0, "missing_items": 0, "tote_supply": 100},
    "Floor 3": {"health": 100, "rate": 100, "quality": 100, "backlog": 0, "pod_gaps": 0, "missing_items": 0, "tote_supply": 100}
}

STOW_FLOORS = {
    "Floor 1": {"health": 100, "rate": 100, "quality": 100, "backlog": 0, "pod_gaps": 0, "overstuffed_bins": 0, "reactive_work": 0},
    "Floor 2": {"health": 100, "rate": 100, "quality": 100, "backlog": 0, "pod_gaps": 0, "overstuffed_bins": 0, "reactive_work": 0},
    "Floor 3": {"health": 100, "rate": 100, "quality": 100, "backlog": 0, "pod_gaps": 0, "overstuffed_bins": 0, "reactive_work": 0}
}

DEPARTMENT_HEALTH = {
    "Pack Singles": {"health": 100, "rate": 100, "quality": 100, "wip": 0, "box_supply": 100, "slam_errors": 0},
    "AFE Pack": {"health": 100, "rate": 100, "quality": 100, "wip": 0, "rebin_backlog": 0, "induct_backlog": 0, "slam_errors": 0},
    "Receive Dock": {"health": 100, "trailer_backlog": 0, "receive_rate": 100, "dock_door_capacity": 100, "quality": 100},
    "Decant": {"health": 100, "line_rate": 100, "carton_backlog": 0, "tote_supply": 100, "quality": 100},
    "Learning": {"health": 100, "training_backlog": 0, "certifications_completed": 0, "audit_score": 100, "ambassador_coverage": 100},
    "Non-Inventory": {"health": 100, "box_supply": 100, "tape_supply": 100, "label_supply": 100, "water_supply": 100, "supply_requests": 0},
    "Safety": {"health": 100, "safety_audits": 0, "incident_risk": 0, "compliance": 100, "coaching_completed": 0},
    "PXT / HR": {"health": 100, "cases_open": 0, "associate_support": 100, "policy_accuracy": 100, "engagement": 100},
    "Shipping Sorter": {"health": 100, "backlog": 0, "lane_capacity": 0, "missorts": 0, "cpt_risk": 0},
    "Transship": {"health": 100, "yellow_tote_backlog": 0, "destination_accuracy": 100},
    "Lower Mezzanine": {"health": 100, "utilization": 100, "lane_jams": 0},
    "Upper Mezzanine": {"health": 100, "feed_balance": 100, "flow_rate": 100},
    "Quality": {"health": 100, "audits": 0, "defects": 0, "tdr_compliance": 100},
    "VRETS": {"health": 100, "return_backlog": 0, "quality": 100},
    "ICQA": {"health": 100, "inventory_accuracy": 100, "open_variances": 0, "resolved_variances": 0, "bin_quality": 100}
}

def clamp_area(area):
    for key, value in area.items():
        if isinstance(value, int):
            area[key] = max(0, min(100, value))
