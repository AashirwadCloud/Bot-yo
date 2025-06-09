import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get
import json
import asyncio
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command("help")

OWNER_ID = 1217747285463531522
FRIEND_ID = 1244871880012206161
ALLOWED_USERS = [OWNER_ID, FRIEND_ID]

FEATURES_FILE = "features.json"
RULES_FILE = "rules.json"
feature_status = {}
rules_data = {}

default_features = {
    "welcome": True,
    "maintenance": False,
    "reaction_roles": True,
    "auto_moderation": True,
    "fun_commands": True,
    "utility_tools": True,
    "anime": True,
    "tickets": True,
    "maintenance_message": "🚧 The bot is under maintenance. Please try again later."
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
rules_data = load_json(RULES_FILE, {"rules": "No rules set yet."})

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd)
    print(f"✅ Bot online as {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced.")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

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
        try:
            await message.channel.send(feature_status.get("maintenance_message", "🚧 Maintenance mode is on."))
        except:
            pass
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

    await bot.process_commands(message)
# --- Moderation Commands ---

@app_commands.checks.has_permissions(ban_members=True)
@app_commands.command(name="ban", description="Ban a user")
@app_commands.describe(user="User to ban", reason="Reason for ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message(feature_status["maintenance_message"], ephemeral=True)
    await user.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {user} | Reason: {reason}")

@app_commands.checks.has_permissions(kick_members=True)
@app_commands.command(name="kick", description="Kick a user")
@app_commands.describe(user="User to kick", reason="Reason for kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message(feature_status["maintenance_message"], ephemeral=True)
    await user.kick(reason=reason)
    await interaction.response.send_message(f"👢 Kicked {user} | Reason: {reason}")

@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.command(name="mute", description="Mute a user")
@app_commands.describe(user="User to mute")
async def mute(interaction: discord.Interaction, user: discord.Member):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message(feature_status["maintenance_message"], ephemeral=True)
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

# --- Text Command: Set & Show Rules ---

@bot.command(name="setrules")
@commands.is_owner()
async def set_rules(ctx, *, rules: str):
    rules_data["rules"] = rules
    save_json(RULES_FILE, rules_data)
    await ctx.send("✅ Rules have been updated.")

@bot.command(name="rules")
async def show_rules(ctx):
    await ctx.send(f"📜 Server Rules:\n{rules_data.get('rules', 'No rules set.')}")

# --- Text Command: Set Maintenance Message ---

@bot.command(name="setmaintmsg")
@commands.is_owner()
async def set_maint_msg(ctx, *, message: str):
    feature_status["maintenance_message"] = message
    save_json(FEATURES_FILE, feature_status)
    await ctx.send("✅ Maintenance message updated.")

# --- Slash Command: Announce ---

@app_commands.command(name="announce", description="Make a server-wide announcement")
@app_commands.describe(message="The announcement message")
async def announce(interaction: discord.Interaction, message: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ You need administrator permissions to use this.", ephemeral=True)
    for channel in interaction.guild.text_channels:
        try:
            await channel.send(f"📢 Announcement:\n{message}")
            break
        except:
            continue
    await interaction.response.send_message("✅ Announcement sent!", ephemeral=True)

bot.tree.add_command(announce)

# --- Ticket System ---

tickets = {}

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not feature_status.get("tickets", False):
            return await interaction.response.send_message("🎟️ Ticket system is disabled.", ephemeral=True)

        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        channel_name = f"ticket-{interaction.user.name}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            return await interaction.response.send_message("❗ You already have a ticket open.", ephemeral=True)

        ticket_channel = await guild.create_text_channel(channel_name, overwrites=overwrites)
        await ticket_channel.send(f"{interaction.user.mention} Thank you for creating a ticket. How can we help?")
        await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)
# --- Close Ticket Command ---

@bot.command(name="close")
async def close_ticket(ctx):
    if not ctx.channel.name.startswith("ticket-"):
        return await ctx.send("❌ This is not a ticket channel.")
    await ctx.send("📌 Ticket will be closed in 5 seconds.")
    await asyncio.sleep(5)
    await ctx.channel.delete()

# --- Help Command ---

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(title="📘 Help - All Commands", color=discord.Color.blurple())
    embed.add_field(name="🔧 Moderation", value="`/ban`, `/kick`, `/mute`, `/unmute`, `/clear`", inline=False)
    embed.add_field(name="🎟️ Tickets", value="`!close`", inline=False)
    embed.add_field(name="🛠️ Utility", value="`/announce`, `!setmaintmsg`, `!setrules`, `!rules`", inline=False)
    embed.add_field(name="⚙️ Owner Only", value="`!setmaintmsg`, `!setrules`", inline=False)
    embed.add_field(name="💡 Note", value="Slash commands must be typed using `/`, not `!`.", inline=False)
    embed.set_footer(text="Made by AASHIRWADGAMINGXD")
    await ctx.send(embed=embed)

# --- Error Handler ---

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Missing required argument.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Unknown command. Use `!help` to see available commands.")
    elif isinstance(error, commands.NotOwner):
        await ctx.send("❌ This command is owner-only.")
    else:
        await ctx.send("⚠️ An unexpected error occurred.")
        print(f"Error in command {ctx.command}: {error}")

# --- Run the Bot ---

import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("TOKEN")  # Use your .env for security or hardcode if testing

if not TOKEN:
    print("❌ Bot token not found in environment.")
else:
    bot.run(TOKEN)
