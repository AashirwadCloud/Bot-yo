    import discord
    from discord.ext import commands
    from discord.ui import Button, View

    class Tickets(commands.Cog):
        def __init__(self, bot):
            self.bot = bot

        @commands.command()
        async def ticketsetup(self, ctx):
            button = Button(label="Create Ticket", style=discord.ButtonStyle.green)

            async def callback(interaction):
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                    interaction.user: discord.PermissionOverwrite(read_messages=True)
                }
                ticket = await ctx.guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
                await ticket.send(f"{interaction.user.mention} Welcome to your ticket!")
                await interaction.response.send_message("Ticket created!", ephemeral=True)

            button.callback = callback
            view = View()
            view.add_item(button)
            await ctx.send("Press the button to create a ticket.", view=view)

    def setup(bot):
        bot.add_cog(Tickets(bot))
