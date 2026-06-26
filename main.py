
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

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing. Add it to Railway variables.")

bot.run(DISCORD_TOKEN)
