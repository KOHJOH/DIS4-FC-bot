
import discord
from discord.ext import commands
from config import DISCORD_TOKEN, BOT_OWNER_ID
from solo_engine import *

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def is_owner(user): return user.id == BOT_OWNER_ID
def fmt(n): return f"{int(n):,}"


# =========================
# V4.1 INTERACTIVE UI
# =========================

class SoloDashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Foresight", style=discord.ButtonStyle.primary, emoji="📊")
    async def foresight_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = load_state()
        v = state["volume"]
        b = state["building"]
        await interaction.response.send_message(
            f"📊 **FORESIGHT**\n\n"
            f"Forecast: **{b['forecast_level']}**\n"
            f"Inbound Expected: **{fmt(v['inbound_expected'])}**\n"
            f"Outbound Expected: **{fmt(v['outbound_expected'])}**\n"
            f"Ship Dock Carts: **{fmt(v['ship_dock_carts'])}**\n"
            f"Expected Trailers: **{v['trailers_expected']}**",
            ephemeral=True
        )

    @discord.ui.button(label="Staffing", style=discord.ButtonStyle.secondary, emoji="👥")
    async def staffing_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = load_state()
        s = get_staffing(state)
        await interaction.response.send_message(
            f"👥 **AI STAFFING**\n\n"
            f"Scheduled: **{s['scheduled']}**\n"
            f"Clocked In: **{s['clocked_in']}**\n"
            f"Late: **{s['late']}**\n"
            f"Call-Offs: **{s['calloffs']}**\n"
            f"VTO: **{s['vto']}**",
            ephemeral=True
        )

    @discord.ui.button(label="CPT Board", style=discord.ButtonStyle.danger, emoji="🚛")
    async def cpt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = load_state()
        trailers = [t for t in state["trailers"] if not t["departed"]][:8]
        lines = []
        for t in trailers:
            icon = "🔴" if t["status"] == "At Risk" else "🟢" if t["status"] == "Ready" else "🟡"
            lines.append(f"{icon} **{t['id']}** | Door {t['door']} | CPT {t['cpt']} | {t['packages_remaining']} pkgs | {t['status']}")
        await interaction.response.send_message("🚛 **CPT BOARD**\n\n" + "\n".join(lines), ephemeral=True)

    @discord.ui.button(label="Sim Hour", style=discord.ButtonStyle.success, emoji="⏱️")
    async def sim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction.user):
            await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
            return
        state = load_state()
        simulate_hour(state)
        recs = recommendations(state)
        await interaction.response.send_message(
            f"⏱️ **One Hour Simulated**\n\n"
            f"Building Health: **{state['building']['building_health']}%**\n"
            f"CPT Compliance: **{state['building']['cpt_compliance']}%**\n"
            f"Missorts: **{state['building']['missorts']}**\n\n"
            f"🧠 **AI Recommendations**\n" + "\n".join([f"• {r}" for r in recs]),
            ephemeral=True
        )

class ManagerRequestView(discord.ui.View):
    def __init__(self, request_id):
        super().__init__(timeout=300)
        self.request_id = str(request_id)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction.user):
            await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
            return
        state = load_state()
        ok, msg = apply_request_decision(state, self.request_id, True)
        await interaction.response.send_message(("✅ " if ok else "❌ ") + msg, ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="❌")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_owner(interaction.user):
            await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
            return
        state = load_state()
        ok, msg = apply_request_decision(state, self.request_id, False)
        await interaction.response.send_message(("✅ " if ok else "❌ ") + msg, ephemeral=True)

    @discord.ui.button(label="View Metrics", style=discord.ButtonStyle.secondary, emoji="📊")
    async def metrics(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = load_state()
        b = state["building"]
        dept_lines = "\n".join([f"• **{d}:** {h}%" for d, h in list(state["department_health"].items())[:10]])
        await interaction.response.send_message(
            f"📊 **Current Metrics**\n\n"
            f"Building Health: **{b['building_health']}%**\n"
            f"CPT Compliance: **{b['cpt_compliance']}%**\n"
            f"Safety: **{b['safety']}%**\n"
            f"Quality: **{b['quality']}%**\n"
            f"Missorts: **{b['missorts']}**\n\n"
            f"{dept_lines}",
            ephemeral=True
        )

    @discord.ui.button(label="Escalate", style=discord.ButtonStyle.primary, emoji="⬆️")
    async def escalate(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = load_state()
        state.setdefault("events", []).append({
            "time": "Now",
            "type": "Escalation",
            "message": f"Request {self.request_id} escalated to Senior OM/GM review."
        })
        save_state(state)
        await interaction.response.send_message(f"⬆️ Request **{self.request_id}** escalated to Senior OM/GM.", ephemeral=True)

def request_embed(req):
    embed = discord.Embed(
        title=f"📻 {req['title']}",
        description=req["message"],
        color=discord.Color.orange()
    )
    embed.add_field(name="Manager", value=f"{req['manager_name']}\n{req['manager_role']}", inline=True)
    embed.add_field(name="Department", value=req["department"], inline=True)
    embed.add_field(name="Area", value=req["area"], inline=True)
    embed.add_field(name="Personality", value=req["manager_personality"], inline=True)
    embed.add_field(name="Request Type", value=req["type"], inline=True)
    embed.add_field(name="Request ID", value=req["id"], inline=True)
    embed.add_field(name="Recommendation", value=req["recommendation"], inline=False)
    embed.set_footer(text="Approve, deny, view metrics, or escalate.")
    return embed


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Command sync failed: {e}")

@bot.tree.command(name="solo_help", description="View Solo FC Simulator commands.")
async def solo_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🏢 **DIS4 Solo FC Simulator V4.0**\n\n"
        "`/solo_start` — Create/reset solo FC world\n"
        "`/solo_profile` — View your OM profile\n"
        "`/solo_assign_me` — Rotate yourself to a department\n"
        "`/solo_dashboard` — Executive dashboard\n"
        "`/solo_foresight` — Inbound/outbound volume forecast\n"
        "`/solo_staffing` — AI workforce staffing\n"
        "`/solo_cpt_board` — Ship Dock CPT board\n"
        "`/solo_depart_trailer` — Ship Clerk/TOM departure action\n"
        "`/solo_ai_recommendations` — Building AI suggestions\n"
        "`/solo_shift_start` — Start FHN/BHN shift\n"
        "`/solo_simulate_hour` — Advance operation one hour\n"
        "`/solo_simulate_shift` — Simulate a full shift\n"
        "`/solo_ai_associate` — Inspect an AI associate\n"
        "`/solo_leadership` — View AI leadership\n"
        "`/solo_business_review` — BR summary\n"
        "`/solo_events` — Recent building events\n"
        "`/solo_equipment` — Equipment status"
    )

@bot.tree.command(name="solo_start", description="Create/reset your solo AI FC world.")
async def solo_start(interaction: discord.Interaction):
    if not is_owner(interaction.user): return await interaction.response.send_message("❌ Solo simulator is owner-only.", ephemeral=True)
    state = reset_state()
    await interaction.response.send_message(f"✅ **Solo DIS4 FC world created.**\n\nAI Associates: **{len(state['ai_associates'])}**\nDefault Role: **{state['player']['rank']}**\nDefault Department: **{state['player']['department']}**\n\nRun `/solo_dashboard` to begin.")

@bot.tree.command(name="solo_profile", description="View your solo simulator role.")
async def solo_profile(interaction: discord.Interaction):
    state = load_state(); p = state["player"]
    await interaction.response.send_message(f"👔 **Solo Career Profile**\n\nRank: **{p['rank']}**\nDepartment: **{p['department']}**\nShift: **{p['shift']}**\n\nYou are the only real person. The rest of DIS4 is AI.")

@bot.tree.command(name="solo_assign_me", description="Rotate yourself to a department.")
async def solo_assign_me(interaction: discord.Interaction, department: str, rank: str = "L6 Operations Manager"):
    if not is_owner(interaction.user): return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    if department not in DEPARTMENTS: return await interaction.response.send_message("❌ Invalid department.", ephemeral=True)
    if rank not in RANKS: return await interaction.response.send_message("❌ Invalid rank.", ephemeral=True)
    state = load_state(); state["player"]["department"] = department; state["player"]["rank"] = rank; save_state(state)
    await interaction.response.send_message(f"✅ You are now assigned as **{rank}** over **{department}**.")

@bot.tree.command(name="solo_dashboard", description="View executive FC dashboard.")
async def solo_dashboard(interaction: discord.Interaction):
    state = load_state(); b = state["building"]; v = state["volume"]; s = get_staffing(state); c = cpt_summary(state)
    embed = discord.Embed(title="🏢 DIS4 Solo Executive Dashboard", color=discord.Color.blue())
    for name, value in [
        ("Building Health", f"{b['building_health']}%"), ("Forecast", b["forecast_level"]), ("Reputation", f"{b['reputation']} / 5"),
        ("Safety", f"{b['safety']}%"), ("Quality", f"{b['quality']}%"), ("CPT Compliance", f"{b['cpt_compliance']}%"),
        ("Inbound", fmt(v["inbound_expected"])), ("Outbound", fmt(v["outbound_expected"])), ("Trailers", str(v["trailers_expected"])),
        ("AI Staffing", f"{s['clocked_in']} / {s['scheduled']}"), ("Open CPTs", str(c["open"])), ("At Risk CPTs", str(c["at_risk"]))
    ]:
        embed.add_field(name=name, value=value, inline=True)
    await interaction.response.send_message(embed=embed, view=SoloDashboardView())

@bot.tree.command(name="solo_foresight", description="View inbound/outbound projections.")
async def solo_foresight(interaction: discord.Interaction):
    state = load_state(); v = state["volume"]; b = state["building"]
    await interaction.response.send_message(f"📊 **DIS4 FORESIGHT — Solo AI**\n\nForecast Level: **{b['forecast_level']}**\nForecast Accuracy: **{b['forecast_accuracy']}%**\n\n📥 **INBOUND**\nExpected Units: **{fmt(v['inbound_expected'])}**\nProcessed: **{fmt(v['inbound_processed'])}**\n\n📦 **OUTBOUND**\nExpected Units: **{fmt(v['outbound_expected'])}**\nProcessed: **{fmt(v['outbound_processed'])}**\n\n🚛 **SHIP DOCK**\nExpected Cart Volume: **{fmt(v['ship_dock_carts'])}**\nProcessed Carts: **{fmt(v['dock_processed'])}**\nExpected Trailers: **{v['trailers_expected']}**")

@bot.tree.command(name="solo_set_forecast", description="Set forecast level.")
async def solo_set_forecast(interaction: discord.Interaction, level: str):
    if not is_owner(interaction.user): return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    valid = ["LOW","NORMAL","HIGH","PEAK","PRIME WEEK","PEAK SEASON"]
    if level not in valid: return await interaction.response.send_message(f"❌ Invalid forecast. Use: {', '.join(valid)}", ephemeral=True)
    state = load_state(); forecast_update(state, level)
    await interaction.response.send_message(f"✅ Forecast updated to **{level}**. Run `/solo_foresight`.")

@bot.tree.command(name="solo_staffing", description="View AI staffing by department.")
async def solo_staffing(interaction: discord.Interaction, department: str = None):
    state = load_state()
    if department:
        s = get_staffing(state, department)
        return await interaction.response.send_message(f"👥 **AI Staffing — {department}**\n\nScheduled: **{s['scheduled']}**\nClocked In: **{s['clocked_in']}**\nLate: **{s['late']}**\nCall-Offs: **{s['calloffs']}**\nVTO: **{s['vto']}**")
    lines = []
    for dept in DEPARTMENTS:
        s = get_staffing(state, dept)
        lines.append(f"**{dept}:** {s['clocked_in']} / {s['scheduled']} | Call-Offs: {s['calloffs']} | VTO: {s['vto']}")
    await interaction.response.send_message("👥 **DIS4 AI Staffing Board**\n\n" + "\n".join(lines))

@bot.tree.command(name="solo_shift_start", description="Start a simulated FHN/BHN shift.")
async def solo_shift_start(interaction: discord.Interaction, shift: str = "Front Half Nights"):
    if not is_owner(interaction.user): return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    if shift not in SHIFTS: return await interaction.response.send_message("❌ Invalid shift. Use Front Half Nights or Back Half Nights.", ephemeral=True)
    state = load_state(); state["building"]["shift"] = shift; state["player"]["shift"] = shift; start_shift(state); s = get_staffing(state)
    await interaction.response.send_message(f"🌙 **{shift} Started**\n\nScheduled: **{s['scheduled']}**\nClocked In: **{s['clocked_in']}**\nLate: **{s['late']}**\nCall-Offs: **{s['calloffs']}**\nVTO: **{s['vto']}**")

@bot.tree.command(name="solo_simulate_hour", description="Advance the AI building one hour.")
async def solo_simulate_hour(interaction: discord.Interaction):
    if not is_owner(interaction.user): return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); simulate_hour(state); recs = recommendations(state)
    await interaction.response.send_message(f"⏱️ **One Hour Simulated**\n\nBuilding Health: **{state['building']['building_health']}%**\nCPT Compliance: **{state['building']['cpt_compliance']}%**\nMissorts: **{state['building']['missorts']}**\n\n🧠 **AI Recommendations**\n" + "\n".join([f"• {r}" for r in recs]))

@bot.tree.command(name="solo_simulate_shift", description="Simulate an entire shift.")
async def solo_simulate_shift(interaction: discord.Interaction, hours: int = 10):
    if not is_owner(interaction.user): return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    hours = max(1, min(12, hours)); state = load_state()
    for _ in range(hours): simulate_hour(state)
    br = business_review(state)
    await interaction.response.send_message(f"🌅 **End of Shift Simulation Complete**\n\nHours Simulated: **{hours}**\nBuilding Health: **{br['building_health']}%**\nCPT Compliance: **{br['cpt_compliance']}%**\nSafety: **{br['safety']}%**\nQuality: **{br['quality']}%**\nMissorts: **{br['missorts']}**\nInbound Processed: **{fmt(br['inbound'])}**\nOutbound Processed: **{fmt(br['outbound'])}**")

@bot.tree.command(name="solo_cpt_board", description="View Ship Dock CPT board.")
async def solo_cpt_board(interaction: discord.Interaction):
    state = load_state(); lines = []
    for t in [t for t in state["trailers"] if not t["departed"]][:12]:
        icon = "🔴" if t["status"] == "At Risk" else "🟢" if t["status"] == "Ready" else "🟡"
        lines.append(f"{icon} **{t['id']}** | Door {t['door']} | CPT {t['cpt']} | {t['packages_remaining']} pkgs | {t['status']} | {t['type']}")
    await interaction.response.send_message("🚛 **Ship Dock CPT Board**\n\n" + "\n".join(lines))

@bot.tree.command(name="solo_depart_trailer", description="Depart a trailer from the CPT board.")
async def solo_depart_trailer(interaction: discord.Interaction, trailer_id: str):
    if not is_owner(interaction.user): return await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
    state = load_state(); ok, msg = depart_trailer(state, trailer_id)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="solo_ai_recommendations", description="View AI recommendations.")
async def solo_ai_recommendations(interaction: discord.Interaction):
    state = load_state()
    await interaction.response.send_message("🧠 **DIS4 Building AI Recommendations**\n\n" + "\n".join([f"• {r}" for r in recommendations(state)]))

@bot.tree.command(name="solo_ai_associate", description="Inspect an AI associate by name.")
async def solo_ai_associate(interaction: discord.Interaction, name: str):
    state = load_state(); matches = [a for a in state["ai_associates"] if name.lower() in a["name"].lower()]
    if not matches:
        sample = ", ".join([a["name"] for a in state["ai_associates"][:5]])
        return await interaction.response.send_message(f"❌ No AI associate found. Try one of: {sample}", ephemeral=True)
    a = matches[0]
    await interaction.response.send_message(f"👤 **AI Associate Profile**\n\nName: **{a['name']}**\nEmployee ID: **{a['id']}**\nRank: **{a['rank']}**\nDepartment: **{a['department']}**\nArea: **{a['area']}**\nShift: **{a['shift']}**\nPersonality: **{a['personality']}**\nStatus: **{a['status']}**\n\nUPH: **{a['uph']}**\nQuality: **{a['quality']}%**\nSafety: **{a['safety']}%**\nAttendance: **{a['attendance']}%**\nMorale: **{a['morale']}%**\n\nCertifications: **{', '.join(a['certifications']) if a['certifications'] else 'None'}**\nCareer Goal: **{a['career_goal']}**")

@bot.tree.command(name="solo_leadership", description="View AI leadership by department.")
async def solo_leadership(interaction: discord.Interaction, department: str = None):
    state = load_state()
    leaders = [a for a in state["ai_associates"] if a["rank"] in ["Process Guide","T3 Process Assistant","L4 Area Manager","L5 Area Manager","L6 Operations Manager","L7 Senior Operations Manager","L8 General Manager"]]
    if department: leaders = [a for a in leaders if a["department"] == department]
    lines = [f"• **{a['name']}** — {a['rank']} | {a['department']} / {a['area']}" for a in leaders[:25]]
    await interaction.response.send_message("👔 **AI Leadership Directory**\n\n" + ("\n".join(lines) or "No leadership found."))

@bot.tree.command(name="solo_business_review", description="Generate business review.")
async def solo_business_review(interaction: discord.Interaction):
    state = load_state(); br = business_review(state)
    await interaction.response.send_message(f"📈 **DIS4 Business Review — Solo**\n\nDay: **{br['day']}**\nForecast: **{br['forecast']}**\nBuilding Health: **{br['building_health']}%**\nSafety: **{br['safety']}%**\nQuality: **{br['quality']}%**\nCPT Compliance: **{br['cpt_compliance']}%**\nMissorts: **{br['missorts']}**\n\nInbound Processed: **{fmt(br['inbound'])}**\nOutbound Processed: **{fmt(br['outbound'])}**\nDock Carts Processed: **{fmt(br['dock'])}**\n\nStaffing: **{br['staffing']['clocked_in']} / {br['staffing']['scheduled']}**\nOpen CPTs: **{br['cpt']['open']}**\nAt Risk CPTs: **{br['cpt']['at_risk']}**")

@bot.tree.command(name="solo_events", description="View recent AI building events.")
async def solo_events(interaction: discord.Interaction):
    state = load_state(); events = state["events"][-10:]
    if not events: return await interaction.response.send_message("No events yet. Run `/solo_simulate_hour`.")
    await interaction.response.send_message("🚨 **Recent Building Events**\n\n" + "\n".join([f"• **{e['time']}** — {e['type']}: {e['message']}" for e in events]))

@bot.tree.command(name="solo_equipment", description="View building equipment status.")
async def solo_equipment(interaction: discord.Interaction):
    state = load_state(); lines = []
    for name, data in state["equipment"].items():
        pct = round((data["available"] / data["total"]) * 100)
        icon = "🟢" if pct >= 85 else "🟡" if pct >= 70 else "🔴"
        lines.append(f"{icon} **{name}:** {data['available']} / {data['total']} ({pct}%)")
    await interaction.response.send_message("🔋 **Equipment Status**\n\n" + "\n".join(lines))




# =========================
# V4.1 INTERACTIVE COMMANDS
# =========================

@bot.tree.command(name="solo_control_panel", description="Open the interactive FC control panel.")
async def solo_control_panel(interaction: discord.Interaction):
    state = load_state()
    b = state["building"]
    v = state["volume"]
    c = cpt_summary(state)
    s = get_staffing(state)

    embed = discord.Embed(
        title="🏢 DIS4 Solo Control Panel",
        description="Interactive operations dashboard. Use the buttons below to move through the building.",
        color=discord.Color.blue()
    )
    embed.add_field(name="Forecast", value=b["forecast_level"], inline=True)
    embed.add_field(name="Health", value=f"{b['building_health']}%", inline=True)
    embed.add_field(name="CPT", value=f"{b['cpt_compliance']}%", inline=True)
    embed.add_field(name="Inbound", value=fmt(v["inbound_expected"]), inline=True)
    embed.add_field(name="Outbound", value=fmt(v["outbound_expected"]), inline=True)
    embed.add_field(name="At Risk CPTs", value=str(c["at_risk"]), inline=True)
    embed.add_field(name="AI Staffing", value=f"{s['clocked_in']} / {s['scheduled']}", inline=True)
    embed.add_field(name="Missorts", value=str(b["missorts"]), inline=True)
    embed.add_field(name="Safety", value=f"{b['safety']}%", inline=True)

    await interaction.response.send_message(embed=embed, view=SoloDashboardView())

@bot.tree.command(name="solo_manager_request", description="Generate an interactive AI manager request.")
async def solo_manager_request(interaction: discord.Interaction, department: str = None):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
        return

    state = load_state()
    if department and department not in DEPARTMENTS:
        await interaction.response.send_message("❌ Invalid department.", ephemeral=True)
        return

    req = generate_manager_request(state, department)
    await interaction.response.send_message(embed=request_embed(req), view=ManagerRequestView(req["id"]))

@bot.tree.command(name="solo_manager_messages", description="View open interactive AI manager requests.")
async def solo_manager_messages(interaction: discord.Interaction):
    state = load_state()
    open_reqs = get_open_requests(state)

    if not open_reqs:
        req = generate_manager_request(state)
        await interaction.response.send_message(embed=request_embed(req), view=ManagerRequestView(req["id"]))
        return

    req = open_reqs[-1]
    await interaction.response.send_message(embed=request_embed(req), view=ManagerRequestView(req["id"]))

@bot.tree.command(name="solo_manager_meeting", description="Start an AI manager meeting with multiple requests.")
async def solo_manager_meeting(interaction: discord.Interaction):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
        return

    state = load_state()
    requests = manager_meeting_summary(state)

    summary = []
    for req in requests:
        summary.append(
            f"**{req['id']} — {req['department']}**\n"
            f"{req['manager_name']}: {req['title']}\n"
            f"Recommendation: {req['recommendation']}"
        )

    await interaction.response.send_message(
        "👔 **AI Manager Meeting Started**\n\n"
        + "\n\n".join(summary)
        + "\n\nUse `/solo_manager_messages` to review the latest request with buttons."
    )

@bot.tree.command(name="solo_approve_request", description="Approve an AI manager request by ID.")
async def solo_approve_request(interaction: discord.Interaction, request_id: str):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
        return
    state = load_state()
    ok, msg = apply_request_decision(state, request_id, True)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg)

@bot.tree.command(name="solo_deny_request", description="Deny an AI manager request by ID.")
async def solo_deny_request(interaction: discord.Interaction, request_id: str, reason: str = "Denied by site leader"):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
        return
    state = load_state()
    ok, msg = apply_request_decision(state, request_id, False)
    if ok:
        state = load_state()
        state.setdefault("manager_memory", []).append({"time": "Now", "request": request_id, "decision": "Denied", "reason": reason})
        save_state(state)
    await interaction.response.send_message(("✅ " if ok else "❌ ") + msg + f"\nReason: {reason}")

@bot.tree.command(name="solo_interactive_help", description="View interactive solo AI controls.")
async def solo_interactive_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🎮 **Interactive Solo AI Controls**\n\n"
        "`/solo_control_panel` — Open button dashboard\n"
        "`/solo_manager_request` — Generate AI manager decision prompt\n"
        "`/solo_manager_messages` — View open request with buttons\n"
        "`/solo_manager_meeting` — Generate multiple AI leader issues\n"
        "`/solo_approve_request` — Approve by request ID\n"
        "`/solo_deny_request` — Deny by request ID\n\n"
        "Manager AI follows chain-of-command rules:\n"
        "• PGs cannot request cross-department labor\n"
        "• PAs escalate labor needs\n"
        "• AMs manage within their area\n"
        "• OM/POC/Senior OM/GM approve cross-department labor"
    )

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to Railway variables.")

bot.run(DISCORD_TOKEN)
