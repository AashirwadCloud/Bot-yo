import discord
from discord.ext import commands
import os
import asyncio
import socket

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

# Force DND mode
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd)
    print(f"✅ Bot is online as {bot.user}")

# Feature toggles
feature_status = {
    "welcome": True,
    "maintenance": False,
    "reaction_roles": False,
    "economy": False,
    "auto_moderation": False,
    "fun_commands": False,
    "utility_tools": False
}

# Dashboard access
OWNER_ID = 1217747285463531522 # Replace with your ID
FRIEND_ID = 1244871880012206161  # Replace with your friend's ID
ALLOWED_USERS = [OWNER_ID, FRIEND_ID]
DASHBOARD_PASSWORD = "secret"  # Change this password

# Welcome message
@bot.event
async def on_member_join(member):
    if feature_status["welcome"]:
        channel = discord.utils.get(member.guild.text_channels, name="general")
        if channel:
            await channel.send(f"👋 Welcome {member.mention}!")

# Moderation Commands
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member} has been banned.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member} has been kicked.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)
    await member.add_roles(muted_role)
    await ctx.send(f"🔇 {member} has been muted.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f"🔊 {member} has been unmuted.")

# Ticket Setup
@bot.command()
@commands.has_permissions(administrator=True)
async def ticketsetup(ctx):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    message = await ctx.send("📩 Click the button below to create a ticket.")

    class TicketView(discord.ui.View):
        @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
        async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await ctx.guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
            await channel.send(
                f"🎫 Hello {interaction.user.mention}, support will assist you shortly.",
                view=CloseTicketView()
            )

    class CloseTicketView(discord.ui.View):
        @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
        async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            if "ticket-" in interaction.channel.name:
                await interaction.channel.delete()

    await message.edit(view=TicketView())

# Aternos Server Status
@bot.command()
async def aternos_status(ctx, ip="yourserver.aternos.me"):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    try:
        socket.gethostbyname(ip)
        await ctx.send(f"🟢 Aternos Server `{ip}` is ONLINE (ping successful).")
    except socket.error:
        await ctx.send(f"🔴 Aternos Server `{ip}` is OFFLINE or unreachable.")

# Dashboard
@bot.command()
async def dashboard(ctx):
    if ctx.author.id not in ALLOWED_USERS:
        return await ctx.send("❌ You are not allowed to access the dashboard.")

    await ctx.send("🔐 Please enter the dashboard password:")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        if msg.content != DASHBOARD_PASSWORD:
            return await ctx.send("❌ Incorrect password.")
    except asyncio.TimeoutError:
        return await ctx.send("⌛ Timeout. Try again.")

    async def update_dashboard(interaction):
        embed = discord.Embed(title="🛠 Bot Dashboard", description="Toggle bot features:", color=0x00ff00)
        for feature, status in feature_status.items():
            embed.add_field(name=feature.replace("_", " ").title(), value="🟢 Enabled" if status else "🔴 Disabled", inline=False)
        embed.set_footer(text="Made by AASHIRWADGAMINGXD")
        await interaction.response.edit_message(embed=embed, view=DashboardView())

    class DashboardView(discord.ui.View):
        @discord.ui.button(label="Toggle Welcome", style=discord.ButtonStyle.success)
        async def toggle_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in ALLOWED_USERS:
                return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            feature_status["welcome"] = not feature_status["welcome"]
            await update_dashboard(interaction)

        @discord.ui.button(label="Toggle Maintenance", style=discord.ButtonStyle.danger)
        async def toggle_maintenance(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in ALLOWED_USERS:
                return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            feature_status["maintenance"] = not feature_status["maintenance"]
            await update_dashboard(interaction)

        @discord.ui.button(label="Toggle Reaction Roles", style=discord.ButtonStyle.secondary)
        async def toggle_reaction_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in ALLOWED_USERS:
                return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            feature_status["reaction_roles"] = not feature_status["reaction_roles"]
            await update_dashboard(interaction)

        @discord.ui.button(label="Toggle Economy", style=discord.ButtonStyle.secondary)
        async def toggle_economy(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in ALLOWED_USERS:
                return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            feature_status["economy"] = not feature_status["economy"]
            await update_dashboard(interaction)

        @discord.ui.button(label="Toggle Auto Mod", style=discord.ButtonStyle.secondary)
        async def toggle_auto_mod(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in ALLOWED_USERS:
                return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            feature_status["auto_moderation"] = not feature_status["auto_moderation"]
            await update_dashboard(interaction)

        @discord.ui.button(label="Toggle Fun Commands", style=discord.ButtonStyle.secondary)
        async def toggle_fun(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in ALLOWED_USERS:
                return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            feature_status["fun_commands"] = not feature_status["fun_commands"]
            await update_dashboard(interaction)

        @discord.ui.button(label="Toggle Utility Tools", style=discord.ButtonStyle.secondary)
        async def toggle_utility(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id not in ALLOWED_USERS:
                return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            feature_status["utility_tools"] = not feature_status["utility_tools"]
            await update_dashboard(interaction)

    embed = discord.Embed(title="🛠 Bot Dashboard", description="Toggle bot features:", color=0x00ff00)
    for feature, status in feature_status.items():
        embed.add_field(name=feature.replace("_", " ").title(), value="🟢 Enabled" if status else "🔴 Disabled", inline=False)
    embed.set_footer(text="Made by AASHIRWADGAMINGXD")

    await ctx.send(embed=embed, view=DashboardView())

# Start the bot
bot.run(os.getenv("TOKEN"))
