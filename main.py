import discord
from discord.ext import commands, tasks
from discord.utils import get
import json
import asyncio
import random

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

OWNER_ID = 1217747285463531522
FRIEND_ID = 1244871880012206161
ALLOWED_USERS = [OWNER_ID, FRIEND_ID]

FEATURES_FILE = "features.json"
ECONOMY_FILE = "economy.json"
WARNINGS_FILE = "warnings.json"
TICKETS_FILE = "tickets.json"

default_features = {
    "welcome": True,
    "maintenance": False,
    "reaction_roles": True,
    "economy": True,
    "auto_moderation": True,
    "fun_commands": True,
    "utility_tools": True,
    "anime": True,
    "tickets": True,
}

feature_status = {}
eco_data = {}
warn_data = {}
tickets = {}

# Load/save helpers
def load_json(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default.copy()

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def save_all():
    save_json(FEATURES_FILE, feature_status)
    save_json(ECONOMY_FILE, eco_data)
    save_json(WARNINGS_FILE, warn_data)
    save_json(TICKETS_FILE, tickets)

# Initialize data
feature_status = load_json(FEATURES_FILE, default_features)
eco_data = load_json(ECONOMY_FILE, {})
warn_data = load_json(WARNINGS_FILE, {})
tickets = load_json(TICKETS_FILE, {})

# Bad words for auto moderation
bad_words = ["teri maa ki", "bsk", "mck", "lund", "bsp", "bc", "mc", "bsdk", "madarchod", "bhosdike" , "https://discord.gg"]
vc_bad_words = ["https://discord.gg"]

RULES_TEXT = """
**⚠️ SERVER RULES ⚠️**
1. Be respectful — No harassment, hate speech, racism, false rumors, sexism, trolling or drama.
2. No NSFW — Don’t post NSFW content anywhere.
3. Don’t beg — No begging for nitro, roles, etc.
4. Don’t spam — No message spam, emoji floods, or nickname spam.
5. Use correct channels.
6. No illegal content — Including grey market or pirated stuff.
7. Listen to staff — Respect their decisions.
8. Follow Discord’s Community Guidelines and Terms of Service.
9. No self-promo or advertising.
10. Don’t abuse or use bad words in VC.
11. No Discord crash GIFs or anything harmful.
12. Avoid religious/family condition discussions (except well wishes).
Caught breaking rules? Screenshot & report to staff.
**🚫 BREAKING RULES = BAN | KICK**
||  ||
"""

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd)
    print(f"✅ Bot online as {bot.user}")

@bot.event
async def on_member_join(member):
    if feature_status.get("welcome", False):
        channel = get(member.guild.text_channels, name="general")
        if channel:
            await channel.send(f"👋 Welcome {member.mention}!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Maintenance blocks commands except for owner/friend
    if feature_status.get("maintenance", False) and message.author.id not in ALLOWED_USERS:
        return

    if feature_status.get("auto_moderation", False):
        msg = message.content.lower()
        for bad_word in bad_words:
            if bad_word in msg:
                try:
                    await message.delete()
                    await message.channel.send(f"🚫 {message.author.mention}, watch your language!")
                except:
                    pass
                return
        # If message is in voice channel (unlikely, but for safety)
        if message.channel.type == discord.ChannelType.voice:
            for bad_word in vc_bad_words:
                if bad_word in msg:
                    try:
                        await message.delete()
                        await message.channel.send(f"🚫 {message.author.mention}, abusive language in VC not allowed.")
                    except:
                        pass
                    return
    await bot.process_commands(message)

# === Moderation commands ===
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if feature_status.get("maintenance", False):
        return await ctx.send("Bot is in maintenance.")
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member} | Reason: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if feature_status.get("maintenance", False):
        return await ctx.send("Bot is in maintenance.")
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member} | Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    if feature_status.get("maintenance", False):
        return await ctx.send("Bot is in maintenance.")
    muted_role = get(ctx.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)
    await member.add_roles(muted_role)
    await ctx.send(f"🔇 Muted {member}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    if feature_status.get("maintenance", False):
        return await ctx.send("Bot is in maintenance.")
    muted_role = get(ctx.guild.roles, name="Muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f"🔊 Unmuted {member}")
    else:
        await ctx.send(f"{member} is not muted.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    if feature_status.get("maintenance", False):
        return await ctx.send("Bot is in maintenance.")
    await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"🧹 Cleared {amount} messages.", delete_after=5)

# Warn system
@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    if feature_status.get("maintenance", False):
        return await ctx.send("Bot is in maintenance.")
    user_id = str(member.id)
    if user_id not in warn_data:
        warn_data[user_id] = []
    warn_data[user_id].append(reason)
    save_json(WARNINGS_FILE, warn_data)
    await ctx.send(f"⚠️ Warned {member} for: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warnings(ctx, member: discord.Member):
    user_id = str(member.id)
    warns = warn_data.get(user_id, [])
    if not warns:
        await ctx.send(f"{member} has no warnings.")
    else:
        embed = discord.Embed(title=f"Warnings for {member}", color=discord.Color.orange())
        for i, w in enumerate(warns, 1):
            embed.add_field(name=f"Warning #{i}", value=w, inline=False)
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def clearwarns(ctx, member: discord.Member):
    user_id = str(member.id)
    if user_id in warn_data:
        warn_data.pop(user_id)
        save_json(WARNINGS_FILE, warn_data)
        await ctx.send(f"Cleared all warnings for {member}")
    else:
        await ctx.send(f"{member} has no warnings.")

# === Economy commands ===
@bot.command()
async def balance(ctx, member: discord.Member = None):
    if not feature_status.get("economy", False):
        return await ctx.send("Economy system is disabled.")
    user = member or ctx.author
    bal = eco_data.get(str(user.id), 0)
    await ctx.send(f"💰 {user.display_name} has {bal} coins.")

@bot.command()
async def daily(ctx):
    if not feature_status.get("economy", False):
        return await ctx.send("Economy system is disabled.")
    user_id = str(ctx.author.id)
    import time
    now = int(time.time())
    last_daily = eco_data.get(f"{user_id}_lastdaily", 0)
    if now - last_daily < 86400:  # 24 hours cooldown
        await ctx.send("You have already claimed your daily reward today! Come back later.")
        return
    eco_data[user_id] = eco_data.get(user_id, 0) + 100
    eco_data[f"{user_id}_lastdaily"] = now
    save_json(ECONOMY_FILE, eco_data)
    await ctx.send(f"🎉 You claimed your daily 100 coins! Your balance is now {eco_data[user_id]} coins.")

# === Fun commands ===
@bot.command()
async def hunt(ctx):
    if not feature_status.get("fun_commands", False):
        return await ctx.send("Fun commands are disabled.")
    animals = ["rabbit", "fox", "deer", "bear"]
    catch = random.choice(animals)
    user_id = str(ctx.author.id)
    # For simplicity, store hunted animals count
    zoo_data = load_json("zoo.json", {})
    zoo_data.setdefault(user_id, {})
    zoo_data[user_id][catch] = zoo_data[user_id].get(catch, 0) + 1
    save_json("zoo.json", zoo_data)
    await ctx.send(f"🏹 You hunted a {catch}! Added to your zoo.")

@bot.command()
async def zoo(ctx):
    if not feature_status.get("fun_commands", False):
        return await ctx.send("Fun commands are disabled.")
    user_id = str(ctx.author.id)
    zoo_data = load_json("zoo.json", {})
    animals = zoo_data.get(user_id, {})
    if not animals:
        await ctx.send("Your zoo is empty. Use `!hunt` to catch animals!")
        return
    embed = discord.Embed(title=f"{ctx.author.display_name}'s Zoo", color=discord.Color.green())
    for animal, count in animals.items():
        embed.add_field(name=animal.capitalize(), value=str(count), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def inventory(ctx):
    # Could show economy items, here simplified
    if not feature_status.get("economy", False):
        return await ctx.send("Economy system is disabled.")
    user_id = str(ctx.author.id)
    bal = eco_data.get(user_id, 0)
    await ctx.send(f"Your inventory:\nCoins: {bal}\nUse economy commands to expand.")

# === Reaction role setup (simplified) ===
@bot.command()
@commands.has_permissions(manage_roles=True)
async def reactionrole(ctx, message_id: int, emoji: str, role: discord.Role):
    if not feature_status.get("reaction_roles", False):
        return await ctx.send("Reaction roles are disabled.")
    try:
        msg = await ctx.channel.fetch_message(message_id)
        await msg.add_reaction(emoji)
    except:
        return await ctx.send("Message not found or invalid emoji.")
    # Save reaction roles config to a file (simplified here)
    rr_data = load_json("reaction_roles.json", {})
    rr_data[str(message_id)] = {"emoji": emoji, "role_id": role.id}
    save_json("reaction_roles.json", rr_data)
    await ctx.send(f"Reaction role setup: React with {emoji} to get {role.name}")

@bot.event
async def on_raw_reaction_add(payload):
    if not feature_status.get("reaction_roles", False):
        return
    rr_data = load_json("reaction_roles.json", {})
    data = rr_data.get(str(payload.message_id))
    if not data:
        return
    if str(payload.emoji) == data["emoji"]:
        guild = bot.get_guild(payload.guild_id)
        role = get(guild.roles, id=data["role_id"])
        member = guild.get_member(payload.user_id)
        if role and member and not member.bot:
            await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    if not feature_status.get("reaction_roles", False):
        return
    rr_data = load_json("reaction_roles.json", {})
    data = rr_data.get(str(payload.message_id))
    if not data:
        return
    if str(payload.emoji) == data["emoji"]:
        guild = bot.get_guild(payload.guild_id)
        role = get(guild.roles, id=data["role_id"])
        member = guild.get_member(payload.user_id)
        if role and member and not member.bot:
            await member.remove_roles(role)

# === Ticket system ===
@bot.command()
async def ticket(ctx, action: str = None):
    if not feature_status.get("tickets", False):
        return await ctx.send("Tickets are disabled.")
    user_id = str(ctx.author.id)
    guild = ctx.guild
    if action == "open":
        if user_id in tickets:
            return await ctx.send("You already have an open ticket!")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ticket_channel = await guild.create_text_channel(f"ticket-{ctx.author.name}", overwrites=overwrites)
        tickets[user_id] = ticket_channel.id
        save_json(TICKETS_FILE, tickets)
        await ctx.send(f"🎫 Ticket opened: {ticket_channel.mention}")
    elif action == "close":
        if user_id not in tickets:
            return await ctx.send("You have no open tickets.")
        channel_id = tickets.pop(user_id)
        save_json(TICKETS_FILE, tickets)
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.delete()
        await ctx.send("Ticket closed and channel deleted.")
    else:
        await ctx.send("Usage: `!ticket open` or `!ticket close`")

# === Dashboard for Owner and Friend only ===
class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for feat in feature_status:
            label = f"{feat.capitalize()} [{'ON' if feature_status[feat] else 'OFF'}]"
            style = discord.ButtonStyle.green if feature_status[feat] else discord.ButtonStyle.red
            self.add_item(DashboardButton(feat, label, style))

class DashboardButton(discord.ui.Button):
    def __init__(self, feature_key, label, style):
        super().__init__(label=label, style=style)
        self.feature_key = feature_key

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id not in ALLOWED_USERS:
            await interaction.response.send_message("You are not authorized to use this dashboard.", ephemeral=True)
            return
        # Toggle feature
        current = feature_status.get(self.feature_key, False)
        feature_status[self.feature_key] = not current
        save_json(FEATURES_FILE, feature_status)
        # Update buttons label/colors
        self.view.update_buttons()
        await interaction.response.edit_message(view=self.view)
        await interaction.followup.send(f"{self.feature_key.capitalize()} set to {'ON' if feature_status[self.feature_key] else 'OFF'}", ephemeral=True)

@bot.command()
async def dashboard(ctx):
    if ctx.author.id not in ALLOWED_USERS:
        return await ctx.send("You are not authorized to use the dashboard.")
    try:
        dm = await ctx.author.create_dm()
        view = DashboardView()
        await dm.send("Dashboard: Toggle bot features by clicking buttons.", view=view)
        await ctx.send("Dashboard sent to your DMs.")
    except Exception as e:
        await ctx.send("Failed to send dashboard DM. Enable your DMs.")

# === Help command ===
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Help - Commands", color=discord.Color.blue())
    embed.add_field(name="Moderation",
                    value="!ban @user [reason]\n!kick @user [reason]\n!mute @user\n!unmute @user\n!warn @user [reason]\n!warnings @user\n!clearwarns @user\n!clear [number]",
                    inline=False)
    embed.add_field(name="Economy",
                    value="!balance [user]\n!daily\n!inventory",
                    inline=False)
    embed.add_field(name="Fun",
                    value="!hunt\n!zoo",
                    inline=False)
    embed.add_field(name="Reaction Roles",
                    value="!reactionrole <message_id> <emoji> <role>",
                    inline=False)
    embed.add_field(name="Tickets",
                    value="!ticket open\n!ticket close",
                    inline=False)
    embed.add_field(name="Dashboard",
                    value="!dashboard (Owner & Friend only)",
                    inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def rules(ctx):
    await ctx.send(RULES_TEXT)

# === Error handling ===
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 You don't have permission to run this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("🚫 Missing required argument.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # ignore unknown commands silently
    else:
        await ctx.send(f"Error: {error}")

# Run the bot
import os
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
