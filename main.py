import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
OWNER_ID = 1217747285463531522  # Replace with your ID
maintenance_mode = False  # Toggle this to True to enable maintenance


# ----------------- GLOBAL CHECK -----------------
@bot.check
async def global_check(ctx):
    if maintenance_mode and ctx.author.id != OWNER_ID:
        await ctx.send("🛠️ Bot is under maintenance. Please try again later.")
        return False
    return True


# ----------------- EVENTS -----------------
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Game("Under maintenance" if maintenance_mode else "Moderating server"))
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")


# ----------------- COMMANDS -----------------

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 Banned {member} | Reason: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 Kicked {member} | Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, *, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Added {role.name} to {member.mention}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"✅ Removed {role.name} from {member.mention}")

@bot.command()
async def afk(ctx, *, reason="AFK"):
    await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")


# ----------------- MAINTENANCE SLASH COMMAND -----------------

class Maintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="maintenance", description="Toggle maintenance mode")
    async def maintenance_toggle(self, interaction: discord.Interaction):
        global maintenance_mode
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ You are not authorized to use this.", ephemeral=True)

        maintenance_mode = not maintenance_mode
        await bot.change_presence(
            status=discord.Status.dnd
            activity=discord.Game("Bot is Under maintenance" if maintenance_mode else "Moderating")
        )
        await interaction.response.send_message(f"🔧 Maintenance mode is now {'ON' if maintenance_mode else 'OFF'}.")

async def setup(bot):
    await bot.add_cog(Maintenance(bot))


@bot.event
async def setup_hook():
    await bot.add_cog(Maintenance(bot))


# ----------------- ERROR HANDLING -----------------

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 You don’t have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Missing arguments.")
    else:
        await ctx.send(f"❌ Error: {error}")


# ----------------- RUN BOT -----------------

TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
