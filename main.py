import discord
from discord.ext import commands
import os
from webserver import keep_alive

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

# Load cogs
initial_cogs = ["cogs.moderation", "cogs.tickets", "cogs.aternos"]
for cog in initial_cogs:
    bot.load_extension(cog)

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
