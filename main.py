import discord
from discord.ext import commands
import os
import asyncio
import socket
import random
import json

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
    "reaction_roles": True,
    "economy": True,
    "auto_moderation": True,
    "fun_commands": False,
    "utility_tools": False,
    "anime": True
}

# Dashboard access
OWNER_ID = 1217747285463531522
FRIEND_ID = 1244871880012206161
ALLOWED_USERS = [OWNER_ID, FRIEND_ID]
DASHBOARD_PASSWORD = "secret"

# Economy Data
eco_data = {}

def save_data():
    with open("economy.json", "w") as f:
        json.dump(eco_data, f)

def load_data():
    global eco_data
    try:
        with open("economy.json", "r") as f:
            eco_data = json.load(f)
    except:
        eco_data = {}

load_data()

# Auto moderation
bad_words = ["badword1", "badword2"]

@bot.event
async def on_message(message):
    if feature_status["auto_moderation"] and not message.author.bot:
        for word in bad_words:
            if word in message.content.lower():
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, watch your language!")
                return
    await bot.process_commands(message)

# Welcome message
@bot.event
async def on_member_join(member):
    if feature_status["welcome"]:
        channel = discord.utils.get(member.guild.text_channels, name="general")
        if channel:
            await channel.send(f"👋 Welcome {member.mention}!")

# Moderation
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

# Reaction Roles
@bot.command()
async def reactionrole(ctx, emoji: str, role: discord.Role, *, message_text: str):
    if not feature_status["reaction_roles"]:
        return await ctx.send("❌ Reaction roles are disabled.")
    message = await ctx.send(message_text)
    await message.add_reaction(emoji)

    @bot.event
    async def on_raw_reaction_add(payload):
        if str(payload.emoji) == emoji and payload.message_id == message.id:
            guild = ctx.guild
            member = guild.get_member(payload.user_id)
            if member and role not in member.roles:
                await member.add_roles(role)

# Ping Command
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")

# Economy
@bot.command()
async def daily(ctx):
    if not feature_status["economy"]: return await ctx.send("❌ Economy is disabled.")
    user_id = str(ctx.author.id)
    if user_id not in eco_data:
        eco_data[user_id] = 0
    reward = random.randint(100, 500)
    eco_data[user_id] += reward
    save_data()
    await ctx.send(f"💰 You received {reward} coins today!")

@bot.command()
async def balance(ctx):
    if not feature_status["economy"]: return await ctx.send("❌ Economy is disabled.")
    user_id = str(ctx.author.id)
    coins = eco_data.get(user_id, 0)
    await ctx.send(f"💼 {ctx.author.mention}, you have `{coins}` coins.")

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
            display = "🟢 Enabled" if status else "🔴 Disabled"
            if feature == "anime":
                display += " (Coming soon!)"
            embed.add_field(name=feature.replace("_", " ").title(), value=display, inline=False)
        embed.set_footer(text="Made by AASHIRWADGAMINGXD")
        await interaction.response.edit_message(embed=embed, view=DashboardView())

    class DashboardView(discord.ui.View):
        def add_toggle_button(self, label, key, style):
            @discord.ui.button(label=label, style=style)
            async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id not in ALLOWED_USERS:
                    return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
                feature_status[key] = not feature_status[key]
                await update_dashboard(interaction)
            setattr(DashboardView, f"toggle_{key}", toggle)

    view = DashboardView()
    features = {
        "welcome": discord.ButtonStyle.success,
        "maintenance": discord.ButtonStyle.danger,
        "reaction_roles": discord.ButtonStyle.secondary,
        "economy": discord.ButtonStyle.secondary,
        "auto_moderation": discord.ButtonStyle.secondary,
        "fun_commands": discord.ButtonStyle.secondary,
        "utility_tools": discord.ButtonStyle.secondary,
        "anime": discord.ButtonStyle.grey  # Anime coming soon
    }
    for name, style in features.items():
        view.add_toggle_button(name.replace("_", " ").title(), name, style)

    embed = discord.Embed(title="🛠 Bot Dashboard", description="Toggle bot features:", color=0x00ff00)
    for feature, status in feature_status.items():
        display = "🟢 Enabled" if status else "🔴 Disabled"
        if feature == "anime":
            display += " (Coming soon!)"
        embed.add_field(name=feature.replace("_", " ").title(), value=display, inline=False)
    embed.set_footer(text="Made by AASHIRWADGAMINGXD")

    await ctx.send(embed=embed, view=view)

# Start the bot
bot.run(os.getenv("TOKEN"))
