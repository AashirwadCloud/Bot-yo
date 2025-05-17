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
    "maintenance": False
}

# Dashboard password system
OWNER_ID = 1217747285463531522 ,  1244871880012206161 # Replace with your user ID
DASHBOARD_PASSWORD = "XD"  # Change this password

# Welcome
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
async def ticket(ctx):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    message = await ctx.send("📩 Click the button below to create a ticket.")

    class TicketButton(discord.ui.View):
        @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green)
        async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True)
            }
            channel = await ctx.guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
            await channel.send(f"🎫 Hello {interaction.user.mention}, be patient. Our staff will be seen your ticket.")

    await message.edit(view=TicketButton())

# Aternos Status Checker (Simulated IP Ping)
@bot.command()
async def aternos_status(ctx, ip="yourserver.aternos.me"):
    if feature_status["maintenance"]: return await ctx.send("🛠 Maintenance mode.")
    try:
        socket.gethostbyname(ip)
        await ctx.send(f"🟢  Server `{ip}` is ONLINE *** You Can Play ***.")
    except socket.error:
        await ctx.send(f"🔴 Aternos Server `{ip}` is OFFLINE You Can't Play.")

# Dashboard Command (password-protected)
@bot.command()
async def dashboard(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("❌ You Are Not Admin.")
    
    await ctx.send("🔐 Pls Enter You Dash PassWord")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        if msg.content != DASHBOARD_PASSWORD:
            return await ctx.send("❌ Incorrect password.")
    except asyncio.TimeoutError:
        return await ctx.send("⌛ Timeout. Try again.")

    embed = discord.Embed(title="🛠 Bot Dashboard", description="Toggle features below", color=0x00ff00)
    embed.add_field(name="Welcome Message", value=str(feature_status["welcome"]), inline=False)
    embed.add_field(name="Maintenance Mode", value=str(feature_status["maintenance"]), inline=False)
    embed.set_footer(text="Made by AASHIRWADGAMINGXD")

    view = discord.ui.View()

    class ToggleFeature(discord.ui.Button):
        def __init__(self, feature):
            super().__init__(label=f"Toggle {feature}", style=discord.ButtonStyle.primary)
            self.feature = feature

        async def callback(self, interaction):
            if interaction.user.id != OWNER_ID:
                return await interaction.response.send_message("❌ Unauthorized", ephemeral=True)
            feature_status[self.feature] = not feature_status[self.feature]
            await interaction.response.edit_message(embed=discord.Embed(
                title="🛠 Bot Dashboard (V1)",
                description="Toggle features below",
                color=0x00ff00
            ).add_field(name="Welcome Message", value=str(feature_status["welcome"]), inline=False)
             .add_field(name="Maintenance Mode", value=str(feature_status["maintenance"]), inline=False)
             .set_footer(text="Made by AASHIRWADGAMINGXD"))

    view.add_item(ToggleFeature("welcome"))
    view.add_item(ToggleFeature("maintenance"))

    await ctx.send(embed=embed, view=view)

# Start Bot
bot.run(os.getenv("TOKEN"))
