import aiohttp

@bot.command()
async def aternos(ctx, *, server_name):
    await ctx.send("🔍 Checking Aternos server...")

    # Example API usage (You need your own API wrapper or parser)
    # This is a mockup
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.mcsrvstat.us/2/{server_name}.aternos.me") as resp:
            data = await resp.json()

    if data["online"]:
        await ctx.send(f"✅ Aternos server `{server_name}` is online with {data['players']['online']} players.")
    else:
        await ctx.send(f"❌ Aternos server `{server_name}` is offline.")
