import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
import json
import asyncio
import random
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
# Remove default help command to keep your own if needed
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

feature_status = load_json(FEATURES_FILE, default_features)
eco_data = load_json(ECONOMY_FILE, {})
warn_data = load_json(WARNINGS_FILE, {})
tickets = load_json(TICKETS_FILE, {})

bad_words = ["teri maa ki", "bsk", "mck", "lund", "bsp", "bc", "mc", "bsdk", "madarchod", "bhosdike", "https://discord.gg"]
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
    # Sync slash commands globally (or for guilds you want)
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

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

# Moderation slash commands
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.command(name="ban", description="Ban a user")
@app_commands.describe(user="User to ban", reason="Reason for ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message("Bot is in maintenance.", ephemeral=True)
    await user.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {user} | Reason: {reason}")

@app_commands.checks.has_permissions(kick_members=True)
@app_commands.command(name="kick", description="Kick a user")
@app_commands.describe(user="User to kick", reason="Reason for kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message("Bot is in maintenance.", ephemeral=True)
    await user.kick(reason=reason)
    await interaction.response.send_message(f"👢 Kicked {user} | Reason: {reason}")

@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.command(name="mute", description="Mute a user")
@app_commands.describe(user="User to mute")
async def mute(interaction: discord.Interaction, user: discord.Member):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message("Bot is in maintenance.", ephemeral=True)
    muted_role = get(interaction.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await interaction.guild.create_role(name="Muted")
        for channel in interaction.guild.channels:
            await channel.set_permissions(muted_role, speak=False, send_messages=False)
    await user.add_roles(muted_role)
    await interaction.response.send_message(f"🔇 Muted {user}")

@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.command(name="unmute", description="Unmute a user")
@app_commands.describe(user="User to unmute")
async def unmute(interaction: discord.Interaction, user: discord.Member):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message("Bot is in maintenance.", ephemeral=True)
    muted_role = get(interaction.guild.roles, name="Muted")
    if muted_role and muted_role in user.roles:
        await user.remove_roles(muted_role)
        await interaction.response.send_message(f"🔊 Unmuted {user}")
    else:
        await interaction.response.send_message(f"{user} is not muted.")

@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.command(name="clear", description="Clear messages")
@app_commands.describe(amount="Number of messages to delete (max 100)")
async def clear(interaction: discord.Interaction, amount: int = 10):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message("Bot is in maintenance.", ephemeral=True)
    if amount < 1 or amount > 100:
        return await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount+1)
    await interaction.response.send_message(f"🧹 Deleted {len(deleted)-1} messages.", ephemeral=True)

# Economy slash commands
@app_commands.command(name="balance", description="Show your coin balance")
async def balance(interaction: discord.Interaction):
    if not feature_status.get("economy", False):
        return await interaction.response.send_message("Economy is disabled.", ephemeral=True)
    user_id = str(interaction.user.id)
    bal = eco_data.get(user_id, 0)
    await interaction.response.send_message(f"💰 {interaction.user.mention}, your balance is {bal} coins.")

@app_commands.command(name="daily", description="Claim your daily coins")
async def daily(interaction: discord.Interaction):
    if not feature_status.get("economy", False):
        return await interaction.response.send_message("Economy is disabled.", ephemeral=True)
    user_id = str(interaction.user.id)
    if user_id not in eco_data:
        eco_data[user_id] = 0
    # For simplicity, no cooldown implemented here (add if needed)
    eco_data[user_id] += 100
    save_json(ECONOMY_FILE, eco_data)
    await interaction.response.send_message(f"🎉 {interaction.user.mention}, you claimed 100 coins! Your balance is now {eco_data[user_id]}.")

@app_commands.command(name="pay", description="Pay coins to another user")
@app_commands.describe(user="User to pay", amount="Amount of coins")
async def pay(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not feature_status.get("economy", False):
        return await interaction.response.send_message("Economy is disabled.", ephemeral=True)
    if amount < 1:
        return await interaction.response.send_message("Amount must be positive.", ephemeral=True)
    payer = str(interaction.user.id)
    payee = str(user.id)
    if eco_data.get(payer, 0) < amount:
        return await interaction.response.send_message("You don't have enough coins.", ephemeral=True)
    eco_data[payer] = eco_data.get(payer, 0) - amount
    eco_data[payee] = eco_data.get(payee, 0) + amount
    save_json(ECONOMY_FILE, eco_data)
    await interaction.response.send_message(f"💸 {interaction.user.mention} paid {amount} coins to {user.mention}.")

# Ticket system with buttons
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket"))

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not feature_status.get("tickets", False):
            return await interaction.response.send_message("Ticket system is disabled.", ephemeral=True)
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        ticket_number = len(tickets) + 1
        channel_name = f"ticket-{ticket_number}"
        existing_channel = get(guild.channels, name=channel_name)
        if existing_channel:
            return await interaction.response.send_message("You already have an open ticket.", ephemeral=True)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, topic=f"Ticket for {interaction.user}")
        tickets[str(channel.id)] = str(interaction.user.id)
        save_json(TICKETS_FILE, tickets)
        await interaction.response.send_message(f"🎫 Ticket created: {channel.mention}", ephemeral=True)

@app_commands.command(name="ticket", description="Manage tickets")
@app_commands.describe(action="Create or close a ticket")
async def ticket(interaction: discord.Interaction, action: str):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message("Bot is in maintenance.", ephemeral=True)
    if not feature_status.get("tickets", False):
        return await interaction.response.send_message("Ticket system is disabled.", ephemeral=True)
    action = action.lower()
    if action == "create":
        view = TicketView()
        await interaction.response.send_message("Click below to create a ticket.", view=view, ephemeral=True)
    elif action == "close":
        channel_id = str(interaction.channel.id)
        if channel_id in tickets:
            del tickets[channel_id]
            save_json(TICKETS_FILE, tickets)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid action. Use create or close.", ephemeral=True)

# Dashboard with buttons to toggle features (owner + friend only)
class DashboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for feat in feature_status:
            self.add_item(FeatureToggleButton(feat))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in ALLOWED_USERS:
            await interaction.response.send_message("You can't use this dashboard.", ephemeral=True)
            return False
        return True

class FeatureToggleButton(discord.ui.Button):
    def __init__(self, feature_name):
        status = feature_status.get(feature_name, False)
        super().__init__(
            label=f"{feature_name.capitalize()} [{'ON' if status else 'OFF'}]",
            style=discord.ButtonStyle.green if status else discord.ButtonStyle.red,
            custom_id=feature_name,
        )

    async def callback(self, interaction: discord.Interaction):
        feat = self.custom_id
        feature_status[feat] = not feature_status[feat]
        save_json(FEATURES_FILE, feature_status)
        self.label = f"{feat.capitalize()} [{'ON' if feature_status[feat] else 'OFF'}]"
        self.style = discord.ButtonStyle.green if feature_status[feat] else discord.ButtonStyle.red
        await interaction.response.edit_message(view=self.view)

@app_commands.command(name="dashboard", description="Owner-only feature toggle dashboard")
async def dashboard(interaction: discord.Interaction):
    if interaction.user.id not in ALLOWED_USERS:
        return await interaction.response.send_message("You can't use this dashboard.", ephemeral=True)
    view = DashboardView()
    await interaction.response.send_message("Feature toggle dashboard:", view=view, ephemeral=True)

# Anime role command
@app_commands.command(name="anime", description="Get Anime role")
async def anime(interaction: discord.Interaction):
    if not feature_status.get("anime", False):
        return await interaction.response.send_message("Anime feature is disabled.", ephemeral=True)
    role = get(interaction.guild.roles, name="Anime")
    if not role:
        role = await interaction.guild.create_role(name="Anime")
    if role in interaction.user.roles:
        await interaction.response.send_message("You already have the Anime role.", ephemeral=True)
    else:
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Anime role added!", ephemeral=True)

# Help command as slash command
@app_commands.command(name="help", description="Show help message")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="Bot Commands", color=discord.Color.purple())
    embed.add_field(name="/ban [user] [reason]", value="Ban a user (moderator only).", inline=False)
    embed.add_field(name="/kick [user] [reason]", value="Kick a user (moderator only).", inline=False)
    embed.add_field(name="/mute [user]", value="Mute a user (moderator only).", inline=False)
    embed.add_field(name="/unmute [user]", value="Unmute a user (moderator only).", inline=False)
    embed.add_field(name="/clear [amount]", value="Clear messages (moderator only).", inline=False)
    embed.add_field(name="/balance", value="Show your balance.", inline=False)
    embed.add_field(name="/daily", value="Claim daily coins.", inline=False)
    embed.add_field(name="/pay [user] [amount]", value="Pay coins to a user.", inline=False)
    embed.add_field(name="/ticket [create/close]", value="Create or close a ticket.", inline=False)
    embed.add_field(name="/dashboard", value="Owner-only feature toggle dashboard.", inline=False)
    embed.add_field(name="/anime", value="Get Anime role.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.tree.add_command(ban)
bot.tree.add_command(kick)
bot.tree.add_command(mute)
bot.tree.add_command(unmute)
bot.tree.add_command(clear)
bot.tree.add_command(balance)
bot.tree.add_command(daily)
bot.tree.add_command(pay)
bot.tree.add_command(ticket)
bot.tree.add_command(dashboard)
bot.tree.add_command(anime)
bot.tree.add_command(help_command)

bot.run(os.getenv("TOKEN"))
