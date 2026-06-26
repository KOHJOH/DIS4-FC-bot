
import discord
from engine import *

def is_owner_user(interaction, owner_id):
    return interaction.user.id == owner_id

def build_request_embed(req):
    embed = discord.Embed(title=f"📻 {req['title']}", description=req["message"], color=discord.Color.orange())
    embed.add_field(name="Manager", value=f"{req['manager_name']}\n{req['manager_role']}", inline=True)
    embed.add_field(name="Department", value=req["department"], inline=True)
    embed.add_field(name="Area", value=req["area"], inline=True)
    embed.add_field(name="Personality", value=req["manager_personality"], inline=True)
    embed.add_field(name="Type", value=req["type"], inline=True)
    embed.add_field(name="Request ID", value=req["id"], inline=True)
    embed.add_field(name="Recommendation", value=req["recommendation"], inline=False)
    embed.set_footer(text="Approve, deny, view metrics, or escalate.")
    return embed

class DashboardView(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=240)
        self.owner_id = owner_id

    @discord.ui.button(label="Foresight", style=discord.ButtonStyle.primary, emoji="📊")
    async def foresight(self, interaction, button):
        state = load_state()
        v = state["volume"]
        b = state["building"]
        await interaction.response.send_message(
            f"📊 **FORESIGHT**\n\nForecast: **{b['forecast_level']}**\nInbound: **{fmt(v['inbound_expected'])}**\nOutbound: **{fmt(v['outbound_expected'])}**\nShip Dock Carts: **{fmt(v['ship_dock_carts'])}**\nTrailers: **{v['trailers_expected']}**",
            ephemeral=True
        )

    @discord.ui.button(label="Staffing", style=discord.ButtonStyle.secondary, emoji="👥")
    async def staffing(self, interaction, button):
        state = load_state()
        s = get_staffing(state)
        await interaction.response.send_message(
            f"👥 **AI STAFFING**\n\nScheduled: **{s['scheduled']}**\nClocked In: **{s['clocked_in']}**\nLate: **{s['late']}**\nCall-Offs: **{s['calloffs']}**\nVTO: **{s['vto']}**",
            ephemeral=True
        )

    @discord.ui.button(label="CPT Board", style=discord.ButtonStyle.danger, emoji="🚛")
    async def cpt(self, interaction, button):
        state = load_state()
        trailers = [t for t in state["trailers"] if not t["departed"]][:8]
        lines = []
        for t in trailers:
            icon = "🔴" if t["status"] == "At Risk" else "🟢" if t["status"] == "Ready" else "🟡"
            lines.append(f"{icon} **{t['id']}** | Door {t['door']} | CPT {t['cpt']} | {t['packages_remaining']} pkgs | {t['status']}")
        await interaction.response.send_message("🚛 **CPT BOARD**\n\n" + "\n".join(lines), ephemeral=True)

    @discord.ui.button(label="Sim Hour", style=discord.ButtonStyle.success, emoji="⏱️")
    async def sim_hour(self, interaction, button):
        if not is_owner_user(interaction, self.owner_id):
            await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
            return
        state = load_state()
        simulate_hour(state)
        recs = recommendations(state)
        await interaction.response.send_message(
            f"⏱️ **One Hour Simulated**\n\nHealth: **{state['building']['building_health']}%**\nCPT: **{state['building']['cpt_compliance']}%**\nMissorts: **{state['building']['missorts']}**\n\n🧠 " + "\n".join([f"• {r}" for r in recs]),
            ephemeral=True
        )

class RequestView(discord.ui.View):
    def __init__(self, owner_id, request_id):
        super().__init__(timeout=360)
        self.owner_id = owner_id
        self.request_id = str(request_id)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, emoji="✅")
    async def approve(self, interaction, button):
        if not is_owner_user(interaction, self.owner_id):
            await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
            return
        state = load_state()
        ok, msg = apply_request(state, self.request_id, True)
        await interaction.response.send_message(("✅ " if ok else "❌ ") + msg, ephemeral=True)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, emoji="❌")
    async def deny(self, interaction, button):
        if not is_owner_user(interaction, self.owner_id):
            await interaction.response.send_message("❌ Owner-only.", ephemeral=True)
            return
        state = load_state()
        ok, msg = apply_request(state, self.request_id, False)
        await interaction.response.send_message(("✅ " if ok else "❌ ") + msg, ephemeral=True)

    @discord.ui.button(label="Metrics", style=discord.ButtonStyle.secondary, emoji="📊")
    async def metrics(self, interaction, button):
        state = load_state()
        b = state["building"]
        dept_lines = "\n".join([f"• **{d}:** {h}%" for d, h in list(state["department_health"].items())[:10]])
        await interaction.response.send_message(
            f"📊 **CURRENT METRICS**\n\nHealth: **{b['building_health']}%**\nCPT: **{b['cpt_compliance']}%**\nSafety: **{b['safety']}%**\nQuality: **{b['quality']}%**\nMissorts: **{b['missorts']}**\n\n{dept_lines}",
            ephemeral=True
        )

    @discord.ui.button(label="Escalate", style=discord.ButtonStyle.primary, emoji="⬆️")
    async def escalate(self, interaction, button):
        state = load_state()
        state["events"].append({"time": "Now", "type": "Escalation", "message": f"Request {self.request_id} escalated to Senior OM/GM review."})
        save_state(state)
        await interaction.response.send_message(f"⬆️ Request **{self.request_id}** escalated to Senior OM/GM.", ephemeral=True)
