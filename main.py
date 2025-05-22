import discord
from discord.ext import commands
import os
import asyncio
import socket
import random
import json

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)
bot.remove_command("help")

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd)
    print(f"✅ Bot is online as {bot.user}")

# === Configuration ===
feature_status = {
    "welcome": False,
    "maintenance": False,
    "reaction_roles": True,
    "economy": False,
    "auto_moderation": True,
    "fun_commands": False,
    "utility_tools": False,
    "anime": True
}

OWNER_ID = 1217747285463531522
FRIEND_ID = 1244871880012206161
ALLOWED_USERS = [OWNER_ID, FRIEND_ID]
DASHBOARD_PASSWORD = "1Year"

eco_data = {}
zoo_data = {}
afk_data = {}

bad_words = ["teri maa ki", "bsk", "mck", "lund", "bsp"]
vc_bad_words = ["bc", "mc", "bsdk", "madarchod", "bhosdike"]

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
|| By AashirwadGamingXD ||
"""

# === Load & Save ===
def save_all_data():
    with open("economy.json", "w") as f:
        json.dump(eco_data, f)
    with open("zoo.json", "w") as f:
        json.dump(zoo_data, f)

def load_all_data():
    global eco_data, zoo_data
    try:
        with open("economy.json", "r") as f:
            eco_data = json.load(f)
    except:
        eco_data = {}
    try:
        with open("zoo.json", "r") as f:
            zoo_data = json.load(f)
    except:
        zoo_data = {}

load_all_data()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Auto moderation
    if feature_status["auto_moderation"]:
        for word in bad_words:
            if word in message.content.lower():
                await message.delete()
                await message.channel.send(f"🚫 {message.author.mention}, Don't abuse or you will be timed out.")
                return
        if message.channel.type == discord.ChannelType.voice:
            for word in vc_bad_words:
                if word in message.content.lower():
                    await message.delete()
                    await message.channel.send(f"🚫 {message.author.mention}, abusive language in VC is prohibited.")
                    return

    # AFK Notify
    for mention in message.mentions:
        if mention.id in afk_data:
            await message.channel.send(f"💤 {mention.display_name} is AFK: {afk_data[mention.id]}")

    if message.author.id in afk_data:
        del afk_data[message.author.id]
        await message.channel.send(f"👋 Welcome back {message.author.mention}, you are no longer AFK.")

    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if feature_status["welcome"]:
        channel = discord.utils.get(member.guild.text_channels, name="general")
        if channel:
            await channel.send(f"👋 Welcome {member.mention}!")

# === Commands ===
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📘 Help Menu", description="List of available commands", color=0x00ffcc)
    embed.add_field(name="Moderation", value="`ban`, `kick`, `mute`, `unmute`, `roleupdate`", inline=False)
    embed.add_field(name="Utilities", value="`ping`, `aternos_status`, `afk`", inline=False)
    embed.add_field(name="Economy", value="`daily`, `balance`, `sell`", inline=False)
    embed.add_field(name="Fun Games", value="`hunt`, `zoo`, `inventory`", inline=False)
    embed.add_field(name="Setup", value="`ticketsetup`, `reactionrole`", inline=False)
    embed.add_field(name="Dashboard", value="`dashboard`", inline=False)
    embed.add_field(name="Rules", value="`rules`", inline=False)
    embed.set_footer(text="Made by AASHIRWADGAMINGXD")
    await ctx.send(embed=embed)

@bot.command()
async def rules(ctx):
    await ctx.send(RULES_TEXT)

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
            await channel.send(f"🎫 Hello {interaction.user.mention}, support will assist you shortly.", view=CloseTicketView())

    class CloseTicketView(discord.ui.View):
        @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red)
        async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            if "ticket-" in interaction.channel.name:
                await interaction.channel.delete()

    await message.edit(view=TicketView())

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

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! `{latency}ms`")

@bot.command()
async def aternos_status(ctx, ip="yourserver.aternos.me"):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    try:
        socket.gethostbyname(ip)
        await ctx.send(f"🟢 Aternos Server `{ip}` is ONLINE (ping successful).")
    except socket.error:
        await ctx.send(f"🔴 Aternos Server `{ip}` is OFFLINE or unreachable.")

@bot.command()
async def daily(ctx):
    if not feature_status["economy"]: return await ctx.send("❌ Economy is disabled.")
    user_id = str(ctx.author.id)
    reward = random.randint(100, 500)
    eco_data[user_id] = eco_data.get(user_id, 0) + reward
    save_all_data()
    await ctx.send(f"💰 You received {reward} Coins today!")

@bot.command()
async def balance(ctx):
    if not feature_status["economy"]: return await ctx.send("❌ Economy is disabled.")
    coins = eco_data.get(str(ctx.author.id), 0)
    await ctx.send(f"💼 {ctx.author.mention}, you have `{coins}` cowoncy.")

@bot.command()
async def hunt(ctx):
    if not feature_status["fun_commands"]: return await ctx.send("❌ Fun Games are disabled.")
    animals = ["🦊 fox", "🐻 bear", "🐰 rabbit", "🦁 lion", "🐺 wolf"]
    caught = random.choice(animals)
    uid = str(ctx.author.id)
    zoo_data.setdefault(uid, []).append(caught)
    save_all_data()
    await ctx.send(f"🔫 You hunted and caught a {caught}!")

@bot.command()
async def sell(ctx):
    if not feature_status["fun_commands"]: return await ctx.send("❌ Fun Games are disabled.")
    uid = str(ctx.author.id)
    if uid not in zoo_data or not zoo_data[uid]:
        return await ctx.send("❌ You have no animals to sell!")
    sold_animal = zoo_data[uid].pop()
    reward = random.randint(50, 150)
    eco_data[uid] = eco_data.get(uid, 0) + reward
    save_all_data()
    await ctx.send(f"💵 You sold a {sold_animal} and earned {reward} cowoncy!")

@bot.command()
async def zoo(ctx):
    animals = zoo_data.get(str(ctx.author.id), [])
    if not animals:
        return await ctx.send("🦙 Your zoo is empty!")
    await ctx.send(f"🦁 Your zoo: {', '.join(animals)}")

@bot.command()
async def inventory(ctx):
    await zoo(ctx)

@bot.command()
async def dashboard(ctx):
    if ctx.author.id not in ALLOWED_USERS:
        return await ctx.send("❌ You are not allowed to access the dashboard.")

    await ctx.send("🔐 Please enter the dashboard password:")

    def check(msg): return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        if msg.content != DASHBOARD_PASSWORD:
            return await ctx.send("❌ Incorrect password.")
    except asyncio.TimeoutError:
        return await ctx.send("⌛ Timeout. Try again.")

    class DashboardView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            for key in feature_status:
                label = key.replace("_", " ").title()
                style = discord.ButtonStyle.green if feature_status[key] else discord.ButtonStyle.red
                self.add_item(self.make_toggle_button(label, key, style))

        def make_toggle_button(self, label, key, style):
            button = discord.ui.Button(label=label, style=style)

            async def callback(interaction: discord.Interaction):
                if interaction.user.id not in ALLOWED_USERS:
                    return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
                if key == "anime" and feature_status["anime"]:
                    role = discord.utils.get(interaction.guild.roles, name="Anime")
                    if not role:
                        role = await interaction.guild.create_role(name="Anime")
                    member = interaction.guild.get_member(interaction.user.id)
                    if role not in member.roles:
                        await member.add_roles(role)
                        await interaction.response.send_message("✨ You got the Anime role!", ephemeral=True)
                        return
                feature_status[key] = not feature_status[key]
                new_embed = build_dashboard_embed()
                new_view = DashboardView()
                await interaction.response.edit_message(embed=new_embed, view=new_view)

            button.callback = callback
            return button

    def build_dashboard_embed():
        embed = discord.Embed(title="🛠 Bot Dashboard", description="Toggle bot features:", color=0x00ff00)
        for feature, status in feature_status.items():
            display = "🟢 Enabled" if status else "🔴 Disabled"
            if feature == "anime": display += " (Gives role)"
            embed.add_field(name=feature.replace("_", " ").title(), value=display, inline=False)
        embed.set_footer(text="Made by AASHIRWADGAMINGXD")
        return embed

    embed = build_dashboard_embed()
    view = DashboardView()
    await ctx.send(embed=embed, view=view)

# === Role Restrictions ===
@bot.event
async def on_guild_role_create(role):
    restricted_names = ["indian army", "pakistan army", "india army"]
    if role.name.lower() in restricted_names:
        await role.delete()
        channel = discord.utils.get(role.guild.text_channels, name="general")
        if channel:
            await channel.send(f"🚫 Role `{role.name}` is not allowed and has been deleted.")

# === NEW: AFK Command ===
@bot.command()
async def afk(ctx, *, reason="AFK"):
    afk_data[ctx.author.id] = reason
    await ctx.send(f"💤 {ctx.author.mention} is now AFK: `{reason}`")

# === NEW: Role Update Command ===
@bot.command()
@commands.has_permissions(manage_roles=True)
async def roleupdate(ctx, role: discord.Role, new_name: str, hex_color: str):
    try:
        await role.edit(name=new_name, colour=discord.Colour(int(hex_color.replace("#", ""), 16)))
        await ctx.send(f"✅ Role updated to `{new_name}` with color `{hex_color}`")
    except Exception as e:
        await ctx.send(f"❌ Error updating role: {e}")

# === Start Bot ===
bot.run(os.getenv("TOKEN"))
