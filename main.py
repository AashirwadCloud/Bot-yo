import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
import json
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

OWNER_ID = 1217747285463531522
FRIEND_ID =  78363839376373
ALLOWED_USERS = [OWNER_ID, FRIEND_ID]

FEATURES_FILE = "features.json"
feature_status = {}

default_features = {
    "welcome": True,
    "maintenance": False,
    "reaction_roles": True,
    "auto_moderation": True,
    "fun_commands": True,
    "utility_tools": True,
    "anime": True,
    "tickets": True,
}

def load_json(file, default):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except:
        return default.copy()

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

feature_status = load_json(FEATURES_FILE, default_features)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd)
    print(f"✅ Bot online as {bot.user}")
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
    bad_words = ["teri maa ki", "bsk", "mck", "lund", "bsp", "bc", "mc", "bsdk", "madarchod", "bhosdike", "https://discord.gg"]
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

# --- Moderation commands ---

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
            await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=False)
    await user.add_roles(muted_role)
    await interaction.response.send_message(f"🔇 {user} has been muted.")

@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.command(name="unmute", description="Unmute a user")
@app_commands.describe(user="User to unmute")
async def unmute(interaction: discord.Interaction, user: discord.Member):
    muted_role = get(interaction.guild.roles, name="Muted")
    if muted_role in user.roles:
        await user.remove_roles(muted_role)
        await interaction.response.send_message(f"🔊 {user} has been unmuted.")
    else:
        await interaction.response.send_message(f"{user} is not muted.", ephemeral=True)

@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.command(name="clear", description="Clear messages")
@app_commands.describe(amount="Number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if amount < 1:
        return await interaction.response.send_message("Amount must be positive.", ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.response.send_message(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)

# --- Ticket system ---

tickets = {}

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
        channel_name = f"ticket-{interaction.user.name}"
        existing = get(guild.channels, name=channel_name)
        if existing:
            return await interaction.response.send_message(f"You already have an open ticket: {existing.mention}", ephemeral=True)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, topic=f"Ticket for {interaction.user}")
        tickets[str(channel.id)] = str(interaction.user.id)
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
        if channel_id in tickets and tickets[channel_id] == str(interaction.user.id):
            del tickets[channel_id]
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("This is not your ticket or no ticket found here.", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid action. Use create or close.", ephemeral=True)

# --- Dashboard ---

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

# --- Anime role ---

@app_commands.command(name="anime", description="Get Anime role")
async def anime(interaction: discord.Interaction):
    if not feature_status.get("anime", False):
        return await interaction.response.send_message"", ephemeral=True)
    role = get(interaction.guild.roles, name="Anime")
    if not role:
        role = await interaction.guild.create_role(name="Anime")
    if role in interaction.user.roles:
        await interaction.response.send_message("You already have the Anime role.", ephemeral=True)
    else:
        await interaction.user.add_roles(role)
        await interaction.response.send_message("Anime role added!", ephemeral=True)

# --- Reaction Role Management ---

reaction_roles = {}  # {message_id: {emoji: role_id}}

REACTION_ROLES_FILE = "reaction_roles.json"

def load_reaction_roles():
    global reaction_roles
    try:
        with open(REACTION_ROLES_FILE, "r") as f:
            reaction_roles = json.load(f)
    except:
        reaction_roles = {}

def save_reaction_roles():
    with open(REACTION_ROLES_FILE, "w") as f:
        json.dump(reaction_roles, f, indent=4)

load_reaction_roles()

@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.command(name="reactionrole_add", description="Add reaction role to a message")
@app_commands.describe(message_id="Message ID to attach reaction role", emoji="Emoji for reaction", role="Role to assign")
async def reactionrole_add(interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):
    if not feature_status.get("reaction_roles", False):
        return await interaction.response.send_message("Reaction roles feature is disabled.", ephemeral=True)
    try:
        channel = interaction.channel
        message = await channel.fetch_message(int(message_id))
    except Exception:
        return await interaction.response.send_message("Message not found in this channel.", ephemeral=True)

    # Add reaction to message
    try:
        await message.add_reaction(emoji)
    except Exception as e:
        return await interaction.response.send_message(f"Failed to add reaction: {e}", ephemeral=True)

    # Save reaction role mapping
    str_msg_id = str(message.id)
    if str_msg_id not in reaction_roles:
        reaction_roles[str_msg_id] = {}
    reaction_roles[str_msg_id][emoji] = role.id
    save_reaction_roles()

    await interaction.response.send_message(f"Reaction role set: React with {emoji} to get the {role.name} role.")

@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.command(name="reactionrole_remove", description="Remove reaction role from a message")
@app_commands.describe(message_id="Message ID", emoji="Reaction to remove")
async def reactionrole_remove(interaction: discord.Interaction, message_id: str, emoji: str):
    if not feature_status.get("reaction_roles", False):
        return await interaction.response.send_message("Reaction roles feature is disabled.", ephemeral=True)

    str_msg_id = str(message_id)
    if str_msg_id not in reaction_roles or emoji not in reaction_roles[str_msg_id]:
        return await interaction.response.send_message("That reaction role mapping does not exist.", ephemeral=True)

    del reaction_roles[str_msg_id][emoji]
    if not reaction_roles[str_msg_id]:
        del reaction_roles[str_msg_id]
    save_reaction_roles()

    await interaction.response.send_message(f"Removed reaction role for {emoji} on message {message_id}.")

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if feature_status.get("maintenance", False):
        return
    if not feature_status.get("reaction_roles", False):
        return
    if payload.user_id == bot.user.id:
        return

    str_msg_id = str(payload.message_id)
    if str_msg_id in reaction_roles:
        emoji = str(payload.emoji)
        if emoji in reaction_roles[str_msg_id]:
            guild = bot.get_guild(payload.guild_id)
            if guild:
                role_id = reaction_roles[str_msg_id][emoji]
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                if role and member:
                    try:
                        await member.add_roles(role)
                    except:
                        pass

@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if feature_status.get("maintenance", False):
        return
    if not feature_status.get("reaction_roles", False):
        return
    if payload.user_id == bot.user.id:
        return

    str_msg_id = str(payload.message_id)
    if str_msg_id in reaction_roles:
        emoji = str(payload.emoji)
        if emoji in reaction_roles[str_msg_id]:
            guild = bot.get_guild(payload.guild_id)
            if guild:
                role_id = reaction_roles[str_msg_id][emoji]
                role = guild.get_role(role_id)
                member = guild.get_member(payload.user_id)
                if role and member:
                    try:
                        await member.remove_roles(role)
                    except:
                        pass

# Run the bot
import os

bot.tree.add_command(ban)
bot.tree.add_command(kick)
bot.tree.add_command(mute)
bot.tree.add_command(unmute)
bot.tree.add_command(clear)
bot.tree.add_command(ticket)
bot.tree.add_command(dashboard)
bot.tree.add_command(anime)
bot.tree.add_command(reactionrole_add)
bot.tree.add_command(reactionrole_remove)

bot.run(os.getenv("TOKEN"))
