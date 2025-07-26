import discord
from discord.ext import commands
from discord import app_commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.reactions = True

TOKEN = os.getenv("DISCORD_TOKEN")  # Store token in Railway secrets
GUILD_ID = YOUR_GUILD_ID  # Replace with your server ID

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ========== AUTORESPONDER ==========
auto_responses = {
    "hello": "Hi there!",
    "help": "Need help? Use /ticket!"
}

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    content = message.content.lower()
    for trigger, response in auto_responses.items():
        if trigger in content:
            await message.channel.send(response)
            break
    await bot.process_commands(message)

# ========== SLASH: KICK ==========
@tree.command(name="kick", description="Kick a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="Member to kick", reason="Reason")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"Kicked {member.mention} for {reason}")

# ========== SLASH: BAN ==========
@tree.command(name="ban", description="Ban a user", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(member="Member to ban", reason="Reason")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"Banned {member.mention} for {reason}")

# ========== SLASH: CLEAR ==========
@tree.command(name="clear", description="Clear messages", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(amount="Number of messages to delete")
async def clear(interaction: discord.Interaction, amount: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("You don't have permission!", ephemeral=True)
        return
    await interaction.channel.purge(limit=amount + 1)
    await interaction.response.send_message(f"Cleared {amount} messages", ephemeral=True)

# ========== REACTION ROLE ==========
@tree.command(name="reactionrole", description="Set a reaction role", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(role="Role to assign", emoji="Emoji to use")
async def reactionrole(interaction: discord.Interaction, role: discord.Role, emoji: str):
    msg = await interaction.channel.send(f"React with {emoji} to get the {role.mention} role!")
    await msg.add_reaction(emoji)

    def check(reaction, user):
        return str(reaction.emoji) == emoji and reaction.message.id == msg.id and not user.bot

    @bot.event
    async def on_reaction_add(reaction, user):
        if reaction.message.id == msg.id and str(reaction.emoji) == emoji:
            await user.add_roles(role)

    await interaction.response.send_message("Reaction role set!", ephemeral=True)

# ========== BASIC TICKET ==========
@tree.command(name="ticket", description="Create a ticket", guild=discord.Object(id=GUILD_ID))
async def ticket(interaction: discord.Interaction):
    view = discord.ui.View()
    button = discord.ui.Button(label="Open Ticket", style=discord.ButtonStyle.green)

    async def button_callback(interaction2: discord.Interaction):
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction2.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction2.user.name}",
            overwrites=overwrites
        )
        await interaction2.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)

    button.callback = button_callback
    view.add_item(button)
    await interaction.response.send_message("Click below to open a ticket", view=view, ephemeral=True)

# ========== READY ==========
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Logged in as {bot.user}!")

bot.run(TOKEN)
