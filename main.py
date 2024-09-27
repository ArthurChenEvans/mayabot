    c.execute('''CREATE TABLE IF NOT EXISTS deleted_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  guild_id INTEGER,
                  channel_id INTEGER,
                  content TEXT,
                  deleted_at TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.tree.sync()
    print("Slash commands synced")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

async def setup(bot):
    await setup_story_game(bot)
    await setup_snipe_cog(bot)
    await setup_chatgpt(bot)
    await setup_health(bot)

async def main():
    async with bot:
        await setup(bot)
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())