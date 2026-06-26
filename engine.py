
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
