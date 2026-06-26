
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, BOT_OWNER_ID
from engine import *
from sim_data import DEPARTMENTS, SHIFTS, RANKS, FORECAST_LEVELS
from views import DashboardView, RequestView, build_request_embed

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def owner_only(interaction):
    return interaction.user.id == BOT_OWNER_ID

def dashboard_embed(state):
    b = state["building"]
    v = state["volume"]
    s = get_staffing(state)
    c = cpt_summary(state)

    embed = discord.Embed(title="🏢 DIS4 FC Simulator V5", description="Interactive AI Operations Control Panel", color=discord.Color.blue())
    embed.add_field(name="Forecast", value=b["forecast_level"], inline=True)
    embed.add_field(name="Health", value=f"{b['building_health']}%", inline=True)
    embed.add_field(name="CPT", value=f"{b['cpt_compliance']}%", inline=True)
    embed.add_field(name="Inbound", value=fmt(v["inbound_expected"]), inline=True)
    embed.add_field(name="Outbound", value=fmt(v["outbound_expected"]), inline=True)
    embed.add_field(name="At Risk CPTs", value=str(c["at_risk"]), inline=True)
    embed.add_field(name="AI Staffing", value=f"{s['clocked_in']} / {s['scheduled']}", inline=True)
    embed.add_field(name="Missorts", value=str(b["missorts"]), inline=True)
    embed.add_field(name="Open SEVs", value=str(b.get("open_sevs", 0)), inline=True)
    return embed

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Command sync failed: {e}")

@bot.tree.command(name="v5_help", description="View V5 commands.")
async def v5_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🏢 **DIS4 FC Simulator V5**\n\n"
        "`/v5_start` — create/reset the AI building\n"
        "`/v5_panel` — interactive dashboard with buttons\n"
        "`/v5_dashboard` — executive dashboard\n"
        "`/v5_foresight` — inbound/outbound forecast\n"
        "`/v5_start_shift` — start FHN/BHN\n"
        "`/v5_sim_hour` — simulate one hour\n"
        "`/v5_sim_shift` — simulate full shift\n"
        "`/v5_manager_request` — interactive AI manager request\n"
        "`/v5_manager_messages` — latest open manager message\n"
        "`/v5_manager_meeting` — multiple AI manager issues\n"
        "`/v5_approve` / `/v5_deny` — decide requests\n"
        "`/v5_staffing` — AI staffing board\n"
        "`/v5_cpt` — Ship Dock CPT board\n"
        "`/v5_depart` — depart a trailer\n"
        "`/v5_ai_associate` — inspect AI associate\n"
        "`/v5_leadership` — AI leadership directory\n"
        "`/v5_equipment` — equipment status\n"
        "`/v5_business_review` — BR summary"
    )

@bot.tree.command(name="v5_start", description="Create/reset the V5 AI building.")
async def v5_start(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = reset_state()
    await interaction.response.send_message(f"✅ **DIS4 V5 created.**\n\nAI Associates: **{len(state['ai_associates'])}**\nDefault Role: **{state['player']['rank']}**\nDepartment: **{state['player']['department']}**\n\nRun `/v5_panel`.")

@bot.tree.command(name="v5_panel", description="Open interactive V5 control panel.")
async def v5_panel(interaction: discord.Interaction):
    state = load_state()
    await interaction.response.send_message(embed=dashboard_embed(state), view=DashboardView(BOT_OWNER_ID))

@bot.tree.command(name="v5_dashboard", description="View executive dashboard.")
async def v5_dashboard(interaction: discord.Interaction):
    state = load_state()
    await interaction.response.send_message(embed=dashboard_embed(state), view=DashboardView(BOT_OWNER_ID))

@bot.tree.command(name="v5_assign_me", description="Rotate yourself to a department/rank.")
async def v5_assign_me(interaction: discord.Interaction, department: str, rank: str = "L6 Operations Manager"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    if department not in DEPARTMENTS:
        return await interaction.response.send_message("❌ Invalid department.", ephemeral=True)
    if rank not in RANKS:
        return await interaction.response.send_message("❌ Invalid rank.", ephemeral=True)
    state = load_state()
    state["player"]["department"] = department
    state["player"]["rank"] = rank
    save_state(state)
    await interaction.response.send_message(f"✅ You are now **{rank}** over **{department}**.")

@bot.tree.command(name="v5_foresight", description="View Foresight-style inbound/outbound forecast.")
async def v5_foresight(interaction: discord.Interaction):
    state = load_state()
    v = state["volume"]
    b = state["building"]
    await interaction.response.send_message(
        f"📊 **DIS4 FORESIGHT**\n\n"
        f"Forecast Level: **{b['forecast_level']}**\n"
        f"Forecast Accuracy: **{b['forecast_accuracy']}%**\n\n"
        f"📥 **INBOUND**\nExpected: **{fmt(v['inbound_expected'])}**\nProcessed: **{fmt(v['inbound_processed'])}**\n\n"
        f"📦 **OUTBOUND**\nExpected: **{fmt(v['outbound_expected'])}**\nProcessed: **{fmt(v['outbound_processed'])}**\n\n"
        f"🚛 **SHIP DOCK**\nCarts: **{fmt(v['ship_dock_carts'])}**\nProcessed: **{fmt(v['dock_processed'])}**\nTrailers: **{v['trailers_expected']}**"
    )

@bot.tree.command(name="v5_set_forecast", description="Set forecast level.")
async def v5_set_forecast(interaction: discord.Interaction, level: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    if level not in FORECAST_LEVELS:
        return await interaction.response.send_message("❌ Invalid forecast. Use LOW, NORMAL, HIGH, PEAK, PRIME WEEK, or PEAK SEASON.", ephemeral=True)
    state = load_state()
    forecast_update(state, level)
    await interaction.response.send_message(f"✅ Forecast updated to **{level}**.")

@bot.tree.command(name="v5_start_shift", description="Start FHN/BHN AI shift.")
async def v5_start_shift(interaction: discord.Interaction, shift: str = "Front Half Nights"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    if shift not in SHIFTS:
        return await interaction.response.send_message("❌ Invalid shift. Use Front Half Nights or Back Half Nights.", ephemeral=True)
    state = load_state()
    start_shift(state, shift)
    s = get_staffing(state)
    await interaction.response.send_message(f"🌙 **{shift} Started**\n\nScheduled: **{s['scheduled']}**\nClocked In: **{s['clocked_in']}**\nLate: **{s['late']}**\nCall-Offs: **{s['calloffs']}**\nVTO: **{s['vto']}**")

@bot.tree.command(name="v5_sim_hour", description="Advance the FC by one simulated hour.")
async def v5_sim_hour(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    simulate_hour(state)
    recs = recommendations(state)
    await interaction.response.send_message(
        f"⏱️ **One Hour Simulated**\n\nHealth: **{state['building']['building_health']}%**\nCPT: **{state['building']['cpt_compliance']}%**\nMissorts: **{state['building']['missorts']}**\n\n🧠 **AI Recommendations**\n" + "\n".join([f"• {r}" for r in recs])
    )

@bot.tree.command(name="v5_sim_shift", description="Simulate a full shift.")
async def v5_sim_shift(interaction: discord.Interaction, hours: int = 10):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    hours = max(1, min(12, hours))
    state = load_state()
    for _ in range(hours):
        simulate_hour(state)
    br = business_review(state)
    await interaction.response.send_message(
        f"🌅 **Shift Simulation Complete**\n\nHours: **{hours}**\nHealth: **{br['building_health']}%**\nCPT: **{br['cpt_compliance']}%**\nSafety: **{br['safety']}%**\nQuality: **{br['quality']}%**\nMissorts: **{br['missorts']}**\nInbound: **{fmt(br['inbound'])}**\nOutbound: **{fmt(br['outbound'])}**"
    )

@bot.tree.command(name="v5_manager_request", description="Generate interactive AI manager request.")
async def v5_manager_request(interaction: discord.Interaction, department: str = None):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    if department and department not in DEPARTMENTS:
        return await interaction.response.send_message("❌ Invalid department.", ephemeral=True)
    req = generate_manager_request(state, department)
    await interaction.response.send_message(embed=build_request_embed(req), view=RequestView(BOT_OWNER_ID, req["id"]))

@bot.tree.command(name="v5_manager_messages", description="View latest open AI manager message.")
async def v5_manager_messages(interaction: discord.Interaction):
    state = load_state()
    reqs = open_requests(state)
    if not reqs:
        req = generate_manager_request(state)
    else:
        req = reqs[-1]
    await interaction.response.send_message(embed=build_request_embed(req), view=RequestView(BOT_OWNER_ID, req["id"]))

@bot.tree.command(name="v5_manager_meeting", description="Start AI manager meeting.")
async def v5_manager_meeting(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    reqs = manager_meeting(state)
    text = []
    for r in reqs:
        text.append(f"**{r['id']} — {r['department']}**\n{r['manager_name']}: {r['title']}\nRecommendation: {r['recommendation']}")
    await interaction.response.send_message("👔 **AI Manager Meeting**\n\n" + "\n\n".join(text) + "\n\nUse `/v5_manager_messages` to handle the latest request with buttons.")

@bot.tree.command(name="v5_approve", description="Approve manager request by ID.")
async def v5_approve(interaction: discord.Interaction, request_id: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    ok, msg = apply_request(state, request_id, True)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_deny", description="Deny manager request by ID.")
async def v5_deny(interaction: discord.Interaction, request_id: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    ok, msg = apply_request(state, request_id, False)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_staffing", description="View AI staffing by department.")
async def v5_staffing(interaction: discord.Interaction, department: str = None):
    state = load_state()
    if department:
        s = get_staffing(state, department)
        return await interaction.response.send_message(f"👥 **AI Staffing — {department}**\n\nScheduled: **{s['scheduled']}**\nClocked In: **{s['clocked_in']}**\nLate: **{s['late']}**\nCall-Offs: **{s['calloffs']}**\nVTO: **{s['vto']}**")
    lines = []
    for dept in DEPARTMENTS:
        s = get_staffing(state, dept)
        lines.append(f"**{dept}:** {s['clocked_in']} / {s['scheduled']} | Call-Offs: {s['calloffs']} | VTO: {s['vto']}")
    await interaction.response.send_message("👥 **DIS4 AI Staffing Board**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_cpt", description="View Ship Dock CPT board.")
async def v5_cpt(interaction: discord.Interaction):
    state = load_state()
    trailers = [t for t in state["trailers"] if not t["departed"]][:15]
    lines = []
    for t in trailers:
        icon = "🔴" if t["status"] == "At Risk" else "🟢" if t["status"] == "Ready" else "🟡"
        lines.append(f"{icon} **{t['id']}** | Door {t['door']} | CPT {t['cpt']} | {t['packages_remaining']} pkgs | {t['status']} | {t['type']}")
    await interaction.response.send_message("🚛 **Ship Dock CPT Board**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_depart", description="Depart a trailer.")
async def v5_depart(interaction: discord.Interaction, trailer_id: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    ok, msg = depart_trailer(state, trailer_id)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_ai_associate", description="Inspect AI associate by name.")
async def v5_ai_associate(interaction: discord.Interaction, name: str):
    state = load_state()
    matches = [a for a in state["ai_associates"] if name.lower() in a["name"].lower()]
    if not matches:
        sample = ", ".join([a["name"] for a in state["ai_associates"][:6]])
        return await interaction.response.send_message(f"❌ No AI associate found. Try: {sample}", ephemeral=True)
    a = matches[0]
    await interaction.response.send_message(
        f"👤 **AI Associate Profile**\n\nName: **{a['name']}**\nEmployee ID: **{a['id']}**\nRank: **{a['rank']}**\nDepartment: **{a['department']}**\nArea: **{a['area']}**\nShift: **{a['shift']}**\nPersonality: **{a['personality']}**\nStatus: **{a['status']}**\n\nUPH: **{a['uph']}**\nQuality: **{a['quality']}%**\nSafety: **{a['safety']}%**\nAttendance: **{a['attendance']}%**\nMorale: **{a['morale']}%**\nStress: **{a['stress']}%**\nTrust: **{a['trust']}%**\n\nCertifications: **{', '.join(a['certifications']) if a['certifications'] else 'None'}**\nCareer Goal: **{a['career_goal']}**"
    )

@bot.tree.command(name="v5_leadership", description="View AI leadership.")
async def v5_leadership(interaction: discord.Interaction, department: str = None):
    state = load_state()
    leaders = [a for a in state["ai_associates"] if a["rank"] in ["Process Guide", "T3 Process Assistant", "L4 Area Manager", "L5 Area Manager"]]
    if department:
        leaders = [a for a in leaders if a["department"] == department]
    lines = [f"• **{a['name']}** — {a['rank']} | {a['department']} / {a['area']}" for a in leaders[:25]]
    await interaction.response.send_message("👔 **AI Leadership Directory**\n\n" + ("\n".join(lines) or "No leadership found."))

@bot.tree.command(name="v5_equipment", description="View equipment status.")
async def v5_equipment(interaction: discord.Interaction):
    state = load_state()
    lines = []
    for name, data in state["equipment"].items():
        pct = round((data["available"] / data["total"]) * 100)
        icon = "🟢" if pct >= 85 else "🟡" if pct >= 70 else "🔴"
        lines.append(f"{icon} **{name}:** {data['available']} / {data['total']} ({pct}%)")
    await interaction.response.send_message("🔋 **Equipment Status**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_business_review", description="Generate business review.")
async def v5_business_review(interaction: discord.Interaction):
    state = load_state()
    br = business_review(state)
    await interaction.response.send_message(
        f"📈 **DIS4 Business Review — V5**\n\nDay: **{br['day']}**\nForecast: **{br['forecast']}**\nHealth: **{br['building_health']}%**\nSafety: **{br['safety']}%**\nQuality: **{br['quality']}%**\nCPT: **{br['cpt_compliance']}%**\nMissorts: **{br['missorts']}**\n\nInbound Processed: **{fmt(br['inbound'])}**\nOutbound Processed: **{fmt(br['outbound'])}**\nDock Carts: **{fmt(br['dock'])}**\nStaffing: **{br['staffing']['clocked_in']} / {br['staffing']['scheduled']}**\nOpen CPTs: **{br['cpt']['open']}**\nAt Risk CPTs: **{br['cpt']['at_risk']}**"
    )

@bot.tree.command(name="v5_events", description="View recent building events.")
async def v5_events(interaction: discord.Interaction):
    state = load_state()
    events = state["events"][-10:]
    if not events:
        return await interaction.response.send_message("No events yet. Run `/v5_sim_hour`.")
    lines = [f"• **{e['time']}** — {e['type']}: {e['message']}" for e in events]
    await interaction.response.send_message("🚨 **Recent Events**\n\n" + "\n".join(lines))




# =========================
# V5 FULL SIMULATOR COMMAND PACK
# =========================

@bot.tree.command(name="v5_live_operations", description="Live operations summary.")
async def v5_live_operations(interaction: discord.Interaction):
    state = load_state(); recs = recommendations(state); c = cpt_summary(state)
    await interaction.response.send_message(
        f"📡 **LIVE OPERATIONS**\n\nHealth: **{state['building']['building_health']}%**\nForecast: **{state['building']['forecast_level']}**\nCPT Compliance: **{state['building']['cpt_compliance']}%**\nOpen CPTs: **{c['open']}**\nAt Risk: **{c['at_risk']}**\nMissorts: **{state['building']['missorts']}**\n\n🧠 **AI Brain**\n" + "\n".join([f"• {r}" for r in recs])
    )

@bot.tree.command(name="v5_department", description="View department summary.")
async def v5_department(interaction: discord.Interaction, department: str):
    state = load_state()
    if department not in DEPARTMENTS:
        return await interaction.response.send_message("❌ Invalid department.", ephemeral=True)
    d = summarize_department(state, department)
    s = d["staffing"]
    await interaction.response.send_message(
        f"🏢 **{department} Summary**\n\nHealth: **{d['health']}%**\nHeadcount: **{d['headcount']}**\nAvg UPH: **{d['avg_uph']}**\nAvg Quality: **{d['avg_quality']}%**\nAvg Morale: **{d['avg_morale']}%**\n\nScheduled: **{s['scheduled']}**\nClocked In: **{s['clocked_in']}**\nCall-Offs: **{s['calloffs']}**"
    )

@bot.tree.command(name="v5_department_health", description="View all department health.")
async def v5_department_health(interaction: discord.Interaction):
    state = load_state()
    lines = []
    for d, h in state["department_health"].items():
        icon = "🟢" if h >= 90 else "🟡" if h >= 75 else "🔴"
        lines.append(f"{icon} **{d}:** {h}%")
    await interaction.response.send_message("🏥 **Department Health**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_labor_move", description="Move AI labor between departments.")
async def v5_labor_move(interaction: discord.Interaction, from_department: str, to_department: str, amount: int):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    ok, msg = labor_move_ai(state, from_department, to_department, amount)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_yard", description="View AI TOM yard status.")
async def v5_yard(interaction: discord.Interaction):
    state = load_state(); y = yard_status(state)
    await interaction.response.send_message(
        f"🚛 **AI TOM Yard Status**\n\nPending Pulls: **{y['pending_pulls']}**\nPending Spots: **{y['pending_spots']}**\nCongestion: **{y['yard_congestion']}**\nAvailable Doors: **{y['available_doors']}**\nOccupied Doors: **{y['occupied_doors']}**"
    )

@bot.tree.command(name="v5_request_pull", description="Request AI TOM pull for trailer.")
async def v5_request_pull(interaction: discord.Interaction, trailer_id: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    ok, msg = request_tom_pull(state, trailer_id)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_trailer", description="View trailer details.")
async def v5_trailer(interaction: discord.Interaction, trailer_id: str):
    state = load_state()
    t = next((x for x in state["trailers"] if x["id"].lower() == trailer_id.lower()), None)
    if not t:
        return await interaction.response.send_message("❌ Trailer not found.", ephemeral=True)
    await interaction.response.send_message(
        f"🚛 **Trailer {t['id']}**\n\nDoor: **{t['door']}**\nType: **{t['type']}**\nCPT: **{t['cpt']}**\nPackages Remaining: **{t['packages_remaining']}**\nStatus: **{t['status']}**\nTOM: **{t.get('tom_status','Docked')}**\nPull Requested: **{t['pull_requested']}**"
    )

@bot.tree.command(name="v5_cpt_recovery", description="Launch CPT recovery.")
async def v5_cpt_recovery(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    state["department_health"]["Ship Dock"] = min(100, state["department_health"]["Ship Dock"] + 5)
    state["building"]["cpt_compliance"] = min(100, round(state["building"]["cpt_compliance"] + 0.5, 1))
    create_action_item(state, "CPT Recovery", "Ship Dock AM", "Current Shift")
    save_state(state)
    await interaction.response.send_message("🚨 **CPT Recovery Launched**\n\n+5 Ship Dock Health\n+0.5 CPT Compliance\nAction item created.")

@bot.tree.command(name="v5_action_item", description="Create action item.")
async def v5_action_item(interaction: discord.Interaction, title: str, owner: str = "AI Leadership", due: str = "Next Shift"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); item = create_action_item(state, title, owner, due)
    await interaction.response.send_message(f"📋 **Action Item Created**\n\nID: **{item['id']}**\nTitle: **{title}**\nOwner: **{owner}**\nDue: **{due}**")

@bot.tree.command(name="v5_action_items", description="View action items.")
async def v5_action_items(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state)
    if not state["action_items"]:
        return await interaction.response.send_message("No action items.")
    lines = [f"• **{i['id']}** — {i['title']} | Owner: {i['owner']} | Due: {i['due']} | {i['status']}" for i in state["action_items"][-15:]]
    await interaction.response.send_message("📋 **Action Items**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_start_training", description="Schedule AI training class.")
async def v5_start_training(interaction: discord.Interaction, topic: str, seats: int = 8):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); c = create_training_class(state, topic, seats)
    await interaction.response.send_message(f"🎓 **Training Scheduled**\n\nID: **{c['id']}**\nTopic: **{topic}**\nRegistered: **{c['registered']} / {c['seats']}**")

@bot.tree.command(name="v5_complete_training", description="Complete AI training class.")
async def v5_complete_training(interaction: discord.Interaction, class_id: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = complete_training_class(state, class_id)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_training_classes", description="View training classes.")
async def v5_training_classes(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state)
    if not state["training_classes"]:
        return await interaction.response.send_message("No training classes.")
    lines = [f"• **{c['id']}** — {c['topic']} | {c['registered']}/{c['seats']} | {c['status']}" for c in state["training_classes"][-15:]]
    await interaction.response.send_message("🎓 **Training Classes**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_safety_report", description="Open safety report.")
async def v5_safety_report(interaction: discord.Interaction, issue: str, department: str = "Ship Dock", severity: str = "Medium"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    if department not in DEPARTMENTS:
        return await interaction.response.send_message("❌ Invalid department.", ephemeral=True)
    r = create_safety_report(state, issue, department, severity)
    await interaction.response.send_message(f"🦺 **Safety Report Opened**\n\nID: **{r['id']}**\nIssue: **{issue}**\nDepartment: **{department}**\nSeverity: **{severity}**")

@bot.tree.command(name="v5_close_safety", description="Close safety report.")
async def v5_close_safety(interaction: discord.Interaction, report_id: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = close_safety_report(state, report_id)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_safety_reports", description="View safety reports.")
async def v5_safety_reports(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state)
    if not state["safety_reports"]:
        return await interaction.response.send_message("No safety reports.")
    lines = [f"• **{r['id']}** — {r['issue']} | {r['department']} | {r['severity']} | {r['status']}" for r in state["safety_reports"][-15:]]
    await interaction.response.send_message("🦺 **Safety Reports**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_audit", description="Conduct department audit.")
async def v5_audit(interaction: discord.Interaction, department: str, audit_type: str = "Safety Audit"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state()
    if department not in DEPARTMENTS:
        return await interaction.response.send_message("❌ Invalid department.", ephemeral=True)
    a = conduct_audit(state, department, audit_type)
    await interaction.response.send_message(f"🔎 **Audit Complete**\n\nDepartment: **{department}**\nType: **{audit_type}**\nScore: **{a['score']}%**")

@bot.tree.command(name="v5_audits", description="View audit history.")
async def v5_audits(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state)
    if not state["audits"]:
        return await interaction.response.send_message("No audits yet.")
    lines = [f"• **{a['id']}** — {a['department']} | {a['type']} | {a['score']}%" for a in state["audits"][-15:]]
    await interaction.response.send_message("🔎 **Audit History**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_recognize", description="Recognize AI associate.")
async def v5_recognize(interaction: discord.Interaction, name: str, reason: str = "Great work"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = recognize_ai(state, name, reason)
    await interaction.response.send_message(("🏆 " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_coach", description="Coach AI associate.")
async def v5_coach(interaction: discord.Interaction, name: str, topic: str = "Productivity"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = coach_ai(state, name, topic)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_writeup", description="Write up AI associate.")
async def v5_writeup(interaction: discord.Interaction, name: str, reason: str = "Policy violation"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = writeup_ai(state, name, reason)
    await interaction.response.send_message(("📝 " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_promote_ai", description="Promote AI associate.")
async def v5_promote_ai(interaction: discord.Interaction, name: str, new_rank: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = promote_ai(state, name, new_rank)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_talk", description="Talk to AI manager or associate.")
async def v5_talk(interaction: discord.Interaction, target: str = "manager"):
    state = load_state()
    await interaction.response.send_message("💬 **AI Conversation**\n\n" + ai_conversation(state, target))

@bot.tree.command(name="v5_radio", description="Send leadership radio message.")
async def v5_radio(interaction: discord.Interaction, message: str):
    state = load_state()
    state["events"].append({"time": "Now", "type": "Radio", "message": f"Jump radioed: {message}"})
    save_state(state)
    await interaction.response.send_message(f"📻 **FLOW RADIO**\n\n{message}\n\n— Site Leader")

@bot.tree.command(name="v5_standup", description="Start shift standup.")
async def v5_standup(interaction: discord.Interaction):
    state = load_state()
    await interaction.response.send_message(
        f"📋 **SHIFT STANDUP**\n\nShift: **{state['building']['shift']}**\nForecast: **{state['building']['forecast_level']}**\nSafety: **{state['building']['safety']}%**\nQuality: **{state['building']['quality']}%**\nCPT: **{state['building']['cpt_compliance']}%**\nFocus: **Protect CPTs, reduce missorts, keep safety clean.**"
    )

@bot.tree.command(name="v5_handoff", description="Generate shift handoff.")
async def v5_handoff(interaction: discord.Interaction):
    state = load_state(); c = cpt_summary(state)
    await interaction.response.send_message(
        f"📋 **SHIFT HANDOFF**\n\nHealth: **{state['building']['building_health']}%**\nOpen CPTs: **{c['open']}**\nAt Risk: **{c['at_risk']}**\nMissorts: **{state['building']['missorts']}**\nOpen SEVs: **{state['building'].get('open_sevs',0)}**\n\nNotes: Watch Ship Dock and Quality. Review manager requests before next volume push."
    )

@bot.tree.command(name="v5_station_assign", description="Assign AI associate to station.")
async def v5_station_assign(interaction: discord.Interaction, name: str, station: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = station_assign(state, name, station)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_station_board", description="View station assignments.")
async def v5_station_board(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state)
    if not state["station_board"]:
        return await interaction.response.send_message("No station assignments yet.")
    lines = [f"• **{station}:** {name}" for station, name in list(state["station_board"].items())[-20:]]
    await interaction.response.send_message("📍 **Station Board**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_hr_case", description="Open HR/PXT case.")
async def v5_hr_case(interaction: discord.Interaction, case_type: str, associate: str = "AI Associate"):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); case = open_hr_case(state, case_type, associate)
    await interaction.response.send_message(f"📁 **PXT Case Opened**\n\nID: **{case['id']}**\nType: **{case_type}**\nAssociate: **{associate}**")

@bot.tree.command(name="v5_hr_cases", description="View HR/PXT cases.")
async def v5_hr_cases(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state)
    if not state["hr_cases"]:
        return await interaction.response.send_message("No HR cases.")
    lines = [f"• **{c['id']}** — {c['type']} | {c['associate']} | {c['status']}" for c in state["hr_cases"][-15:]]
    await interaction.response.send_message("📁 **PXT Cases**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_application", description="Create AI application.")
async def v5_application(interaction: discord.Interaction, name: str, position: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); app = create_application(state, name, position)
    await interaction.response.send_message(f"📄 **Application Created**\n\nID: **{app['id']}**\nName: **{name}**\nPosition: **{position}**\nScore: **{app['score']}%**")

@bot.tree.command(name="v5_applications", description="View applications.")
async def v5_applications(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state)
    if not state["applications"]:
        return await interaction.response.send_message("No applications.")
    lines = [f"• **{a['id']}** — {a['name']} | {a['position']} | {a['status']} | Score {a['score']}%" for a in state["applications"][-15:]]
    await interaction.response.send_message("📄 **Applications**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_schedule_interview", description="Schedule AI interview.")
async def v5_schedule_interview(interaction: discord.Interaction, name: str, position: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); inv = schedule_interview(state, name, position)
    await interaction.response.send_message(f"🗣️ **Interview Scheduled**\n\nID: **{inv['id']}**\nName: **{name}**\nPosition: **{position}**")

@bot.tree.command(name="v5_record_interview", description="Record AI interview score.")
async def v5_record_interview(interaction: discord.Interaction, interview_id: str):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = record_interview(state, interview_id)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="v5_interviews", description="View interviews.")
async def v5_interviews(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state)
    if not state["interviews"]:
        return await interaction.response.send_message("No interviews.")
    lines = [f"• **{i['id']}** — {i['name']} | {i['position']} | {i['status']} | Score: {i['score']}" for i in state["interviews"][-15:]]
    await interaction.response.send_message("🗣️ **Interviews**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_ai_logs", description="View AI logs/events.")
async def v5_ai_logs(interaction: discord.Interaction):
    state = load_state()
    events = state["events"][-20:]
    if not events:
        return await interaction.response.send_message("No logs yet.")
    lines = [f"• **{e['time']}** — {e['type']}: {e['message']}" for e in events]
    await interaction.response.send_message("🤖 **AI Logs**\n\n" + "\n".join(lines))

@bot.tree.command(name="v5_sim_day", description="Simulate one full day.")
async def v5_sim_day(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); simulate_day(state)
    await interaction.response.send_message(f"📅 **Day Simulated**\n\nCurrent Day: **{state['building']['day']}**\nHealth: **{state['building']['building_health']}%**")

@bot.tree.command(name="v5_sim_week", description="Simulate one full week.")
async def v5_sim_week(interaction: discord.Interaction):
    if not owner_only(interaction):
        return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); simulate_week(state)
    await interaction.response.send_message(f"📆 **Week Simulated**\n\nCurrent Day: **{state['building']['day']}**\nHealth: **{state['building']['building_health']}%**")

@bot.tree.command(name="v5_pause", description="Pause simulation.")
async def v5_pause(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state); state["paused"] = True; save_state(state)
    await interaction.response.send_message("⏸️ Simulation paused.")

@bot.tree.command(name="v5_resume", description="Resume simulation.")
async def v5_resume(interaction: discord.Interaction):
    state = load_state(); ensure_full_systems(state); state["paused"] = False; save_state(state)
    await interaction.response.send_message("▶️ Simulation resumed.")

@bot.tree.command(name="v5_speed", description="Set sim speed label.")
async def v5_speed(interaction: discord.Interaction, speed: str):
    state = load_state(); ensure_full_systems(state); state["sim_speed"] = speed.upper(); save_state(state)
    await interaction.response.send_message(f"⚡ Simulation speed set to **{speed.upper()}**.")

@bot.tree.command(name="v5_records", description="View building records.")
async def v5_records(interaction: discord.Interaction):
    state = load_state(); r = state["records"]
    await interaction.response.send_message(f"🏆 **Building Records**\n\nBest CPT Compliance: **{r['best_cpt_compliance']}%**\nHighest Building Health: **{r['highest_building_health']}%**\nMost CPT Saves: **{r['most_cpt_saves']}**")

@bot.tree.command(name="v5_site_goal", description="Set site goal.")
async def v5_site_goal(interaction: discord.Interaction, goal: str):
    state = load_state(); state["site_goal"] = goal; save_state(state)
    await interaction.response.send_message(f"🎯 **Site Goal Set**\n\n{goal}")

@bot.tree.command(name="v5_full_help", description="List full simulator command categories.")
async def v5_full_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🏢 **V5 Full Simulator Command Categories**\n\n"
        "**Core:** `/v5_panel`, `/v5_dashboard`, `/v5_live_operations`, `/v5_foresight`\n"
        "**Simulation:** `/v5_sim_hour`, `/v5_sim_shift`, `/v5_sim_day`, `/v5_sim_week`, `/v5_pause`, `/v5_resume`\n"
        "**Managers:** `/v5_manager_request`, `/v5_manager_messages`, `/v5_manager_meeting`, `/v5_approve`, `/v5_deny`\n"
        "**Ship Dock/TOM:** `/v5_cpt`, `/v5_trailer`, `/v5_depart`, `/v5_request_pull`, `/v5_yard`, `/v5_cpt_recovery`\n"
        "**AI People:** `/v5_ai_associate`, `/v5_talk`, `/v5_recognize`, `/v5_coach`, `/v5_writeup`, `/v5_promote_ai`\n"
        "**Labor/Departments:** `/v5_staffing`, `/v5_department`, `/v5_department_health`, `/v5_labor_move`\n"
        "**Learning/Safety/HR:** `/v5_start_training`, `/v5_safety_report`, `/v5_audit`, `/v5_hr_case`, `/v5_application`, `/v5_schedule_interview`\n"
        "**Meetings:** `/v5_standup`, `/v5_handoff`, `/v5_business_review`\n"
        "**Logs:** `/v5_events`, `/v5_ai_logs`, `/v5_records`"
    )

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to Railway variables.")

bot.run(DISCORD_TOKEN)
