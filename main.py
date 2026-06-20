import discord
from discord import app_commands
from discord.ext import commands
import random, time
from datetime import datetime

from config import DISCORD_TOKEN, BOT_OWNER_ID, TASK_COOLDOWN
from database import setup_database, get_profile, update_profile, list_profiles
from constants import RANKS, T3_PLUS_RANKS, TRAINING_CERTS, ASSIGNMENTS
from health import PICK_FLOORS, STOW_FLOORS, DEPARTMENT_HEALTH, clamp_area
from tasks import TASKS

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

active_tasks = {}
task_cooldowns = {}
OPEN_POSTINGS = {}

CPTS = {
    "18:00": {"risk": 10},
    "20:00": {"risk": 25},
    "22:00": {"risk": 45},
    "00:00": {"risk": 65},
}


async def sync_discord_role(member: discord.Member, role_name: str):
    """Add a Discord role if it exists in the server."""
    guild = member.guild
    role = discord.utils.get(guild.roles, name=role_name)

    if role is None:
        return False, f"Role '{role_name}' does not exist in this server."

    if role in member.roles:
        return True, f"{member.display_name} already has {role_name}."

    try:
        await member.add_roles(role, reason="FC bot role sync")
        return True, f"Added Discord role: {role_name}"
    except discord.Forbidden:
        return False, "Bot does not have permission to manage that role. Move the bot role above the target role."
    except discord.HTTPException:
        return False, "Discord rejected the role update."

async def remove_discord_role(member: discord.Member, role_name: str):
    guild = member.guild
    role = discord.utils.get(guild.roles, name=role_name)

    if role is None or role not in member.roles:
        return False

    try:
        await member.remove_roles(role, reason="FC bot role sync cleanup")
        return True
    except Exception:
        return False

async def sync_rank_role(member: discord.Member, new_rank: str):
    # Remove old rank roles so users do not keep multiple ranks.
    for rank in RANKS:
        if rank != new_rank:
            await remove_discord_role(member, rank)

    return await sync_discord_role(member, new_rank)

async def sync_assignment_role(member: discord.Member, new_assignment: str):
    # Remove old assignment roles so users only have one assignment at a time.
    for assignment in ASSIGNMENTS:
        if assignment != new_assignment:
            await remove_discord_role(member, assignment)

    return await sync_discord_role(member, new_assignment)

async def sync_certificate_role(member: discord.Member, certificate: str):
    # Certifications stack, so do not remove other cert roles.
    return await sync_discord_role(member, certificate)

def is_owner(user):
    return user.id == BOT_OWNER_ID

def has_leadership_permission(member):
    profile = get_profile(member.id)
    return profile["rank"] in T3_PLUS_RANKS or profile["rank"] == "Learning Ambassador"

@bot.event
async def on_ready():
    setup_database()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.tree.command(name="profile", description="View an FC profile.")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    p = get_profile(target.id)

    embed = discord.Embed(title=f"{target.display_name}'s FC Profile", color=discord.Color.blue())
    embed.add_field(name="Rank", value=p["rank"], inline=True)
    embed.add_field(name="Assignment", value=p["assignment"], inline=True)
    embed.add_field(name="Department", value=p["department"], inline=True)
    embed.add_field(name="Pick Floor", value=p["pick_floor"], inline=True)
    embed.add_field(name="Stow Floor", value=p["stow_floor"], inline=True)
    embed.add_field(name="Write-Ups", value=p["writeups"], inline=True)
    embed.add_field(name="Productivity", value=p["productivity"], inline=True)
    embed.add_field(name="Quality", value=f"{p['quality']}%", inline=True)
    embed.add_field(name="Safety", value=f"{p['safety']}%", inline=True)
    embed.add_field(name="Shift", value=p.get("shift", "Unassigned"), inline=True)
    embed.add_field(name="Area", value=p.get("area", "Unassigned"), inline=True)
    embed.add_field(name="Morale", value=f"{p.get('morale', 100)}%", inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="certificates", description="View training certificates.")
async def certificates(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    p = get_profile(target.id)
    certs = p.get("certifications", [])
    text = "\n".join([f"✅ {c}" for c in certs]) if certs else "No certifications on record."
    embed = discord.Embed(title=f"{target.display_name}'s Certificates", description=text, color=discord.Color.green())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="sync_roles", description="Sync a user's Discord roles from their FC profile.")
async def sync_roles(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user

    if target != interaction.user and not has_leadership_permission(interaction.user) and not is_owner(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    p = get_profile(target.id)
    messages = []

    ok, msg = await sync_rank_role(target, p["rank"])
    messages.append((ok, msg))

    if p["assignment"] != "Unassigned":
        ok, msg = await sync_assignment_role(target, p["assignment"])
        messages.append((ok, msg))

    for cert in p.get("certifications", []):
        ok, msg = await sync_certificate_role(target, cert)
        messages.append((ok, msg))

    text = "\n".join([f"{'✅' if ok else '⚠️'} {msg}" for ok, msg in messages])
    await interaction.response.send_message(f"🔁 **Role Sync Complete for {target.mention}**\n{text}")

@bot.tree.command(name="create_fc_roles", description="Owner-only: create missing FC Discord roles.")
async def create_fc_roles(interaction: discord.Interaction):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Only the bot owner can create FC roles.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    role_names = RANKS + ASSIGNMENTS + TRAINING_CERTS
    created = []
    skipped = []
    failed = []

    for role_name in role_names:
        if discord.utils.get(interaction.guild.roles, name=role_name):
            skipped.append(role_name)
            continue
        try:
            await interaction.guild.create_role(name=role_name, reason="FC bot role setup")
            created.append(role_name)
        except Exception:
            failed.append(role_name)

    await interaction.followup.send(
        f"✅ Created: **{len(created)}** roles\n"
        f"↪️ Already existed: **{len(skipped)}** roles\n"
        f"⚠️ Failed: **{len(failed)}** roles\n\n"
        f"Important: move the bot's Discord role above all FC roles so it can manage them."
    )

@bot.tree.command(name="appoint_rank", description="Owner-only: appoint a rank.")
async def appoint_rank(interaction: discord.Interaction, user: discord.Member, rank: str):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Only the bot owner can appoint ranks.", ephemeral=True)
        return
    if rank not in RANKS:
        await interaction.response.send_message("❌ Invalid rank.", ephemeral=True)
        return
    p = get_profile(user.id)
    p["rank"] = rank
    update_profile(user.id, p)

    synced, sync_message = await sync_rank_role(user, rank)
    await interaction.response.send_message(
        f"✅ {user.mention} is now **{rank}**.\n"
        f"Role Sync: {'✅' if synced else '⚠️'} {sync_message}"
    )

@bot.tree.command(name="assign_position", description="Owner-only: assign leadership/department position.")
async def assign_position(interaction: discord.Interaction, user: discord.Member, assignment: str):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Only the bot owner can assign positions.", ephemeral=True)
        return
    if assignment not in ASSIGNMENTS:
        await interaction.response.send_message("❌ Invalid assignment.", ephemeral=True)
        return
    p = get_profile(user.id)
    p["assignment"] = assignment
    update_profile(user.id, p)

    synced, sync_message = await sync_assignment_role(user, assignment)
    await interaction.response.send_message(
        f"✅ {user.mention} assigned to **{assignment}**.\n"
        f"Role Sync: {'✅' if synced else '⚠️'} {sync_message}"
    )

@bot.tree.command(name="train", description="Leadership trains/certifies an associate.")
async def train(interaction: discord.Interaction, user: discord.Member, certificate: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ You are not authorized to train associates.", ephemeral=True)
        return
    if certificate not in TRAINING_CERTS:
        await interaction.response.send_message("❌ Invalid certificate.", ephemeral=True)
        return
    p = get_profile(user.id)
    if certificate not in p["certifications"]:
        p["certifications"].append(certificate)
    update_profile(user.id, p)

    synced, sync_message = await sync_certificate_role(user, certificate)
    await interaction.response.send_message(
        f"✅ {user.mention} has been trained in **{certificate}**.\n"
        f"Role Sync: {'✅' if synced else '⚠️'} {sync_message}"
    )

@bot.tree.command(name="assign_pick_floor", description="Assign a Pick-trained associate to a Pick floor.")
@app_commands.choices(floor=[
    app_commands.Choice(name="Floor 1", value="Floor 1"),
    app_commands.Choice(name="Floor 2", value="Floor 2"),
    app_commands.Choice(name="Floor 3", value="Floor 3")
])
async def assign_pick_floor(interaction: discord.Interaction, user: discord.Member, floor: app_commands.Choice[str]):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Not authorized.", ephemeral=True)
        return
    p = get_profile(user.id)
    if "Pick" not in p["certifications"]:
        await interaction.response.send_message("❌ Associate is not Pick trained.", ephemeral=True)
        return
    p["pick_floor"] = floor.value
    update_profile(user.id, p)
    await interaction.response.send_message(f"✅ {user.mention} assigned to **Pick {floor.value}**.")

@bot.tree.command(name="assign_stow_floor", description="Assign a Stow-trained associate to a Stow floor.")
@app_commands.choices(floor=[
    app_commands.Choice(name="Floor 1", value="Floor 1"),
    app_commands.Choice(name="Floor 2", value="Floor 2"),
    app_commands.Choice(name="Floor 3", value="Floor 3")
])
async def assign_stow_floor(interaction: discord.Interaction, user: discord.Member, floor: app_commands.Choice[str]):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Not authorized.", ephemeral=True)
        return
    p = get_profile(user.id)
    if "Stow" not in p["certifications"]:
        await interaction.response.send_message("❌ Associate is not Stow trained.", ephemeral=True)
        return
    p["stow_floor"] = floor.value
    update_profile(user.id, p)
    await interaction.response.send_message(f"✅ {user.mention} assigned to **Stow {floor.value}**.")

@bot.tree.command(name="health", description="View all building health metrics.")
async def health(interaction: discord.Interaction):
    pick_avg = round(sum(f["health"] for f in PICK_FLOORS.values()) / len(PICK_FLOORS))
    stow_avg = round(sum(f["health"] for f in STOW_FLOORS.values()) / len(STOW_FLOORS))
    other_avg = round(sum(a["health"] for a in DEPARTMENT_HEALTH.values()) / len(DEPARTMENT_HEALTH))
    overall = round((pick_avg + stow_avg + other_avg) / 3)
    await interaction.response.send_message(
        f"🏢 **FC Health**\n\nPick Avg: **{pick_avg}%**\nStow Avg: **{stow_avg}%**\nOther Departments Avg: **{other_avg}%**\n\nOverall Building Health: **{overall}%**"
    )

@bot.tree.command(name="department_health", description="View department health.")
async def department_health(interaction: discord.Interaction, department: str):
    if department not in DEPARTMENT_HEALTH:
        await interaction.response.send_message("❌ Invalid department.", ephemeral=True)
        return
    area = DEPARTMENT_HEALTH[department]
    embed = discord.Embed(title=f"🏢 {department} Health", color=discord.Color.green())
    for stat, value in area.items():
        embed.add_field(name=stat.replace("_", " ").title(), value=value, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pick_health", description="View Pick floor health.")
async def pick_health(interaction: discord.Interaction):
    embed = discord.Embed(title="📦 Pick Health", color=discord.Color.green())
    for floor, stats in PICK_FLOORS.items():
        embed.add_field(name=floor, value=f"Health: {stats['health']}% | Rate: {stats['rate']}% | Quality: {stats['quality']}% | Pod Gaps: {stats['pod_gaps']}", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="stow_health", description="View Stow floor health.")
async def stow_health(interaction: discord.Interaction):
    embed = discord.Embed(title="📥 Stow Health", color=discord.Color.green())
    for floor, stats in STOW_FLOORS.items():
        embed.add_field(name=floor, value=f"Health: {stats['health']}% | Rate: {stats['rate']}% | Quality: {stats['quality']}% | Pod Gaps: {stats['pod_gaps']}", inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="task", description="Start a department task.")
async def task(interaction: discord.Interaction, department: str):
    user_id = interaction.user.id
    p = get_profile(user_id)

    if department not in TASKS:
        await interaction.response.send_message("❌ Invalid task department.", ephemeral=True)
        return

    if department in TRAINING_CERTS and department not in p["certifications"]:
        await interaction.response.send_message(f"❌ You are not trained in **{department}**.", ephemeral=True)
        return

    now = time.time()
    if user_id in task_cooldowns:
        remaining = TASK_COOLDOWN - (now - task_cooldowns[user_id])
        if remaining > 0:
            await interaction.response.send_message(f"⏳ Cooldown: **{int(remaining)} seconds** remaining.", ephemeral=True)
            return

    selected = random.choice(TASKS[department])
    floor = None

    if department == "Pick":
        floor = p["pick_floor"]
        if floor == "Unassigned":
            await interaction.response.send_message("❌ You are not assigned to a Pick floor.", ephemeral=True)
            return
    elif department == "Stow":
        floor = p["stow_floor"]
        if floor == "Unassigned":
            await interaction.response.send_message("❌ You are not assigned to a Stow floor.", ephemeral=True)
            return

    active_tasks[user_id] = {"department": department, "floor": floor, "task": selected}
    choices = "\n".join([f"**{i+1}.** {c}" for i, c in enumerate(selected["choices"])])
    await interaction.response.send_message(f"📋 **{department} Task**\n\n{selected['scenario']}\n\n{choices}\n\nUse `/answer choice:1`, `/answer choice:2`, or `/answer choice:3`.")

@bot.tree.command(name="answer", description="Answer your active task.")
async def answer(interaction: discord.Interaction, choice: int):
    user_id = interaction.user.id

    if user_id not in active_tasks:
        await interaction.response.send_message("❌ You have no active task.", ephemeral=True)
        return

    task_data = active_tasks[user_id]
    task = task_data["task"]
    p = get_profile(user_id)
    correct = choice - 1 == task["answer"]

    if correct:
        for stat, amount in task.get("reward", {}).items():
            if stat in p:
                p[stat] += amount

        department = task_data["department"]
        effects = task.get("area_effect", {})

        if department == "Pick":
            area = PICK_FLOORS[task_data["floor"]]
        elif department == "Stow":
            area = STOW_FLOORS[task_data["floor"]]
        elif department in DEPARTMENT_HEALTH:
            area = DEPARTMENT_HEALTH[department]
        else:
            area = None

        if area:
            for stat, amount in effects.items():
                if stat in area:
                    area[stat] += amount
            clamp_area(area)

        p["department"] = department
        p["last_activity_time"] = time.time()
        p["current_station"] = department
        p["station_status"] = "Recently Active"
        update_profile(user_id, p)
        await interaction.response.send_message("✅ **Task completed successfully.**")
    else:
        p["quality"] = max(0, p["quality"] - 2)
        p["safety"] = max(0, p["safety"] - 1)
        p["last_activity_time"] = time.time()
        p["station_status"] = "Task Failed"
        update_profile(user_id, p)
        await interaction.response.send_message("❌ **Task failed.** Quality -2 | Safety -1")

    task_cooldowns[user_id] = time.time()
    del active_tasks[user_id]

@bot.tree.command(name="clockin", description="Clock in for your FC shift.")
async def clockin(interaction: discord.Interaction):
    p = get_profile(interaction.user.id)
    if p.get("clocked_in"):
        await interaction.response.send_message("❌ You are already clocked in.", ephemeral=True)
        return
    p["clocked_in"] = True
    p["clockin_time"] = time.time()
    p["last_activity_time"] = time.time()
    p["station_status"] = "Clocked In"
    update_profile(interaction.user.id, p)
    await interaction.response.send_message(f"✅ {interaction.user.mention} clocked in.")

@bot.tree.command(name="clockout", description="Clock out from your FC shift.")
async def clockout(interaction: discord.Interaction):
    p = get_profile(interaction.user.id)
    if not p.get("clocked_in"):
        await interaction.response.send_message("❌ You are not clocked in.", ephemeral=True)
        return
    shift_minutes = round((time.time() - p.get("clockin_time", time.time())) / 60)
    p["clocked_in"] = False
    p["clockin_time"] = None
    p["station_status"] = "Clocked Out"
    p["current_station"] = "Unassigned"
    p["total_minutes_worked"] = p.get("total_minutes_worked", 0) + shift_minutes
    p["weekly_minutes"] = p.get("weekly_minutes", 0) + shift_minutes
    p["weekly_shifts"] = p.get("weekly_shifts", 0) + 1
    p["attendance"] = min(100, p.get("attendance", 100) + 1)
    update_profile(interaction.user.id, p)
    await interaction.response.send_message(f"✅ Clocked out. Shift Length: **{shift_minutes} minutes**")

@bot.tree.command(name="cpt", description="View CPT risk.")
async def cpt(interaction: discord.Interaction):
    text = "🚛 **CPT Risk Board**\n\n"
    for cpt_time, data in CPTS.items():
        risk = data["risk"]
        status = "🟢 Green" if risk < 35 else "🟡 Yellow" if risk < 65 else "🔴 Red"
        text += f"**{cpt_time} CPT** — {status} — Risk: **{risk}%**\n"
    await interaction.response.send_message(text)

@bot.tree.command(name="labor_move", description="Leadership moves labor between areas.")
async def labor_move(interaction: discord.Interaction, from_area: str, to_area: str, associates: int, reason: str):
    if not has_department_authority(interaction.user, from_area) and not has_department_authority(interaction.user, to_area):
        await interaction.response.send_message("❌ You do not have authority over either of those areas.", ephemeral=True)
        return
    if to_area in DEPARTMENT_HEALTH:
        DEPARTMENT_HEALTH[to_area]["health"] = min(100, DEPARTMENT_HEALTH[to_area]["health"] + associates * 2)
    if from_area in DEPARTMENT_HEALTH:
        DEPARTMENT_HEALTH[from_area]["health"] = max(0, DEPARTMENT_HEALTH[from_area]["health"] - associates)
    await interaction.response.send_message(f"🔁 **Labor Move Logged**\nMoved **{associates}** from **{from_area}** to **{to_area}**\nReason: {reason}")

@bot.tree.command(name="open_posting", description="Owner opens an application posting.")
async def open_posting(interaction: discord.Interaction, role: str, openings: int):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Only the bot owner can open postings.", ephemeral=True)
        return
    OPEN_POSTINGS[role] = {"openings": openings, "applicants": [], "opened_by": interaction.user.id, "opened_at": datetime.utcnow().isoformat()}
    await interaction.response.send_message(f"📢 **Applications Opened**\nRole: **{role}**\nOpenings: **{openings}**\nUse `/apply role:{role}` to apply.")

@bot.tree.command(name="apply", description="Apply for an open posting.")
async def apply(interaction: discord.Interaction, role: str):
    if role not in OPEN_POSTINGS:
        await interaction.response.send_message("❌ Applications are not open for that role.", ephemeral=True)
        return
    if interaction.user.id in OPEN_POSTINGS[role]["applicants"]:
        await interaction.response.send_message("❌ You already applied.", ephemeral=True)
        return
    OPEN_POSTINGS[role]["applicants"].append(interaction.user.id)
    p = get_profile(interaction.user.id)
    p["applications"][role] = {"status": "Submitted", "submitted": datetime.utcnow().isoformat()}
    update_profile(interaction.user.id, p)
    await interaction.response.send_message(f"✅ Application submitted for **{role}**.")

@bot.tree.command(name="view_applicants", description="Leadership views applicants.")
async def view_applicants(interaction: discord.Interaction, role: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return
    if role not in OPEN_POSTINGS:
        await interaction.response.send_message("❌ No posting found.", ephemeral=True)
        return
    applicants = OPEN_POSTINGS[role]["applicants"]
    text = f"📋 **Applicants for {role}**\n\n" + ("\n".join([f"<@{uid}>" for uid in applicants]) if applicants else "No applicants yet.")
    await interaction.response.send_message(text)

@bot.tree.command(name="writeup", description="Leadership issues a write-up.")
async def writeup(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return
    p = get_profile(user.id)
    p["writeups"] += 1
    p["quality"] = max(0, p["quality"] - 5)
    update_profile(user.id, p)
    await interaction.response.send_message(f"⚠️ **Write-Up Issued**\nAssociate: {user.mention}\nReason: {reason}\nTotal Write-Ups: **{p['writeups']}**")

@bot.tree.command(name="review", description="View an associate performance review.")
async def review(interaction: discord.Interaction, user: discord.Member):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return
    p = get_profile(user.id)
    score = round((p["productivity"] + p["quality"] + p["safety"] + p["attendance"] + p["leadership"]) / 5)
    score = max(0, min(100, score - p["writeups"] * 10))
    rating = "Top Performer" if score >= 85 else "Meets Expectations" if score >= 70 else "Needs Coaching" if score >= 50 else "At Risk"
    await interaction.response.send_message(f"📊 **Performance Review: {user.display_name}**\nScore: **{score}%**\nRating: **{rating}**")

@bot.tree.command(name="flow", description="View outbound flow dashboard.")
async def flow(interaction: discord.Interaction):
    if not has_department_authority(interaction.user):
        await interaction.response.send_message("❌ Flow dashboard is restricted to leadership only.", ephemeral=True)
        return
    pick_avg = round(sum(f["health"] for f in PICK_FLOORS.values()) / len(PICK_FLOORS))
    pack_avg = round((DEPARTMENT_HEALTH["Pack Singles"]["health"] + DEPARTMENT_HEALTH["AFE Pack"]["health"]) / 2)
    sorter = DEPARTMENT_HEALTH["Shipping Sorter"]["health"]
    transship = DEPARTMENT_HEALTH["Transship"]["health"]
    bottlenecks = {"Pick": pick_avg, "Pack": pack_avg, "Shipping Sorter": sorter, "Transship": transship}
    lowest = min(bottlenecks, key=bottlenecks.get)
    await interaction.response.send_message(f"🚦 **Flow Dashboard**\nPick: **{pick_avg}%**\nPack: **{pack_avg}%**\nShipping Sorter: **{sorter}%**\nTransship: **{transship}%**\n\nCurrent Bottleneck: **{lowest}**")



FC_EMOJIS = {
    "building": "🏢",
    "profile": "🪪",
    "training": "🎓",
    "rank": "🦺",
    "assignment": "📌",
    "health": "📊",
    "task": "📋",
    "clock": "⏱️",
    "flow": "🚦",
    "cpt": "🚛",
    "labor": "🔁",
    "recruiting": "📢",
    "writeup": "⚠️",
    "review": "📈",
    "roles": "🔄",
    "pick": "📦",
    "stow": "📥",
    "pack": "📮",
    "inbound": "🚚",
    "shipdock": "🚛",
    "learning": "🎓",
    "safety": "🛡️",
    "pxt": "👥",
    "noninventory": "📦",
    "quality": "✅",
    "cpt_risk": "⏰",
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴"
}

@bot.tree.command(name="help", description="View all FC bot commands grouped by category.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"{FC_EMOJIS['building']} FC Roleplay Bot Help",
        description="Commands are grouped by operations category. Some commands require leadership or bot owner permissions.",
        color=discord.Color.orange()
    )

    embed.add_field(
        name=f"{FC_EMOJIS['profile']} Associate Profile",
        value=(
            "`/profile` - View your or another associate's FC profile\\n"
            "`/certificates` - View training/cross-training certificates\\n"
            "`/clockin` - Clock in for shift\\n"
            "`/clockout` - Clock out from shift"
        ),
        inline=False
    )

    embed.add_field(
        name=f"{FC_EMOJIS['training']} Training & Certifications",
        value=(
            "`/train` - Certify an associate in Pick, Stow, Pack, TDR, PIT, etc.\\n"
            "`/assign_pick_floor` - Assign a Pick-trained associate to a Pick floor\\n"
            "`/assign_stow_floor` - Assign a Stow-trained associate to a Stow floor"
        ),
        inline=False
    )

    embed.add_field(
        name=f"{FC_EMOJIS['rank']} Owner Controls",
        value=(
            "`/appoint_rank` - Owner-only: appoint ranks like T3, L4, L5, L6+\\n"
            "`/assign_position` - Owner-only: assign area positions\\n"
            "`/create_fc_roles` - Create FC Discord roles\\n"
            "`/sync_roles` - Sync profile rank/assignment/certs to Discord roles"
        ),
        inline=False
    )

    embed.add_field(
        name=f"{FC_EMOJIS['task']} Work Tasks",
        value=(
            "`/task department:Pick`\\n"
            "`/task department:Stow`\\n"
            "`/task department:Pack Singles`\\n"
            "`/task department:AFE Pack`\\n"
            "`/task department:Receive Dock`\\n"
            "`/task department:Decant`\\n"
            "`/task department:Shipping Sorter`\\n"
            "`/task department:Transship`\\n"
            "`/task department:Quality`\\n"
            "`/task department:PIT Operator`\\n"
            "`/task department:TDR Operator`"
        ),
        inline=False
    )

    embed.add_field(
        name=f"{FC_EMOJIS['health']} Health Metrics",
        value=(
            "`/health` - Overall FC health\\n"
            "`/pick_health` - Pick floor metrics\\n"
            "`/stow_health` - Stow floor metrics\\n"
            "`/department_health` - Specific department health"
        ),
        inline=False
    )

    embed.add_field(
        name=f"{FC_EMOJIS['flow']} Operations",
        value=(
            "`/flow` - Outbound flow dashboard\\n"
            "`/cpt` - CPT risk board\\n"
            "`/labor_move` - Leadership labor move log"
        ),
        inline=False
    )

    embed.add_field(
        name=f"{FC_EMOJIS['recruiting']} Recruiting",
        value=(
            "`/open_posting` - Owner opens applications\\n"
            "`/apply` - Apply for an open posting\\n"
            "`/view_applicants` - Leadership views applicants"
        ),
        inline=False
    )

    embed.add_field(
        name=f"{FC_EMOJIS['review']} Accountability",
        value=(
            "`/writeup` - Leadership issues a write-up\\n"
            "`/review` - View associate performance review"
        ),
        inline=False
    )

    embed.add_field(
        name=f"{FC_EMOJIS['quality']} Metric Legend",
        value=(
            f"{FC_EMOJIS['green']} Green = Healthy\\n"
            f"{FC_EMOJIS['yellow']} Yellow = Watch area\\n"
            f"{FC_EMOJIS['red']} Red = Critical risk\\n"
            f"{FC_EMOJIS['cpt_risk']} CPT Risk = Ship deadline pressure"
        ),
        inline=False
    )

    embed.set_footer(text="FC RP Bot • Rank = level • Assignment = job area • Certificates = trained functions")
    await interaction.response.send_message(embed=embed)





# =========================
# VERSION 2.1 DEPARTMENT OM AUTHORITY
# =========================

DEPARTMENT_AUTHORITY = {
    "Ship Dock Operations Manager": [
        "Shipping Sorter",
        "Transship",
        "Ship Dock",
        "Lower Mezzanine",
        "Upper Mezzanine",
        "Quality",
        "VRETS",
        "TDR Operator",
        "Flow Desk"
    ],
    "Pick Operations Manager": [
        "Pick",
        "Pick Floor 1",
        "Pick Floor 2",
        "Pick Floor 3",
        "Tote Runner",
        "Amnesty"
    ],
    "Stow Operations Manager": [
        "Stow",
        "Stow Floor 1",
        "Stow Floor 2",
        "Stow Floor 3",
        "Amnesty"
    ],
    "Pack Operations Manager": [
        "Pack Singles",
        "AFE Pack",
        "AFE Induct",
        "AFE Rebin",
        "SLAM"
    ],
    "Inbound Operations Manager": [
        "Receive Dock",
        "Decant",
        "Inbound Problem Solve"
    ],
    "Learning Manager": [
        "Learning",
        "Learning Trainer"
    ],
    "Safety Manager": [
        "Safety"
    ],
    "PXT / HR Manager": [
        "PXT / HR"
    ],
    "Non-Inventory Manager": [
        "Non-Inventory"
    ]
}

def has_department_authority(member, area=None):
    p = get_profile(member.id)
    rank = p.get("rank", "New Hire")
    assignment = p.get("assignment", "Unassigned")

    if rank in ["L7 Senior Operations Manager", "L8 General Manager"]:
        return True

    if rank == "L6 Operations Manager":
        if area is None:
            return assignment in DEPARTMENT_AUTHORITY
        return area in DEPARTMENT_AUTHORITY.get(assignment, [])

    if rank in ["L4 Area Manager", "L5 Area Manager", "T3 Process Assistant"]:
        if area is None:
            return assignment != "Unassigned"
        return area.lower() in assignment.lower()

    return has_leadership_permission(member)

@bot.tree.command(name="assign_department_om", description="Owner-only: assign an L6 OM over a full department.")
async def assign_department_om(interaction: discord.Interaction, user: discord.Member, department: str):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Only the bot owner can assign department OMs.", ephemeral=True)
        return

    if department not in DEPARTMENT_AUTHORITY:
        options = "\n".join([f"- {d}" for d in DEPARTMENT_AUTHORITY.keys()])
        await interaction.response.send_message(f"❌ Invalid department OM assignment.\n\nValid options:\n{options}", ephemeral=True)
        return

    p = get_profile(user.id)

    if p.get("rank") != "L6 Operations Manager":
        await interaction.response.send_message("❌ User must be **L6 Operations Manager** first.", ephemeral=True)
        return

    p["assignment"] = department

    if "Ship Dock" in department:
        p["department"] = "Ship Dock"
    elif "Pick" in department:
        p["department"] = "Pick"
    elif "Stow" in department:
        p["department"] = "Stow"
    elif "Pack" in department:
        p["department"] = "Pack"
    elif "Inbound" in department:
        p["department"] = "Inbound"
    elif "Learning" in department:
        p["department"] = "Learning"
    elif "Safety" in department:
        p["department"] = "Safety"
    elif "PXT" in department:
        p["department"] = "PXT / HR"
    elif "Non-Inventory" in department:
        p["department"] = "Non-Inventory"

    update_profile(user.id, p)

    await interaction.response.send_message(
        f"✅ {user.mention} is now assigned as **{department}**.\n\n"
        f"Authority Areas:\n" +
        "\n".join([f"• {area}" for area in DEPARTMENT_AUTHORITY[department]])
    )

@bot.tree.command(name="my_authority", description="View what areas your assignment controls.")
async def my_authority(interaction: discord.Interaction):
    p = get_profile(interaction.user.id)
    assignment = p.get("assignment", "Unassigned")
    areas = DEPARTMENT_AUTHORITY.get(assignment, [])

    if not areas:
        await interaction.response.send_message(
            f"📌 **Current Assignment:** {assignment}\n\nNo department-wide authority found.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"📌 **Current Assignment:** {assignment}\n\n"
        f"✅ **You control these areas:**\n" +
        "\n".join([f"• {area}" for area in areas])
    )

# =========================
# VERSION 2.0 OPERATIONS
# =========================

LOG_CHANNEL_NAMES = {
    "leadership": "leadership-logs",
    "promotions": "promotion-logs",
    "recruiting": "recruiting-logs",
    "operations": "operations-logs",
    "discipline": "writeup-logs"
}

WEEKLY_REQUIREMENTS = {
    "New Hire": 1,
    "T1 Fulfillment Associate": 3,
    "Process Guide": 3,
    "Learning Ambassador": 3,
    "T3 Process Assistant": 4,
    "T3 Learning Trainer": 4,
    "T3 Non-Inventory Receiver": 4,
    "L4 Area Manager": 2,
    "L5 Area Manager": 2,
    "L6 Operations Manager": 2,
    "L7 Senior Operations Manager": 1,
    "L8 General Manager": 1
}

STAFFING_TARGETS = {
    "Pick Floor 1": 8,
    "Pick Floor 2": 8,
    "Pick Floor 3": 8,
    "Stow Floor 1": 8,
    "Stow Floor 2": 8,
    "Stow Floor 3": 8,
    "Pack Singles": 10,
    "AFE Pack": 12,
    "Receive Dock": 8,
    "Decant": 8,
    "Shipping Sorter": 10,
    "Transship": 6,
    "Lower Mezzanine": 6,
    "Upper Mezzanine": 6,
    "Quality": 4,
    "VRETS": 4,
    "Learning": 3,
    "Non-Inventory": 3,
    "Safety": 2,
    "PXT / HR": 2
}

async def send_log(guild, log_type, message):
    channel_name = LOG_CHANNEL_NAMES.get(log_type)
    if not channel_name:
        return
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel:
        await channel.send(message)

@bot.tree.command(name="create_log_channels", description="Owner-only: create recommended FC log channels.")
async def create_log_channels(interaction: discord.Interaction):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Only the bot owner can create log channels.", ephemeral=True)
        return

    created = []
    for channel_name in LOG_CHANNEL_NAMES.values():
        existing = discord.utils.get(interaction.guild.text_channels, name=channel_name)
        if not existing:
            await interaction.guild.create_text_channel(channel_name)
            created.append(channel_name)

    if created:
        await interaction.response.send_message("✅ Created log channels:\n" + "\n".join([f"`#{c}`" for c in created]))
    else:
        await interaction.response.send_message("✅ All log channels already exist.")

@bot.tree.command(name="hire", description="Owner-only: hire/promote an applicant after interview.")
async def hire(interaction: discord.Interaction, user: discord.Member, rank: str, assignment: str = "Unassigned"):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Only the bot owner can hire/promote applicants.", ephemeral=True)
        return

    if rank not in RANKS:
        await interaction.response.send_message("❌ Invalid rank.", ephemeral=True)
        return

    if assignment != "Unassigned" and assignment not in ASSIGNMENTS:
        await interaction.response.send_message("❌ Invalid assignment.", ephemeral=True)
        return

    p = get_profile(user.id)
    old_rank = p["rank"]
    old_assignment = p["assignment"]

    p["rank"] = rank
    p["assignment"] = assignment

    for role_name, application in p.get("applications", {}).items():
        if application.get("status") in ["Submitted", "Under Review", "Interview Scheduled", "Interview Passed"]:
            application["status"] = "Accepted"

    update_profile(user.id, p)

    await interaction.response.send_message(
        f"✅ {user.mention} has been hired/promoted.\n"
        f"Rank: **{rank}**\n"
        f"Assignment: **{assignment}**"
    )

    await send_log(
        interaction.guild,
        "promotions",
        f"✅ **Hire/Promotion Logged**\nUser: {user.mention}\nOld Rank: **{old_rank}**\nNew Rank: **{rank}**\nOld Assignment: **{old_assignment}**\nNew Assignment: **{assignment}**\nApproved By: {interaction.user.mention}"
    )

@bot.tree.command(name="reject", description="Leadership rejects an application.")
async def reject(interaction: discord.Interaction, user: discord.Member, role: str, reason: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    p = get_profile(user.id)

    if role not in p["applications"]:
        await interaction.response.send_message("❌ This user has no application for that role.", ephemeral=True)
        return

    p["applications"][role]["status"] = f"Rejected: {reason}"
    update_profile(user.id, p)

    await interaction.response.send_message(f"❌ {user.mention}'s application for **{role}** was rejected.\nReason: {reason}")
    await send_log(interaction.guild, "recruiting", f"❌ **Application Rejected**\nUser: {user.mention}\nRole: **{role}**\nReason: {reason}\nBy: {interaction.user.mention}")

@bot.tree.command(name="interview_pass", description="Leadership marks an applicant as passed interview.")
async def interview_pass(interaction: discord.Interaction, user: discord.Member, role: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    p = get_profile(user.id)

    if role not in p["applications"]:
        await interaction.response.send_message("❌ This user has no application for that role.", ephemeral=True)
        return

    p["applications"][role]["status"] = "Interview Passed"
    update_profile(user.id, p)

    await interaction.response.send_message(f"✅ {user.mention} passed interview for **{role}**.")
    await send_log(interaction.guild, "recruiting", f"✅ **Interview Passed**\nUser: {user.mention}\nRole: **{role}**\nMarked By: {interaction.user.mention}")

@bot.tree.command(name="interview_fail", description="Leadership marks an applicant as failed interview.")
async def interview_fail(interaction: discord.Interaction, user: discord.Member, role: str, reason: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    p = get_profile(user.id)

    if role not in p["applications"]:
        await interaction.response.send_message("❌ This user has no application for that role.", ephemeral=True)
        return

    p["applications"][role]["status"] = f"Interview Failed: {reason}"
    update_profile(user.id, p)

    await interaction.response.send_message(f"❌ {user.mention} failed interview for **{role}**.\nReason: {reason}")
    await send_log(interaction.guild, "recruiting", f"❌ **Interview Failed**\nUser: {user.mention}\nRole: **{role}**\nReason: {reason}\nMarked By: {interaction.user.mention}")

@bot.tree.command(name="activity", description="View weekly activity requirement status.")
async def activity(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    p = get_profile(target.id)

    required = WEEKLY_REQUIREMENTS.get(p["rank"], 1)
    shifts = p.get("weekly_shifts", 0)
    minutes = p.get("weekly_minutes", 0)
    status = "✅ Met" if shifts >= required else "⚠️ Not Met"

    await interaction.response.send_message(
        f"⏱️ **Weekly Activity: {target.display_name}**\n\n"
        f"Rank: **{p['rank']}**\n"
        f"Shifts Worked: **{shifts}/{required}**\n"
        f"Minutes Worked: **{minutes}**\n"
        f"Status: **{status}**"
    )

@bot.tree.command(name="staffing", description="View department staffing targets.")
async def staffing(interaction: discord.Interaction):
    embed = discord.Embed(
        title="👥 FC Staffing Dashboard",
        description="Current targets for department staffing. Actual assigned counts can be expanded later with scheduled shifts.",
        color=discord.Color.blue()
    )

    for area, target in STAFFING_TARGETS.items():
        embed.add_field(name=area, value=f"Target: **{target} associates**", inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="peak_event", description="Leadership triggers a Peak-style event.")
async def peak_event(interaction: discord.Interaction, severity: int):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    if severity < 1 or severity > 10:
        await interaction.response.send_message("❌ Severity must be from 1 to 10.", ephemeral=True)
        return

    impact = severity * 2

    for floor in PICK_FLOORS.values():
        floor["health"] = max(0, floor["health"] - impact)
        floor["backlog"] = min(100, floor["backlog"] + severity)

    for floor in STOW_FLOORS.values():
        floor["health"] = max(0, floor["health"] - impact)
        floor["backlog"] = min(100, floor["backlog"] + severity)

    for area_name in ["Pack Singles", "AFE Pack", "Shipping Sorter", "Transship"]:
        if area_name in DEPARTMENT_HEALTH:
            DEPARTMENT_HEALTH[area_name]["health"] = max(0, DEPARTMENT_HEALTH[area_name]["health"] - impact)
            if "wip" in DEPARTMENT_HEALTH[area_name]:
                DEPARTMENT_HEALTH[area_name]["wip"] = min(100, DEPARTMENT_HEALTH[area_name]["wip"] + severity)
            if "backlog" in DEPARTMENT_HEALTH[area_name]:
                DEPARTMENT_HEALTH[area_name]["backlog"] = min(100, DEPARTMENT_HEALTH[area_name]["backlog"] + severity)

    await interaction.response.send_message(
        f"🚨 **Peak Event Triggered**\n\n"
        f"Severity: **{severity}/10**\n"
        f"Building Impact: **-{impact}% health** to major production areas.\n"
        f"Leadership should check `/flow`, `/health`, and `/staffing`."
    )
    await send_log(interaction.guild, "operations", f"🚨 **Peak Event**\nSeverity: **{severity}/10**\nTriggered By: {interaction.user.mention}")

@bot.tree.command(name="health_decay", description="Owner-only: manually decay building health.")
async def health_decay(interaction: discord.Interaction, amount: int = 1):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        return

    amount = max(1, min(10, amount))

    for floor in PICK_FLOORS.values():
        floor["health"] = max(0, floor["health"] - amount)

    for floor in STOW_FLOORS.values():
        floor["health"] = max(0, floor["health"] - amount)

    for area in DEPARTMENT_HEALTH.values():
        area["health"] = max(0, area["health"] - amount)

    await interaction.response.send_message(f"📉 Building health decayed by **{amount}%** across all areas.")
    await send_log(interaction.guild, "operations", f"📉 **Health Decay Applied**\nAmount: **{amount}%**\nBy: {interaction.user.mention}")

@bot.tree.command(name="setup_channels", description="Owner-only: create a basic FC server channel layout.")
async def setup_channels(interaction: discord.Interaction):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        return

    categories = {
        "📢 INFORMATION": ["welcome", "rules", "announcements", "fc-map", "help-desk"],
        "📋 RECRUITING": ["job-postings", "applications", "interview-schedule", "hiring-results"],
        "📦 PICK": ["pick-floor-1", "pick-floor-2", "pick-floor-3", "pick-pa-office"],
        "📥 STOW": ["stow-floor-1", "stow-floor-2", "stow-floor-3", "stow-pa-office"],
        "📮 PACK": ["pack-singles", "afe-pack", "afe-problem-solve"],
        "🚚 INBOUND": ["receive-dock", "decant", "inbound-problem-solve"],
        "🚛 SHIP DOCK": ["shipping-sorter", "transship", "lower-mezzanine", "upper-mezzanine", "quality", "vrets", "flow-desk", "tdr-desk"],
        "🎓 LEARNING": ["learning-office", "ambassador-chat", "training-records", "cross-training"],
        "🏢 SUPPORT": ["pxt-support", "safety-reports", "non-inventory", "supply-requests"],
        "📊 OPERATIONS": ["ops-dashboard", "building-health", "cpt-board", "labor-moves", "manager-chat"],
        "🔒 LOGS": list(LOG_CHANNEL_NAMES.values())
    }

    created_count = 0

    for category_name, channels in categories.items():
        category = discord.utils.get(interaction.guild.categories, name=category_name)
        if not category:
            category = await interaction.guild.create_category(category_name)

        for channel_name in channels:
            existing = discord.utils.get(interaction.guild.text_channels, name=channel_name)
            if not existing:
                await interaction.guild.create_text_channel(channel_name, category=category)
                created_count += 1

    await interaction.response.send_message(f"✅ FC channel layout created/checked. New channels created: **{created_count}**.")




# =========================
# VERSION 3.0 FC OPERATIONS SIMULATOR
# =========================

SHIFTS = {
    "Front Half Nights": "Sunday - Wednesday",
    "Back Half Nights": "Wednesday - Saturday"
}

CERTIFICATION_GROUPS = {
    "Equipment": ["PIT Operator", "TDR Operator", "AFM"],
    "Leadership": ["Learning Ambassador", "Process Guide", "Flow Lead"],
    "Problem Solve": ["Pick Problem Solve", "Stow Problem Solve", "AFE Problem Solve", "Inbound Problem Solve", "ICQA Problem Solve", "Dock Problem Solve", "Problem Solve"],
    "Pick/Stow": ["Pick", "Stow", "Tote Runner", "Water Spider"],
    "Pack": ["Pack Singles", "AFE Pack", "AFE Induct", "AFE Rebin", "SLAM"],
    "Ship Dock": ["Ship Dock", "Transship", "VRETS", "Shipping Clerk", "Quality Specialist", "VRETS Specialist"],
    "Inbound": ["Receive Dock", "Decant"],
    "ICQA": ["ICQA", "SRC", "SBC", "Cycle Count"],
    "Safety": ["Associate Safety Committee", "Safety Champion"]
}

AREA_TO_DEPARTMENT = {
    "Shipping Sorter": "Ship Dock",
    "Transship": "Ship Dock",
    "Flow Lead": "Ship Dock",
    "Quality": "Ship Dock",
    "TDR Operator": "Ship Dock",
    "Shipping Clerk": "Ship Dock",
    "Lower Mezzanine": "Ship Dock",
    "Upper Mezzanine": "Ship Dock",
    "VRETS": "Ship Dock",
    "Pick Floor 1": "Pick",
    "Pick Floor 2": "Pick",
    "Pick Floor 3": "Pick",
    "Stow Floor 1": "Stow",
    "Stow Floor 2": "Stow",
    "Stow Floor 3": "Stow",
    "Pack Singles": "Pack",
    "AFE Pack": "Pack",
    "Receive Dock": "Inbound",
    "Decant": "Inbound",
    "ICQA": "ICQA"
}

AREA_MANAGER_AUTHORITY = {
    "Shipping Sorter & Transship Manager": ["Shipping Sorter", "Transship", "Flow Lead"],
    "Quality Manager": ["Quality", "TDR Operator", "Shipping Clerk"],
    "Lower & Upper Mezz Manager": ["Lower Mezzanine", "Upper Mezzanine"],
    "VRETS Manager": ["VRETS"],
    "Pick Floor 1 Manager": ["Pick Floor 1"],
    "Pick Floor 2 Manager": ["Pick Floor 2"],
    "Pick Floor 3 Manager": ["Pick Floor 3"],
    "Stow Floor 1 Manager": ["Stow Floor 1"],
    "Stow Floor 2 Manager": ["Stow Floor 2"],
    "Stow Floor 3 Manager": ["Stow Floor 3"],
    "Pack Singles Manager": ["Pack Singles"],
    "AFE Manager": ["AFE Pack", "AFE Induct", "AFE Rebin", "SLAM"],
    "Receive Dock Manager": ["Receive Dock"],
    "Decant Manager": ["Decant"],
    "ICQA Manager": ["ICQA", "SRC", "SBC", "Cycle Count"]
}

PA_ASSIGNMENTS = {
    "Shipping Sorter PA": "Shipping Sorter",
    "Transship PA": "Transship",
    "FLOW Lead PA": "Flow Lead",
    "Quality PA": "Quality",
    "Lower Mezzanine PA": "Lower Mezzanine",
    "Upper Mezzanine PA": "Upper Mezzanine",
    "VRETS PA": "VRETS",
    "Pick PA Floor 1": "Pick Floor 1",
    "Pick PA Floor 2": "Pick Floor 2",
    "Pick PA Floor 3": "Pick Floor 3",
    "Stow PA Floor 1": "Stow Floor 1",
    "Stow PA Floor 2": "Stow Floor 2",
    "Stow PA Floor 3": "Stow Floor 3",
    "Pack Singles PA": "Pack Singles",
    "AFE Pack PA": "AFE Pack",
    "Receive Dock PA": "Receive Dock",
    "Decant PA": "Decant",
    "ICQA PA": "ICQA"
}

DOCK_DOORS = {str(i): {"status": "Empty", "trailer": "None"} for i in list(range(120, 151)) + list(range(201, 223))}

def department_from_area(area):
    return AREA_TO_DEPARTMENT.get(area, area)

def get_display_name(guild, user_id):
    member = guild.get_member(int(user_id)) if guild else None
    return member.mention if member else f"<@{user_id}>"

def profile_matches_department(profile, department):
    return profile.get("department") == department or department in profile.get("assignment", "")

def find_leadership(guild, department, area=None, shift=None):
    leaders = {
        "PG": [],
        "PA": [],
        "AM": [],
        "OM": [],
        "Senior OM": [],
        "GM": []
    }

    for p in list_profiles():
        if shift and p.get("shift") not in [shift, "Unassigned", None]:
            continue

        rank = p.get("rank", "")
        assignment = p.get("assignment", "")
        p_department = p.get("department", "")
        p_area = p.get("area", "")

        same_dept = p_department == department or department in assignment
        same_area = area and (p_area == area or area in assignment)

        if rank == "Process Guide" and (same_area or same_dept):
            leaders["PG"].append(p)
        elif rank == "T3 Process Assistant" and (same_area or same_dept):
            leaders["PA"].append(p)
        elif rank in ["L4 Area Manager", "L5 Area Manager"] and (same_area or same_dept):
            leaders["AM"].append(p)
        elif rank == "L6 Operations Manager" and same_dept:
            leaders["OM"].append(p)
        elif rank == "L7 Senior Operations Manager":
            leaders["Senior OM"].append(p)
        elif rank == "L8 General Manager":
            leaders["GM"].append(p)

    return leaders

@bot.tree.command(name="assign_shift", description="Leadership assigns an associate to FHN or BHN.")
async def assign_shift(interaction: discord.Interaction, user: discord.Member, shift: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    if shift not in SHIFTS:
        await interaction.response.send_message("❌ Invalid shift. Use `Front Half Nights` or `Back Half Nights`.", ephemeral=True)
        return

    p = get_profile(user.id)
    p["shift"] = shift
    update_profile(user.id, p)

    await interaction.response.send_message(f"✅ {user.mention} assigned to **{shift}** ({SHIFTS[shift]}).")

@bot.tree.command(name="my_shift", description="View your shift assignment.")
async def my_shift(interaction: discord.Interaction):
    p = get_profile(interaction.user.id)
    shift = p.get("shift", "Unassigned")
    await interaction.response.send_message(
        f"🌙 **Shift Info**\n\n"
        f"Shift: **{shift}**\n"
        f"Schedule: **{SHIFTS.get(shift, 'Unassigned')}**\n"
        f"Department: **{p.get('department', 'Unassigned')}**\n"
        f"Area: **{p.get('area', 'Unassigned')}**"
    )

@bot.tree.command(name="assign_area_manager", description="Owner-only: assign an L4/L5 AM to an area.")
async def assign_area_manager(interaction: discord.Interaction, user: discord.Member, area_manager_assignment: str):
    if not is_owner(interaction.user):
        await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        return

    if area_manager_assignment not in AREA_MANAGER_AUTHORITY:
        options = "\n".join([f"- {x}" for x in AREA_MANAGER_AUTHORITY])
        await interaction.response.send_message(f"❌ Invalid AM assignment.\n\nValid options:\n{options}", ephemeral=True)
        return

    p = get_profile(user.id)
    if p.get("rank") not in ["L4 Area Manager", "L5 Area Manager"]:
        await interaction.response.send_message("❌ User must be **L4 Area Manager** or **L5 Area Manager**.", ephemeral=True)
        return

    areas = AREA_MANAGER_AUTHORITY[area_manager_assignment]
    p["assignment"] = area_manager_assignment
    p["area"] = areas[0]
    p["department"] = department_from_area(areas[0])
    update_profile(user.id, p)

    await interaction.response.send_message(
        f"✅ {user.mention} assigned as **{area_manager_assignment}**.\n"
        f"Authority: " + ", ".join(areas)
    )

@bot.tree.command(name="assign_pa", description="Owner/AM: assign a T3 PA to an area.")
async def assign_pa(interaction: discord.Interaction, user: discord.Member, pa_assignment: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    if pa_assignment not in PA_ASSIGNMENTS:
        options = "\n".join([f"- {x}" for x in PA_ASSIGNMENTS])
        await interaction.response.send_message(f"❌ Invalid PA assignment.\n\nValid options:\n{options}", ephemeral=True)
        return

    p = get_profile(user.id)
    if p.get("rank") != "T3 Process Assistant":
        await interaction.response.send_message("❌ User must be **T3 Process Assistant**.", ephemeral=True)
        return

    area = PA_ASSIGNMENTS[pa_assignment]
    p["assignment"] = pa_assignment
    p["area"] = area
    p["department"] = department_from_area(area)
    update_profile(user.id, p)

    await interaction.response.send_message(f"✅ {user.mention} assigned as **{pa_assignment}** in **{p['department']}**.")

@bot.tree.command(name="appoint_pg", description="AM/OM: appoint a Process Guide.")
async def appoint_pg(interaction: discord.Interaction, user: discord.Member, area: str):
    if not has_department_authority(interaction.user, area):
        await interaction.response.send_message("❌ You do not have authority over that area.", ephemeral=True)
        return

    p = get_profile(user.id)
    p["rank"] = "Process Guide"
    p["assignment"] = f"{area} Process Guide"
    p["area"] = area
    p["department"] = department_from_area(area)
    update_profile(user.id, p)

    await interaction.response.send_message(f"✅ {user.mention} appointed as **Process Guide** for **{area}**.")

@bot.tree.command(name="grant_certification", description="Leadership grants a certification.")
async def grant_certification(interaction: discord.Interaction, user: discord.Member, certification: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    if certification not in TRAINING_CERTS:
        await interaction.response.send_message("❌ Invalid certification.", ephemeral=True)
        return

    p = get_profile(user.id)
    if certification not in p["certifications"]:
        p["certifications"].append(certification)
    update_profile(user.id, p)

    await interaction.response.send_message(f"✅ {user.mention} granted certification: **{certification}**.")

@bot.tree.command(name="revoke_certification", description="AM/OM revokes a certification.")
async def revoke_certification(interaction: discord.Interaction, user: discord.Member, certification: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    p = get_profile(user.id)
    if certification in p["certifications"]:
        p["certifications"].remove(certification)
        update_profile(user.id, p)
        await interaction.response.send_message(f"✅ Removed **{certification}** from {user.mention}.")
    else:
        await interaction.response.send_message("❌ User does not have that certification.", ephemeral=True)

@bot.tree.command(name="certification_directory", description="View everyone with a certification.")
async def certification_directory(interaction: discord.Interaction, certification: str):
    matches = [p for p in list_profiles() if certification in p.get("certifications", [])]

    if not matches:
        await interaction.response.send_message(f"No associates found with **{certification}**.")
        return

    text = "\n".join([f"• {get_display_name(interaction.guild, p['user_id'])}" for p in matches[:30]])
    await interaction.response.send_message(f"🎓 **Certification Directory: {certification}**\n\n{text}")

@bot.tree.command(name="department_leadership", description="View leadership in your department or a selected department.")
async def department_leadership(interaction: discord.Interaction, department: str = None):
    p = get_profile(interaction.user.id)
    department = department or p.get("department", "Unassigned")
    shift = p.get("shift", None)

    if department == "Unassigned":
        await interaction.response.send_message("❌ You are not assigned to a department yet.", ephemeral=True)
        return

    leaders = find_leadership(interaction.guild, department, shift=shift)

    embed = discord.Embed(
        title=f"🏢 {department} Leadership",
        description=f"Shift Filter: **{shift or 'All'}**",
        color=discord.Color.orange()
    )

    for group, profiles in leaders.items():
        value = "\n".join([f"• {get_display_name(interaction.guild, x['user_id'])} — {x.get('assignment', 'Unassigned')}" for x in profiles]) or "None assigned"
        embed.add_field(name=group, value=value, inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="who_is_my_manager", description="View your PA, AM, OM, Senior OM, and GM.")
async def who_is_my_manager(interaction: discord.Interaction):
    p = get_profile(interaction.user.id)
    department = p.get("department", "Unassigned")
    area = p.get("area", "Unassigned")
    shift = p.get("shift", None)

    if department == "Unassigned":
        await interaction.response.send_message("❌ You are not assigned to a department yet.", ephemeral=True)
        return

    leaders = find_leadership(interaction.guild, department, area=area, shift=shift)

    def first_or_none(group):
        return leaders.get(group, [None])[0]

    pa = first_or_none("PA")
    am = first_or_none("AM")
    om = first_or_none("OM")
    som = first_or_none("Senior OM")
    gm = first_or_none("GM")

    await interaction.response.send_message(
        f"👥 **Your Leadership Chain**\n\n"
        f"Department: **{department}**\n"
        f"Area: **{area}**\n"
        f"Shift: **{shift or 'Unassigned'}**\n\n"
        f"PA: {get_display_name(interaction.guild, pa['user_id']) if pa else 'None assigned'}\n"
        f"AM: {get_display_name(interaction.guild, am['user_id']) if am else 'None assigned'}\n"
        f"OM: {get_display_name(interaction.guild, om['user_id']) if om else 'None assigned'}\n"
        f"Senior OM: {get_display_name(interaction.guild, som['user_id']) if som else 'None assigned'}\n"
        f"GM: {get_display_name(interaction.guild, gm['user_id']) if gm else 'None assigned'}"
    )

@bot.tree.command(name="org_chart", description="View the building org chart.")
async def org_chart(interaction: discord.Interaction):
    all_profiles = list_profiles()

    def people(rank):
        return [p for p in all_profiles if p.get("rank") == rank]

    gms = people("L8 General Manager")
    soms = people("L7 Senior Operations Manager")
    oms = people("L6 Operations Manager")
    ams = [p for p in all_profiles if p.get("rank") in ["L4 Area Manager", "L5 Area Manager"]]
    pas = people("T3 Process Assistant")
    pgs = people("Process Guide")

    text = "🏢 **DIS4 Fulfillment Center Org Chart**\n\n"
    text += "**GM**\n" + ("\n".join([f"• {get_display_name(interaction.guild, p['user_id'])}" for p in gms]) or "• None") + "\n\n"
    text += "**Senior OM**\n" + ("\n".join([f"• {get_display_name(interaction.guild, p['user_id'])}" for p in soms]) or "• None") + "\n\n"
    text += "**Operations Managers**\n" + ("\n".join([f"• {get_display_name(interaction.guild, p['user_id'])} — {p.get('assignment', 'Unassigned')}" for p in oms]) or "• None") + "\n\n"
    text += "**Area Managers**\n" + ("\n".join([f"• {get_display_name(interaction.guild, p['user_id'])} — {p.get('assignment', 'Unassigned')}" for p in ams[:15]]) or "• None") + "\n\n"
    text += f"**PAs:** {len(pas)} active\n"
    text += f"**PGs:** {len(pgs)} active"

    await interaction.response.send_message(text[:1900])

@bot.tree.command(name="site_status", description="View overall DIS4 site status.")
async def site_status(interaction: discord.Interaction):
    pick_avg = round(sum(f["health"] for f in PICK_FLOORS.values()) / len(PICK_FLOORS))
    stow_avg = round(sum(f["health"] for f in STOW_FLOORS.values()) / len(STOW_FLOORS))
    pack_avg = round((DEPARTMENT_HEALTH["Pack Singles"]["health"] + DEPARTMENT_HEALTH["AFE Pack"]["health"]) / 2)
    ship_avg = round(sum(DEPARTMENT_HEALTH[x]["health"] for x in ["Shipping Sorter", "Transship", "Lower Mezzanine", "Upper Mezzanine", "Quality", "VRETS"]) / 6)
    icqa = DEPARTMENT_HEALTH.get("ICQA", {}).get("health", 100)
    overall = round((pick_avg + stow_avg + pack_avg + ship_avg + icqa) / 5)

    await interaction.response.send_message(
        f"🏢 **DIS4 Site Status**\n\n"
        f"Overall Building Health: **{overall}%**\n\n"
        f"📦 Pick: **{pick_avg}%**\n"
        f"📥 Stow: **{stow_avg}%**\n"
        f"📮 Pack: **{pack_avg}%**\n"
        f"🚛 Ship Dock: **{ship_avg}%**\n"
        f"🔎 ICQA: **{icqa}%**\n\n"
        f"CPT Risk: **{'Low' if overall >= 85 else 'Medium' if overall >= 70 else 'High'}**"
    )

@bot.tree.command(name="manager_dashboard", description="Manager dashboard for your area or department.")
async def manager_dashboard(interaction: discord.Interaction):
    p = get_profile(interaction.user.id)

    if not has_department_authority(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    department = p.get("department", "Unassigned")
    assignment = p.get("assignment", "Unassigned")

    embed = discord.Embed(
        title=f"📊 Manager Dashboard — {assignment}",
        description=f"Department: **{department}**",
        color=discord.Color.blue()
    )

    if department == "Ship Dock":
        for area in ["Shipping Sorter", "Transship", "Lower Mezzanine", "Upper Mezzanine", "Quality", "VRETS"]:
            stats = DEPARTMENT_HEALTH.get(area, {})
            embed.add_field(name=area, value=f"Health: **{stats.get('health', 'N/A')}%**", inline=True)
    elif department == "Pick":
        for floor, stats in PICK_FLOORS.items():
            embed.add_field(name=f"Pick {floor}", value=f"Health: **{stats['health']}%**", inline=True)
    elif department == "Stow":
        for floor, stats in STOW_FLOORS.items():
            embed.add_field(name=f"Stow {floor}", value=f"Health: **{stats['health']}%**", inline=True)
    elif department in DEPARTMENT_HEALTH:
        stats = DEPARTMENT_HEALTH[department]
        for k, v in stats.items():
            embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
    else:
        embed.add_field(name="Status", value="No dashboard data for this department yet.", inline=False)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="view_doors", description="View Ship Dock door status.")
async def view_doors(interaction: discord.Interaction):
    lines = []
    for door, data in list(DOCK_DOORS.items())[:60]:
        lines.append(f"Door {door}: **{data['status']}** | Trailer: {data['trailer']}")

    await interaction.response.send_message("🚛 **Dock Doors**\n\n" + "\n".join(lines[:35]))

@bot.tree.command(name="assign_trailer", description="TDR/Clerk: assign a trailer to a dock door.")
async def assign_trailer(interaction: discord.Interaction, door: str, trailer: str):
    p = get_profile(interaction.user.id)
    if "TDR Operator" not in p.get("certifications", []) and "Shipping Clerk" not in p.get("certifications", []) and not has_department_authority(interaction.user, "TDR Operator"):
        await interaction.response.send_message("❌ Requires TDR Operator or Shipping Clerk certification.", ephemeral=True)
        return

    if door not in DOCK_DOORS:
        await interaction.response.send_message("❌ Invalid door. Valid ranges are 120-150 and 201-222.", ephemeral=True)
        return

    DOCK_DOORS[door]["trailer"] = trailer
    DOCK_DOORS[door]["status"] = "Assigned"

    await interaction.response.send_message(f"✅ Trailer **{trailer}** assigned to Door **{door}**.")

@bot.tree.command(name="open_door", description="TDR: open a dock door.")
async def open_door(interaction: discord.Interaction, door: str):
    p = get_profile(interaction.user.id)
    if "TDR Operator" not in p.get("certifications", []) and not has_department_authority(interaction.user, "TDR Operator"):
        await interaction.response.send_message("❌ Requires TDR Operator certification.", ephemeral=True)
        return

    if door not in DOCK_DOORS:
        await interaction.response.send_message("❌ Invalid door.", ephemeral=True)
        return

    DOCK_DOORS[door]["status"] = "Open"
    await interaction.response.send_message(f"✅ Door **{door}** opened using TDR process.")

@bot.tree.command(name="close_door", description="TDR: close a dock door.")
async def close_door(interaction: discord.Interaction, door: str):
    p = get_profile(interaction.user.id)
    if "TDR Operator" not in p.get("certifications", []) and not has_department_authority(interaction.user, "TDR Operator"):
        await interaction.response.send_message("❌ Requires TDR Operator certification.", ephemeral=True)
        return

    if door not in DOCK_DOORS:
        await interaction.response.send_message("❌ Invalid door.", ephemeral=True)
        return

    DOCK_DOORS[door]["status"] = "Closed"
    await interaction.response.send_message(f"✅ Door **{door}** closed using TDR process.")

@bot.tree.command(name="recognize", description="Leadership recognizes an associate.")
async def recognize(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    p = get_profile(user.id)
    p["morale"] = min(100, p.get("morale", 100) + 10)
    p["swag_points"] = p.get("swag_points", 0) + 25
    update_profile(user.id, p)

    await interaction.response.send_message(
        f"🏆 **Associate Recognition**\n\n"
        f"Associate: {user.mention}\n"
        f"Reason: {reason}\n\n"
        f"+10 Morale\n+25 Swag Points"
    )

@bot.tree.command(name="time_balance", description="View UPT, PTO, and Vacation.")
async def time_balance(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    p = get_profile(target.id)

    await interaction.response.send_message(
        f"🕒 **Time Balance: {target.display_name}**\n\n"
        f"UPT: **{p.get('upt', 20)} hrs**\n"
        f"PTO: **{p.get('pto', 10)} hrs**\n"
        f"Vacation: **{p.get('vacation', 0)} hrs**"
    )

@bot.tree.command(name="use_upt", description="Use UPT hours.")
async def use_upt(interaction: discord.Interaction, hours: int):
    p = get_profile(interaction.user.id)
    p["upt"] = p.get("upt", 20) - max(1, hours)
    update_profile(interaction.user.id, p)

    status = "⚠️ Negative UPT — Termination Review triggered." if p["upt"] < 0 else "✅ UPT used."
    await interaction.response.send_message(f"{status}\nCurrent UPT: **{p['upt']} hrs**")

@bot.tree.command(name="shift_handoff", description="Leadership creates a shift handoff note.")
async def shift_handoff(interaction: discord.Interaction, department: str, notes: str):
    if not has_leadership_permission(interaction.user):
        await interaction.response.send_message("❌ Leadership only.", ephemeral=True)
        return

    await interaction.response.send_message(
        f"📋 **Shift Handoff — {department}**\n\n"
        f"Submitted By: {interaction.user.mention}\n"
        f"Notes: {notes}\n\n"
        f"Recommended Follow-Up: Check `/site_status`, `/manager_dashboard`, and `/flow`."
    )




# =========================
# VERSION 3.1 PA LOOKUP FEATURE
# =========================

def format_idle_time(profile):
    if not profile.get("clocked_in"):
        return "Not clocked in"

    last = profile.get("last_activity_time") or profile.get("clockin_time")
    if not last:
        return "Unknown"

    idle_seconds = max(0, int(time.time() - float(last)))
    minutes = idle_seconds // 60
    hours = minutes // 60
    remaining_minutes = minutes % 60

    if hours > 0:
        return f"{hours}h {remaining_minutes}m"
    return f"{minutes}m"

def lookup_permission(member, target_profile=None):
    viewer = get_profile(member.id)

    if viewer.get("rank") in [
        "T3 Process Assistant",
        "T3 Learning Trainer",
        "T3 Non-Inventory Receiver",
        "L4 Area Manager",
        "L5 Area Manager",
        "L6 Operations Manager",
        "L7 Senior Operations Manager",
        "L8 General Manager"
    ]:
        return True

    if viewer.get("rank") in ["Process Guide", "Learning Ambassador"]:
        if target_profile:
            return viewer.get("department") == target_profile.get("department")
        return True

    return False

@bot.tree.command(name="lookup_associate", description="PA/Leadership: lookup associate details and idle time.")
async def lookup_associate(interaction: discord.Interaction, user: discord.Member):
    target = get_profile(user.id)

    if not lookup_permission(interaction.user, target):
        await interaction.response.send_message("❌ Lookup is restricted to PGs, PAs, Learning Ambassadors, and leadership.", ephemeral=True)
        return

    idle = format_idle_time(target)
    certs = target.get("certifications", [])
    cert_text = ", ".join(certs[:12]) if certs else "None"
    if len(certs) > 12:
        cert_text += f" +{len(certs) - 12} more"

    clock_status = "Clocked In" if target.get("clocked_in") else "Clocked Out"

    embed = discord.Embed(
        title=f"🔎 Associate Lookup — {user.display_name}",
        description="Internal associate details for leadership use.",
        color=discord.Color.blue()
    )

    embed.add_field(name="Rank", value=target.get("rank", "New Hire"), inline=True)
    embed.add_field(name="Department", value=target.get("department", "Unassigned"), inline=True)
    embed.add_field(name="Area", value=target.get("area", "Unassigned"), inline=True)
    embed.add_field(name="Shift", value=target.get("shift", "Unassigned"), inline=True)
    embed.add_field(name="Assignment", value=target.get("assignment", "Unassigned"), inline=True)
    embed.add_field(name="Station", value=target.get("current_station", "Unassigned"), inline=True)

    embed.add_field(name="Clock Status", value=clock_status, inline=True)
    embed.add_field(name="Station Status", value=target.get("station_status", "Idle"), inline=True)
    embed.add_field(name="Idle Time", value=idle, inline=True)

    embed.add_field(name="Productivity", value=str(target.get("productivity", 0)), inline=True)
    embed.add_field(name="Quality", value=f"{target.get('quality', 100)}%", inline=True)
    embed.add_field(name="Safety", value=f"{target.get('safety', 100)}%", inline=True)
    embed.add_field(name="Attendance", value=f"{target.get('attendance', 100)}%", inline=True)
    embed.add_field(name="Write-Ups", value=str(target.get("writeups", 0)), inline=True)
    embed.add_field(name="Morale", value=f"{target.get('morale', 100)}%", inline=True)

    embed.add_field(name="Certifications", value=cert_text, inline=False)

    embed.set_footer(text="V3.1 Lookup Feature • Idle time starts from last task/clock-in")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="set_station", description="PA/Leadership: assign an associate to a station or function.")
async def set_station(interaction: discord.Interaction, user: discord.Member, station: str):
    target = get_profile(user.id)

    if not lookup_permission(interaction.user, target):
        await interaction.response.send_message("❌ Station assignment is restricted to PGs, PAs, and leadership.", ephemeral=True)
        return

    target["current_station"] = station
    target["station_status"] = "Assigned"
    target["last_activity_time"] = time.time()
    update_profile(user.id, target)

    await interaction.response.send_message(f"✅ {user.mention} assigned to station/function **{station}**.")

@bot.tree.command(name="mark_active", description="PA/Leadership: mark an associate as active after check-in.")
async def mark_active(interaction: discord.Interaction, user: discord.Member, note: str = "Checked in"):
    target = get_profile(user.id)

    if not lookup_permission(interaction.user, target):
        await interaction.response.send_message("❌ Active checks are restricted to PGs, PAs, and leadership.", ephemeral=True)
        return

    target["last_activity_time"] = time.time()
    target["station_status"] = f"Active - {note}"
    update_profile(user.id, target)

    await interaction.response.send_message(f"✅ {user.mention} marked active. Note: **{note}**")

@bot.tree.command(name="idle_report", description="PA/Leadership: view idle associates in your department.")
async def idle_report(interaction: discord.Interaction, department: str = None):
    viewer = get_profile(interaction.user.id)

    if not lookup_permission(interaction.user):
        await interaction.response.send_message("❌ Idle report is restricted to PGs, PAs, and leadership.", ephemeral=True)
        return

    department = department or viewer.get("department", "Unassigned")

    if department == "Unassigned":
        await interaction.response.send_message("❌ You are not assigned to a department. Provide a department name.", ephemeral=True)
        return

    profiles = []
    for p in list_profiles():
        if p.get("department") == department and p.get("clocked_in"):
            profiles.append(p)

    profiles.sort(key=lambda p: float(p.get("last_activity_time") or p.get("clockin_time") or time.time()))

    if not profiles:
        await interaction.response.send_message(f"✅ No clocked-in associates found for **{department}**.")
        return

    lines = []
    for p in profiles[:20]:
        idle = format_idle_time(p)
        lines.append(
            f"• {get_display_name(interaction.guild, p['user_id'])} | "
            f"Area: **{p.get('area', 'Unassigned')}** | "
            f"Station: **{p.get('current_station', 'Unassigned')}** | "
            f"Idle: **{idle}**"
        )

    await interaction.response.send_message(
        f"⏱️ **Idle Report — {department}**\n\n" + "\n".join(lines),
        ephemeral=True
    )

@bot.tree.command(name="lookup_help", description="View PA lookup feature commands.")
async def lookup_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🔎 **V3.1 Lookup Feature**\n\n"
        "`/lookup_associate user:@associate` — View profile, certs, metrics, station, and idle time\n"
        "`/set_station user:@associate station:Transship Door 143` — Assign station/function\n"
        "`/mark_active user:@associate note:Checked at lane 120` — Reset idle timer after check-in\n"
        "`/idle_report department:Ship Dock` — View idle clocked-in associates\n\n"
        "Idle time is based on the associate's last `/task`, `/clockin`, `/set_station`, or `/mark_active`.",
        ephemeral=True
    )




# =========================
# VERSION 3.1.1 ASSOCIATE ASSIGNMENT HOTFIX
# =========================

ASSOCIATE_AREAS = [
    "Shipping Sorter",
    "Transship",
    "Flow Lead",
    "Quality",
    "TDR Operator",
    "Shipping Clerk",
    "Lower Mezzanine",
    "Upper Mezzanine",
    "VRETS",

    "Pick Floor 1",
    "Pick Floor 2",
    "Pick Floor 3",

    "Stow Floor 1",
    "Stow Floor 2",
    "Stow Floor 3",

    "Pack Singles",
    "AFE Pack",
    "AFE Induct",
    "AFE Rebin",
    "SLAM",

    "Receive Dock",
    "Decant",
    "Inbound Problem Solve",

    "ICQA",
    "SRC",
    "SBC",
    "Cycle Count",

    "Learning",
    "Safety",
    "PXT / HR",
    "Non-Inventory"
]

def can_assign_associate(actor, area):
    actor_profile = get_profile(actor.id)

    if is_owner(actor):
        return True

    if actor_profile.get("rank") in ["L7 Senior Operations Manager", "L8 General Manager"]:
        return True

    if has_department_authority(actor, area):
        return True

    # PAs can assign within their own area only.
    if actor_profile.get("rank") == "T3 Process Assistant":
        return actor_profile.get("area") == area

    return False

@bot.tree.command(name="assign_associate", description="Leadership: assign an associate to a department area and shift.")
async def assign_associate(interaction: discord.Interaction, user: discord.Member, area: str, shift: str = "Unassigned"):
    if area not in ASSOCIATE_AREAS:
        options = "\n".join([f"- {x}" for x in ASSOCIATE_AREAS])
        await interaction.response.send_message(f"❌ Invalid area.\n\nValid areas:\n{options}", ephemeral=True)
        return

    if shift not in list(SHIFTS.keys()) + ["Unassigned"]:
        await interaction.response.send_message("❌ Invalid shift. Use `Front Half Nights`, `Back Half Nights`, or `Unassigned`.", ephemeral=True)
        return

    if not can_assign_associate(interaction.user, area):
        await interaction.response.send_message("❌ You do not have authority to assign associates to that area.", ephemeral=True)
        return

    p = get_profile(user.id)
    p["rank"] = p.get("rank", "T1 Fulfillment Associate")
    if p["rank"] == "New Hire":
        p["rank"] = "T1 Fulfillment Associate"

    p["area"] = area
    p["department"] = department_from_area(area)
    p["assignment"] = f"{area} Associate"
    p["shift"] = shift
    p["current_station"] = area
    p["station_status"] = "Assigned"

    update_profile(user.id, p)

    await interaction.response.send_message(
        f"✅ {user.mention} assigned successfully.\n\n"
        f"Department: **{p['department']}**\n"
        f"Area: **{area}**\n"
        f"Shift: **{shift}**"
    )

@bot.tree.command(name="transfer_associate", description="Leadership: transfer an associate to a new department area.")
async def transfer_associate(interaction: discord.Interaction, user: discord.Member, new_area: str, reason: str = "Operational need"):
    if new_area not in ASSOCIATE_AREAS:
        options = "\n".join([f"- {x}" for x in ASSOCIATE_AREAS])
        await interaction.response.send_message(f"❌ Invalid area.\n\nValid areas:\n{options}", ephemeral=True)
        return

    if not can_assign_associate(interaction.user, new_area):
        await interaction.response.send_message("❌ You do not have authority to transfer associates to that area.", ephemeral=True)
        return

    p = get_profile(user.id)
    old_department = p.get("department", "Unassigned")
    old_area = p.get("area", "Unassigned")

    p["area"] = new_area
    p["department"] = department_from_area(new_area)
    p["assignment"] = f"{new_area} Associate"
    p["current_station"] = new_area
    p["station_status"] = "Transferred"

    update_profile(user.id, p)

    await interaction.response.send_message(
        f"🔁 **Associate Transfer Complete**\n\n"
        f"Associate: {user.mention}\n"
        f"From: **{old_department} / {old_area}**\n"
        f"To: **{p['department']} / {new_area}**\n"
        f"Reason: {reason}"
    )

@bot.tree.command(name="remove_assignment", description="Leadership: remove an associate's department/area assignment.")
async def remove_assignment(interaction: discord.Interaction, user: discord.Member, reason: str = "Assignment removed"):
    target = get_profile(user.id)
    old_area = target.get("area", "Unassigned")

    if old_area != "Unassigned" and not can_assign_associate(interaction.user, old_area):
        await interaction.response.send_message("❌ You do not have authority over this associate's current area.", ephemeral=True)
        return

    old_department = target.get("department", "Unassigned")

    target["department"] = "Unassigned"
    target["area"] = "Unassigned"
    target["assignment"] = "Unassigned"
    target["current_station"] = "Unassigned"
    target["station_status"] = "Unassigned"

    update_profile(user.id, target)

    await interaction.response.send_message(
        f"🗑️ **Assignment Removed**\n\n"
        f"Associate: {user.mention}\n"
        f"Previous Department: **{old_department}**\n"
        f"Previous Area: **{old_area}**\n"
        f"Reason: {reason}"
    )

@bot.tree.command(name="assignment_help", description="View associate assignment commands and valid areas.")
async def assignment_help(interaction: discord.Interaction):
    areas = "\n".join([f"• {x}" for x in ASSOCIATE_AREAS])

    await interaction.response.send_message(
        "📌 **Associate Assignment Commands**\n\n"
        "`/assign_associate user:@associate area:Transship shift:Front Half Nights`\n"
        "`/transfer_associate user:@associate new_area:Shipping Sorter reason:CPT recovery`\n"
        "`/remove_assignment user:@associate reason:Moved to flex pool`\n\n"
        "**Valid Areas:**\n" + areas,
        ephemeral=True
    )

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN in .env")

bot.run(DISCORD_TOKEN)
