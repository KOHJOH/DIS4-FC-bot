
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from sim_data import *
from state_store import save_state, load_raw_state, delete_state

def fmt(n):
    return f"{int(n):,}"

def random_name(existing):
    for _ in range(2000):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if name not in existing:
            existing.add(name)
            return name
    return f"Associate {random.randint(1000, 9999)}"

def base_stats(personality):
    return {
        "High Performer": (138, 99, 100, 98, 92),
        "Reliable Veteran": (121, 99, 100, 99, 90),
        "New Hire": (86, 94, 97, 95, 82),
        "Speed Demon": (151, 93, 97, 96, 85),
        "Safety First": (106, 98, 100, 98, 88),
        "Future Leader": (129, 99, 100, 99, 94),
        "Quiet Worker": (113, 98, 99, 97, 84),
        "Needs Coaching": (80, 90, 94, 88, 70),
        "Problem Solver": (116, 99, 100, 97, 91),
        "Trainer Type": (109, 99, 100, 98, 93),
        "Burnout Risk": (118, 96, 96, 92, 58),
        "Morale Booster": (115, 98, 99, 97, 96),
        "Detail Oriented": (108, 100, 100, 98, 88),
        "Fast Learner": (122, 98, 99, 96, 90)
    }[personality]

def make_ai_associate(i, existing_names):
    dept = random.choice(list(DEPARTMENTS.keys()))
    area = random.choice(DEPARTMENTS[dept])
    personality = random.choice(PERSONALITIES)
    rank = random.choices(
        ["T1 Fulfillment Associate", "Learning Ambassador", "Process Guide", "T3 Process Assistant", "L4 Area Manager", "L5 Area Manager"],
        weights=[70, 8, 8, 7, 5, 2]
    )[0]

    uph, quality, safety, attendance, morale = base_stats(personality)
    certs = random.sample(CERTIFICATIONS, random.randint(0, 5))

    if rank == "Learning Ambassador" and "Learning Ambassador" not in certs:
        certs.append("Learning Ambassador")
    if rank == "Process Guide" and "Process Guide" not in certs:
        certs.append("Process Guide")
    if area == "Ship Clerk" and "Shipping Clerk" not in certs:
        certs.append("Shipping Clerk")
    if area == "TDR" and "TDR" not in certs:
        certs.append("TDR")

    return {
        "id": f"DIS4-{10000+i}",
        "name": random_name(existing_names),
        "rank": rank,
        "department": dept,
        "area": area,
        "shift": random.choice(list(SHIFTS.keys())),
        "personality": personality,
        "status": "Scheduled",
        "station": area,
        "uph": max(50, int(random.gauss(uph, 10))),
        "quality": max(75, min(100, int(random.gauss(quality, 2)))),
        "safety": max(75, min(100, int(random.gauss(safety, 1)))),
        "attendance": max(55, min(100, int(random.gauss(attendance, 4)))),
        "morale": max(30, min(100, int(random.gauss(morale, 5)))),
        "stress": random.randint(10, 55),
        "trust": random.randint(65, 95),
        "certifications": certs,
        "tenure_days": random.randint(1, 900),
        "writeups": 0,
        "positive_feedback": random.randint(0, 14),
        "cpt_saves": random.randint(0, 6),
        "career_goal": random.choice(["Stay Associate", "Become PG", "Become PA", "Become AM", "Become Trainer", "Move to ICQA", "Move to Learning"]),
        "history": []
    }

def create_trailers():
    trailers = []
    for _ in range(22):
        cpt = datetime.now() + timedelta(minutes=random.randint(35, 420))
        door = str(random.choice(list(range(120, 151)) + list(range(201, 223))))
        packages = random.randint(0, 1700)
        status = "Ready" if packages == 0 else random.choice(["On Track", "On Track", "Loading", "At Risk"])
        trailers.append({
            "id": f"TR-{random.randint(100,999)}",
            "door": door,
            "type": random.choice(TRAILER_TYPES),
            "cpt": cpt.strftime("%H:%M"),
            "packages_remaining": packages,
            "status": status,
            "pull_requested": False,
            "departed": False,
            "tom_status": "Docked"
        })
    return trailers

def create_state():
    existing = set()
    associates = [make_ai_associate(i, existing) for i in range(260)]

    state = {
        "version": "DIS4 FC Simulator V5",
        "created_at": datetime.now().isoformat(),
        "player": {
            "name": "Jump",
            "rank": "L6 Operations Manager",
            "department": "Ship Dock",
            "shift": "Front Half Nights"
        },
        "building": {
            "day": 1,
            "shift": "Front Half Nights",
            "forecast_level": "NORMAL",
            "building_health": 96,
            "safety": 99,
            "quality": 99,
            "cpt_compliance": 99.2,
            "missorts": 8,
            "reputation": 4.7,
            "forecast_accuracy": 97.5,
            "labor_efficiency": 95,
            "open_sevs": 0
        },
        "volume": {
            "inbound_expected": 165000,
            "outbound_expected": 245000,
            "ship_dock_carts": 3500,
            "trailers_expected": 72,
            "inbound_processed": 0,
            "outbound_processed": 0,
            "dock_processed": 0
        },
        "department_health": {dept: random.randint(88, 100) for dept in DEPARTMENTS},
        "area_health": {area: random.randint(85, 100) for areas in DEPARTMENTS.values() for area in areas},
        "ai_associates": associates,
        "trailers": create_trailers(),
        "events": [],
        "manager_requests": [],
        "manager_memory": [],
        "request_counter": 1000,
        "action_items": [],
        "business_history": [],
        "equipment": {
            "Scanners": {"available": 180, "total": 200},
            "Pallet Jacks": {"available": 46, "total": 55},
            "Radios": {"available": 28, "total": 35},
            "Printers": {"available": 19, "total": 22},
            "Go Carts": {"available": 640, "total": 800},
            "Yellow Totes": {"available": 2200, "total": 3000},
            "PIT Batteries": {"available": 32, "total": 40}
        },
        "records": {
            "best_cpt_compliance": 99.2,
            "highest_building_health": 96,
            "most_cpt_saves": 0
        }
    }
    save_state(state)
    return state

def load_state():
    state = load_raw_state()
    if state is None:
        return create_state()

    # migration-safe defaults
    state.setdefault("manager_requests", [])
    state.setdefault("manager_memory", [])
    state.setdefault("request_counter", 1000)
    state.setdefault("events", [])
    state.setdefault("action_items", [])
    return state

def reset_state():
    delete_state()
    return create_state()

def get_staffing(state, department=None):
    associates = state["ai_associates"]
    if department:
        associates = [a for a in associates if a["department"] == department]
    return {
        "scheduled": len(associates),
        "clocked_in": sum(1 for a in associates if a["status"] in ["Working", "Training", "Problem Solve", "Helping Another Area"]),
        "late": sum(1 for a in associates if a["status"] == "Late"),
        "calloffs": sum(1 for a in associates if a["status"] == "Call Off"),
        "vto": sum(1 for a in associates if a["status"] == "VTO")
    }

def start_shift(state, shift):
    state["building"]["shift"] = shift
    state["player"]["shift"] = shift
    for a in state["ai_associates"]:
        roll = random.random()
        if roll < 0.04:
            a["status"] = "Call Off"
        elif roll < 0.07:
            a["status"] = "Late"
        elif roll < 0.12 and state["building"]["forecast_level"] in ["LOW", "NORMAL"]:
            a["status"] = "VTO"
        else:
            a["status"] = "Working"
    state["events"].append({"time": datetime.now().strftime("%H:%M"), "type": "Shift Start", "message": f"{shift} started. AI staffing initialized."})
    save_state(state)

def forecast_update(state, level=None):
    if level is None:
        level = random.choices(FORECAST_LEVELS, weights=[10, 35, 30, 15, 6, 4])[0]
    mult = {"LOW": 0.72, "NORMAL": 1.0, "HIGH": 1.23, "PEAK": 1.45, "PRIME WEEK": 1.75, "PEAK SEASON": 1.9}[level]
    state["building"]["forecast_level"] = level
    state["volume"]["inbound_expected"] = int(165000 * mult * random.uniform(0.9, 1.1))
    state["volume"]["outbound_expected"] = int(245000 * mult * random.uniform(0.9, 1.1))
    state["volume"]["ship_dock_carts"] = int(3500 * mult * random.uniform(0.9, 1.15))
    state["volume"]["trailers_expected"] = int(72 * mult * random.uniform(0.9, 1.1))
    save_state(state)

def cpt_summary(state):
    open_cpts = [t for t in state["trailers"] if not t["departed"]]
    return {
        "open": len(open_cpts),
        "at_risk": sum(1 for t in open_cpts if t["status"] == "At Risk"),
        "ready": sum(1 for t in open_cpts if t["status"] == "Ready"),
        "departed": sum(1 for t in state["trailers"] if t["departed"])
    }

def create_event(state):
    event = random.choice(EVENTS)
    dept = random.choice(list(DEPARTMENTS.keys()))
    impact = random.randint(2, 10)

    state["department_health"][dept] = max(40, state["department_health"][dept] - impact)

    if event == "Missort Spike":
        state["building"]["missorts"] += random.randint(8, 35)
    if event in ["Safety Near Miss", "Dock Plate Issue"]:
        state["building"]["safety"] = max(80, state["building"]["safety"] - random.randint(1, 4))
    if event in ["Quality Defect Spike", "Missort Spike"]:
        state["building"]["quality"] = max(80, state["building"]["quality"] - random.randint(1, 4))
    if event in ["Trailer Delay", "Yard Congestion"]:
        state["building"]["cpt_compliance"] = max(80, round(state["building"]["cpt_compliance"] - random.uniform(0.2, 1.8), 1))
    if event in ["Conveyor Jam", "Dock Plate Issue", "Scanner Network Issue"]:
        state["building"]["open_sevs"] += random.choice([0, 1])

    rec = {"time": datetime.now().strftime("%H:%M"), "type": event, "department": dept, "impact": impact, "message": f"{event} impacted {dept}. Health -{impact}%."}
    state["events"].append(rec)
    return rec

def simulate_hour(state):
    forecast = state["building"]["forecast_level"]
    mult = {"LOW": 0.06, "NORMAL": 0.08, "HIGH": 0.09, "PEAK": 0.11, "PRIME WEEK": 0.13, "PEAK SEASON": 0.14}[forecast]
    staffing = get_staffing(state)
    labor = min(1.15, staffing["clocked_in"] / max(1, staffing["scheduled"] * 0.86))

    state["volume"]["inbound_processed"] += int(state["volume"]["inbound_expected"] * mult * labor * random.uniform(0.85, 1.08))
    state["volume"]["outbound_processed"] += int(state["volume"]["outbound_expected"] * mult * labor * random.uniform(0.85, 1.08))
    state["volume"]["dock_processed"] += int(state["volume"]["ship_dock_carts"] * mult * labor * random.uniform(0.85, 1.08))

    for t in state["trailers"]:
        if t["departed"]:
            continue
        reduction = random.randint(40, 220)
        if state["department_health"].get("Ship Dock", 100) < 80:
            reduction = int(reduction * 0.65)
        t["packages_remaining"] = max(0, t["packages_remaining"] - reduction)
        if t["packages_remaining"] == 0:
            t["status"] = "Ready"
        elif t["packages_remaining"] > 500 and random.random() < 0.27:
            t["status"] = "At Risk"
        else:
            t["status"] = "On Track"

    if random.random() < 0.5:
        create_event(state)
    if random.random() < 0.45:
        generate_manager_request(state)

    for dept in state["department_health"]:
        if random.random() < 0.5:
            state["department_health"][dept] = min(100, state["department_health"][dept] + random.randint(1, 3))

    state["building"]["building_health"] = int(sum(state["department_health"].values()) / len(state["department_health"]))
    state["records"]["highest_building_health"] = max(state["records"]["highest_building_health"], state["building"]["building_health"])
    save_state(state)

def recommendations(state):
    recs = []
    s = get_staffing(state)
    if s["clocked_in"] < s["scheduled"] * 0.82:
        recs.append("Cancel VTO and labor share AI associates to critical areas.")
    if state["department_health"].get("Ship Dock", 100) < 85:
        recs.append("Move labor to Ship Dock and start CPT recovery.")
    if state["building"]["missorts"] > 20:
        recs.append("Assign Quality PA to investigate missort root cause.")
    if state["building"]["safety"] < 96:
        recs.append("Run a Safety Gemba walk and pause high-risk moves.")
    if any(t["status"] == "At Risk" for t in state["trailers"]):
        recs.append("Ship Clerk should prioritize at-risk CPTs and request TOM pulls for ready trailers.")
    if state["equipment"]["Scanners"]["available"] < 160:
        recs.append("Request equipment audit: scanner availability is low.")
    if state["building"].get("open_sevs", 0) > 0:
        recs.append("Assign Senior OM/GM review to open SEV events.")
    return recs or ["Operation is stable. Continue monitoring forecast and CPT board."]

def depart_trailer(state, trailer_id):
    for t in state["trailers"]:
        if t["id"].lower() == trailer_id.lower():
            if t["departed"]:
                return False, "Trailer already departed."
            t["departed"] = True
            t["status"] = "Departed"
            t["tom_status"] = "Pulled"
            if t["packages_remaining"] > 0:
                state["building"]["cpt_compliance"] = max(80, round(state["building"]["cpt_compliance"] - random.uniform(0.1, 0.8), 1))
                msg = f"{t['id']} departed with {t['packages_remaining']} packages remaining. CPT risk increased."
            else:
                state["building"]["cpt_compliance"] = min(100, round(state["building"]["cpt_compliance"] + 0.1, 1))
                msg = f"{t['id']} departed on time and clean."
            save_state(state)
            return True, msg
    return False, "Trailer not found."

def generate_manager_request(state, department=None):
    department = department or random.choice(list(DEPARTMENTS.keys()))
    area = random.choice(DEPARTMENTS[department])
    personality = random.choice(MANAGER_PERSONALITIES)
    possible = []

    if department == "Ship Dock":
        risk = [t for t in state["trailers"] if t["status"] == "At Risk" and not t["departed"]]
        if risk:
            t = random.choice(risk)
            possible.append({
                "type": "CPT Recovery",
                "title": f"CPT Risk — {t['id']}",
                "message": f"Trailer {t['id']} at Door {t['door']} is projected at risk. {t['packages_remaining']} packages remain before CPT {t['cpt']}.",
                "recommendation": "Launch CPT recovery, move 2 AI associates from Upper Mezzanine, and request TOM pull when ready.",
                "approve": {"cpt": 0.4, "shipdock": 4, "morale": -1},
                "deny": {"cpt": -0.7, "shipdock": -3, "morale": 0}
            })

    if state["department_health"].get(department, 100) < 88:
        possible.append({
            "type": "Department Recovery",
            "title": f"{department} Health Dropping",
            "message": f"{department} health is trending below target at {state['department_health'][department]}%.",
            "recommendation": "Pause non-critical work, run a Gemba walk, and shift AI labor to the weakest area.",
            "approve": {"dept": 6, "building": 2, "morale": 1},
            "deny": {"dept": -4, "building": -1, "morale": -1}
        })

    if state["building"]["missorts"] > 18:
        possible.append({
            "type": "Quality Escalation",
            "title": "Missorts Trending High",
            "message": f"Missorts are currently at {state['building']['missorts']}, above the expected threshold.",
            "recommendation": "Assign Quality to investigate root cause and place a PA at the sorter lanes.",
            "approve": {"missorts": -8, "quality": 1, "dept": 3},
            "deny": {"missorts": 6, "quality": -1, "dept": -2}
        })

    if state["building"]["safety"] < 97:
        possible.append({
            "type": "Safety Concern",
            "title": "Safety Score Below Target",
            "message": f"Site safety score is {state['building']['safety']}%. Safety recommends a focused audit.",
            "recommendation": "Run safety standdown and assign Safety Specialist to investigate.",
            "approve": {"safety": 2, "building": 1, "morale": 1},
            "deny": {"safety": -2, "building": -1, "morale": -1}
        })

    if not possible:
        possible.append({
            "type": "Proactive Improvement",
            "title": f"{department} Improvement Opportunity",
            "message": f"{department} is stable, but the manager sees an opportunity to improve flow.",
            "recommendation": "Run a 5S walk, recognize top performers, and prep for the next volume push.",
            "approve": {"dept": 3, "building": 1, "morale": 2},
            "deny": {"dept": 0, "building": 0, "morale": 0}
        })

    item = random.choice(possible)
    state["request_counter"] += 1
    req = {
        "id": str(state["request_counter"]),
        "status": "Open",
        "department": department,
        "area": area,
        "manager_name": random.choice(FIRST_NAMES) + " " + random.choice(LAST_NAMES),
        "manager_role": f"{department} Area Manager",
        "manager_personality": personality,
        "type": item["type"],
        "title": item["title"],
        "message": item["message"],
        "recommendation": item["recommendation"],
        "impact_approve": item["approve"],
        "impact_deny": item["deny"],
        "created_at": datetime.now().strftime("%H:%M")
    }
    state["manager_requests"].append(req)
    save_state(state)
    return req

def open_requests(state):
    return [r for r in state["manager_requests"] if r["status"] == "Open"]

def apply_request(state, request_id, approve=True):
    req = next((r for r in state["manager_requests"] if str(r["id"]) == str(request_id)), None)
    if not req:
        return False, "Request not found."
    if req["status"] != "Open":
        return False, f"Request already {req['status']}."

    impacts = req["impact_approve"] if approve else req["impact_deny"]
    dept = req["department"]

    for key, val in impacts.items():
        if key == "cpt":
            state["building"]["cpt_compliance"] = max(70, min(100, round(state["building"]["cpt_compliance"] + val, 1)))
        elif key == "shipdock":
            state["department_health"]["Ship Dock"] = max(40, min(100, state["department_health"]["Ship Dock"] + val))
        elif key == "dept":
            state["department_health"][dept] = max(40, min(100, state["department_health"][dept] + val))
        elif key == "building":
            state["building"]["building_health"] = max(40, min(100, state["building"]["building_health"] + val))
        elif key == "morale":
            for a in state["ai_associates"]:
                if a["department"] == dept:
                    a["morale"] = max(30, min(100, a["morale"] + val))
        elif key == "missorts":
            state["building"]["missorts"] = max(0, state["building"]["missorts"] + val)
        elif key == "quality":
            state["building"]["quality"] = max(70, min(100, state["building"]["quality"] + val))
        elif key == "safety":
            state["building"]["safety"] = max(70, min(100, state["building"]["safety"] + val))

    req["status"] = "Approved" if approve else "Denied"
    req["resolved_at"] = datetime.now().strftime("%H:%M")
    state["manager_memory"].append({"time": datetime.now().strftime("%H:%M"), "request": req["title"], "department": dept, "decision": req["status"]})
    save_state(state)
    return True, f"Request {req['status']}: {req['title']}"

def manager_meeting(state):
    while len(open_requests(state)) < 3:
        generate_manager_request(state)
    return open_requests(state)[:5]

def business_review(state):
    return {
        "day": state["building"]["day"],
        "building_health": state["building"]["building_health"],
        "safety": state["building"]["safety"],
        "quality": state["building"]["quality"],
        "cpt_compliance": state["building"]["cpt_compliance"],
        "missorts": state["building"]["missorts"],
        "forecast": state["building"]["forecast_level"],
        "inbound": state["volume"]["inbound_processed"],
        "outbound": state["volume"]["outbound_processed"],
        "dock": state["volume"]["dock_processed"],
        "staffing": get_staffing(state),
        "cpt": cpt_summary(state)
    }


# =========================
# V5 FULL SIMULATOR SYSTEMS
# =========================

def ensure_full_systems(state):
    state.setdefault("paused", False)
    state.setdefault("sim_speed", "NORMAL")
    state.setdefault("ai_logs", [])
    state.setdefault("action_items", [])
    state.setdefault("hr_cases", [])
    state.setdefault("applications", [])
    state.setdefault("interviews", [])
    state.setdefault("training_classes", [])
    state.setdefault("safety_reports", [])
    state.setdefault("audits", [])
    state.setdefault("rumors", [])
    state.setdefault("conflicts", [])
    state.setdefault("recognition_log", [])
    state.setdefault("promotions_log", [])
    state.setdefault("station_board", {})
    state.setdefault("yard", {
        "pending_pulls": 0,
        "pending_spots": 0,
        "yard_congestion": "NORMAL",
        "available_doors": 14,
        "occupied_doors": 38
    })
    return state

def summarize_department(state, department):
    ensure_full_systems(state)
    associates = [a for a in state["ai_associates"] if a["department"] == department]
    health = state["department_health"].get(department, 100)
    avg_uph = int(sum(a["uph"] for a in associates) / max(1, len(associates)))
    avg_quality = int(sum(a["quality"] for a in associates) / max(1, len(associates)))
    avg_morale = int(sum(a["morale"] for a in associates) / max(1, len(associates)))
    return {
        "department": department,
        "health": health,
        "headcount": len(associates),
        "avg_uph": avg_uph,
        "avg_quality": avg_quality,
        "avg_morale": avg_morale,
        "staffing": get_staffing(state, department)
    }

def labor_move_ai(state, from_department, to_department, amount):
    ensure_full_systems(state)
    if from_department not in DEPARTMENTS or to_department not in DEPARTMENTS:
        return False, "Invalid department."
    candidates = [a for a in state["ai_associates"] if a["department"] == from_department and a["status"] in ["Working", "Scheduled"]]
    moved = candidates[:max(0, min(amount, len(candidates)))]
    for a in moved:
        old = a["department"]
        a["department"] = to_department
        a["area"] = random.choice(DEPARTMENTS[to_department])
        a["station"] = a["area"]
        a["status"] = "Helping Another Area"
        a["history"].append(f"Labor shared from {old} to {to_department}.")
    state["department_health"][to_department] = min(100, state["department_health"][to_department] + len(moved))
    state["department_health"][from_department] = max(40, state["department_health"][from_department] - max(0, len(moved)//2))
    state["events"].append({"time": datetime.now().strftime("%H:%M"), "type": "Labor Move", "message": f"{len(moved)} AI associates moved from {from_department} to {to_department}."})
    save_state(state)
    return True, f"Moved {len(moved)} AI associates from {from_department} to {to_department}."

def create_action_item(state, title, owner="AI Leadership", due="Next Shift"):
    ensure_full_systems(state)
    item = {"id": str(len(state["action_items"]) + 1), "title": title, "owner": owner, "due": due, "status": "Open"}
    state["action_items"].append(item)
    save_state(state)
    return item

def create_training_class(state, topic, seats=8):
    ensure_full_systems(state)
    attendees = random.sample(state["ai_associates"], min(seats, len(state["ai_associates"])))
    item = {
        "id": str(len(state["training_classes"]) + 1),
        "topic": topic,
        "seats": seats,
        "registered": len(attendees),
        "status": "Scheduled",
        "attendees": [a["name"] for a in attendees]
    }
    state["training_classes"].append(item)
    save_state(state)
    return item

def complete_training_class(state, class_id):
    ensure_full_systems(state)
    item = next((c for c in state["training_classes"] if c["id"] == str(class_id)), None)
    if not item:
        return False, "Class not found."
    if item["status"] == "Completed":
        return False, "Class already completed."
    item["status"] = "Completed"
    topic = item["topic"]
    for name in item["attendees"]:
        a = next((x for x in state["ai_associates"] if x["name"] == name), None)
        if a and topic not in a["certifications"]:
            a["certifications"].append(topic)
            a["morale"] = min(100, a["morale"] + 2)
    state["department_health"]["Learning"] = min(100, state["department_health"]["Learning"] + 3)
    save_state(state)
    return True, f"Completed {topic} class. {len(item['attendees'])} AI associates trained."

def create_safety_report(state, issue, department="Ship Dock", severity="Medium"):
    ensure_full_systems(state)
    report = {"id": str(len(state["safety_reports"]) + 1), "issue": issue, "department": department, "severity": severity, "status": "Open"}
    state["safety_reports"].append(report)
    state["building"]["safety"] = max(70, state["building"]["safety"] - (3 if severity.lower()=="high" else 1))
    state["events"].append({"time": datetime.now().strftime("%H:%M"), "type": "Safety Report", "message": f"{severity} safety issue reported in {department}: {issue}"})
    save_state(state)
    return report

def close_safety_report(state, report_id):
    ensure_full_systems(state)
    r = next((x for x in state["safety_reports"] if x["id"] == str(report_id)), None)
    if not r:
        return False, "Safety report not found."
    r["status"] = "Closed"
    state["building"]["safety"] = min(100, state["building"]["safety"] + 2)
    state["department_health"][r["department"]] = min(100, state["department_health"].get(r["department"], 90) + 2)
    save_state(state)
    return True, f"Closed safety report {report_id}."

def conduct_audit(state, department, audit_type="Safety Audit"):
    ensure_full_systems(state)
    score = random.randint(78, 100)
    audit = {"id": str(len(state["audits"]) + 1), "department": department, "type": audit_type, "score": score, "time": datetime.now().strftime("%H:%M")}
    state["audits"].append(audit)
    if score >= 90:
        state["department_health"][department] = min(100, state["department_health"].get(department, 90) + 3)
    else:
        state["department_health"][department] = max(40, state["department_health"].get(department, 90) - 3)
    save_state(state)
    return audit

def recognize_ai(state, name, reason="Great work"):
    ensure_full_systems(state)
    a = next((x for x in state["ai_associates"] if name.lower() in x["name"].lower()), None)
    if not a:
        return False, "AI associate not found."
    a["positive_feedback"] += 1
    a["morale"] = min(100, a["morale"] + 8)
    a["trust"] = min(100, a["trust"] + 3)
    log = {"name": a["name"], "reason": reason, "time": datetime.now().strftime("%H:%M")}
    state["recognition_log"].append(log)
    save_state(state)
    return True, f"Recognized {a['name']}: {reason}"

def coach_ai(state, name, topic="Productivity"):
    ensure_full_systems(state)
    a = next((x for x in state["ai_associates"] if name.lower() in x["name"].lower()), None)
    if not a:
        return False, "AI associate not found."
    if topic.lower() == "quality":
        a["quality"] = min(100, a["quality"] + 2)
    elif topic.lower() == "safety":
        a["safety"] = min(100, a["safety"] + 2)
    else:
        a["uph"] += random.randint(3, 8)
    a["stress"] = min(100, a["stress"] + 2)
    a["history"].append(f"Coached on {topic}.")
    save_state(state)
    return True, f"Coached {a['name']} on {topic}."

def writeup_ai(state, name, reason="Policy violation"):
    ensure_full_systems(state)
    a = next((x for x in state["ai_associates"] if name.lower() in x["name"].lower()), None)
    if not a:
        return False, "AI associate not found."
    a["writeups"] += 1
    a["morale"] = max(30, a["morale"] - 10)
    a["trust"] = max(10, a["trust"] - 5)
    a["history"].append(f"Write-up: {reason}")
    save_state(state)
    return True, f"Issued write-up to {a['name']}: {reason}"

def promote_ai(state, name, new_rank):
    ensure_full_systems(state)
    if new_rank not in RANKS:
        return False, "Invalid rank."
    a = next((x for x in state["ai_associates"] if name.lower() in x["name"].lower()), None)
    if not a:
        return False, "AI associate not found."
    old = a["rank"]
    a["rank"] = new_rank
    a["morale"] = min(100, a["morale"] + 15)
    a["trust"] = min(100, a["trust"] + 6)
    state["promotions_log"].append({"name": a["name"], "from": old, "to": new_rank, "time": datetime.now().strftime("%H:%M")})
    save_state(state)
    return True, f"Promoted {a['name']} from {old} to {new_rank}."

def ai_conversation(state, target="manager"):
    ensure_full_systems(state)
    if target == "manager":
        req = generate_manager_request(state)
        return f"{req['manager_name']} ({req['manager_role']}): {req['message']} Recommendation: {req['recommendation']}"
    a = random.choice(state["ai_associates"])
    lines = [
        f"{a['name']}: I’m currently in {a['department']} / {a['area']}. Morale is {a['morale']}%, stress is {a['stress']}%.",
        f"{a['name']}: I want to work toward {a['career_goal']}.",
        f"{a['name']}: My current station is {a['station']} and my status is {a['status']}.",
        f"{a['name']}: I think {a['department']} could use more support if volume keeps rising."
    ]
    return random.choice(lines)

def yard_status(state):
    ensure_full_systems(state)
    ready = sum(1 for t in state["trailers"] if t["status"] == "Ready" and not t["departed"])
    risk = sum(1 for t in state["trailers"] if t["status"] == "At Risk" and not t["departed"])
    state["yard"]["pending_pulls"] = ready
    state["yard"]["pending_spots"] = random.randint(0, 5)
    state["yard"]["yard_congestion"] = "HIGH" if risk >= 4 else "NORMAL"
    save_state(state)
    return state["yard"]

def request_tom_pull(state, trailer_id):
    ensure_full_systems(state)
    t = next((x for x in state["trailers"] if x["id"].lower() == trailer_id.lower()), None)
    if not t:
        return False, "Trailer not found."
    t["pull_requested"] = True
    t["tom_status"] = "Pull Requested"
    state["yard"]["pending_pulls"] += 1
    state["events"].append({"time": datetime.now().strftime("%H:%M"), "type": "TOM Request", "message": f"TOM pull requested for {t['id']} at Door {t['door']}."})
    save_state(state)
    return True, f"TOM pull requested for {t['id']}."

def station_assign(state, name, station):
    ensure_full_systems(state)
    a = next((x for x in state["ai_associates"] if name.lower() in x["name"].lower()), None)
    if not a:
        return False, "AI associate not found."
    a["station"] = station
    a["status"] = "Working"
    state["station_board"][station] = a["name"]
    save_state(state)
    return True, f"{a['name']} assigned to {station}."

def open_hr_case(state, case_type, associate="AI Associate"):
    ensure_full_systems(state)
    case = {"id": str(len(state["hr_cases"]) + 1), "type": case_type, "associate": associate, "status": "Open"}
    state["hr_cases"].append(case)
    save_state(state)
    return case

def create_application(state, name, position):
    ensure_full_systems(state)
    app = {"id": str(len(state["applications"]) + 1), "name": name, "position": position, "status": "Under Review", "score": random.randint(65, 98)}
    state["applications"].append(app)
    save_state(state)
    return app

def schedule_interview(state, name, position):
    ensure_full_systems(state)
    interview = {"id": str(len(state["interviews"]) + 1), "name": name, "position": position, "status": "Scheduled", "score": None}
    state["interviews"].append(interview)
    save_state(state)
    return interview

def record_interview(state, interview_id):
    ensure_full_systems(state)
    item = next((x for x in state["interviews"] if x["id"] == str(interview_id)), None)
    if not item:
        return False, "Interview not found."
    item["status"] = "Completed"
    item["score"] = random.randint(60, 100)
    save_state(state)
    return True, f"Interview completed. Score: {item['score']}%."

def simulate_day(state):
    for _ in range(10):
        simulate_hour(state)
    state["building"]["day"] += 1
    state["events"].append({"time": datetime.now().strftime("%H:%M"), "type": "Day Complete", "message": f"Day {state['building']['day']} started."})
    save_state(state)

def simulate_week(state):
    for _ in range(7):
        simulate_day(state)
    save_state(state)
