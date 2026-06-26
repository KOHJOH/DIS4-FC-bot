
import json, os, random, time
from datetime import datetime, timedelta

DATA_FILE = "solo_fc_state.json"

FIRST_NAMES = ["Marcus","Emily","Carlos","Sarah","James","Alyssa","Anthony","Nia","Jordan","Maya","Darius","Sofia","Malik","Jasmine","Tyler","Brianna","Chris","Natalie","Andre","Kayla","Devin","Mariah","Ethan","Jada","Noah","Ariana","Luis","Savannah","Jaylen","Taylor"]
LAST_NAMES = ["Johnson","Davis","Ramirez","Miller","Carter","Thompson","Walker","Brown","Williams","Garcia","Anderson","Moore","Jackson","Harris","Clark","Lewis","Young","King","Wright"]

DEPARTMENTS = {
    "Ship Dock": ["Shipping Sorter","Transship","Quality","Lower Mezzanine","Upper Mezzanine","VRETS","Ship Clerk","TDR"],
    "Pick": ["Pick Floor 1","Pick Floor 2","Pick Floor 3","Amnesty"],
    "Stow": ["Stow Floor 1","Stow Floor 2","Stow Floor 3","Amnesty"],
    "Pack": ["Pack Singles","AFE Pack","AFE Induct","AFE Rebin","SLAM"],
    "Inbound": ["Receive Dock","Decant","Inbound Problem Solve"],
    "ICQA": ["SRC","SBC","Cycle Count","ICQA Problem Solve"],
    "Learning": ["Training","Cross Training","Certifications"],
    "Safety": ["Safety Audits","Incident Response"],
    "PXT / HR": ["Attendance","Cases","Schedule"],
    "Non-Inventory": ["Supplies","Inventory Cage"]
}
SHIFTS = {"Front Half Nights":"Sunday-Wednesday","Back Half Nights":"Wednesday-Saturday"}
RANKS = ["T1 Fulfillment Associate","Learning Ambassador","Process Guide","T3 Process Assistant","L4 Area Manager","L5 Area Manager","L6 Operations Manager","L7 Senior Operations Manager","L8 General Manager"]
CERTS = ["PIT","TDR","AFM","Learning Ambassador","Process Guide","Problem Solve","Shipping Clerk","Quality Specialist","Flow Lead","Water Spider","Tote Runner","SRC","SBC","Cycle Count","SLAM","AFE Induct","AFE Rebin"]
PERSONALITIES = ["High Performer","Reliable Veteran","New Hire","Speed Demon","Safety First","Future Leader","Quiet Worker","Needs Coaching","Problem Solver","Trainer Type"]
TRAILER_TYPES = ["Fluid","Palletized","Transship","Amazon Air","Returns","Vendor","Hazmat"]
EVENTS = ["Missort Spike","Conveyor Jam","Scanner Network Issue","Trailer Delay","Yard Congestion","PIT Battery Shortage","Empty Cart Shortage","Dock Plate Issue","Safety Near Miss","Quality Defect Spike","Late Inbound Appointment","AR Floor Fault","Printer Offline"]

def save_state(state):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def load_state():
    if not os.path.exists(DATA_FILE):
        return create_state()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def random_name(existing):
    for _ in range(1000):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if name not in existing:
            existing.add(name)
            return name
    return f"Associate {random.randint(1000,9999)}"

def make_ai_associate(i, existing):
    dept = random.choice(list(DEPARTMENTS.keys()))
    area = random.choice(DEPARTMENTS[dept])
    personality = random.choice(PERSONALITIES)
    rank = random.choices(["T1 Fulfillment Associate","Learning Ambassador","Process Guide","T3 Process Assistant","L4 Area Manager","L5 Area Manager"], weights=[72,8,8,6,4,2])[0]
    certs = random.sample(CERTS, random.randint(0, 5))
    if rank == "Learning Ambassador" and "Learning Ambassador" not in certs: certs.append("Learning Ambassador")
    if rank == "Process Guide" and "Process Guide" not in certs: certs.append("Process Guide")
    base = {
        "High Performer": (135,99,100,98), "Reliable Veteran": (120,99,100,99), "New Hire": (85,94,97,95),
        "Speed Demon": (150,94,98,96), "Safety First": (105,98,100,98), "Future Leader": (128,99,100,99),
        "Quiet Worker": (112,98,99,97), "Needs Coaching": (78,90,94,88), "Problem Solver": (115,99,100,97),
        "Trainer Type": (108,99,100,98)
    }[personality]
    return {
        "id": f"DIS4-{10000+i}", "name": random_name(existing), "rank": rank, "department": dept, "area": area,
        "shift": random.choice(list(SHIFTS.keys())), "personality": personality, "status": "Scheduled", "station": area,
        "uph": max(50, int(random.gauss(base[0], 10))), "quality": max(80, min(100, int(random.gauss(base[1], 2)))),
        "safety": max(80, min(100, int(random.gauss(base[2], 1)))), "attendance": max(60, min(100, int(random.gauss(base[3], 4)))),
        "morale": random.randint(75, 100), "certifications": certs, "tenure_days": random.randint(1, 900),
        "writeups": 0, "positive_feedback": random.randint(0, 12), "cpt_saves": random.randint(0, 5),
        "career_goal": random.choice(["Stay Associate","Become PG","Become PA","Become AM","Become Trainer"]),
        "history": []
    }

def create_trailers():
    trailers = []
    for _ in range(18):
        cpt = datetime.now() + timedelta(minutes=random.randint(45, 420))
        door = str(random.choice(list(range(120,151)) + list(range(201,223))))
        trailers.append({"id": f"TR-{random.randint(100,999)}", "door": door, "type": random.choice(TRAILER_TYPES), "cpt": cpt.strftime("%H:%M"), "packages_remaining": random.randint(0,1500), "status": random.choice(["On Track","On Track","At Risk","Loading","Ready"]), "pull_requested": False, "departed": False})
    return trailers

def create_state():
    existing = set()
    associates = [make_ai_associate(i, existing) for i in range(220)]
    state = {
        "version": "4.0 Solo AI FC Simulator",
        "created_at": datetime.now().isoformat(),
        "player": {"name":"You","rank":"L6 Operations Manager","department":"Ship Dock","shift":"Front Half Nights"},
        "building": {"day":1,"shift":"Front Half Nights","forecast_level":"NORMAL","building_health":96,"safety":99,"quality":99,"cpt_compliance":99.2,"missorts":8,"reputation":4.7,"forecast_accuracy":97.5,"labor_efficiency":95},
        "volume": {"inbound_expected":165000,"outbound_expected":245000,"ship_dock_carts":3500,"trailers_expected":72,"inbound_processed":0,"outbound_processed":0,"dock_processed":0},
        "department_health": {dept: random.randint(88,100) for dept in DEPARTMENTS},
        "area_health": {area: random.randint(85,100) for areas in DEPARTMENTS.values() for area in areas},
        "ai_associates": associates, "trailers": create_trailers(), "events": [], "action_items": [], "handoff_notes": [], "business_history": [],
        "equipment": {"Scanners":{"available":180,"total":200},"Pallet Jacks":{"available":46,"total":55},"Radios":{"available":28,"total":35},"Printers":{"available":19,"total":22},"Go Carts":{"available":640,"total":800},"Yellow Totes":{"available":2200,"total":3000},"PIT Batteries":{"available":32,"total":40}},
        "records": {"best_cpt_compliance":99.2,"highest_building_health":96,"most_cpt_saves":0}
    }
    save_state(state)
    return state

def reset_state():
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    return create_state()

def get_staffing(state, department=None):
    associates = state["ai_associates"]
    if department: associates = [a for a in associates if a["department"] == department]
    return {
        "scheduled": len(associates),
        "clocked_in": sum(1 for a in associates if a["status"] in ["Working","Training","Problem Solve","Helping Another Area"]),
        "late": sum(1 for a in associates if a["status"] == "Late"),
        "calloffs": sum(1 for a in associates if a["status"] == "Call Off"),
        "vto": sum(1 for a in associates if a["status"] == "VTO")
    }

def start_shift(state):
    for a in state["ai_associates"]:
        roll = random.random()
        if roll < 0.04: a["status"] = "Call Off"
        elif roll < 0.07: a["status"] = "Late"
        elif roll < 0.12 and state["building"]["forecast_level"] in ["LOW","NORMAL"]: a["status"] = "VTO"
        else: a["status"] = "Working"
    state["events"].append({"time": datetime.now().strftime("%H:%M"), "type":"Shift Start", "message":f"{state['building']['shift']} started. AI staffing initialized."})
    save_state(state)

def forecast_update(state, level=None):
    levels = ["LOW","NORMAL","HIGH","PEAK","PRIME WEEK","PEAK SEASON"]
    if level is None: level = random.choices(levels, weights=[10,35,30,15,6,4])[0]
    mult = {"LOW":0.72,"NORMAL":1.0,"HIGH":1.23,"PEAK":1.45,"PRIME WEEK":1.75,"PEAK SEASON":1.9}[level]
    state["building"]["forecast_level"] = level
    state["volume"]["inbound_expected"] = int(165000 * mult * random.uniform(0.9,1.1))
    state["volume"]["outbound_expected"] = int(245000 * mult * random.uniform(0.9,1.1))
    state["volume"]["ship_dock_carts"] = int(3500 * mult * random.uniform(0.9,1.15))
    state["volume"]["trailers_expected"] = int(72 * mult * random.uniform(0.9,1.1))
    save_state(state)

def create_event(state):
    event = random.choice(EVENTS); dept = random.choice(list(DEPARTMENTS.keys())); impact = random.randint(2,10)
    state["department_health"][dept] = max(40, state["department_health"][dept] - impact)
    if event == "Missort Spike": state["building"]["missorts"] += random.randint(8,35)
    if event in ["Safety Near Miss","Dock Plate Issue"]: state["building"]["safety"] = max(80, state["building"]["safety"] - random.randint(1,4))
    if event in ["Quality Defect Spike","Missort Spike"]: state["building"]["quality"] = max(80, state["building"]["quality"] - random.randint(1,4))
    if event in ["Trailer Delay","Yard Congestion"]: state["building"]["cpt_compliance"] = max(80, round(state["building"]["cpt_compliance"] - random.uniform(0.2,1.8), 1))
    rec = {"time": datetime.now().strftime("%H:%M"), "type": event, "department": dept, "impact": impact, "message": f"{event} impacted {dept}. Health -{impact}%."}
    state["events"].append(rec)
    return rec

def simulate_hour(state):
    forecast = state["building"]["forecast_level"]
    mult = {"LOW":0.06,"NORMAL":0.08,"HIGH":0.09,"PEAK":0.11,"PRIME WEEK":0.13,"PEAK SEASON":0.14}[forecast]
    staffing = get_staffing(state); labor = min(1.15, staffing["clocked_in"] / max(1, staffing["scheduled"] * 0.86))
    state["volume"]["inbound_processed"] += int(state["volume"]["inbound_expected"] * mult * labor * random.uniform(0.85,1.08))
    state["volume"]["outbound_processed"] += int(state["volume"]["outbound_expected"] * mult * labor * random.uniform(0.85,1.08))
    state["volume"]["dock_processed"] += int(state["volume"]["ship_dock_carts"] * mult * labor * random.uniform(0.85,1.08))
    for t in state["trailers"]:
        if t["departed"]: continue
        reduction = random.randint(40,220)
        if state["department_health"].get("Ship Dock",100) < 80: reduction = int(reduction * 0.7)
        t["packages_remaining"] = max(0, t["packages_remaining"] - reduction)
        t["status"] = "Ready" if t["packages_remaining"] == 0 else ("At Risk" if t["packages_remaining"] > 500 and random.random() < 0.25 else "On Track")
    if random.random() < 0.45: create_event(state)
    for dept in state["department_health"]:
        if random.random() < 0.5: state["department_health"][dept] = min(100, state["department_health"][dept] + random.randint(1,3))
    state["building"]["building_health"] = int(sum(state["department_health"].values()) / len(state["department_health"]))
    state["records"]["highest_building_health"] = max(state["records"]["highest_building_health"], state["building"]["building_health"])
    save_state(state)

def recommendations(state):
    recs = []; s = get_staffing(state)
    if s["clocked_in"] < s["scheduled"] * 0.82: recs.append("Cancel VTO and labor share AI associates to critical areas.")
    if state["department_health"].get("Ship Dock",100) < 85: recs.append("Move labor to Ship Dock and start CPT recovery.")
    if state["building"]["missorts"] > 20: recs.append("Assign Quality PA to investigate missort root cause.")
    if state["building"]["safety"] < 96: recs.append("Run a Safety Gemba walk and pause high-risk moves.")
    if any(t["status"] == "At Risk" for t in state["trailers"]): recs.append("Ship Clerk should prioritize at-risk CPTs and request TOM pulls for ready trailers.")
    if state["equipment"]["Scanners"]["available"] < 160: recs.append("Request equipment audit: scanner availability is low.")
    return recs or ["Operation is stable. Continue monitoring forecast and CPT board."]

def cpt_summary(state):
    open_cpts = [t for t in state["trailers"] if not t["departed"]]
    return {"open": len(open_cpts), "at_risk": sum(1 for t in open_cpts if t["status"]=="At Risk"), "ready": sum(1 for t in open_cpts if t["status"]=="Ready"), "departed": sum(1 for t in state["trailers"] if t["departed"])}

def depart_trailer(state, trailer_id):
    for t in state["trailers"]:
        if t["id"].lower() == trailer_id.lower():
            if t["departed"]: return False, "Trailer already departed."
            t["departed"] = True; t["status"] = "Departed"
            if t["packages_remaining"] > 0:
                state["building"]["cpt_compliance"] = max(80, round(state["building"]["cpt_compliance"] - random.uniform(0.1,0.8),1))
                msg = f"{t['id']} departed with {t['packages_remaining']} packages remaining. CPT risk increased."
            else:
                state["building"]["cpt_compliance"] = min(100, round(state["building"]["cpt_compliance"] + 0.1,1))
                msg = f"{t['id']} departed on time and clean."
            save_state(state); return True, msg
    return False, "Trailer not found."

def business_review(state):
    return {
        "day": state["building"]["day"], "building_health": state["building"]["building_health"], "safety": state["building"]["safety"],
        "quality": state["building"]["quality"], "cpt_compliance": state["building"]["cpt_compliance"], "missorts": state["building"]["missorts"],
        "forecast": state["building"]["forecast_level"], "inbound": state["volume"]["inbound_processed"], "outbound": state["volume"]["outbound_processed"],
        "dock": state["volume"]["dock_processed"], "staffing": get_staffing(state), "cpt": cpt_summary(state)
    }


# =========================
# V4.1 INTERACTIVE AI SYSTEM
# =========================

MANAGER_PERSONALITIES = [
    "Aggressive Operator", "Safety-First Leader", "Metrics-Driven",
    "People-First", "Trainer Type", "Veteran Manager", "New Manager"
]

def ensure_interactive_state(state):
    if "manager_requests" not in state:
        state["manager_requests"] = []
    if "request_counter" not in state:
        state["request_counter"] = 1000
    if "manager_memory" not in state:
        state["manager_memory"] = []
    return state

def next_request_id(state):
    ensure_interactive_state(state)
    state["request_counter"] += 1
    return str(state["request_counter"])

def generate_manager_request(state, department=None):
    ensure_interactive_state(state)

    department = department or random.choice(list(DEPARTMENTS.keys()))
    area = random.choice(DEPARTMENTS[department])
    personality = random.choice(MANAGER_PERSONALITIES)

    possible = []

    if department == "Ship Dock":
        risk_trailers = [t for t in state["trailers"] if t["status"] == "At Risk" and not t["departed"]]
        if risk_trailers:
            t = random.choice(risk_trailers)
            possible.append({
                "type": "CPT Recovery",
                "title": f"CPT Risk — {t['id']}",
                "message": f"Trailer {t['id']} at Door {t['door']} is projected at risk. {t['packages_remaining']} packages remain before CPT {t['cpt']}.",
                "recommendation": "Launch CPT recovery, move 2 AI associates from Upper Mezzanine, and request TOM pull when ready.",
                "impact_approve": {"cpt": 0.4, "shipdock": 4, "morale": -1},
                "impact_deny": {"cpt": -0.7, "shipdock": -3, "morale": 0}
            })

    if state["department_health"].get(department, 100) < 88:
        possible.append({
            "type": "Department Recovery",
            "title": f"{department} Health Dropping",
            "message": f"{department} health is trending below target at {state['department_health'][department]}%.",
            "recommendation": "Pause non-critical work, run a Gemba walk, and shift AI labor to the weakest area.",
            "impact_approve": {"dept": 6, "building": 2, "morale": 1},
            "impact_deny": {"dept": -4, "building": -1, "morale": -1}
        })

    if state["building"]["missorts"] > 18:
        possible.append({
            "type": "Quality Escalation",
            "title": "Missorts Trending High",
            "message": f"Missorts are currently at {state['building']['missorts']}, above the expected threshold.",
            "recommendation": "Assign Quality to investigate root cause and place a PA at the sorter lanes.",
            "impact_approve": {"missorts": -8, "quality": 1, "dept": 3},
            "impact_deny": {"missorts": 6, "quality": -1, "dept": -2}
        })

    if state["building"]["safety"] < 97:
        possible.append({
            "type": "Safety Concern",
            "title": "Safety Score Below Target",
            "message": f"Site safety score is {state['building']['safety']}%. Safety recommends a focused audit.",
            "recommendation": "Run safety standdown and assign Safety Specialist to investigate.",
            "impact_approve": {"safety": 2, "building": 1, "morale": 1},
            "impact_deny": {"safety": -2, "building": -1, "morale": -1}
        })

    if not possible:
        possible.append({
            "type": "Proactive Improvement",
            "title": f"{department} Improvement Opportunity",
            "message": f"{department} is stable, but the manager sees an opportunity to improve flow.",
            "recommendation": "Run a 5S walk, recognize top performers, and prep for the next volume push.",
            "impact_approve": {"dept": 3, "building": 1, "morale": 2},
            "impact_deny": {"dept": 0, "building": 0, "morale": 0}
        })

    req = random.choice(possible)
    request = {
        "id": next_request_id(state),
        "status": "Open",
        "department": department,
        "area": area,
        "manager_name": random.choice(FIRST_NAMES) + " " + random.choice(LAST_NAMES),
        "manager_role": f"{department} Area Manager",
        "manager_personality": personality,
        "type": req["type"],
        "title": req["title"],
        "message": req["message"],
        "recommendation": req["recommendation"],
        "impact_approve": req["impact_approve"],
        "impact_deny": req["impact_deny"],
        "created_at": datetime.now().strftime("%H:%M")
    }

    state["manager_requests"].append(request)
    save_state(state)
    return request

def apply_request_decision(state, request_id, approved=True):
    ensure_interactive_state(state)
    req = None

    for r in state["manager_requests"]:
        if str(r["id"]) == str(request_id):
            req = r
            break

    if not req:
        return False, "Request not found."

    if req["status"] != "Open":
        return False, f"Request already {req['status']}."

    impacts = req["impact_approve"] if approved else req["impact_deny"]
    dept = req["department"]

    for key, value in impacts.items():
        if key == "cpt":
            state["building"]["cpt_compliance"] = max(70, min(100, round(state["building"]["cpt_compliance"] + value, 1)))
        elif key == "shipdock":
            state["department_health"]["Ship Dock"] = max(40, min(100, state["department_health"]["Ship Dock"] + value))
        elif key == "dept":
            state["department_health"][dept] = max(40, min(100, state["department_health"][dept] + value))
        elif key == "building":
            state["building"]["building_health"] = max(40, min(100, state["building"]["building_health"] + value))
        elif key == "morale":
            for a in state["ai_associates"]:
                if a["department"] == dept:
                    a["morale"] = max(30, min(100, a["morale"] + value))
        elif key == "missorts":
            state["building"]["missorts"] = max(0, state["building"]["missorts"] + value)
        elif key == "quality":
            state["building"]["quality"] = max(70, min(100, state["building"]["quality"] + value))
        elif key == "safety":
            state["building"]["safety"] = max(70, min(100, state["building"]["safety"] + value))

    req["status"] = "Approved" if approved else "Denied"
    req["resolved_at"] = datetime.now().strftime("%H:%M")
    state["manager_memory"].append({
        "time": datetime.now().strftime("%H:%M"),
        "request": req["title"],
        "department": req["department"],
        "decision": req["status"]
    })

    save_state(state)
    return True, f"Request {req['status']}: {req['title']}"

def get_open_requests(state):
    ensure_interactive_state(state)
    return [r for r in state["manager_requests"] if r["status"] == "Open"]

def manager_meeting_summary(state):
    ensure_interactive_state(state)
    while len(get_open_requests(state)) < 3:
        generate_manager_request(state)
    return get_open_requests(state)[:5]
