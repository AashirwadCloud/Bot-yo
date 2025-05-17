import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Config toggles
feature_status = {
    "welcome": True,
    "maintenance": False
}

@bot.event
async def on_ready():
    print(f"✅ Bot is online as {bot.user}")

@bot.event
async def on_member_join(member):
    if feature_status["welcome"]:
        channel = discord.utils.get(member.guild.text_channels, name="general")
        if channel:
            await channel.send(f"👋 Welcome {member.mention}!")

# ----------------- Moderation -----------------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if feature_status["maintenance"]: return await ctx.send("🛠 Bot is in maintenance mode.")
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member} has been banned. Reason: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if feature_status["maintenance"]: return await ctx.send("🛠 Bot is in maintenance mode.")
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member} has been kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    if feature_status["maintenance"]: return await ctx.send("🛠 Bot is in maintenance mode.")
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
    if feature_status["maintenance"]: return await ctx.send("🛠 Bot is in maintenance mode.")
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f"🔊 {member} has been unmuted.")
    else:
        await ctx.send("User is not muted.")

# ----------------- Ticket System -----------------
@bot.command()
async def ticket(ctx):
    if feature_status["maintenance"]: return await ctx.send("🛠 Bot is in maintenance mode.")
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }
    channel = await ctx.guild.create_text_channel(f"ticket-{ctx.author.name}", overwrites=overwrites)
    await channel.send(f"🎫 Hello {ctx.author.mention}, staff will assist you shortly.")

# ----------------- Aternos Status -----------------
@bot.command()
async def aternos_status(ctx):
    if feature_status["maintenance"]: return await ctx.send("🛠 Bot is in maintenance mode.")
    await ctx.send("🟢 Aternos server is online with 2/10 players connected (simulated).")

# ----------------- Dashboard (Toggle Feature) -----------------
@bot.command()
@commands.has_permissions(administrator=True)
async def dashboard(ctx):
    embed = discord.Embed(title="🔧 Bot Dashboard", description="Toggle bot features below", color=0x00ff00)
    embed.add_field(name="Welcome Message", value=str(feature_status["welcome"]), inline=False)
    embed.add_field(name="Maintenance Mode", value=str(feature_status["maintenance"]), inline=False)

    view = discord.ui.View()

    class ToggleButton(discord.ui.Button):
        def __init__(self, feature):
            label = f"Toggle {feature}"
            super().__init__(label=label, style=discord.ButtonStyle.primary)
            self.feature = feature

        async def callback(self, interaction):
            feature_status[self.feature] = not feature_status[self.feature]
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="🔧 Bot Dashboard (Updated)",
                    description="Toggle bot features below",
                    color=0x00ff00
                ).add_field(name="Welcome Message", value=str(feature_status["welcome"]), inline=False)
                 .add_field(name="Maintenance Mode", value=str(feature_status["maintenance"]), inline=False),
                view=view
            )

    view.add_item(ToggleButton("welcome"))
    view.add_item(ToggleButton("maintenance"))

    await ctx.send(embed=embed, view=view)

# ----------------- Start Bot -----------------
bot.run(os.getenv("TOKEN"))
