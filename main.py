import os
import discord
import json
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ===============================
# CONFIGURATION
# ===============================
DATA_FILE = "bot_data.json"
BOT_OWNER_ID = 1217747285463531522  # Replace with your ID

# ===============================
# INITIAL LOAD / SAVE
# ===============================
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"toggles": {}, "ticket_config": {}, "reaction_roles": {}}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ===============================
# DASHBOARD COMMAND
# ===============================
@bot.command()
async def dashboard(ctx):
    if ctx.author.id != BOT_OWNER_ID:
        return await ctx.send("❌ You are not authorized.")

    toggles = data.get("toggles", {})
    features = ["Moderation", "Fun", "Tickets", "ReactionRoles"]
    
    view = View()
    for feature in features:
        enabled = toggles.get(feature, False)
        btn = Button(label=f"{feature} {'✅' if enabled else '❌'}",
                     style=discord.ButtonStyle.green if enabled else discord.ButtonStyle.red,
                     custom_id=f"toggle_{feature}")
        view.add_item(btn)

    embed = discord.Embed(title="🛠 Bot Feature Dashboard",
                          description="Toggle features below.",
                          color=0x00ffcc)
    await ctx.send(embed=embed, view=view)

# ===============================
# BUTTON HANDLER (Dashboard + ReactionRoles)
# ===============================
@bot.event
async def on_interaction(interaction: discord.Interaction):
    custom_id = interaction.data.get("custom_id")

    # Toggle Features
    if custom_id and custom_id.startswith("toggle_"):
        feature = custom_id.replace("toggle_", "")
        data["toggles"][feature] = not data["toggles"].get(feature, False)
        save_data(data)
        await interaction.response.edit_message(view=await generate_dashboard_view())
        return

    # Reaction Role button
    if custom_id and custom_id.startswith("rr_"):
        role_id = int(custom_id.split("_")[1])
        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message("Role not found.", ephemeral=True)

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ Role {role.name} removed.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Role {role.name} added.", ephemeral=True)

# ===============================
# TICKET SETUP SYSTEM
# ===============================
@bot.command()
@commands.has_permissions(administrator=True)
async def setticket(ctx):
    class TicketSetup(Modal, title="Ticket System Setup"):
        category_id = TextInput(label="Category ID for tickets", placeholder="1234567890", required=True)
        support_role = TextInput(label="Support Role ID", placeholder="1234567890", required=True)
        ticket_message = TextInput(label="Ticket Message", placeholder="Click to create ticket!", required=True)

        async def on_submit(self, interaction: discord.Interaction):
            guild_id = str(interaction.guild.id)
            data["ticket_config"][guild_id] = {
                "category_id": int(self.category_id.value),
                "support_role": int(self.support_role.value),
                "ticket_message": self.ticket_message.value
            }
            save_data(data)
            await interaction.response.send_message("✅ Ticket system configured!", ephemeral=True)

    await ctx.send_modal(TicketSetup())

@bot.command()
async def setticketbutton(ctx):
    guild_id = str(ctx.guild.id)
    config = data.get("ticket_config", {}).get(guild_id)
    if not config:
        return await ctx.send("❌ Ticket system is not configured.")

    embed = discord.Embed(title="🎫 Support Ticket",
                          description=config["ticket_message"],
                          color=0x3498db)
    view = View()
    view.add_item(Button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket"))
    await ctx.send(embed=embed, view=view)

# ===============================
# HANDLE TICKET BUTTON
# ===============================
@bot.event
async def on_button_click(interaction: discord.Interaction):
    if interaction.custom_id != "create_ticket":
        return

    guild_id = str(interaction.guild.id)
    config = data["ticket_config"].get(guild_id)
    if not config:
        return await interaction.response.send_message("❌ Ticket system not configured.", ephemeral=True)

    category = interaction.guild.get_channel(config["category_id"])
    support_role = interaction.guild.get_role(config["support_role"])
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        support_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    ticket_channel = await interaction.guild.create_text_channel(
        name=f"ticket-{interaction.user.name}",
        category=category,
        overwrites=overwrites
    )
    await ticket_channel.send(f"{interaction.user.mention} ticket created! {support_role.mention}")
    await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

# ===============================
# REACTION ROLE SETUP
# ===============================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def createreactionrole(ctx, role: discord.Role, *, label):
    view = View()
    button = Button(label=label, style=discord.ButtonStyle.primary, custom_id=f"rr_{role.id}")
    view.add_item(button)

    embed = discord.Embed(title="🎭 Get Your Role",
                          description=f"Click the button to toggle the role: {role.name}",
                          color=discord.Color.purple())
    await ctx.send(embed=embed, view=view)

# ===============================
# DASHBOARD VIEW GENERATOR
# ===============================
async def generate_dashboard_view():
    toggles = data.get("toggles", {})
    features = ["Moderation", "Fun", "Tickets", "ReactionRoles"]

    view = View()
    for feature in features:
        enabled = toggles.get(feature, False)
        btn = Button(label=f"{feature} {'✅' if enabled else '❌'}",
                     style=discord.ButtonStyle.green if enabled else discord.ButtonStyle.red,
                     custom_id=f"toggle_{feature}")
        view.add_item(btn)
    return view

# ===============================
# BOT START
# ===============================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

bot.run(os.getenv("TOKEN"))
