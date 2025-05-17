import discord
from discord.ext import commands
from discord.ui import View, Button
from config import OWNER_IDS

class Dashboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.maintenance_mode = False
        self.welcome_cog = None
        self.moderation_cog = None

    @commands.Cog.listener()
    async def on_ready(self):
        # Cache cogs for toggle usage
        self.welcome_cog = self.bot.get_cog("Welcome")
        self.moderation_cog = self.bot.get_cog("Moderation")

    @commands.command()
    async def dashboard(self, ctx):
        """Show dashboard, owner/admin only."""
        if ctx.author.id not in OWNER_IDS and not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ You do not have permission to use the dashboard.")

        embed = discord.Embed(title="Bot Dashboard", description="Toggle features and maintenance mode.", color=0x00ff00)
        embed.add_field(name="Maintenance Mode", value=str(self.maintenance_mode))
        welcome_status = getattr(self.welcome_cog, "enabled", False)
        embed.add_field(name="Welcome Messages", value=str(welcome_status))
        mod_status = getattr(self.moderation_cog, "maintenance", False)
        embed.add_field(name="Moderation Commands Maintenance", value=str(mod_status))

        view = DashboardView(self)
        await ctx.send(embed=embed, view=view)

class DashboardView(View):
    def __init__(self, dashboard_cog):
        super().__init__(timeout=None)
        self.dashboard_cog = dashboard_cog

    @discord.ui.button(label="Toggle Maintenance", style=discord.ButtonStyle.red)
    async def toggle_maintenance(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.dashboard_cog.maintenance_mode = not self.dashboard_cog.maintenance_mode
        state = "enabled" if self.dashboard_cog.maintenance_mode else "disabled"
        # Also apply maintenance to all cogs (for demo)
        if self.dashboard_cog.moderation_cog:
            self.dashboard_cog.moderation_cog.maintenance = self.dashboard_cog.maintenance_mode
        if self.dashboard_cog.welcome_cog:
            self.dashboard_cog.welcome_cog.enabled = not self.dashboard_cog.maintenance_mode  # Disable welcome when maintenance on

        await interaction.response.send_message(f"Maintenance mode {state}.", ephemeral=True)

    @discord.ui.button(label="Toggle Welcome Msg", style=discord.ButtonStyle.green)
    async def toggle_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.dashboard_cog.welcome_cog:
            self.dashboard_cog.welcome_cog.enabled = not self.dashboard_cog.welcome_cog.enabled
            state = "enabled" if self.dashboard_cog.welcome_cog.enabled else "disabled"
            await interaction.response.send_message(f"Welcome messages {state}.", ephemeral=True)
        else:
            await interaction.response.send_message("Welcome cog not loaded.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Dashboard(bot))
