import discord
from discord.ext import commands
import random
import os
import yt_dlp
import asyncio
from pytube import YouTube
import json

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Constants
TICKET_FILE = '/app/data/tickets.json'
RESTRICTED_ROLE_NAMES = ['india army', 'pakistan army', 'badword1', 'badword2', 'offensive term']
YOUR_REACTION_MESSAGE_ID = 0  # Replace with actual message ID
YOUR_ROLE_ID = 0  # Replace with actual role ID

# Music queue
music_queues = {}

# File handling for tickets
def load_tickets():
    if not os.path.exists(TICKET_FILE):
        return {}
    with open(TICKET_FILE, 'r') as f:
        return json.load(f)

def save_tickets(data):
    with open(TICKET_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Bot events
@bot.event
async def on_ready():
    os.makedirs('/app/data', exist_ok=True)
    if not os.path.exists(TICKET_FILE):
        save_tickets({})
    print(f'Logged in as {bot.user.name} at {discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}')
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Game(name="Made by AashirwadGamingXD")
    )

@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(f'Welcome {member.mention} to {member.guild.name}! Enjoy your stay!')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member:
        return

    tickets = load_tickets()
    ticket_message_id = tickets.get(str(payload.guild_id), {}).get('message_id')
    if payload.message_id == ticket_message_id and str(payload.emoji) == '📩':
        await create_ticket_channel(member, guild)
    elif payload.message_id == YOUR_REACTION_MESSAGE_ID and str(payload.emoji) == '✅':
        role = guild.get_role(YOUR_ROLE_ID)
        if role:
            await member.add_roles(role)
            await member.send(f'You received the {role.name} role!')

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id != YOUR_REACTION_MESSAGE_ID or str(payload.emoji) != '✅':
        return
    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return
    role = guild.get_role(YOUR_ROLE_ID)
    if role:
        await member.remove_roles(role)
        await member.send(f'The {role.name} role was removed.')

@bot.event
async def on_guild_role_create(role):
    if role.name.lower() in [name.lower() for name in RESTRICTED_ROLE_NAMES]:
        await role.delete(reason="Restricted role name detected")
        channel = role.guild.system_channel
        if channel:
            await channel.send(f"Role creation blocked: '{role.name}' is a restricted name.")

# Ticket helper function
async def create_ticket_channel(member, guild):
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.owner: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    channel = await guild.create_text_channel(
        f'ticket-{member.name}-{member.discriminator}',
        overwrites=overwrites,
        reason=f'Ticket for {member}'
    )
    embed = discord.Embed(
        title="Support Ticket",
        description=f"Welcome {member.mention}! Describe your issue, and an admin will assist you.",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    close_button = discord.ui.Button(label="Close Ticket", style=discord.ButtonStyle.red)
    
    async def close_callback(interaction):
        if interaction.user.guild_permissions.manage_channels:
            await interaction.channel.delete(reason="Ticket closed")
            await interaction.user.send(f'Ticket {interaction.channel.name} closed.')
        else:
            await interaction.response.send_message("Only admins can close tickets!", ephemeral=True)
    
    close_button.callback = close_callback
    view = discord.ui.View()
    view.add_item(close_button)
    
    await channel.send(embed=embed, view=view)
    await channel.send(f'{member.mention}, your ticket has been created!')

# Commands
@bot.hybrid_command(description="Check bot latency")
async def ping(ctx):
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.hybrid_command(description="Kick a member from the server")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason: str = None):
    await member.kick(reason=reason)
    await ctx.send(f'Kicked {member.mention} for reason: {reason or "No reason provided"}')

@bot.hybrid_command(description="Ban a member from the server")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason: str = None):
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention} for reason: {reason or "No reason provided"}')

@bot.hybrid_command(description="Clear a number of messages")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'Cleared {amount} messages', delete_after=5)

@bot.hybrid_command(description="Roll a die with specified sides")
async def roll(ctx, sides: int = 6):
    result = random.randint(1, sides)
    await ctx.send(f'You rolled a {result} on a {sides}-sided die!')

@bot.hybrid_command(description="Display server information")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"{guild.name} Info", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Display user information")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"{member.name} Info", color=discord.Color.green(), timestamp=discord.utils.utcnow())
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Roles", value=", ".join([r.name for r in member.roles[1:]]), inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    await ctx.send(embed=embed)

@bot.hybrid_command(description="Send an announcement to a channel")
@commands.has_permissions(manage_messages=True)
async def announce(ctx, channel: discord.TextChannel, *, message: str):
    embed = discord.Embed(title="Announcement", description=message, color=discord.Color.red(), timestamp=discord.utils.utcnow())
    embed.set_footer(text=f"Announced by {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await channel.send(embed=embed)
    await ctx.send(f'Announcement sent to {channel.mention}')

@bot.hybrid_command(description="Set up a ticket message with reaction")
@commands.has_permissions(manage_channels=True)
async def ticketsetup(ctx):
    embed = discord.Embed(
        title="Support Tickets",
        description="React with 📩 to open a support ticket!",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )
    message = await ctx.send(embed=embed)
    await message.add_reaction('📩')
    tickets = load_tickets()
    tickets[str(ctx.guild.id)] = {'message_id': message.id}
    save_tickets(tickets)
    await ctx.send("Ticket system set up successfully!", delete_after=5)

@bot.hybrid_command(description="Create a support ticket")
async def ticket(ctx):
    await create_ticket_channel(ctx.author, ctx.guild)
    await ctx.send("Your ticket has been created!", ephemeral=True)

@bot.hybrid_command(description="Close a ticket channel")
@commands.has_permissions(manage_channels=True)
async def close(ctx):
    if 'ticket-' in ctx.channel.name.lower():
        await ctx.channel.delete(reason="Ticket closed")
        await ctx.author.send(f'Ticket {ctx.channel.name} closed.')
    else:
        await ctx.send("This command can only be used in a ticket channel!", ephemeral=True)

# Music commands
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'cookiefile': '/app/data/cookies.txt'  # Path to cookies file
}

ffmpeg_options = {'options': '-vn'}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            if 'entries' in data:
                data = data['entries'][0]
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        except Exception as e:
            raise commands.CommandInvokeError(f"Failed to fetch audio: {str(e)}")

@bot.hybrid_command(description="Play a song from a YouTube URL")
async def play(ctx, url: str):
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel to play music!")
        return
    channel = ctx.author.voice.channel
    if ctx.guild.id not in music_queues:
        music_queues[ctx.guild.id] = []
    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            music_queues[ctx.guild.id].append(player)
            voice_client = ctx.guild.voice_client or await channel.connect()
            if not voice_client.is_playing():
                voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(ctx)))
                await ctx.send(f'Now playing: {player.title}')
            else:
                await ctx.send(f'Added to queue: {player.title}')
        except Exception as e:
            await ctx.send(f"Error playing song: {str(e)}")

async def play_next(ctx):
    if ctx.guild.id not in music_queues or not music_queues[ctx.guild.id]:
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect()
        return
    player = music_queues[ctx.guild.id].pop(0)
    ctx.guild.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(ctx)))
    await ctx.send(f'Now playing: {player.title}')

@bot.hybrid_command(description="Pause the current song")
async def pause(ctx):
    if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
        ctx.guild.voice_client.pause()
        await ctx.send("Paused the music.")
    else:
        await ctx.send("No music is playing!")

@bot.hybrid_command(description="Resume the paused song")
async def resume(ctx):
    if ctx.guild.voice_client and ctx.guild.voice_client.is_paused():
        ctx.guild.voice_client.resume()
        await ctx.send("Resumed the music.")
    else:
        await ctx.send("No music is paused!")

@bot.hybrid_command(description="Stop the music and disconnect")
async def stop(ctx):
    if ctx.guild.voice_client:
        music_queues[ctx.guild.id].clear()
        ctx.guild.voice_client.stop()
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Stopped the music and disconnected.")
    else:
        await ctx.send("Not connected to a voice channel!")

@bot.hybrid_command(description="Show the music queue")
async def queue(ctx):
    if ctx.guild.id not in music_queues or not music_queues[ctx.guild.id]:
        await ctx.send("The queue is empty!")
        return
    embed = discord.Embed(title="Music Queue", color=discord.Color.purple(), timestamp=discord.utils.utcnow())
    for i, player in enumerate(music_queues[ctx.guild.id], 1):
        embed.add_field(name=f"{i}. {player.title}", value=player.url, inline=False)
    await ctx.send(embed=embed)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument! Check the command syntax.")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"An error occurred while executing the command: {error.original}")
    else:
        await ctx.send(f"An error occurred: {error}")

# Run bot
bot.run(os.getenv('TOKEN'))
