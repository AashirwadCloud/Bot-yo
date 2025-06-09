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
feature_status = {}

default_features = {
    "welcome": True,
    "maintenance": False,
    "reaction_roles": True,
    "auto_moderation": True,
    "fun_commands": True,
    "utility_tools": True,
    "anime": True,
    "tickets": True
}

# Load/save features
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

# Maintenance message
maintenance_message = "Bot is under maintenance."

# --- Events ---

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
        return await message.channel.send(maintenance_message)
    if feature_status.get("auto_moderation", False):
        bad_words = ["teri maa ki", "bsk", "mck", "lund", "bsp", "bc", "mc", "bsdk", "madarchod", "bhosdike", "https://discord.gg"]
        msg = message.content.lower()
        for word in bad_words:
            if word in msg:
                try:
                    await message.delete()
                    await message.channel.send(f"🚫 {message.author.mention}, watch your language!")
                except:
                    pass
                return
    await bot.process_commands(message)

# --- Slash Commands ---

@app_commands.checks.has_permissions(ban_members=True)
@app_commands.command(name="ban", description="Ban a user")
@app_commands.describe(user="User to ban", reason="Reason for ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message(maintenance_message, ephemeral=True)
    await user.ban(reason=reason)
    await interaction.response.send_message(f"🔨 Banned {user} | Reason: {reason}")

@app_commands.checks.has_permissions(kick_members=True)
@app_commands.command(name="kick", description="Kick a user")
@app_commands.describe(user="User to kick", reason="Reason for kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message(maintenance_message, ephemeral=True)
    await user.kick(reason=reason)
    await interaction.response.send_message(f"👢 Kicked {user} | Reason: {reason}")

@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.command(name="mute", description="Mute a user")
@app_commands.describe(user="User to mute")
async def mute(interaction: discord.Interaction, user: discord.Member):
    if feature_status.get("maintenance", False):
        return await interaction.response.send_message(maintenance_message, ephemeral=True)
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

@app_commands.command(name="announce", description="Make a server-wide announcement")
@app_commands.describe(message="The message to announce")
async def announce(interaction: discord.Interaction, message: str):
    if interaction.user.id not in ALLOWED_USERS:
        return await interaction.response.send_message("You are not allowed to use this.", ephemeral=True)
    for channel in interaction.guild.text_channels:
        try:
            await channel.send(f"📢 {message}")
        except:
            continue
    await interaction.response.send_message("✅ Announcement sent to all text channels.", ephemeral=True)

bot.tree.add_command(ban)
bot.tree.add_command(kick)
bot.tree.add_command(mute)
bot.tree.add_command(unmute)
bot.tree.add_command(clear)
bot.tree.add_command(announce)

# --- Tickets ---

class TicketView(discord.ui.View):
    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, button: discord.ui.Button, interaction: discord.Interaction):
        if not feature_status.get("tickets", False):
            return await interaction.response.send_message("❌ Tickets are disabled.", ephemeral=True)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        channel = await interaction.guild.create_text_channel(name=f"ticket-{interaction.user.name}", overwrites=overwrites)
        await channel.send(f"{interaction.user.mention}, thanks for opening a ticket!")
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

@bot.command()
async def close(ctx):
    if not ctx.channel.name.startswith("ticket-"):
        return await ctx.send("❌ This is not a ticket channel.")
    await ctx.send("🛑 Closing ticket in 5 seconds...")
    await asyncio.sleep(5)
    await ctx.channel.delete()

@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📘 Help - All Commands", color=discord.Color.blurple())
    embed.add_field(name="🔧 Moderation", value="`/ban`, `/kick`, `/mute`, `/unmute`, `/clear`", inline=False)
    embed.add_field(name="🎟️ Tickets", value="`!close`", inline=False)
    embed.add_field(name="🛠️ Utility", value="`/announce`, `!setmaintmsg`, `!setrules`, `!rules`", inline=False)
    embed.add_field(name="⚙️ Owner Only", value="`!setmaintmsg`, `!setrules`", inline=False)
    embed.set_footer(text="Made by AASHIRWADGAMINGXD")
    await ctx.send(embed=embed)

# --- Maintenance Custom Message ---

@bot.command()
async def setmaintmsg(ctx, *, message: str):
    if ctx.author.id in ALLOWED_USERS:
        global maintenance_message
        maintenance_message = message
        await ctx.send("✅ Maintenance message updated.")
    else:
        await ctx.send("❌ You are not allowed to use this.")

# --- Rules ---

rules_message = "No rules have been set yet."

@bot.command()
async def setrules(ctx, *, message: str):
    global rules_message
    if ctx.author.id in ALLOWED_USERS:
        rules_message = message
        await ctx.send("✅ Rules updated.")
    else:
        await ctx.send("❌ You are not allowed to set rules.")

@bot.command()
async def rules(ctx):
    await ctx.send(f"📜 {rules_message}")

# --- Slash Command Force Sync (Optional) ---

@bot.command()
@commands.is_owner()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Synced {len(synced)} slash commands.")

# --- Error Handling ---

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Unknown command. Try `!help`.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❗ Missing required argument.")
    else:
        await ctx.send("⚠️ Something went wrong.")
        print(error)

# --- Start Bot ---

TOKEN = os.getenv("TOKEN")
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ No token provided.")
