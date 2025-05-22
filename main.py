import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")
tree = bot.tree

OWNER_ID = 1217747285463531522
FRIEND_ID = 1244871880012206161
ALLOWED_USERS = [OWNER_ID, FRIEND_ID]
DASHBOARD_PASSWORD = "1Year"

BAD_WORDS = ["teri maa ki", "bsk", "mck", "lund", "bsp"]
AFK_DATA = {}

FEATURES_FILE = "features.json"

# Economy data stored in-memory for simplicity (you can expand to JSON persistence)
ECONOMY = {}
DAILY_COOLDOWN = timedelta(hours=24)

def load_features():
    try:
        with open(FEATURES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        # default feature states
        return {
            "welcome": False,
            "maintenance": False,
            "reaction_roles": True,
            "economy": False,
            "auto_moderation": True,
            "fun_commands": False,
            "utility_tools": False,
            "anime": True
        }

def save_features(features):
    with open(FEATURES_FILE, "w") as f:
        json.dump(features, f, indent=4)

feature_status = load_features()

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd)
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ---------------------
# Slash Commands
# ---------------------

@tree.command(name="help", description="Show the help menu")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Bot Help", color=discord.Color.green())
    embed.add_field(name="/help", value="Show this help menu", inline=False)
    embed.add_field(name="/rules", value="View server rules", inline=False)
    embed.add_field(name="/afk", value="Set yourself as AFK", inline=False)
    embed.add_field(name="/dashboard", value="Open bot dashboard (Owner only)", inline=False)
    embed.add_field(name="/ban", value="Ban a user (moderation)", inline=False)
    embed.add_field(name="/kick", value="Kick a user (moderation)", inline=False)
    embed.add_field(name="/mute", value="Mute a user for X minutes", inline=False)
    embed.add_field(name="/daily", value="Claim daily reward", inline=False)
    embed.add_field(name="/balance", value="Check your balance", inline=False)
    embed.add_field(name="/hunt", value="Go hunting for coins (fun)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="rules", description="Show server rules")
async def rules_command(interaction: discord.Interaction):
    rules = """
**⚠️ SERVER RULES ⚠️**
1. Be respectful — No harassment, hate speech, racism, etc.
2. No NSFW content.
3. No begging/spam/ads.
4. Use correct channels.
5. No harmful content.

|| By AashirwadGamingXD ||
"""
    await interaction.response.send_message(rules)

@tree.command(name="afk", description="Set yourself as AFK")
@app_commands.describe(reason="Why are you going AFK?")
async def afk_command(interaction: discord.Interaction, reason: str):
    AFK_DATA[interaction.user.id] = reason
    await interaction.response.send_message(f"✅ You are now AFK: {reason}", ephemeral=True)

# Moderation commands (owner+friend only)

def is_mod(interaction):
    return interaction.user.id in ALLOWED_USERS or interaction.user.guild_permissions.administrator

@tree.command(name="ban", description="Ban a user")
@app_commands.describe(user="User to ban", reason="Reason for ban (optional)")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    if not is_mod(interaction):
        return await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
    try:
        await user.ban(reason=reason)
        await interaction.response.send_message(f"✅ Banned {user} | Reason: {reason or 'No reason provided'}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to ban: {e}", ephemeral=True)

@tree.command(name="kick", description="Kick a user")
@app_commands.describe(user="User to kick", reason="Reason for kick (optional)")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = None):
    if not is_mod(interaction):
        return await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
    try:
        await user.kick(reason=reason)
        await interaction.response.send_message(f"✅ Kicked {user} | Reason: {reason or 'No reason provided'}")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to kick: {e}", ephemeral=True)

@tree.command(name="mute", description="Mute a user for given minutes")
@app_commands.describe(user="User to mute", minutes="Mute duration in minutes")
async def mute(interaction: discord.Interaction, user: discord.Member, minutes: int):
    if not is_mod(interaction):
        return await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
    mute_role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await interaction.guild.create_role(name="Muted")
        for ch in interaction.guild.channels:
            await ch.set_permissions(mute_role, send_messages=False, speak=False, add_reactions=False)
    try:
        await user.add_roles(mute_role, reason=f"Muted by {interaction.user} for {minutes} minutes")
        await interaction.response.send_message(f"✅ Muted {user} for {minutes} minutes")
        await asyncio.sleep(minutes * 60)
        await user.remove_roles(mute_role, reason="Mute expired")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to mute: {e}", ephemeral=True)

# Economy system

def get_balance(user_id):
    return ECONOMY.get(str(user_id), 0)

def add_balance(user_id, amount):
    ECONOMY[str(user_id)] = get_balance(user_id) + amount

# daily cooldown tracker in-memory
DAILY_USERS = {}

@tree.command(name="daily", description="Claim your daily reward (100 coins)")
async def daily(interaction: discord.Interaction):
    if not feature_status.get("economy", False):
        return await interaction.response.send_message("❌ Economy system is disabled.", ephemeral=True)

    last_claim = DAILY_USERS.get(interaction.user.id)
    now = datetime.utcnow()
    if last_claim and now - last_claim < DAILY_COOLDOWN:
        remaining = DAILY_COOLDOWN - (now - last_claim)
        hours = remaining.seconds // 3600
        minutes = (remaining.seconds % 3600) // 60
        return await interaction.response.send_message(f"⌛ You already claimed daily! Try again in {hours}h {minutes}m.", ephemeral=True)
    
    add_balance(interaction.user.id, 100)
    DAILY_USERS[interaction.user.id] = now
    await interaction.response.send_message("✅ You claimed your daily 100 coins!")

@tree.command(name="balance", description="Check your coin balance")
async def balance(interaction: discord.Interaction, user: discord.Member = None):
    if not feature_status.get("economy", False):
        return await interaction.response.send_message("❌ Economy system is disabled.", ephemeral=True)
    target = user or interaction.user
    bal = get_balance(target.id)
    await interaction.response.send_message(f"💰 {target.display_name} has {bal} coins.")

@tree.command(name="hunt", description="Go hunting to get coins")
async def hunt(interaction: discord.Interaction):
    if not feature_status.get("fun_commands", False):
        return await interaction.response.send_message("❌ Fun commands are disabled.", ephemeral=True)
    import random
    coins = random.randint(10, 100)
    add_balance(interaction.user.id, coins)
    await interaction.response.send_message(f"🏹 You went hunting and earned {coins} coins!")

# ========== Dashboard ==========

@tree.command(name="dashboard", description="Owner Dashboard - toggle features")
async def dashboard(interaction: discord.Interaction):
    if interaction.user.id not in ALLOWED_USERS:
        return await interaction.response.send_message("❌ You're not allowed to use this command.", ephemeral=True)

    await interaction.response.send_message("🔐 Please enter the dashboard password:", ephemeral=True)

    def check(m): return m.author.id == interaction.user.id and m.channel == interaction.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        if msg.content != DASHBOARD_PASSWORD:
            return await interaction.followup.send("❌ Incorrect password.", ephemeral=True)
    except asyncio.TimeoutError:
        return await interaction.followup.send("⌛ Timeout. Try again.", ephemeral=True)

    def build_embed():
        embed = discord.Embed(title="🛠 Bot Dashboard", color=0x3498db)
        for feat, enabled in feature_status.items():
            status = "🟢 ON" if enabled else "🔴 OFF"
            embed.add_field(name=feat.replace("_", " ").title(), value=status, inline=True)
        embed.set_footer(text="Made by AASHIRWADGAMINGXD")
        return embed

    class DashboardView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            for key in feature_status:
                style = discord.ButtonStyle.green if feature_status[key] else discord.ButtonStyle.red
                label = key.replace("_", " ").title()
                self.add_item(self.make_button(key, label, style))

        def make_button(self, key, label, style):
            button = discord.ui.Button(label=label, style=style)

            async def callback(inter: discord.Interaction):
                if inter.user.id not in ALLOWED_USERS:
                    return await inter.response.send_message("❌ Not authorized.", ephemeral=True)

                # Anime button special: assign role if toggled ON
                if key == "anime" and not feature_status[key]:
                    # Turning ON anime role feature
                    role = discord.utils.get(inter.guild.roles, name="Anime")
                    if not role:
                        role = await inter.guild.create_role(name="Anime")
                    member = inter.guild.get_member(inter.user.id)
                    if role not in member.roles:
                        await member.add_roles(role)
                        await inter.response.send_message("🎉 Anime role given!", ephemeral=True)
                    else:
                        await inter.response.send_message("🎉 Anime role already assigned!", ephemeral=True)
                    feature_status[key] = True
                else:
                    feature_status[key] = not feature_status[key]

                save_features(feature_status)
                await inter.response.edit_message(embed=build_embed(), view=DashboardView())

            button.callback = callback
            return button

    await interaction.followup.send(embed=build_embed(), view=DashboardView(), ephemeral=True)

# Auto moderation for bad words & mention timeout

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return

    # Auto moderation
    if feature_status.get("auto_moderation", False):
        lowered = message.content.lower()
        if any(bad_word in lowered for bad_word in BAD_WORDS):
            try:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, that word is not allowed here!", delete_after=5)
            except Exception:
                pass

        # Timeout if pinging @👑〢 「Founder」 role (name assumed exactly)
        if any(role.name == "👑〢 「Founder」" for role in message.role_mentions):
            timeout_duration = 60  # 1 minute timeout
            try:
                await message.author.timeout(duration=timeout_duration, reason="Pinged Founder role")
                await message.channel.send(f"{message.author.mention} has been timed out for pinging Founder.", delete_after=5)
            except Exception:
                pass

    # AFK check: notify if someone mentions an AFK user
    for user_id, reason in AFK_DATA.items():
        if message.mentions and any(u.id == user_id for u in message.mentions):
            await message.channel.send(f"{message.author.mention}, {bot.get_user(user_id)} is currently AFK: {reason}")

    # Remove AFK if AFK user speaks
    if message.author.id in AFK_DATA:
        AFK_DATA.pop(message.author.id)
        await message.channel.send(f"Welcome back {message.author.mention}, I removed your AFK.")

    await bot.process_commands(message)

bot.run(os.getenv("TOKEN"))
